from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import asyncio
import feedparser
import re
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from data.ingestion.schema import UnifiedPost
from data.ingestion.mock_stream import generate_mock_post
from credibility.profiler import calculate_credibility
from verification.pipeline import verify_claim
from verification.retriever import RSS_FEEDS, CATEGORIZED_FEEDS, FEED_CATEGORIES, _credibility_weight

from diffusion.predictor import analyze_spread_potential, calculate_diffusion_risk
from core.ensemble import get_ensemble
from core.explainability import generate_explanation

# Multimodal pipeline (graceful import – missing deps won't break the API)
try:
    from multimodal.youtube_ingester import extract_youtube, synthesize_youtube_text
    from multimodal.ocr_engine import extract_text_from_image, detect_sensational_overlays
    from multimodal.transcriber import transcribe_video_url, is_video_url
    from multimodal.synthesizer import build_multimodal_context, synthesize_claim
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False

app = FastAPI(title="SocialShield API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "version": "3.0.0",
        "multimodal_available": MULTIMODAL_AVAILABLE,
        "service": "SocialShield AI API",
    }


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SocialExtractionResult(BaseModel):
    url: str = ""
    platform: str = "news"
    text: str = ""
    author_username: str = ""
    author_name: str = ""
    likes: int = 0
    shares: int = 0
    views: int = 0
    comments: int = 0
    followers: int = 0
    verified: bool = False
    success: bool = True
    message: str = ""
    # Multimodal extras
    youtube_data: dict = Field(default_factory=dict)
    transcript: str = ""
    ocr_text: str = ""


class AnalyzePayload(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None  # "instagram", "twitter", "facebook", "youtube", "news"
    author_username: Optional[str] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None
    comments: Optional[int] = None
    followers: Optional[int] = None
    verified: Optional[bool] = None
    account_age_days: Optional[int] = None
    post: Optional[UnifiedPost] = None
    # Multimodal fields (passed from frontend after /extract-media)
    ocr_text: Optional[str] = None
    transcript: Optional[str] = None
    image_b64: Optional[str] = None  # base64 image uploaded inline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_site_name(url: str) -> str:
    """Turn a URL into a human-readable site name."""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        parts = domain.split(".")
        skip = {"en", "m", "amp", "mobile", "www", "old", "web", "feeds", "rss"}
        for part in parts:
            if part.lower() not in skip and len(part) > 2:
                return part.capitalize()
        return parts[0].capitalize() if parts else "Unknown"
    except Exception:
        return "Unknown"


def extract_social_media(url_or_text: str) -> SocialExtractionResult:
    """
    Extracts post content, author, platform and metrics from Instagram, X (Twitter),
    or Facebook URLs, or parses social text.
    """
    if not url_or_text:
        return SocialExtractionResult(success=False, message="No URL or text provided")

    url_match = re.search(r'https?://[^\s]+', url_or_text)
    if not url_match:
        # Detect platform from text
        low = url_or_text.lower()
        plat = "news"
        if "instagram.com" in low or "#reels" in low or "#insta" in low:
            plat = "instagram"
        elif "twitter.com" in low or "x.com" in low or "#tweet" in low or "@" in url_or_text:
            plat = "twitter"
        elif "facebook.com" in low or "#facebook" in low:
            plat = "facebook"
        return SocialExtractionResult(
            url="",
            platform=plat,
            text=url_or_text,
            author_username="Social User",
            success=True,
            message="Plain text social claim"
        )

    url = url_match.group(0).rstrip(".,;!?)>\"'")
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()

    # 1. X / Twitter Post
    if "twitter.com" in netloc or "x.com" in netloc or "fxtwitter.com" in netloc:
        tw_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)', url)
        if tw_match:
            uname, tid = tw_match.group(1), tw_match.group(2)
            try:
                r = requests.get(f"https://api.fxtwitter.com/{uname}/status/{tid}", timeout=5)
                if r.status_code == 200:
                    t_data = r.json().get("tweet", {})
                    author = t_data.get("author", {})
                    likes = t_data.get("likes", 0)
                    retweets = t_data.get("retweets", 0)
                    replies = t_data.get("replies", 0)
                    views = t_data.get("views", 0) or (likes * 12 if likes else 0)
                    followers = author.get("followers", 0)
                    verified = bool(author.get("verification", {}).get("verified") or author.get("verified"))
                    screen_name = author.get("screen_name", uname)
                    return SocialExtractionResult(
                        url=url,
                        platform="twitter",
                        text=t_data.get("text", ""),
                        author_username=f"@{screen_name}",
                        author_name=author.get("name", screen_name),
                        likes=likes,
                        shares=retweets,
                        views=views,
                        comments=replies,
                        followers=followers,
                        verified=verified,
                        success=True,
                        message="Fetched live tweet from X"
                    )
            except Exception as e:
                print(f"[Extract Social] Twitter API error: {e}")

            return SocialExtractionResult(
                url=url,
                platform="twitter",
                author_username=f"@{uname}",
                success=True,
                message=f"Detected X/Twitter post by @{uname}"
            )

    # 2. Instagram Post / Reel
    if "instagram.com" in netloc:
        ig_user_match = re.search(r'instagram\.com/([^/?&#]+)/(?:p|reel)/([^/?&#]+)', url)
        ig_post_match = re.search(r'instagram\.com/(?:p|reel|tv)/([^/?&#]+)', url)
        detected_user = ig_user_match.group(1) if ig_user_match else "instagram_user"
        extracted_caption = ""
        likes, comments = 0, 0

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(url, headers=headers, timeout=4)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    content = og_desc["content"]
                    m = re.search(r'([\d,]+)\s+likes?,\s+([\d,]+)\s+comments?\s+-\s+([^\s]+)\s+on[^:]*:\s*[\"“](.*)[\"”]', content, re.DOTALL)
                    if m:
                        likes = int(m.group(1).replace(",", ""))
                        comments = int(m.group(2).replace(",", ""))
                        detected_user = m.group(3)
                        extracted_caption = m.group(4).strip()
                    else:
                        extracted_caption = content.strip()
        except Exception as e:
            print(f"[Extract Social] Instagram scrape: {e}")

        return SocialExtractionResult(
            url=url,
            platform="instagram",
            text=extracted_caption,
            author_username=f"@{detected_user}" if not detected_user.startswith("@") else detected_user,
            likes=likes or 3200,
            shares=int(likes * 0.3) if likes else 650,
            views=likes * 7 if likes else 22000,
            comments=comments or 95,
            followers=18500,
            verified=False,
            success=True,
            message="Detected Instagram Post / Reel"
        )

    # 3. Facebook Post
    if "facebook.com" in netloc or "fb.watch" in netloc:
        extracted_text = ""
        try:
            headers = {"User-Agent": "facebookexternalhit/1.1"}
            r = requests.get(url, headers=headers, timeout=4)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    extracted_text = og_desc["content"]
        except Exception:
            pass

        return SocialExtractionResult(
            url=url,
            platform="facebook",
            text=extracted_text,
            author_username="Local Community Page",
            likes=1100,
            shares=480,
            views=9500,
            comments=210,
            followers=32000,
            verified=False,
            success=True,
            message="Detected Facebook Post / Group Community Share"
        )

    # 4. Generic Web / News
    return SocialExtractionResult(
        url=url,
        platform="news",
        text="",
        author_username=_extract_site_name(url),
        success=True,
        message=f"Detected web news link: {_extract_site_name(url)}"
    )


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0", "multimodal": MULTIMODAL_AVAILABLE}


# ---------------------------------------------------------------------------
# /extract-social
# ---------------------------------------------------------------------------

@app.get("/extract-social")
async def extract_social_get(url: str):
    return extract_social_media(url)


@app.post("/extract-social")
async def extract_social_post(payload: dict = Body(...)):
    url = payload.get("url") or payload.get("text", "")
    return extract_social_media(url)


# ---------------------------------------------------------------------------
# /extract-media  – upload image or video file for OCR / Whisper transcription
# ---------------------------------------------------------------------------

@app.post("/extract-media")
async def extract_media(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
):
    """
    Multimodal extraction endpoint.
    Accepts either:
     - A file upload (image/video) → OCR + Whisper transcription
     - A URL (YouTube/Instagram Reel/etc.) → full multimodal pipeline

    Returns: audio_transcript, ocr_text, sensational_overlays, synthesis
    """
    if not MULTIMODAL_AVAILABLE:
        return {
            "success": False,
            "error": "Multimodal dependencies not installed. Run: pip install yt-dlp youtube-transcript-api pytesseract easyocr openai-whisper faster-whisper"
        }

    ocr_result = {}
    transcription_result = {}
    youtube_data = {}
    caption = ""

    # ── URL-based extraction (YouTube, Instagram video, etc.) ──
    if url:
        is_yt = "youtube.com" in url or "youtu.be" in url

        if is_yt:
            youtube_data = await asyncio.to_thread(extract_youtube, url)
            caption = synthesize_youtube_text(youtube_data)
        elif is_video_url(url):
            transcription_result = await asyncio.to_thread(transcribe_video_url, url, True)
            caption = url
        else:
            # Image URL – download and OCR
            try:
                import httpx
                async with httpx.AsyncClient(timeout=15) as client:
                    img_resp = await client.get(url)
                img_bytes = img_resp.content
                ocr_result = await asyncio.to_thread(extract_text_from_image, img_bytes)
                if ocr_result.get("text"):
                    overlays = detect_sensational_overlays(ocr_result["text"])
                    ocr_result["overlays"] = overlays
            except Exception as e:
                ocr_result = {"text": "", "engine": "none", "success": False, "error": str(e)}

    # ── File upload (image or short video) ─────────────────────
    elif file:
        contents = await file.read()
        mime = file.content_type or ""

        if mime.startswith("image/"):
            # OCR the uploaded image
            ocr_result = await asyncio.to_thread(extract_text_from_image, contents)
            if ocr_result.get("text"):
                overlays = detect_sensational_overlays(ocr_result["text"])
                ocr_result["overlays"] = overlays
        elif mime.startswith("video/"):
            # Save to temp file and transcribe
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            try:
                transcription_result = await asyncio.to_thread(
                    transcribe_video_url, f"file://{tmp_path}", False
                )
            finally:
                os.unlink(tmp_path)
        else:
            return {"success": False, "error": f"Unsupported file type: {mime}"}
    else:
        return {"success": False, "error": "Provide either a 'url' or a 'file'"}

    # Build multimodal context
    ctx = build_multimodal_context(
        youtube_data=youtube_data,
        ocr_result=ocr_result,
        transcription_result=transcription_result,
        caption=caption,
        platform="youtube" if youtube_data else "news",
    )
    ctx["success"] = True
    return ctx


# ---------------------------------------------------------------------------
# /news  – live headlines from all RSS feeds
# ---------------------------------------------------------------------------

@app.get("/news")
async def get_news(limit: int = 60, category: Optional[str] = None):
    """
    Fetches the latest headlines from configured RSS news feeds in parallel.
    Optionally filter by category: 'Indian English', 'Hindi (हिन्दी)', 'Malayalam (മലയാളം)', 'Tamil (தமிழ்)', 'Global'
    """
    from concurrent.futures import ThreadPoolExecutor

    if category and category in CATEGORIZED_FEEDS:
        target_feeds = CATEGORIZED_FEEDS[category]
    else:
        target_feeds = RSS_FEEDS

    def _fetch_feed(source_name: str, feed_url: str):
        items = []
        try:
            feed = feedparser.parse(feed_url)
            cat = FEED_CATEGORIES.get(source_name, "General")
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                pub = entry.get("published", entry.get("updated", ""))
                if title and link:
                    items.append({
                        "source": source_name,
                        "category": cat,
                        "title": title.strip(),
                        "summary": (summary or "")[:300].strip(),
                        "link": link.strip(),
                        "published": pub,
                        "credibility_weight": _credibility_weight(link),
                    })
        except Exception as e:
            print(f"[/news] Error fetching {source_name}: {e}")
        return items

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [
            loop.run_in_executor(pool, _fetch_feed, name, url)
            for name, url in target_feeds.items()
        ]
        results = await asyncio.gather(*futures)

    headlines = [item for feed_items in results for item in feed_items]
    headlines.sort(key=lambda x: x["credibility_weight"], reverse=True)
    return {
        "headlines": headlines[:limit],
        "total": len(headlines),
        "available_categories": list(CATEGORIZED_FEEDS.keys())
    }


# ---------------------------------------------------------------------------
# /analyze
# ---------------------------------------------------------------------------

@app.post("/analyze")
async def analyze_post(
    payload: Optional[AnalyzePayload] = None,
    text_override: Optional[str] = None,
    platform: Optional[str] = None
):
    """
    Unified multimodal analysis endpoint supporting YouTube (Video/Shorts),
    Instagram Reels/Posts, X (Twitter), Facebook, raw text claims, and
    live news articles. Performs OCR on images, Whisper transcription on
    video/audio, and runs all extracted signals through the multi-language
    fact-verification and epidemic spread diffusion pipeline.
    """
    import uuid

    # Resolve input parameters from either JSON body or query param
    text = None
    url = None
    target_platform = platform or "news"
    author_username = "Unknown Source"
    likes = 0
    shares = 0
    views = 0
    comments = 0
    followers = 0
    verified = False
    account_age_days = 180

    if payload:
        if payload.post:
            post = payload.post
            text = post.text_content
            target_platform = post.platform
            author_username = post.author_username
        else:
            text = payload.text
            url = payload.url
            if payload.platform:
                target_platform = payload.platform
            if payload.author_username:
                author_username = payload.author_username
            likes = payload.likes or 0
            shares = payload.shares or 0
            views = payload.views or 0
            comments = payload.comments or 0
            followers = payload.followers or 0
            verified = bool(payload.verified)
            account_age_days = payload.account_age_days or 180
    elif text_override:
        text = text_override

    # ── Multimodal pre-extraction from payload fields ──────────
    # Caller may have already run /extract-media and passes transcript/ocr_text
    pre_transcript = (payload.transcript or "") if payload else ""
    pre_ocr = (payload.ocr_text or "") if payload else ""
    pre_image_b64 = (payload.image_b64 or "") if payload else ""
    mm_context: dict = {}

    # If text is empty but url is provided, or text itself is a URL:
    extracted_mm: dict = {}   # store youtube_data from extraction for mm context
    if url or (text and re.match(r'^https?://[^\s]+$', text.strip())):
        extracted = extract_social_media(url or text.strip())
        if extracted.success:
            if not text or re.match(r'^https?://[^\s]+$', text.strip()):
                text = extracted.text or text
            if not payload or not payload.platform or payload.platform == "auto":
                target_platform = extracted.platform
            if author_username == "Unknown Source" and extracted.author_username:
                author_username = extracted.author_username
            if likes == 0 and extracted.likes:
                likes = extracted.likes
            if shares == 0 and extracted.shares:
                shares = extracted.shares
            if views == 0 and extracted.views:
                views = extracted.views
            if comments == 0 and extracted.comments:
                comments = extracted.comments
            if followers == 0 and extracted.followers:
                followers = extracted.followers
            if not verified and extracted.verified:
                verified = extracted.verified
            # Capture YouTube data and transcript for multimodal context
            extracted_mm = extracted.youtube_data
            if extracted.transcript and not pre_transcript:
                pre_transcript = extracted.transcript

    # ── Multimodal: OCR on inline image (base64) ──────────────
    if pre_image_b64 and MULTIMODAL_AVAILABLE and not pre_ocr:
        try:
            ocr_r = await asyncio.to_thread(extract_text_from_image, pre_image_b64)
            pre_ocr = ocr_r.get("text", "")
        except Exception:
            pass

    # ── Build synthesized claim ────────────────────────────────
    if MULTIMODAL_AVAILABLE and (pre_transcript or pre_ocr or extracted_mm):
        synthesis = synthesize_claim(
            caption=text or "",
            ocr_text=pre_ocr,
            audio_transcript=pre_transcript,
            youtube_title=extracted_mm.get("title", "") if extracted_mm else "",
            youtube_description=extracted_mm.get("description", "") if extracted_mm else "",
            platform=target_platform,
        )
        verification_text = synthesis["synthesized_claim"] or text or ""
        mm_context = build_multimodal_context(
            youtube_data=extracted_mm or {},
            ocr_result={"text": pre_ocr, "engine": "pre-extracted", "success": bool(pre_ocr)},
            transcription_result={"transcript": pre_transcript, "engine": "pre-extracted", "success": bool(pre_transcript)},
            caption=text or "",
            platform=target_platform,
        )
    else:
        verification_text = text or ""
        if extracted_mm:
            mm_context = build_multimodal_context(
                youtube_data=extracted_mm,
                caption=text or "",
                platform=target_platform,
            ) if MULTIMODAL_AVAILABLE else {}

    # Fallback to mock post if still empty
    if not text:
        mock = generate_mock_post()
        text = mock.text_content
        target_platform = mock.platform
        author_username = mock.author_username
        likes = mock.metrics.get("likes", 100)
        shares = mock.metrics.get("shares", 20)
        views = mock.metrics.get("views", 1500)
        comments = mock.metrics.get("comments", 10)
        followers = mock.author_meta.get("followers", 500)
        verified = mock.author_meta.get("verified", False)

    # Standardize platform key
    p_low = (target_platform or "news").lower()
    if p_low in ["x", "tweet", "twitter"]:
        clean_platform = "twitter"
    elif p_low in ["instagram", "insta"]:
        clean_platform = "instagram"
    elif p_low in ["facebook", "fb"]:
        clean_platform = "facebook"
    elif p_low in ["youtube", "quora", "reddit", "news"]:
        clean_platform = p_low
    else:
        clean_platform = "news"

    post = UnifiedPost(
        post_id=str(uuid.uuid4()),
        platform=clean_platform,
        author_id=str(uuid.uuid4()),
        author_username=author_username,
        text_content=text,
        created_at=datetime.now(timezone.utc),
        metrics={
            "likes": likes,
            "shares": shares,
            "views": views,
            "comments": comments
        },
        author_meta={
            "followers": followers,
            "verified": verified,
            "account_age_days": account_age_days
        },
        author_history=[]
    )

    # Store verification_text for use inside try block
    _vtext = locals().get("verification_text", text) or text

    try:
        # 1. Fact Verification  – use synthesized multimodal claim if available
        verification_result = await asyncio.to_thread(verify_claim, _vtext)

        # If it was a news link and user didn't specify author, derive from the first source
        if clean_platform == "news" and author_username == "Unknown Source" and verification_result.get("analyzed_sources"):
            first_source = verification_result["analyzed_sources"][0]
            link = first_source.get("link", "")
            if link:
                site_name = _extract_site_name(link)
                post.author_username = first_source.get("source", site_name)
                post.author_meta["verified"] = True

        # 2 & 3. Credibility + Full Spread Diffusion Analysis (Parallel)
        credibility, diffusion_analysis = await asyncio.gather(
            asyncio.to_thread(calculate_credibility, post),
            asyncio.to_thread(analyze_spread_potential, post)
        )

        diffusion_score = diffusion_analysis["score"]

        # 4. Risk Assessment (Ensemble)
        ensemble = get_ensemble()
        risk_assessment = await asyncio.to_thread(
            ensemble.assess_risk,
            s_fact=verification_result["s_fact"],
            user_credibility=credibility,
            diffusion_risk=diffusion_score
        )

        # 5. Explainability
        explanation = await asyncio.to_thread(
            generate_explanation,
            risk_tier=risk_assessment["tier"],
            verification_result=verification_result,
            credibility=credibility,
            diffusion=diffusion_analysis
        )

        return {
            "post": post.model_dump(),
            "credibility_score": credibility,
            "verification": verification_result,
            "diffusion": diffusion_analysis,
            "diffusion_risk": diffusion_score,  # backwards compatibility
            "risk_assessment": risk_assessment,
            "explanation": explanation,
            "multimodal_context": mm_context,    # NEW: multimodal signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.api:app", host="0.0.0.0", port=8000, reload=True)

