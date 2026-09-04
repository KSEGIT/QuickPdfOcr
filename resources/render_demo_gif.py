#!/usr/bin/env python3
"""Render docs/assets/quickpdfocr-demo.gif: the animated demo loop.

An ASCII mock of the QuickPdfOcr window (drop a PDF, scan beam sweeps the
page, result copied) drawn with the brand charset and palette from
specs/2026-08-15-ascii-terminal-brand-design.md. One HTML page per frame via
Playwright on a fixed monospace grid, assembled with ffmpeg's two-pass
palette. Requires resources/requirements-assets.txt and ffmpeg on PATH.

Usage:  python3 resources/render_demo_gif.py
"""

import math
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

RESOURCES = Path(__file__).resolve().parent
RENDER_DIR = RESOURCES / "_render" / "demo"
TARGET = RESOURCES.parent / "docs" / "assets" / "quickpdfocr-demo.gif"

WIDTH, HEIGHT = 1200, 675
FPS = 12
FRAMES = 108  # 9s seamless loop
TARGET_BYTES = 2_000_000
MAX_BYTES = 5_000_000

BG = "#0F172A"
TEXT = "#E2E8F0"
DIM = "#94A3B8"
FRAME_INK = "#818CF8"
BAR_INK = "#A78BFA"
ACCENT = "#22D3EE"

INNER = 62  # window content columns
ROWS = 20  # window content rows

# Timeline boundaries, in frames: flight 0-11, landed 12-17, button flash
# 18-23, scan 24-77, done buttons 78-89, copied status + cursor 90-107.
LAND, CLICK, SCAN, DONE = 12, 24, 78, 90

_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body {{ margin: 0; padding: 0; background: {bg}; }}
body {{ width: {w}px; height: {h}px; display: flex;
        align-items: center; justify-content: center; }}
pre {{ margin: 0; color: {text};
       font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
       font-size: 24px; line-height: 24px; }}
.f {{ color: {frame}; }}
.d {{ color: {dim}; }}
.a {{ color: {accent}; }}
.b {{ color: {bar}; }}
.inv {{ background: {accent}; color: {bg}; }}
</style></head><body><pre>%s</pre></body></html>"""

_CARD = [
    [("┌──────────────────┐", "f")],
    [("│", "f"), (" ", ""), (">", "a"), (" report.pdf     ", ""), ("│", "f")],
    [("│", "f"), ("   17 pages       ", "d"), ("│", "f")],
    [("└────────┬─────────┘", "f")],
    [(" " * 9, ""), ("▼", "a")],
]


def _pad(segs, width=INNER):
    return segs + [(" " * (width - sum(len(t) for t, _ in segs)), "")]


def _center(segs, width=INNER):
    left = (width - sum(len(t) for t, _ in segs)) // 2
    return [(" " * left, "")] + segs


def _drop_content(f):
    rows = [[] for _ in range(ROWS)]
    if f < LAND:
        card_top = round(4 * (f / (LAND - 1)) ** 2)
        left = (INNER - 20) // 2
        for i, line in enumerate(_CARD):
            rows[card_top + i] = [(" " * left, "")] + line
    dz_cls = "a" if LAND <= f < LAND + 2 else "d"
    dz_left = (INNER - 34) // 2
    rows[9] = [(" " * dz_left, ""), ("┌" + " ─" * 16 + "┐", dz_cls)]
    rows[11] = [(" " * (dz_left + 10), ""), ("Drop PDF here", "")]
    rows[13] = [(" " * (dz_left + 8), ""), ("[ Open PDF File ]", "d")]
    rows[15] = [(" " * dz_left, ""), ("└" + " ─" * 16 + "┘", dz_cls)]
    if f >= LAND:
        rows[16] = _center([("ready · report.pdf · 17 pages", "d")])
        cls = "inv" if LAND + 6 <= f < LAND + 9 else ""
        rows[18] = _center([("[ Start OCR ]", cls)])
    return rows


def _scan_content(f):
    rows = [[] for _ in range(ROWS)]
    i = min(f, SCAN - 1) - CLICK  # 0..53; frames past SCAN pin the end state
    p = (i + 1) / (SCAN - CLICK)
    left = (INNER - 20) // 2
    rows[1] = [(" " * left, ""), ("┌──────────────────┐", "d")]
    beam = int(p * 10)
    for r in range(10):
        if r < beam or beam >= 10:
            run = ("▓" * 18, "b")
        elif r == beam:
            run = ("═" * 18, "a")
        else:
            run = ("░" * 18, "d")
        rows[2 + r] = [(" " * left, ""), ("│", "d"), run, ("│", "d")]
    rows[12] = [(" " * left, ""), ("└──────────────────┘", "d")]
    filled = round(p * 16)
    rows[14] = _center([
        ("[", ""), ("█" * filled, "b"), ("░" * (16 - filled), "d"),
        ("]", ""), (f" {round(p * 100):>3}%", ""),
    ])
    page = min(17, max(1, math.ceil(p * 17)))
    rows[16] = _center([(f"page {page}/17 · vision.framework", "d")])
    if f >= SCAN:
        cls = "inv" if SCAN + 3 <= f < SCAN + 7 else ""
        rows[18] = _center([
            ("[ Copy to Clipboard ]", cls), ("   ", ""), ("[ Start Over ]", "d"),
        ])
    if f >= DONE:
        cursor = "_" if (f - DONE) % 6 < 3 else " "
        rows[19] = _center([
            ("> ", "a"), ("4,812 words copied to clipboard", ""), (cursor, "a"),
        ])
    return rows


def _segs_html(segs):
    return "".join(
        f'<span class="{cls}">{text}</span>' if cls else text
        for text, cls in segs if text
    )


def _frame_html(f):
    body = _drop_content(f) if f < CLICK else _scan_content(f)
    grid = [
        [("┌" + "─" * INNER + "┐", "f")],
        [("│", "f")] + _pad([("  ", ""), ("● ● ●", "d"), ("   QuickPdfOcr", "")])
        + [("│", "f")],
        [("├" + "─" * INNER + "┤", "f")],
    ]
    grid += [[("│", "f")] + _pad(row) + [("│", "f")] for row in body]
    grid.append([("└" + "─" * INNER + "┘", "f")])
    return _HTML.format(
        bg=BG, w=WIDTH, h=HEIGHT, text=TEXT,
        frame=FRAME_INK, dim=DIM, accent=ACCENT, bar=BAR_INK,
    ) % "\n".join(_segs_html(line) for line in grid)


def _render_frames(frame_dir):
    shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=1,
            )
            for f in range(FRAMES):
                page.set_content(_frame_html(f))
                page.screenshot(path=str(frame_dir / f"f_{f:03d}.png"))
        finally:
            browser.close()


def _assemble(frame_dir, out_gif):
    palette = frame_dir / "palette.png"
    pattern = str(frame_dir / "f_%03d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
         "-i", pattern,
         "-vf", "palettegen=max_colors=64:stats_mode=diff", str(palette)],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
         "-i", pattern, "-i", str(palette),
         "-lavfi", "paletteuse=dither=none:diff_mode=rectangle",
         "-loop", "0", str(out_gif)],
        check=True,
    )


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg not found on PATH")
        return 1

    print(f"Rendering {FRAMES} frames...")
    _render_frames(RENDER_DIR)

    rendered = RENDER_DIR / "quickpdfocr-demo.gif"
    _assemble(RENDER_DIR, rendered)
    size = rendered.stat().st_size
    if size > MAX_BYTES:
        print(f"Error: {size:,} bytes exceeds {MAX_BYTES:,} byte budget")
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    staging = TARGET.with_suffix(".tmp.gif")
    try:
        shutil.copyfile(rendered, staging)
        os.replace(staging, TARGET)
    finally:
        staging.unlink(missing_ok=True)

    with Image.open(TARGET) as gif:
        print(
            f"Wrote {TARGET}: {gif.width}x{gif.height}, "
            f"{gif.n_frames} frames, {gif.info.get('duration')}ms/frame, "
            f"loop={gif.info.get('loop')}, {size:,} bytes"
        )
    if size > TARGET_BYTES:
        print(f"Warning: above the {TARGET_BYTES:,} byte target")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
