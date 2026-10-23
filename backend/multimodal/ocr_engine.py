"""
ocr_engine.py
────────────────────────────────────────────────────────────────
Extracts text embedded in images (screenshots, memes, infographics,
banners, WhatsApp forwards) using pytesseract (Tesseract OCR) with
EasyOCR as a GPU-capable fallback.

Can also process individual video frames (NumPy arrays) extracted by
the transcription engine.
"""
from __future__ import annotations

import io
import re
import base64
from typing import Union, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Singleton EasyOCR reader – initialised lazily to avoid startup cost
_easyocr_reader = None


def _get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None and EASYOCR_AVAILABLE:
        # Support Indian languages + English; gpu=False for CPU-only servers
        _easyocr_reader = easyocr.Reader(["en", "hi"], gpu=False, verbose=False)
    return _easyocr_reader


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _clean_ocr_text(raw: str) -> str:
    """Remove garbage chars, collapse whitespace, dedupe blank lines."""
    # Strip non-printable characters except common Unicode
    raw = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u0080-\uFFFF]", " ", raw)
    # Collapse runs of whitespace
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def _open_image(source: Union[str, bytes, "Image.Image"]) -> Optional["Image.Image"]:
    """Accept file path, raw bytes, base64 string, or PIL Image."""
    if not PIL_AVAILABLE:
        return None

    if isinstance(source, Image.Image):
        return source
    if isinstance(source, bytes):
        return Image.open(io.BytesIO(source))
    if isinstance(source, str):
        # base64
        if source.startswith("data:image"):
            b64data = source.split(",", 1)[1]
            return Image.open(io.BytesIO(base64.b64decode(b64data)))
        if source.startswith("/") or source[1:3] == ":\\":
            return Image.open(source)
        # Try as raw base64
        try:
            return Image.open(io.BytesIO(base64.b64decode(source)))
        except Exception:
            pass
    return None


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def extract_text_from_image(
    source: Union[str, bytes, "Image.Image"],
    lang: str = "eng+hin",
) -> dict:
    """
    Extract text from an image using Tesseract (primary) or EasyOCR (fallback).

    Parameters
    ----------
    source : str | bytes | PIL.Image
        File path, raw bytes, base64 data URI, or PIL.Image object.
    lang   : str
        Tesseract language codes (e.g. "eng+hin+mal+tam").

    Returns
    -------
    dict with keys:
        text       str  – extracted OCR text
        confidence float – rough confidence 0.0–1.0 (1.0 if no engine available)
        engine     str  – "tesseract" | "easyocr" | "none"
        success    bool
    """
    img = _open_image(source)

    # ── Tesseract OCR ──────────────────────────────────────────
    if img is not None and TESSERACT_AVAILABLE:
        try:
            raw = pytesseract.image_to_string(img, lang=lang, config="--oem 3 --psm 6")
            text = _clean_ocr_text(raw)
            if text:
                return {"text": text, "confidence": 0.85, "engine": "tesseract", "success": True}
        except Exception:
            pass

    # ── EasyOCR fallback ──────────────────────────────────────
    if img is not None and EASYOCR_AVAILABLE:
        try:
            import numpy as np
            reader = _get_easyocr_reader()
            if reader:
                img_array = np.array(img.convert("RGB"))
                results = reader.readtext(img_array, detail=1)
                texts = [r[1] for r in results if r[2] > 0.3]
                text = _clean_ocr_text(" ".join(texts))
                if text:
                    avg_conf = sum(r[2] for r in results) / len(results) if results else 0
                    return {"text": text, "confidence": round(avg_conf, 2), "engine": "easyocr", "success": True}
        except Exception:
            pass

    # ── No OCR engine available or image load failed ───────────
    return {
        "text": "",
        "confidence": 0.0,
        "engine": "none",
        "success": False,
        "error": "No OCR engine available (install pytesseract or easyocr) or image could not be loaded.",
    }


def detect_sensational_overlays(ocr_text: str) -> list[str]:
    """
    Scan OCR text for on-screen chyron-style alert phrases commonly used
    in sensationalist broadcasts and viral memes.
    Returns list of detected overlay phrases.
    """
    ALERT_PATTERNS = [
        r"\bBREAKING\b", r"\bALERT\b", r"\bURGENT\b", r"\bWARNING\b",
        r"\bFLASH\b", r"\bEXCLUSIVE\b", r"\bSHOCKING\b", r"\bVIRAL\b",
        r"\bSCOOP\b", r"\bDEATH\b", r"\bDEADLY\b", r"\bTOXIC\b",
        r"\bEMERGENCY\b", r"\bCRISIS\b", r"\bEXPOSED\b", r"\bBLACKOUT\b",
        # Hindi in Latin script
        r"\bJaruuri\b", r"\bSavdhaan\b", r"\bKhatre\b",
    ]
    found = []
    for pat in ALERT_PATTERNS:
        if re.search(pat, ocr_text, re.IGNORECASE):
            # Extract matched word
            m = re.search(pat, ocr_text, re.IGNORECASE)
            found.append(m.group(0).upper())
    return list(set(found))
