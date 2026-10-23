"""
transcriber.py
────────────────────────────────────────────────────────────────
Downloads the audio track from a video URL (using yt-dlp) and
transcribes it with OpenAI Whisper (or faster-whisper for CPU-
constrained environments).

Also samples key video frames and runs them through the OCR engine
to detect on-screen chyrons, breaking-news banners, and headline
overlays.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Try to import Whisper (openai-whisper or faster-whisper)
# ─────────────────────────────────────────────────────────────
try:
    import whisper as openai_whisper
    OPENAI_WHISPER = True
except ImportError:
    OPENAI_WHISPER = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER = True
except ImportError:
    FASTER_WHISPER = False

# Singleton model – loaded lazily
_whisper_model = None


def _load_whisper():
    """Load the smallest available Whisper model for CPU inference."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    if FASTER_WHISPER:
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        return _whisper_model
    if OPENAI_WHISPER:
        _whisper_model = openai_whisper.load_model("tiny")
        return _whisper_model
    return None


# ─────────────────────────────────────────────────────────────
# Audio download via yt-dlp
# ─────────────────────────────────────────────────────────────

def _download_audio(url: str, output_path: str) -> bool:
    """
    Download audio-only stream with yt-dlp to output_path (mp3/m4a).
    Returns True on success.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "-x",                        # extract audio
                "--audio-format", "mp3",
                "--audio-quality", "5",      # 128kbps – sufficient for speech
                "--no-playlist",
                "--max-filesize", "50m",     # hard limit to avoid huge downloads
                "-o", output_path,
                url,
            ],
            capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except FileNotFoundError:
        return False  # yt-dlp not installed
    except Exception:
        return False


def _download_audio_ffmpeg(url: str, output_path: str) -> bool:
    """
    Alternative: use ffmpeg directly to grab audio from a streamable URL.
    Only works for direct media URLs (not YouTube HTML pages).
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", url,
             "-vn", "-ar", "16000", "-ac", "1",
             "-t", "300",       # max 5 minutes
             output_path],
            capture_output=True, timeout=90
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# Whisper transcription
# ─────────────────────────────────────────────────────────────

def _transcribe_file(audio_path: str) -> Optional[str]:
    model = _load_whisper()
    if model is None:
        return None

    try:
        if FASTER_WHISPER and isinstance(model, WhisperModel):
            segments, _ = model.transcribe(audio_path, beam_size=5, language=None)
            return " ".join(s.text for s in segments).strip() or None
        elif OPENAI_WHISPER:
            result = model.transcribe(audio_path)
            return result.get("text", "").strip() or None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Frame sampling for OCR
# ─────────────────────────────────────────────────────────────

def _sample_video_frames(url: str, num_frames: int = 5) -> list:
    """
    Download a few frames from the video at evenly-spaced timestamps.
    Returns list of PIL Image objects. Requires yt-dlp + ffmpeg.
    """
    frames = []
    try:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            # Get duration first
            dur_result = subprocess.run(
                ["yt-dlp", "--print", "%(duration)s", "--no-playlist", url],
                capture_output=True, text=True, timeout=15
            )
            try:
                duration = float(dur_result.stdout.strip())
            except (ValueError, AttributeError):
                duration = 120  # default 2 min

            step = max(1, int(duration / (num_frames + 1)))
            timestamps = [step * (i + 1) for i in range(num_frames)]

            # Get best video URL from yt-dlp
            url_result = subprocess.run(
                ["yt-dlp", "-g", "--no-playlist", url],
                capture_output=True, text=True, timeout=20
            )
            if url_result.returncode != 0:
                return frames
            stream_url = url_result.stdout.strip().split("\n")[0]

            for i, ts in enumerate(timestamps):
                frame_path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
                result = subprocess.run(
                    ["ffmpeg", "-y",
                     "-ss", str(ts),
                     "-i", stream_url,
                     "-frames:v", "1",
                     "-q:v", "2",
                     frame_path],
                    capture_output=True, timeout=20
                )
                if result.returncode == 0 and os.path.exists(frame_path):
                    frames.append(Image.open(frame_path).copy())

    except Exception:
        pass
    return frames


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def transcribe_video_url(url: str, extract_frames: bool = True) -> dict:
    """
    Full pipeline:
     1. Download audio → Whisper transcription
     2. Sample video frames → OCR for on-screen text
     3. Return combined result dict

    Returns
    -------
    dict with:
        transcript          str  – Whisper speech-to-text
        frame_ocr_texts     list[str] – OCR text from sampled frames
        combined_text       str  – merged for fact-checking
        sensational_overlays list[str]
        engine              str  – "whisper" | "faster-whisper" | "none"
        success             bool
    """
    from .ocr_engine import extract_text_from_image, detect_sensational_overlays

    transcript = ""
    frame_texts = []
    sensational = []
    engine_used = "none"

    # ── Whisper transcription ──────────────────────────────────
    model = _load_whisper()
    if model is not None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.mp3")
            downloaded = _download_audio(url, audio_path)
            if downloaded:
                t = _transcribe_file(audio_path)
                if t:
                    transcript = t
                    engine_used = "faster-whisper" if FASTER_WHISPER else "whisper"

    # ── Frame OCR ─────────────────────────────────────────────
    if extract_frames:
        try:
            frames = _sample_video_frames(url, num_frames=5)
            for frame in frames:
                ocr_result = extract_text_from_image(frame)
                if ocr_result.get("success") and ocr_result.get("text"):
                    frame_texts.append(ocr_result["text"])
            # Detect sensational overlays in all frame text combined
            all_frame_text = " ".join(frame_texts)
            if all_frame_text:
                sensational = detect_sensational_overlays(all_frame_text)
        except Exception:
            pass

    # ── Merge ─────────────────────────────────────────────────
    parts = []
    if transcript:
        parts.append(transcript[:3000])
    for ft in frame_texts:
        if ft:
            parts.append(ft[:500])
    combined = " | ".join(parts)

    return {
        "transcript": transcript[:5000],
        "frame_ocr_texts": frame_texts,
        "combined_text": combined[:6000],
        "sensational_overlays": sensational,
        "engine": engine_used,
        "success": bool(transcript or frame_texts),
    }


def is_video_url(url: str) -> bool:
    """Check if a URL points to a video platform we support."""
    VIDEO_PATTERNS = [
        r"youtube\.com", r"youtu\.be",
        r"instagram\.com/reel", r"instagram\.com/p/",
        r"twitter\.com.*video", r"x\.com.*video",
        r"facebook\.com.*video", r"fb\.watch",
        r"\.mp4", r"\.mov", r"\.webm", r"\.avi",
    ]
    return any(re.search(p, url, re.IGNORECASE) for p in VIDEO_PATTERNS)
