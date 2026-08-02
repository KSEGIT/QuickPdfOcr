#!/usr/bin/env python3
"""Regenerate tests/fixtures/sample_invoice.pdf. macOS only; run manually.

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
