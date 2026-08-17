#!/usr/bin/env python3
"""Render every raster icon artefact from the two SVG masters.

The detailed master (icon.svg) feeds 128px and above; the simplified
master (icon_small.svg) feeds 64px and below, so Dock, taskbar and
favicon sizes stay legible instead of becoming a smear of the large art.

Requires resources/requirements-assets.txt (Playwright + Pillow) and
`playwright install chromium`. This is asset tooling, not a runtime
dependency of the app.

Usage:  python3 resources/render_icons.py
"""

import shutil
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from create_icns import create_icns_from_pngs

RESOURCES = Path(__file__).resolve().parent
DETAILED = RESOURCES / "icon.svg"
SIMPLE = RESOURCES / "icon_small.svg"
RENDER_DIR = RESOURCES / "_render"

# GitHub Pages publishes from main:/docs, so resources/ (outside that root)
# is unreachable from the published site with a relative path. docs/assets/
# holds the subset of rendered artefacts the page actually references,
# copied straight from the same masters so they cannot drift from
# resources/*.png. This is the single place those copies are produced.
DOCS_ASSETS = RESOURCES.parent / "docs" / "assets"

SIZE_SOURCES = {
    16: SIMPLE,
    32: SIMPLE,
    48: SIMPLE,
    64: SIMPLE,
    128: DETAILED,
    256: DETAILED,
    512: DETAILED,
    1024: DETAILED,
}

ICO_SIZES = [16, 32, 48, 64, 128, 256]

_WRAPPER = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; padding: 0; background: transparent; }
svg { display: block; width: 100vw; height: 100vh; }
</style></head><body>%s</body></html>"""


def render_all(out_dir: Path) -> dict[int, Path]:
    """Render each size from its designated master. Returns {size: png_path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: dict[int, Path] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for size, master in sorted(SIZE_SOURCES.items()):
                page = browser.new_page(
                    viewport={"width": size, "height": size},
                    device_scale_factor=1,
                )
                page.set_content(_WRAPPER % master.read_text(encoding="utf-8"))
                target = out_dir / f"icon_{size}.png"
                page.screenshot(path=str(target), omit_background=True)
                page.close()
                rendered[size] = target
                print(f"  rendered {size:>4}px from {master.name}")
        finally:
            browser.close()

    return rendered


def main() -> int:
    for master in (DETAILED, SIMPLE):
        if not master.exists():
            print(f"Error: master not found: {master}")
            return 1

    print("Rendering icon sizes...")
    pngs = render_all(RENDER_DIR)

    shutil.copyfile(pngs[256], RESOURCES / "icon.png")
    shutil.copyfile(pngs[512], RESOURCES / "icon_512.png")
    shutil.copyfile(pngs[32], RESOURCES / "favicon.png")
    print("Wrote icon.png, icon_512.png, favicon.png")

    # docs/index.html's <link rel="icon"> wants the same 32px favicon; its
    # header ".logo img" (the <a class="logo"> wrapper's child <img>)
    # renders into a 36px box, so the 64px slot (still from the simple
    # master — see the two-master rationale above) is the closest fit
    # rather than pulling the 256px detailed render.
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)
    docs_favicon = DOCS_ASSETS / "favicon.png"
    docs_logo = DOCS_ASSETS / "logo.png"
    shutil.copyfile(pngs[32], docs_favicon)
    shutil.copyfile(pngs[64], docs_logo)
    print(f"Wrote {docs_favicon}, {docs_logo}")

    images = [Image.open(pngs[s]).convert("RGBA") for s in ICO_SIZES]
    images[-1].save(
        RESOURCES / "icon.ico",
        format="ICO",
        append_images=images[:-1],
        sizes=[(s, s) for s in ICO_SIZES],
    )
    for image in images:
        image.close()
    print(f"Wrote icon.ico ({len(ICO_SIZES)} sizes)")

    create_icns_from_pngs(pngs, RESOURCES / "icon.icns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
