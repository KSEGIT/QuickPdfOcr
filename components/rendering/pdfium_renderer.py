#!/usr/bin/env python3
"""PDF rendering via pypdfium2.

pypdfium2 ships PDFium inside the wheel, so there is no external binary and no
dynamic library to locate at runtime. This is what replaced poppler, whose
Homebrew binaries linked 24 uncopied dylibs by @rpath and produced issue #26.
"""

from pathlib import Path

import pypdfium2 as pdfium

from components.page_image import PageImage

# 1 PDF canvas unit is 1/72 inch.
POINTS_PER_INCH = 72


class PdfiumRenderer:
    """Renders pages of one PDF document. Works on macOS, Windows and Linux."""

    def __init__(self, pdf_path):
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        self._path = path
        self._doc = pdfium.PdfDocument(str(path))

    def __enter__(self) -> "PdfiumRenderer":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def page_count(self) -> int:
        """Number of pages in the document."""
        return len(self._doc)

    def page_size_inches(self, index: int) -> tuple[float, float]:
        """(width, height) of a page in inches."""
        self._check_index(index)
        width_points, height_points = self._doc[index].get_size()
        return width_points / POINTS_PER_INCH, height_points / POINTS_PER_INCH

    def render_page(self, index: int, dpi: int) -> PageImage:
        """Rasterize one page to a 4-byte-per-pixel RGBX buffer.

        Both render flags are load-bearing. prefer_bgrx forces 4-byte pixels,
        without which pypdfium2 emits 24-bit RGB and CoreGraphics builds a 0x0
        image. rev_byteorder gives RGBx rather than BGRx byte order.
        """
        self._check_index(index)
        bitmap = self._doc[index].render(
            scale=dpi / POINTS_PER_INCH,
            rev_byteorder=True,
            prefer_bgrx=True,
        )
        # Validate that the library produced RGBX format. If either prefer_bgrx
        # or rev_byteorder stopped taking effect, this will catch it loudly
        # rather than silently swapping red and blue channels to CoreGraphics.
        mode = bitmap.mode
        if mode != "RGBX":
            raise RuntimeError(
                f"Expected RGBX pixel format from render(), got {mode!r}. "
                "Check that prefer_bgrx=True and rev_byteorder=True are still effective."
            )
        return PageImage(
            width=bitmap.width,
            height=bitmap.height,
            stride=bitmap.stride,
            buffer=bytes(bitmap.buffer),
            mode=mode,
        )

    def close(self) -> None:
        """Release the underlying document."""
        self._doc.close()

    def _check_index(self, index: int) -> None:
        if not 0 <= index < len(self._doc):
            raise IndexError(
                f"Page index {index} out of range for {self._path.name} "
                f"({len(self._doc)} page(s))"
            )
