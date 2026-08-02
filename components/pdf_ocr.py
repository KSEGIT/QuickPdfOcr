#!/usr/bin/env python3
"""PDF OCR orchestration.

Deliberately knows nothing about binaries, dylibs, PATH, or TESSDATA_PREFIX.
It renders pages through a PdfRenderer and recognizes them through an
OcrEngine; which concrete implementations those are is decided in
components/rendering/__init__.py and components/ocr/__init__.py.
"""

import sys
from pathlib import Path
from typing import Callable, Optional

from components.ocr.base import OcrEngine
from components.rendering import get_renderer

# DPI bands keyed on the page's longest edge in inches. Small pages (receipts)
# need more pixels per inch to resolve small type; very large pages do not.
DPI_BANDS = (
    (6, 400, "small document detected"),
    (10, 300, "standard document size"),
    (14, 250, "large document detected"),
)
FALLBACK_DPI = 200
DEFAULT_DPI = 300


class PdfOcrProcessor:
    """Extracts text from a PDF, one page at a time."""

    def __init__(
        self,
        engine: Optional[OcrEngine] = None,
        languages: Optional[list[str]] = None,
    ):
        """
        Args:
            engine: OCR backend. Defaults to the platform's engine.
            languages: Engine-native language codes. Defaults to the engine's own.
        """
        if engine is None:
            from components.ocr import get_engine

            engine = get_engine()
        self.engine = engine
        self.languages = languages
        self.dpi = None

    def detect_optimal_dpi(self, pdf_path) -> int:
        """Pick a rendering resolution from the first page's physical size."""
        try:
            with get_renderer(pdf_path) as renderer:
                if renderer.page_count() == 0:
                    return DEFAULT_DPI
                width_in, height_in = renderer.page_size_inches(0)
        except FileNotFoundError:
            raise
        except Exception as exc:
            print(f"Warning: could not auto-detect DPI ({exc}), using {DEFAULT_DPI}")
            return DEFAULT_DPI

        longest_edge = max(width_in, height_in)
        for limit, dpi, reason in DPI_BANDS:
            if longest_edge < limit:
                print(f"Auto-detected DPI: {dpi} ({reason})")
                print(f'  Page size: {width_in:.1f}" x {height_in:.1f}"')
                return dpi

        print(f"Auto-detected DPI: {FALLBACK_DPI} (very large document detected)")
        return FALLBACK_DPI

    def process(
        self,
        pdf_path,
        output_file: Optional[str] = None,
        dpi: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Extract text from every page of a PDF.

        Args:
            pdf_path: Path to the PDF.
            output_file: If given, the extracted text is also written here.
            dpi: Rendering resolution. Auto-detected when None.
            progress_callback: Called with a status string per page.

        Returns:
            The extracted text, with a '--- Page N ---' header per page.

        Raises:
            FileNotFoundError: The PDF does not exist.
            ValueError: The path is not a PDF.
            RuntimeError: The document could not be opened.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF: {pdf_path}")

        self._log(f"Processing PDF: {pdf_path.name}", progress_callback)

        if dpi is None:
            dpi = self.detect_optimal_dpi(pdf_path)
        self.dpi = dpi

        try:
            renderer = get_renderer(pdf_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to open PDF: {exc}") from exc

        try:
            total = renderer.page_count()
            self._log(f"Found {total} page(s)", progress_callback)

            sections = []
            for index in range(total):
                self._log(f"Processing page {index + 1}/{total}...", progress_callback)
                sections.append(self._process_page(renderer, index, dpi))
        finally:
            renderer.close()

        final_text = "\n".join(sections)

        if output_file:
            output_path = Path(output_file)
            output_path.write_text(final_text, encoding="utf-8")
            self._log(f"Text extracted and saved to: {output_path}", progress_callback)

        return final_text

    def _process_page(self, renderer, index: int, dpi: int) -> str:
        """Render and recognize one page. A page-level failure is recorded in
        the output rather than aborting the whole document."""
        try:
            page = renderer.render_page(index, dpi=dpi)
            text = self.engine.recognize(page, languages=self.languages)
        except Exception as exc:
            print(f"Warning: failed to process page {index + 1}: {exc}")
            return f"--- Page {index + 1} ---\n[OCR Error: {exc}]\n"
        return f"--- Page {index + 1} ---\n{text}\n"

    def _log(self, message: str, callback: Optional[Callable[[str], None]] = None):
        """Report progress via the callback if given, else stdout."""
        if callback:
            callback(message)
        else:
            print(message)


def ocr_pdf(pdf_path, output_file=None, dpi=None, languages=None) -> str:
    """Convenience wrapper for command-line use."""
    processor = PdfOcrProcessor(languages=languages)
    final_text = processor.process(pdf_path, output_file=output_file, dpi=dpi)

    if not output_file:
        print("\n" + "=" * 60)
        print("EXTRACTED TEXT:")
        print("=" * 60)
        print(final_text)

    return final_text


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_ocr.py <pdf_file> [output_file] [--dpi DPI] [--lang LANG]")
        print("\nExamples:")
        print("  python pdf_ocr.py document.pdf")
        print("  python pdf_ocr.py document.pdf output.txt --dpi 400")
        print("  python pdf_ocr.py document.pdf --lang pl-PL   # macOS (Vision)")
        print("  python pdf_ocr.py document.pdf --lang pol      # Windows/Linux")
        print("\nDPI is auto-detected by default based on page size.")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_file = None
    dpi = None
    languages = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--dpi" and i + 1 < len(sys.argv):
            dpi = int(sys.argv[i + 1])
            i += 2
        elif arg == "--lang" and i + 1 < len(sys.argv):
            languages = sys.argv[i + 1].split("+")
            i += 2
        elif not arg.startswith("--"):
            output_file = arg
            i += 1
        else:
            i += 1

    try:
        ocr_pdf(pdf_path, output_file, dpi=dpi, languages=languages)
        print("\n[OK] OCR completed successfully!")
    except Exception as exc:
        print(f"\n[FAIL] Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
