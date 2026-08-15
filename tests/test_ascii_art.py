"""Guards for the character-grid ASCII blocks on docs/index.html."""
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.test_site_theme import read_index

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


def test_icon_color_classes_render_three_distinct_colours():
    """.icon-indigo / .icon-violet / .icon-cyan must cascade a distinct
    computed `color` onto their .ascii-art <pre> child.

    Regression guard for a real cascade bug, not a hypothetical one:
    .ascii-art originally declared `color: var(--frame)` directly on the
    <pre> itself. A specified value on the element always beats an
    *inherited* value from an ancestor, no matter the ancestor's
    specificity — so the wrapping div's .icon-indigo/.icon-violet/.icon-cyan
    colour never reached the art, and all 12 icons rendered identically in
    --frame. Source inspection cannot see this; it only shows up in the
    browser's resolved cascade, so this test renders the real page with a
    headless engine and reads getComputedStyle() rather than parsing CSS.
    """
    url = INDEX.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url)
            colors = {}
            for cls in ("icon-indigo", "icon-violet", "icon-cyan"):
                el = page.query_selector(f".{cls} .ascii-art")
                assert el is not None, f"no .ascii-art found under .{cls}"
                colors[cls] = el.evaluate("e => getComputedStyle(e).color")
        finally:
            browser.close()

    assert len(set(colors.values())) == 3, (
        f"expected 3 distinct computed colours across .icon-indigo/.icon-violet/"
        f".icon-cyan, got {colors}"
    )
