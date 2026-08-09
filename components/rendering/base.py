#!/usr/bin/env python3
"""The rendering interface. One job: PDF page -> raw pixels."""

from typing import Protocol, runtime_checkable

from components.page_image import PageImage


@runtime_checkable
class PdfRenderer(Protocol):
    """Rasterizes pages of a single PDF document."""

    def page_count(self) -> int:
        """Number of pages in the document."""
        ...

    def page_size_inches(self, index: int) -> tuple[float, float]:
        """(width, height) of a page in inches, used for DPI auto-detection."""
        ...

    def render_page(self, index: int, dpi: int) -> PageImage:
        """Rasterize one page at the given resolution."""
        ...

    def close(self) -> None:
        """Release the underlying document."""
        ...

    def __enter__(self) -> "PdfRenderer":
        """Renderers are context managers; callers should prefer `with`."""
        ...

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        ...
