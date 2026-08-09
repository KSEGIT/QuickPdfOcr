#!/usr/bin/env python3
"""Rendering backend selection."""

from components.rendering.base import PdfRenderer
from components.rendering.pdfium_renderer import PdfiumRenderer

__all__ = ["PdfRenderer", "PdfiumRenderer", "get_renderer"]


def get_renderer(pdf_path) -> PdfRenderer:
    """Return a renderer for the given PDF.

    pypdfium2 works identically on every supported platform, so unlike
    get_engine() this makes no platform decision. It exists so callers depend
    on the interface rather than the concrete class.
    """
    return PdfiumRenderer(pdf_path)
