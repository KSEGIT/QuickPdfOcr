#!/usr/bin/env python3
"""Regenerate tests/fixtures/sample_invoice.pdf and sample_multipage.pdf.

macOS only; run manually.

    python tests/fixtures/make_fixture.py

The content deliberately mirrors issue #26: a Polish invoice, which exercises
non-ASCII-adjacent text and the pl-PL recognition language.
"""

from pathlib import Path

import Quartz
from Foundation import NSURL

LINES = [
    b"FAKTURA VAT PL6972514",
    b"Kwota brutto: 1234,56 PLN",
    b"NIP 527-10-26-863",
    b"Termin platnosci: 2026-08-14",
]

out = Path(__file__).parent / "sample_invoice.pdf"
url = NSURL.fileURLWithPath_(str(out))
ctx = Quartz.CGPDFContextCreateWithURL(url, Quartz.CGRectMake(0, 0, 595, 842), None)
Quartz.CGPDFContextBeginPage(ctx, None)
Quartz.CGContextSelectFont(ctx, b"Helvetica", 24.0, Quartz.kCGEncodingMacRoman)
Quartz.CGContextSetTextDrawingMode(ctx, Quartz.kCGTextFill)
for i, line in enumerate(LINES):
    Quartz.CGContextShowTextAtPoint(ctx, 60, 700 - i * 40, line, len(line))
Quartz.CGPDFContextEndPage(ctx)
Quartz.CGPDFContextClose(ctx)
print(f"wrote {out}")

# Three-page fixture used to test that OCR containment (one bad page does not
# abort the rest of the document) actually exercises multiple pages, not just
# a single-page document that happens to fail.
multipage_out = Path(__file__).parent / "sample_multipage.pdf"
multipage_url = NSURL.fileURLWithPath_(str(multipage_out))
multipage_ctx = Quartz.CGPDFContextCreateWithURL(
    multipage_url, Quartz.CGRectMake(0, 0, 595, 842), None
)
for page_num in range(1, 4):
    page_lines = [
        f"STRONA {page_num}".encode("ascii"),
        f"Kwota brutto: {page_num}00,00 PLN".encode("ascii"),
    ]
    Quartz.CGPDFContextBeginPage(multipage_ctx, None)
    Quartz.CGContextSelectFont(multipage_ctx, b"Helvetica", 24.0, Quartz.kCGEncodingMacRoman)
    Quartz.CGContextSetTextDrawingMode(multipage_ctx, Quartz.kCGTextFill)
    for i, line in enumerate(page_lines):
        Quartz.CGContextShowTextAtPoint(multipage_ctx, 60, 700 - i * 40, line, len(line))
    Quartz.CGPDFContextEndPage(multipage_ctx)
Quartz.CGPDFContextClose(multipage_ctx)
print(f"wrote {multipage_out}")

# Two-page fixture with no drawn text on either page. Used to test that the
# self-test entry point (main._run_selftest) correctly reports "no text
# extracted" for a document Vision/Tesseract legitimately return nothing for,
# rather than false-passing on the "--- Page N ---" headers PdfOcrProcessor
# adds regardless of content.
blank_out = Path(__file__).parent / "sample_blank.pdf"
blank_url = NSURL.fileURLWithPath_(str(blank_out))
blank_ctx = Quartz.CGPDFContextCreateWithURL(
    blank_url, Quartz.CGRectMake(0, 0, 595, 842), None
)
for _ in range(2):
    Quartz.CGPDFContextBeginPage(blank_ctx, None)
    Quartz.CGPDFContextEndPage(blank_ctx)
Quartz.CGPDFContextClose(blank_ctx)
print(f"wrote {blank_out}")
