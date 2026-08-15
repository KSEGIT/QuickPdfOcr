"""Guards for the character-grid ASCII blocks on docs/index.html."""
import re
from pathlib import Path

import pytest

from tests.test_site_theme import _declared_tokens, _resolve_token, read_index

INDEX = Path(__file__).resolve().parent.parent / "docs" / "index.html"

# The cp437/DEC-derived subset every mainstream monospace font carries.
# Rounded box-drawing is deliberately excluded — it is the least supported set.
ALLOWED_NON_ASCII = set("┌┐└┘├┤┬┴┼─│╔╗╚╝═║░▒▓█▀▄▶▼▲●○·")

FORBIDDEN = set("╭╮╰╯")

BLOCK_RE = re.compile(
    r'<pre[^>]*class="[^"]*\bascii-art\b[^"]*"[^>]*>(.*?)</pre>', re.S
)


def ascii_blocks() -> list[str]:
    """Every .ascii-art block's text content, inner tags stripped."""
    return [re.sub(r"<[^>]+>", "", b) for b in BLOCK_RE.findall(read_index())]


def test_twelve_icons_present():
    """8 feature + 1 privacy + 3 platform icons."""
    icons = re.findall(
        r'<pre[^>]*class="[^"]*\bascii-icon\b[^"]*"', read_index()
    )
    assert len(icons) == 12, f"expected 12 ascii-icon blocks, found {len(icons)}"


def test_no_svg_icons_remain():
    """The inline SVG icon set is fully replaced."""
    html = read_index()
    for cls in ("feature-icon", "privacy-icon", "platform-icon"):
        section = re.findall(rf'class="[^"]*\b{cls}\b[^"]*"[^>]*>(.*?)</div>',
                             html, re.S)
        assert section, f"no {cls} blocks found"
        assert not any("<svg" in s for s in section), f"{cls} still contains <svg"


def test_only_permitted_non_ascii_characters():
    blocks = ascii_blocks()
    assert blocks, "no .ascii-art blocks found"
    for block in blocks:
        bad = {c for c in block
               if ord(c) > 127 and c not in ALLOWED_NON_ASCII}
        assert not bad, f"forbidden characters {bad!r} in block: {block[:60]!r}"


def test_no_rounded_box_drawing_anywhere():
    """Rounded corners are banned across the whole document, not just blocks."""
    bad = FORBIDDEN & set(read_index())
    assert not bad, f"rounded box-drawing found: {bad!r}"


def test_icons_are_aria_hidden():
    for tag in re.findall(r"<pre[^>]*class=\"[^\"]*\bascii-art\b[^\"]*\"[^>]*>",
                          read_index()):
        assert 'aria-hidden="true"' in tag, f"missing aria-hidden: {tag}"


def test_every_icon_is_five_lines():
    """A consistent grid — every icon block is exactly 5 rows."""
    icon_re = re.compile(
        r'<pre[^>]*class="[^"]*\bascii-icon\b[^"]*"[^>]*>(.*?)</pre>', re.S
    )
    for raw in icon_re.findall(read_index()):
        text = re.sub(r"<[^>]+>", "", raw).strip("\n")
        lines = text.split("\n")
        assert len(lines) == 5, f"icon has {len(lines)} lines, expected 5:\n{text}"


def _rgb_string_to_hex(rgb: str) -> str:
    """Convert a browser-computed 'rgb(r, g, b)' string to '#RRGGBB'."""
    match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", rgb)
    assert match, f"unexpected computed colour format: {rgb!r}"
    r, g, b = (int(x) for x in match.groups())
    return f"#{r:02X}{g:02X}{b:02X}"


def test_icon_color_classes_map_to_their_tokens():
    """.icon-indigo / .icon-violet / .icon-cyan must each cascade their
    *own* token onto their .ascii-art <pre> child — not merely three
    distinct colours, but the exact indigo/violet/cyan assignment, so a
    bug that swaps two classes (e.g. violet and cyan transposed) is
    caught rather than passing as "still 3 distinct colours".

    Regression guard for a real cascade bug, not a hypothetical one:
    .ascii-art originally declared `color: var(--frame)` directly on the
    <pre> itself. A specified value on the element always beats an
    *inherited* value from an ancestor, no matter the ancestor's
    specificity — so the wrapping div's .icon-indigo/.icon-violet/.icon-cyan
    colour never reached the art, and all 12 icons rendered identically in
    --frame. Source inspection cannot see this; it only shows up in the
    browser's resolved cascade, so this test renders the real page with a
    headless engine and reads getComputedStyle() rather than parsing CSS.

    Playwright is asset-authoring tooling, not a runtime or test
    dependency — it is deliberately absent from requirements.txt and CI.
    The importorskip is scoped to this function (not module level) so a
    missing Playwright skips only this one browser-backed test, leaving
    the other six pure source/regex guards in this module to run and pass
    normally rather than taking the whole module down at collection time.
    """
    sync_playwright = pytest.importorskip(
        "playwright.sync_api", reason="asset tooling not installed"
    ).sync_playwright

    html = read_index()
    tokens = _declared_tokens(html)
    expected = {
        "icon-indigo": _resolve_token(tokens, "var(--frame)"),
        "icon-violet": _resolve_token(tokens, "var(--bar-ink)"),
        "icon-cyan": _resolve_token(tokens, "var(--accent)"),
    }

    url = INDEX.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url)
            actual = {}
            for cls in expected:
                el = page.query_selector(f".{cls} .ascii-art")
                assert el is not None, f"no .ascii-art found under .{cls}"
                computed = el.evaluate("e => getComputedStyle(e).color")
                actual[cls] = _rgb_string_to_hex(computed)
        finally:
            browser.close()

    assert actual == expected, (
        f"icon colour classes did not map to their tokens: {actual} != {expected}"
    )
