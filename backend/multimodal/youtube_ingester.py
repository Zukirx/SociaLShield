"""
youtube_ingester.py
────────────────────────────────────────────────────────────────
Extracts metadata, description, auto-generated subtitles / captions,
and chapter info from any YouTube URL (video, Short, or community post)
using yt-dlp.  Falls back to youtube-transcript-api for subtitle-only
extraction when yt-dlp is unavailable.

All heavy network I/O is kept synchronous so callers can run it inside
asyncio.to_thread() from the FastAPI route.
"""
from __future__ import annotations

import re
import json
import subprocess
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _is_youtube_url(url: str) -> bool:
    patterns = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/",
        r"(?:https?://)?youtu\.be/",
        r"(?:https?://)?(?:www\.)?youtube\.com/community",
        r"(?:https?://)?(?:www\.)?youtube\.com/@",
        r"(?:https?://)?(?:www\.)?youtube\.com/clip/",
    ]
    return any(re.search(p, url) for p in patterns)


def _extract_video_id(url: str) -> Optional[str]:
    """Best-effort video-ID extraction from any YouTube URL form."""
    # Standard watch?v=
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    # Shorts
    m = re.search(r"/shorts/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    # youtu.be short links
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    # clip
    m = re.search(r"/clip/([A-Za-z0-9_-]+)", url)
    if m:
        return m.group(1)
    return None


# ─────────────────────────────────────────────────────────────
# yt-dlp extraction  (returns dict with all useful fields)
# ─────────────────────────────────────────────────────────────

def _ytdlp_extract(url: str) -> Optional[dict]:
    """
    Call yt-dlp --dump-json to get video metadata without downloading the
    video file.  Returns parsed dict or None on failure.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist",
             "--write-auto-sub", "--skip-download",
             "--sub-lang", "en,hi,ml,ta",
             url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            # yt-dlp can output multiple JSON objects for playlists; take first
            first_line = result.stdout.strip().split("\n")[0]
            return json.loads(first_line)
    except FileNotFoundError:
        pass  # yt-dlp not installed – handled by fallback
    except Exception:
        pass
    return None


def _ytdlp_transcript_only(url: str) -> Optional[str]:
    """
    Ask yt-dlp to print auto-subtitle vtt to stdout without downloading
    video, then parse it into plain text.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--skip-download",
             "--write-auto-sub", "--sub-lang", "en",
             "--output", "-",           # write subtitle to stdout
             "--no-playlist",
             url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return _clean_vtt(result.stdout)
    except Exception:
        pass
    return None


def _clean_vtt(vtt_text: str) -> str:
    """Strip VTT timing headers and deduplicate subtitle lines."""
    seen: list[str] = []
    for line in vtt_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "-->" in line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        # Remove HTML-like tags inserted by YouTube
        line = re.sub(r"<[^>]+>", "", line)
        if line and (not seen or seen[-1] != line):
            seen.append(line)
    return " ".join(seen)


# ─────────────────────────────────────────────────────────────
# youtube-transcript-api fallback
# ─────────────────────────────────────────────────────────────

def _transcript_api_extract(video_id: str) -> Optional[str]:
    """
    Use youtube-transcript-api (pip install youtube-transcript-api)
    to retrieve auto-generated or manual captions without yt-dlp.
    Prefers English, then falls back to any available language.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Try English first, then any language
            try:
                t = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            except Exception:
                t = transcript_list.find_generated_transcript(["hi", "ml", "ta", "en"])
            snippets = t.fetch()
            text = " ".join(s["text"] for s in snippets)
            return text.strip() or None
        except (NoTranscriptFound, TranscriptsDisabled):
            return None
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def extract_youtube(url: str) -> dict:
    """
    Main entry point.  Returns a dict with:
      platform         "youtube"
      video_id         str or ""
      title            str
      description      str
      transcript       str  (auto captions / subtitles)
      channel          str
      likes            int
      views            int
      comments         int
      duration_sec     int
      is_short         bool
      thumbnail_url    str
      success          bool
      source           "yt-dlp" | "transcript-api" | "metadata-only" | "failed"
      error            str (if not success)
    """
    if not _is_youtube_url(url):
        return {"success": False, "error": "Not a YouTube URL", "platform": "youtube"}

    video_id = _extract_video_id(url) or ""
    is_short = "/shorts/" in url

    # ── Try yt-dlp first ──────────────────────────────────────
    info = _ytdlp_extract(url)
    if info:
        title = info.get("title", "")
        description = info.get("description", "")
        channel = info.get("uploader", info.get("channel", ""))
        likes = info.get("like_count", 0) or 0
        views = info.get("view_count", 0) or 0
        comments = info.get("comment_count", 0) or 0
        duration = info.get("duration", 0) or 0
        thumbnail = info.get("thumbnail", "")

        # Subtitles: automatic_captions dict or subtitles dict
        transcript = ""
        for lang in ["en", "en-US", "en-GB", "hi", "ml", "ta"]:
            caps = (info.get("automatic_captions") or {}).get(lang) or \
                   (info.get("subtitles") or {}).get(lang)
            if caps:
                # Each entry may be list of dicts with "data" or direct text
                try:
                    entries = caps[0].get("data", "") if isinstance(caps[0], dict) else ""
                    if isinstance(entries, list):
                        transcript = " ".join(e.get("utf8", "") for e in entries)
                    elif isinstance(entries, str):
                        transcript = _clean_vtt(entries)
                except Exception:
                    pass
                if transcript:
                    break

        # If no embedded transcript, try transcript-api as supplement
        if not transcript and video_id:
            transcript = _transcript_api_extract(video_id) or ""

        return {
            "platform": "youtube",
            "video_id": video_id,
            "title": title,
            "description": description[:3000],
            "transcript": transcript[:5000],
            "channel": channel,
            "likes": int(likes),
            "views": int(views),
            "comments": int(comments),
            "duration_sec": int(duration),
            "is_short": is_short,
            "thumbnail_url": thumbnail,
            "success": True,
            "source": "yt-dlp",
        }

    # ── Fallback: transcript-api only ─────────────────────────
    if video_id:
        transcript = _transcript_api_extract(video_id)
        if transcript:
            return {
                "platform": "youtube",
                "video_id": video_id,
                "title": "",
                "description": "",
                "transcript": transcript[:5000],
                "channel": "Unknown",
                "likes": 0,
                "views": 0,
                "comments": 0,
                "duration_sec": 0,
                "is_short": is_short,
                "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                "success": True,
                "source": "transcript-api",
            }

    # ── Final fallback: metadata-only skeleton ─────────────────
    return {
        "platform": "youtube",
        "video_id": video_id,
        "title": "",
        "description": "",
        "transcript": "",
        "channel": "Unknown",
        "likes": 0,
        "views": 0,
        "comments": 0,
        "duration_sec": 0,
        "is_short": is_short,
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else "",
        "success": True,
        "source": "metadata-only",
        "error": "Could not retrieve transcript; only URL metadata available.",
    }


def synthesize_youtube_text(yt_data: dict) -> str:
    """
    Merge title + description + transcript into a single claim string
    suitable for the verification pipeline.
    """
    parts = []
    if yt_data.get("title"):
        parts.append(yt_data["title"])
    if yt_data.get("description"):
        # Take only the first 800 chars of description to avoid flooding
        parts.append(yt_data["description"][:800])
    if yt_data.get("transcript"):
        parts.append(yt_data["transcript"][:2000])
    return " | ".join(parts) if parts else ""
