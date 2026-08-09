#!/usr/bin/env python3
"""The OCR interface. One job: raw pixels -> text."""

from typing import Protocol, runtime_checkable

from components.page_image import PageImage


class OcrEngineUnavailable(Exception):
    """Raised when the OCR backend itself cannot run at all -- e.g.
    Tesseract is not installed, or none of the requested languages has its
    .traineddata installed.

    This is a whole-document failure, categorically different from a
    per-page rendering/recognition glitch: if the engine is unavailable,
    every page would fail identically, so PdfOcrProcessor lets this
    propagate out of process() instead of recording it as page text (see
    PdfOcrProcessor._process_page()). OCRWorker then reports it to the
    caller as a run failure rather than emitting a false "OCR completed
    successfully!".
    """


@runtime_checkable
class OcrEngine(Protocol):
    """Recognizes text in a rasterized page.

    Language codes are engine-specific: Tesseract uses ISO 639-2 ('eng'),
    Vision uses BCP-47 ('en-US'). Callers should treat the strings returned by
    supported_languages() as opaque and pass them straight back to recognize().
    """

    @property
    def name(self) -> str:
        """Human-readable engine name, shown in the UI."""
        ...

    def supported_languages(self) -> list[str]:
        """Language codes this engine can recognize, in engine-native form."""
        ...

    def default_languages(self) -> list[str]:
        """Languages to use when the caller expresses no preference."""
        ...

    def recognize(self, page: PageImage, languages: list[str] | None = None) -> str:
        """Extract text from one page. Returns '' when nothing is found."""
        ...
