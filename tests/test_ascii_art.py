"""Guards for the character-grid ASCII blocks on docs/index.html."""
import re

from tests.test_site_theme import read_index

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
