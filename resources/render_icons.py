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

import os
import shutil
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from create_icns import create_icns_from_pngs
from icon_manifest import DETAILED, ICO_SIZES, RESOURCES, SIMPLE, SIZE_SOURCES

RENDER_DIR = RESOURCES / "_render"


def _atomic_copy(src: Path, dst: Path) -> None:
    """Copy src to dst via a same-directory temp file + os.replace().

    os.replace() is atomic on POSIX and, since Python 3.3, on Windows too,
    for a rename within the same filesystem -- guaranteed here since the
    temp file is a sibling of dst. This bounds each *individual* tracked
    file to "either the old bytes or the new bytes, never a partial write";
    it does not make the group of tracked-file updates below a single
    cross-file transaction, so a crash between two calls can still leave
    one file updated and the next stale. That residual window is far
    smaller than the one this replaces (a mid-copyfile crash could
    previously leave a single file half-written).
    """
    tmp = dst.with_name(dst.name + ".tmp")
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


# GitHub Pages publishes from main:/docs, so resources/ (outside that root)
# is unreachable from the published site with a relative path. docs/assets/
# holds the subset of rendered artefacts the page actually references,
# copied straight from the same masters so they cannot drift from
# resources/*.png. This is the single place those copies are produced.
DOCS_ASSETS = RESOURCES.parent / "docs" / "assets"

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

    # icon.icns assembly (below) requires the macOS-only iconutil binary and
    # raises an uncaught RuntimeError when it's absent. Checking that up
    # front -- before any tracked artefact is touched -- means a Linux or
    # Windows contributor following resources/README.md gets a clean error
    # instead of six visibly-updated PNGs/.ico plus a stale icon.icns that
    # packaging/quickpdfocr.spec then bakes into the app bundle.
    if shutil.which("iconutil") is None:
        print(
            "Error: iconutil not found. It is a macOS-only tool required to "
            "assemble icon.icns; run this pipeline on macOS. No tracked "
            "artefact has been modified."
        )
        return 1

    print("Rendering icon sizes...")
    pngs = render_all(RENDER_DIR)

    # Build icon.ico and icon.icns entirely inside the gitignored render
    # directory first. Only after *both* containers succeed do we start
    # copying anything into a tracked location -- so a failure in
    # rendering or assembly (e.g. a corrupt iconset, a permissions error)
    # can never leave some tracked artefacts updated and others stale. The
    # five _atomic_copy() calls below are each individually atomic (temp
    # file + os.replace()), but are not one cross-file transaction: a crash
    # between two of those calls can still leave one updated and the next
    # stale. That is a much smaller window than rendering/assembly failing
    # (which is what this section guards against), not a claim that the
    # whole run is transactional end to end.
    render_ico = RENDER_DIR / "icon.ico"
    images = [Image.open(pngs[s]).convert("RGBA") for s in ICO_SIZES]
    try:
        images[-1].save(
            render_ico,
            format="ICO",
            append_images=images[:-1],
            sizes=[(s, s) for s in ICO_SIZES],
        )
    finally:
        for image in images:
            image.close()
    print(f"Rendered icon.ico ({len(ICO_SIZES)} sizes)")

    render_icns = RENDER_DIR / "icon.icns"
    create_icns_from_pngs(pngs, render_icns)
    print("Rendered icon.icns")

    # Every container succeeded -- now, and only now, update the tracked
    # artefacts main.py and packaging/quickpdfocr.spec depend on, each via
    # _atomic_copy (see above for exactly what guarantee that does and does
    # not provide).
    _atomic_copy(pngs[256], RESOURCES / "icon.png")
    _atomic_copy(pngs[512], RESOURCES / "icon_512.png")
    _atomic_copy(pngs[32], RESOURCES / "favicon.png")
    _atomic_copy(render_ico, RESOURCES / "icon.ico")
    _atomic_copy(render_icns, RESOURCES / "icon.icns")
    print("Wrote icon.png, icon_512.png, favicon.png, icon.ico, icon.icns")

    # docs/index.html's <link rel="icon"> wants the same 32px favicon; its
    # header ".logo img" (the <a class="logo"> wrapper's child <img>)
    # renders into a 36px box, so the 64px slot (still from the simple
    # master — see the two-master rationale above) is the closest fit
    # rather than pulling the 256px detailed render.
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)
    docs_favicon = DOCS_ASSETS / "favicon.png"
    docs_logo = DOCS_ASSETS / "logo.png"
    _atomic_copy(pngs[32], docs_favicon)
    _atomic_copy(pngs[64], docs_logo)
    print(f"Wrote {docs_favicon}, {docs_logo}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
