#!/usr/bin/env python3
"""OCR backend selection.

macOS uses Apple Vision, which the OS provides. Every other platform uses
Tesseract. The two use different language-code schemes, so codes are treated as
opaque strings outside the engines; describe_language() maps either scheme to a
label for display.
"""

import sys

from components.ocr.base import OcrEngine

__all__ = ["OcrEngine", "get_engine", "describe_language"]

# Maps both BCP-47 (Vision) and ISO 639-2 (Tesseract) codes to display names,
# so the UI can label whichever engine is active.
_LANGUAGE_NAMES = {
    "ar": "Arabic", "ara": "Arabic", "ars": "Arabic",
    "cs": "Czech", "ces": "Czech",
    "da": "Danish", "dan": "Danish",
    "de": "German", "deu": "German",
    "en": "English", "eng": "English",
    "es": "Spanish", "spa": "Spanish",
    "fr": "French", "fra": "French",
    "id": "Indonesian", "ind": "Indonesian",
    "it": "Italian", "ita": "Italian",
    "ja": "Japanese", "jpn": "Japanese",
    "ko": "Korean", "kor": "Korean",
    "ms": "Malay", "msa": "Malay",
    "nb": "Norwegian", "nn": "Norwegian", "no": "Norwegian", "nor": "Norwegian",
    "nl": "Dutch", "nld": "Dutch",
    "pl": "Polish", "pol": "Polish",
    "pt": "Portuguese", "por": "Portuguese",
    "ro": "Romanian", "ron": "Romanian",
    "ru": "Russian", "rus": "Russian",
    "sv": "Swedish", "swe": "Swedish",
    "th": "Thai", "tha": "Thai",
    "tr": "Turkish", "tur": "Turkish",
    "uk": "Ukrainian", "ukr": "Ukrainian",
    "vi": "Vietnamese", "vie": "Vietnamese",
    "yue": "Cantonese",
    "zh": "Chinese", "chi_sim": "Chinese", "chi_tra": "Chinese",
}


def get_engine() -> OcrEngine:
    """Return the OCR engine for this platform."""
    if sys.platform == "darwin":
        from components.ocr.vision_engine import VisionOcrEngine

        return VisionOcrEngine()

    from components.ocr.tesseract_engine import TesseractOcrEngine

    return TesseractOcrEngine()


def describe_language(code: str) -> str:
    """Human-readable name for an engine-native language code.

    Accepts BCP-47 ('pl-PL') and ISO 639-2 ('pol'). Unknown codes are returned
    unchanged so the UI degrades to showing the raw code.
    """
    if code in _LANGUAGE_NAMES:
        return _LANGUAGE_NAMES[code]
    base = code.split("-")[0]
    return _LANGUAGE_NAMES.get(base, code)
