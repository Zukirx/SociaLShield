"""
synthesizer.py
────────────────────────────────────────────────────────────────
Unified Claim Synthesizer: merges all extracted signals from
caption text, OCR image/video text, Whisper audio transcript, and
YouTube metadata into a single consolidated claim string that the
fact-verification pipeline ingests.
"""
from __future__ import annotations

import re
from typing import Optional


def synthesize_claim(
    *,
    caption: str = "",
    ocr_text: str = "",
    audio_transcript: str = "",
    youtube_title: str = "",
    youtube_description: str = "",
    platform: str = "news",
    max_chars: int = 2500,
) -> dict:
    """
    Build one claim string from heterogeneous multimodal inputs, applying
    source priority and deduplication.

    Priority order (most → least reliable signal):
      1. Audio speech transcript   (Whisper – captures actual verbal claims)
      2. Caption / post text       (authored text – may be brief or misleading)
      3. YouTube video title       (editorial summary)
      4. OCR screen text           (chyrons, banners – often highly sensational)
      5. YouTube description       (author-provided context)

    Returns
    -------
    dict:
        synthesized_claim   str  – merged fact-check input
        sources_used        list[str] – which signals contributed
        word_count          int
        is_multimodal       bool – True if >1 source contributed
    """
    parts: list[tuple[str, str]] = []  # (source_label, text)

    if audio_transcript.strip():
        parts.append(("🎙️ Audio Transcript", _trim(audio_transcript, 1200)))
    if caption.strip():
        parts.append(("📝 Caption Text", _trim(caption, 600)))
    if youtube_title.strip():
        parts.append(("🎬 Video Title", _trim(youtube_title, 200)))
    if ocr_text.strip():
        parts.append(("🔍 OCR Screen Text", _trim(ocr_text, 400)))
    if youtube_description.strip():
        parts.append(("📄 Description", _trim(youtube_description, 400)))

    if not parts:
        return {
            "synthesized_claim": "",
            "sources_used": [],
            "word_count": 0,
            "is_multimodal": False,
        }

    sources_used = [label for label, _ in parts]
    combined = " | ".join(text for _, text in parts)
    # Trim to max_chars for downstream pipeline
    combined = combined[:max_chars].strip()

    return {
        "synthesized_claim": combined,
        "sources_used": sources_used,
        "word_count": len(combined.split()),
        "is_multimodal": len(parts) > 1,
    }


def _trim(text: str, max_len: int) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text[:max_len] if len(text) > max_len else text


def build_multimodal_context(
    *,
    youtube_data: Optional[dict] = None,
    ocr_result: Optional[dict] = None,
    transcription_result: Optional[dict] = None,
    caption: str = "",
    platform: str = "news",
) -> dict:
    """
    High-level helper that takes raw outputs from each module and
    assembles the full multimodal_context payload to attach to the
    API response.

    Returns a dict ready to be included in the /analyze response.
    """
    yt = youtube_data or {}
    ocr = ocr_result or {}
    trans = transcription_result or {}

    audio_transcript = trans.get("transcript", "") or yt.get("transcript", "")
    ocr_text = ocr.get("text", "") or " ".join(trans.get("frame_ocr_texts", []))
    sensational_overlays = (
        ocr.get("overlays", []) +
        trans.get("sensational_overlays", [])
    )
    # Deduplicate
    sensational_overlays = list(dict.fromkeys(sensational_overlays))

    synthesis = synthesize_claim(
        caption=caption,
        ocr_text=ocr_text,
        audio_transcript=audio_transcript,
        youtube_title=yt.get("title", ""),
        youtube_description=yt.get("description", ""),
        platform=platform,
    )

    return {
        "audio_transcript": audio_transcript[:3000],
        "ocr_text": ocr_text[:1500],
        "sensational_overlays": sensational_overlays,
        "youtube": {
            "video_id": yt.get("video_id", ""),
            "title": yt.get("title", ""),
            "channel": yt.get("channel", ""),
            "views": yt.get("views", 0),
            "likes": yt.get("likes", 0),
            "duration_sec": yt.get("duration_sec", 0),
            "is_short": yt.get("is_short", False),
            "thumbnail_url": yt.get("thumbnail_url", ""),
            "source": yt.get("source", ""),
        } if yt else {},
        "synthesis": synthesis,
        "has_media_analysis": bool(audio_transcript or ocr_text),
        "transcription_engine": trans.get("engine", "none"),
        "ocr_engine": ocr.get("engine", "none"),
    }
