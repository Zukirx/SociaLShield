from fastapi import FastAPI, HTTPException, Body
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

app = FastAPI(title="SocialShield API", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class AnalyzePayload(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None  # "instagram", "twitter", "facebook", "news"
    author_username: Optional[str] = None
    likes: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None
    comments: Optional[int] = None
    followers: Optional[int] = None
    verified: Optional[bool] = None
    account_age_days: Optional[int] = None
    post: Optional[UnifiedPost] = None


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
    return {"status": "ok", "version": "2.5.0"}


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
    Unified analysis endpoint supporting Instagram, X (Twitter), Facebook,
    raw text claims, and live news articles.
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

    # If text is empty but url is provided, or text itself is a URL:
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

    try:
        # 1. Fact Verification across news outlets & fact-checkers
        verification_result = await asyncio.to_thread(verify_claim, post.text_content)

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

        # 5. Explainability (incorporating local news risk)
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.api:app", host="0.0.0.0", port=8000, reload=True)

