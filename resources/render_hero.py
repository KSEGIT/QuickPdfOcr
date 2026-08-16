#!/usr/bin/env python3
"""Render resources/hero.svg to the og:image JPEG.

The hero is no longer displayed on the page — docs/index.html draws a live
ASCII terminal. This JPEG exists solely as the Open Graph / Twitter card
preview referenced by docs/index.html:16 and :22.

Usage:  python3 resources/render_hero.py
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

RESOURCES = Path(__file__).resolve().parent
SOURCE = RESOURCES / "hero.svg"
TARGET = RESOURCES / "quick_pdf_hero_small.jpg"
MAX_BYTES = 350_000

_WRAPPER = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; padding: 0; }
svg { display: block; width: 100vw; height: 100vh; }
</style></head><body>%s</body></html>"""


def main() -> int:
    if not SOURCE.exists():
        print(f"Error: {SOURCE} not found")
        return 1

    svg_markup = SOURCE.read_text(encoding="utf-8")
    try:
        ET.fromstring(svg_markup)
    except ET.ParseError as exc:
        print(f"Error: {SOURCE} is not well-formed XML: {exc}")
        return 1

    png = RESOURCES / "_render" / "hero.png"
    png.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.set_content(_WRAPPER % svg_markup)
            page.screenshot(path=str(png))
        finally:
            browser.close()

    with Image.open(png) as image:
        image.convert("RGB").save(TARGET, "JPEG", quality=85, optimize=True)

    size = TARGET.stat().st_size
    print(f"Wrote {TARGET.name}: {size:,} bytes")
    if size > MAX_BYTES:
        print(f"Error: exceeds {MAX_BYTES:,} byte budget")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
