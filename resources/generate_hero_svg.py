#!/usr/bin/env python3
"""Generate resources/hero.svg -- the og:image source scene.

Why this exists (2026-08-19 site-fix review, finding #6): the previous
hero.svg was hand-tuned once and never regenerated from source -- 31
`<text>` runs at hardcoded per-column x offsets (`760 + n*20.47`, a
0.60206em advance baked in for whatever monospace font resolved on the
author's machine at the time). Any font with a different per-character
advance -- e.g. Consolas on Windows, at 0.5498em -- reflows every run to the
wrong x position, so the frame's right edge and closing corner stop lining
up under the rows above them. `render_hero.py` only validates XML
well-formedness and a byte budget, so a misaligned render like that would
still exit 0.

The fix here is not "recompute more accurate hardcoded offsets" (that just
moves the bug to a different font); it is to stop hardcoding offsets at all.
Each row below is ONE `<text>` element containing one or more `<tspan>`
children. Only the first tspan-implicit position (the `<text>`'s own x) is
set explicitly; every later tspan carries no `x`/`y` of its own, so the SVG
text-layout engine places it immediately after the previous glyph using
whatever font actually resolved -- exactly the same mechanism a browser
uses to lay out a paragraph. Two rows with the same character count end up
the same rendered width on ANY monospace font, because that parity falls
out of the font's own (consistent) advance width rather than out of a
number this script assumed in advance. This is the same font-independence
goal `tests/test_icon_masters.py::test_glyphs_are_paths_not_text` enforces
for the icon masters via vector paths -- hero.svg stays text-based (full
glyph-to-path conversion is a materially larger job, left as recorded
debt), but tspan flow removes the specific *hardcoded-offset* failure mode
that broke this file, without requiring that conversion.

Usage:
    .venv/bin/pip install -r resources/requirements-assets.txt
    .venv/bin/playwright install chromium
    .venv/bin/python resources/generate_hero_svg.py   # writes hero.svg
    .venv/bin/python resources/render_hero.py          # hero.svg -> og:image JPEG

Run on the same machine, back to back: generation measures real glyph
metrics for whatever font is actually installed, and the very next step
(render_hero.py) screenshots that same SVG through the same browser engine,
so there is no window for the font to change out from under the layout.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RESOURCES = Path(__file__).resolve().parent
TARGET = RESOURCES / "hero.svg"

CANVAS_W, CANVAS_H = 1920, 1080

# Matches docs/index.html's --mono exactly (including the "Liberation Mono"
# fallback that file's stack carries and the pre-existing hero.svg lacked),
# so the og:image reads with the same typeface family as the live page.
FONT_STACK = (
    "ui-monospace, SFMono-Regular, Menlo, Consolas, "
    "'DejaVu Sans Mono', 'Liberation Mono', monospace"
)
FONT_SIZE = 34
ROW_DY = 48  # px between row baselines

INK = "#818CF8"   # --frame: default terminal ink, matches .ascii-art.hero-terminal
BEAM = "#22D3EE"  # --accent: .beam span
FILL = "#A78BFA"  # --bar-ink: .fill span

# Mirrors docs/index.html's #hero .hero-terminal <pre> content exactly (see
# tests/test_ascii_art.py::test_hero_terminal_is_fixed_46_columns for the
# 46-column invariant on every framed row). None marks a blank source line
# (no <text> emitted, but the row still advances the baseline for rhythm).
Row = list[tuple[str, str]]

# The frame rows are built from plain strings and then asserted at exactly
# 46 columns, the same invariant docs/index.html's hero terminal is held to
# -- rather than typed out by hand character-by-character where a single
# off-by-one silently breaks the frame. This also guarantees hero.svg and
# the live page's hero terminal content can't quietly drift apart.
_TITLE = "┌─ OCR in progress "
_TITLE = _TITLE + "─" * (46 - len(_TITLE) - 1) + "┐"
_TRACK = "│  " + "░" * 40 + "  │"
_BEAM_TEXT = "│  " + "═" * 40 + "  │"
_FILLBAR = "│  " + "▓" * 40 + "  │"
_PROGRESS_PREFIX = "│  ["
_PROGRESS_FILL = "█" * 16
_PROGRESS_SUFFIX = "░" * 6 + "] 71%" + " " * 14 + "│"
_STATUS = "│  page 12/17  ·  vision.framework           │"
_CLOSE = "└" + "─" * 44 + "┘"

for _row in (_TITLE, _TRACK, _BEAM_TEXT, _FILLBAR, _STATUS, _CLOSE):
    assert len(_row) == 46, f"frame row is {len(_row)} cols, not 46: {_row!r}"
assert len(_PROGRESS_PREFIX) + len(_PROGRESS_FILL) + len(_PROGRESS_SUFFIX) == 46

ROWS = [
    [("  QuickPdfOcr · report.pdf", INK)],
    None,
    [(_TITLE, INK)],
    [(_TRACK, INK)],
    [("│  ", INK), ("═" * 40, BEAM), ("  │", INK)],
    [(_FILLBAR, INK)],
    [(_PROGRESS_PREFIX, INK), (_PROGRESS_FILL, FILL), (_PROGRESS_SUFFIX, INK)],
    [(_STATUS, INK)],
    [(_CLOSE, INK)],
    None,
    [("  4,812 words copied to clipboard", INK)],
]


def _row_svg(row: Row, x: float, y: float) -> str:
    tspans = "".join(
        f'<tspan fill="{color}">{_escape(text)}</tspan>' for text, color in row
    )
    return f'<text x="{x}" y="{y}">{tspans}</text>'


def _escape(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    # U+00A0 (non-breaking space), not U+0020: verified empirically (see the
    # module docstring's measurement notes) that this Chromium build
    # collapses runs of two or more *regular* spaces inside SVG <text>/
    # <tspan> content -- silently, in the actual paint, not just DOM
    # serialization -- regardless of xml:space="preserve" or CSS
    # white-space: pre on an ancestor. A 46-column row with a 2- or
    # 11-space gap (most of these have one) then renders shorter than a
    # same-length row without one, which is exactly the kind of
    # per-row-width drift this rewrite exists to eliminate. NBSP is not
    # subject to that collapsing and was confirmed to render at the same
    # per-character advance as every other glyph tested (~20.47px at
    # font-size 34 on this machine's resolved font) -- this is what
    # actually makes single-<text>-per-row tspan flow produce equal widths
    # for equal character counts, not the tspan-flow mechanism alone.
    return escaped.replace(" ", "\u00A0")  # NBSP, spelled out: see comment above


def _build_group(left_x: float, top_y: float) -> str:
    parts = []
    y = top_y
    for row in ROWS:
        if row is not None:
            parts.append(_row_svg(row, left_x, y))
        y += ROW_DY
    inner = "\n    ".join(parts)
    return (
        f'<g font-family="{FONT_STACK}" font-size="{FONT_SIZE}" '
        f'xml:space="preserve">\n    {inner}\n  </g>'
    )


def _measure(left_x: float, top_y: float) -> tuple[float, float]:
    """Render ROWS at the given position and return (frame_width, block_height).

    Both are position-independent (pure translation does not change a row's
    own rendered width or the group's total height), so this only needs to
    run once; main() reuses the two numbers to compute a centred position
    rather than re-measuring after moving the text.
    """
    group_markup = _build_group(left_x, top_y)
    wrapper = f"""<!doctype html><html><head><meta charset="utf-8"></head>
    <body style="margin:0">
      <svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}"
           viewBox="0 0 {CANVAS_W} {CANVAS_H}">
        {group_markup}
      </svg>
    </body></html>"""

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": CANVAS_W, "height": CANVAS_H})
            page.set_content(wrapper)

            # Regression check for the exact bug this rewrite fixes: every
            # framed row must render to the same pixel width on whatever
            # font actually resolved, or the box will not visually close.
            # Measures each row's <text> element (not the boxed-frame rows
            # by y-position, keeping this generic to the ROWS list above).
            widths = page.evaluate(
                """() => [...document.querySelectorAll('text')]
                    .map(t => t.getComputedTextLength())"""
            )
            frame_row_indices = [i for i, r in enumerate(ROWS) if r is not None]
            # Frame rows are every non-None row except the header (0) and
            # footer (last) -- those are intentionally shorter.
            framed_widths = [
                w for idx, w in zip(frame_row_indices, widths)
                if idx not in (frame_row_indices[0], frame_row_indices[-1])
            ]
            spread = max(framed_widths) - min(framed_widths)
            if spread > 0.5:
                raise SystemExit(
                    f"Error: framed rows render to inconsistent widths "
                    f"(spread {spread:.2f}px) -- the frame will not close. "
                    f"Widths: {framed_widths}"
                )
            frame_width = framed_widths[0]

            bbox = page.evaluate(
                """() => {
                    const g = document.querySelector('svg > g');
                    return g.getBBox().height;
                }"""
            )
        finally:
            browser.close()

    return frame_width, bbox


def main() -> int:
    # Pass 1: measure at an arbitrary position, purely to learn how wide the
    # frame rows and how tall the whole block render on this machine's font.
    try:
        frame_width, block_height = _measure(left_x=200, top_y=340)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1

    pad_x, pad_y = 56, 46
    card_w = frame_width + 2 * pad_x
    card_h = block_height + 2 * pad_y

    # Pass 2: centre that measured card on the canvas and lay the real rows
    # out at the position derived from it.
    card_x = (CANVAS_W - card_w) / 2
    card_y = (CANVAS_H - card_h) / 2
    left_x = card_x + pad_x
    top_y = card_y + pad_y + FONT_SIZE * 0.8  # baseline sits below the cap height

    group_markup = _build_group(left_x, top_y)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0F172A"/>
      <stop offset="1" stop-color="#1E1B4B"/>
    </linearGradient>
    <radialGradient id="glowfield" cx="0.62" cy="0.5" r="0.55">
      <stop offset="0" stop-color="#312E81" stop-opacity="0.45"/>
      <stop offset="1" stop-color="#312E81" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="url(#bg)"/>
  <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="url(#glowfield)"/>

  <!-- Sharp corners (rx omitted), matching the live site's sharp cornered
       terminal aesthetic; the previous rx="16" predated that rebrand. -->
  <rect x="{card_x:.2f}" y="{card_y:.2f}" width="{card_w:.2f}" height="{card_h:.2f}"
        fill="#0B1220" fill-opacity="0.72" stroke="{INK}" stroke-opacity="0.35" stroke-width="1.5"/>

  {group_markup}
</svg>
"""

    TARGET.write_text(svg, encoding="utf-8")
    size = TARGET.stat().st_size
    print(f"Wrote {TARGET.name}: {size:,} bytes, frame rows {frame_width:.2f}px wide")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
