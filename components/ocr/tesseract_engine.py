#!/usr/bin/env python3
"""OCR via Tesseract. Windows and Linux only.

macOS uses components/ocr/vision_engine.py instead, which is why Pillow and
pytesseract may be imported at module level here: this file is never reached on
darwin. Keep it that way -- neither package publishes universal2 wheels.
"""

from PIL import Image
import pytesseract

from components.page_image import PageImage

DEFAULT_LANGUAGES = ["eng"]

# Fallback list used when Tesseract cannot be queried (e.g. not yet installed
# during a packaging step). Keeps the UI populated rather than empty.
FALLBACK_LANGUAGES = ["eng"]


class TesseractOcrEngine:
    """Tesseract-backed OCR. Language codes are ISO 639-2, e.g. 'eng', 'pol'."""

    @property
    def name(self) -> str:
        return "Tesseract"

    def supported_languages(self) -> list[str]:
        """Languages for which a .traineddata file is installed."""
        try:
            languages = list(pytesseract.get_languages(config=""))
        except Exception:
            return list(FALLBACK_LANGUAGES)
        # 'osd' is orientation/script detection, not a text language.
        languages = sorted(code for code in languages if code != "osd")
        return languages or list(FALLBACK_LANGUAGES)

    def default_languages(self) -> list[str]:
        supported = set(self.supported_languages())
        chosen = [code for code in DEFAULT_LANGUAGES if code in supported]
        return chosen or self.supported_languages()[:1]

    def recognize(self, page: PageImage, languages: list[str] | None = None) -> str:
        """Extract text from one page."""
        codes = languages or self.default_languages()
        image = Image.frombuffer(
            "RGBX",
            (page.width, page.height),
            page.buffer,
            "raw",
            "RGBX",
            page.stride,
            1,
        ).convert("RGB")
        return pytesseract.image_to_string(image, lang="+".join(codes))
