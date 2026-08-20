#!/usr/bin/env python3
"""Render resources/hero.svg to the og:image JPEG.

The hero is no longer displayed on the page — docs/index.html draws a live
ASCII terminal. This JPEG exists solely as the Open Graph / Twitter card
preview referenced by docs/index.html:16 and :22.

Usage:  python3 resources/render_hero.py
"""

import defusedxml.ElementTree as ET
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
        root = ET.fromstring(svg_markup)
    except ET.ParseError as exc:
        print(f"Error: {SOURCE} is not well-formed XML: {exc}")
        return 1

    # Read the render viewport from the SVG's own width/height rather than
    # a hardcoded 1920x1080: the wrapper CSS below stretches the SVG to
    # fill whatever viewport Playwright opens (width: 100vw; height: 100vh),
    # so a viewport that doesn't match the SVG's own aspect ratio would
    # silently distort the render -- non-uniform x/y scaling, not a crop --
    # with nothing here to catch it. Deriving from the file itself (not
    # from generate_hero_svg.CANVAS_W/CANVAS_H) keeps this correct even if
    # hero.svg is ever produced or hand-edited some other way.
    try:
        viewport_width = int(float(root.get("width")))
        viewport_height = int(float(root.get("height")))
    except (TypeError, ValueError) as exc:
        print(f"Error: {SOURCE} root <svg> is missing a numeric width/height: {exc}")
        return 1

    png = RESOURCES / "_render" / "hero.png"
    png.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(
                viewport={"width": viewport_width, "height": viewport_height}
            )
            page.set_content(_WRAPPER % svg_markup)
            page.screenshot(path=str(png))
        finally:
            browser.close()

    staging = TARGET.with_suffix(".tmp.jpg")
    try:
        with Image.open(png) as image:
            image.convert("RGB").save(staging, "JPEG", quality=85, optimize=True)

        size = staging.stat().st_size
        if size > MAX_BYTES:
            print(f"Error: {size:,} bytes exceeds {MAX_BYTES:,} byte budget")
            state = "left untouched" if TARGET.exists() else "not written"
            print(f"{TARGET.name} {state}")
            return 1

        staging.replace(TARGET)
    finally:
        # Covers both the over-budget return above and any exception raised
        # while opening/converting/saving: staging.replace() already moved
        # the file away on the success path, so this is a no-op there.
        staging.unlink(missing_ok=True)

    print(f"Wrote {TARGET.name}: {size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
