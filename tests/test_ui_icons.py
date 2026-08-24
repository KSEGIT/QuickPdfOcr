"""Guards for the desktop UI's emoji-to-Lucide-icon migration.

The UI used to embed emoji glyphs directly in button/label text (see the
whole-branch review that flagged this: decorative characters leaking into
accessible names). ui/main_window.py and ui/loading_screen.py now load
tinted SVGs from resources/icons/ via ui.icons.load_icon() instead. These
tests guard both halves of that migration: no emoji crept back into ui/
source, and every icon filename referenced by code actually exists on disk
(a typo'd name would otherwise ship a blank icon -- load_icon() catches a
missing file's FileNotFoundError and degrades to a null QIcon rather than
crashing, see test_load_icon_degrades_gracefully_for_a_missing_file below).
"""
import re
from pathlib import Path

import pytest

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
ICONS_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"

UI_SOURCE_FILES = sorted(UI_DIR.glob("*.py"))

# Emoji + symbol ranges actually capable of appearing in this codebase's
# history: pictographs (U+1F300-1FAFF, covers 📄📁🚀📋🔄🏠), dingbats/misc
# symbols (U+2600-27BF, covers ⚠✅❌), misc technical (U+2300-23FF, covers
# the hourglass ⏳), and the variation-selector range (U+FE00-FE0F) that
# trails several of those base codepoints (e.g. "⚠️" = U+26A0 + U+FE0F) --
# a scan blind to the selector would report the string "clean" after only
# the visible glyph was removed, missing the invisible codepoint left behind.
EMOJI_RANGES = (
    (0x1F300, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2300, 0x23FF),
    (0xFE00, 0xFE0F),
)


def _is_emoji_codepoint(cp: int) -> bool:
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES)


@pytest.mark.parametrize("path", UI_SOURCE_FILES, ids=lambda p: p.name)
def test_no_emoji_in_ui_source(path):
    """A simple codepoint-range scan, mirroring the site's charset guard in
    tests/test_ascii_art.py -- no emoji codepoint may appear anywhere in
    ui/*.py source."""
    text = path.read_text(encoding="utf-8")
    offenders = sorted({c for c in text if _is_emoji_codepoint(ord(c))})
    assert not offenders, (
        f"{path.name} still contains emoji codepoints: "
        f"{[hex(ord(c)) for c in offenders]}"
    )


# Every resources/icons/<name> the code actually loads, gathered from a
# literal scan of the two files rather than importing ui.main_window and
# introspecting it -- the string literal is what a typo would corrupt, so
# the test must read exactly what a typo would touch.
ICON_LOAD_RE = re.compile(r'load_icon\(\s*"([^"]+\.svg)"')


def _referenced_icon_names() -> set[str]:
    names = set()
    for path in UI_SOURCE_FILES:
        names.update(ICON_LOAD_RE.findall(path.read_text(encoding="utf-8")))
    return names


def test_exactly_five_icons_are_referenced():
    """Pinned to the exact count (one per button: Open, Start OCR, Copy,
    Try Again, Start Over) rather than a >= floor, which would silently
    tolerate the count dropping along with a button losing its icon, not
    just the zero-matches case a >= floor is meant to catch. The other four
    vendored icons (file-text, triangle-alert, circle-check, circle-x) are
    committed and license-attributed but deliberately unused -- the status
    labels and drop zone they'd have served use colour alone instead (see
    the desktop-ui report's "Status-label decision" section)."""
    assert len(_referenced_icon_names()) == 5, (
        f"expected exactly 5 load_icon() references, found "
        f"{sorted(_referenced_icon_names())}"
    )


@pytest.mark.parametrize("name", sorted(_referenced_icon_names()))
def test_every_referenced_icon_exists(name):
    """Every icon filename load_icon() is called with must exist under
    resources/icons/, or QIcon silently renders blank for that button."""
    assert (ICONS_DIR / name).exists(), (
        f"ui/ references resources/icons/{name}, but that file is missing"
    )


def test_load_icon_degrades_gracefully_for_a_missing_file(qapp, capsys):
    """A missing icon asset (e.g. a packaging step that has not been taught
    to bundle resources/icons/ yet -- see the desktop-ui report) must not
    crash window construction. ui.icons.load_icon() catches
    FileNotFoundError and returns a null QIcon with a stderr warning,
    mirroring main.py's own app-icon loading convention, rather than
    propagating and aborting MainWindow.__init__() partway through."""
    from ui.icons import load_icon

    icon = load_icon("does-not-exist.svg", "#0F172A", 18)

    assert icon.isNull()
    assert "does-not-exist.svg" in capsys.readouterr().err


def test_load_icon_degrades_gracefully_for_a_malformed_svg(qapp, capsys, monkeypatch):
    """A corrupted-but-present icon file is a different failure mode than a
    missing one: QSvgRenderer does not raise on invalid markup -- it just
    parses nothing, and render() onto a filled-transparent QPixmap silently
    paints nothing, leaving the icon *not null* but fully blank (0 painted
    pixels, verified experimentally). That is exactly the "ships a blank
    icon with no warning" outcome the FileNotFoundError handling exists to
    prevent, just via a corrupted file rather than a missing one. ui.icons
    checks QSvgRenderer.isValid() and raises to trigger the same graceful
    fallback."""
    import ui.icons as icons_mod

    monkeypatch.setattr(icons_mod, "_tinted_svg_bytes", lambda name, color: b"<svg><broken")
    icons_mod._tinted_pixmap.cache_clear()

    icon = icons_mod.load_icon("folder-open.svg", "#0F172A", 18)

    assert icon.isNull()
    assert "folder-open.svg" in capsys.readouterr().err
    icons_mod._tinted_pixmap.cache_clear()


def test_load_icon_disabled_color_registers_a_distinct_disabled_pixmap(qapp):
    """disabled_color registers a second pixmap for QIcon::Disabled mode.
    Without it, Qt auto-generates a disabled-state pixmap via its style's
    default grey-out algorithm -- measured experimentally at #6C6C6C, only
    2.79:1 on SURFACE (below even the 3:1 non-text floor) regardless of
    what the Normal-mode colour was. open_btn/start_ocr_btn in
    ui/main_window.py pass disabled_color=DIM (5.71:1 on SURFACE) for
    exactly this reason -- see tests/test_main_window_theme.py for the
    end-to-end check on those two buttons."""
    from PySide6.QtGui import QIcon
    from ui.icons import load_icon

    icon = load_icon("folder-open.svg", "#0F172A", 18, disabled_color="#94A3B8")

    normal_pixel = _first_opaque_pixel(icon.pixmap(18, 18, QIcon.Mode.Normal))
    disabled_pixel = _first_opaque_pixel(icon.pixmap(18, 18, QIcon.Mode.Disabled))
    assert normal_pixel == "#0f172a"
    assert disabled_pixel == "#94a3b8"


def _first_opaque_pixel(pixmap):
    img = pixmap.toImage()
    for y in range(img.height()):
        for x in range(img.width()):
            color = img.pixelColor(x, y)
            if color.alpha() == 255:
                return color.name()
    return None


def test_vendored_icons_still_use_current_color():
    """load_icon() (ui/icons.py) works by substituting the literal
    stroke="currentColor" placeholder in each vendored SVG. If a future
    edit to resources/icons/*.svg ever hardcodes a colour instead, the
    substitution becomes a silent no-op and every icon in the app renders
    in whatever colour that file happens to hardcode, ignoring the palette
    entirely -- this pins the precondition load_icon() depends on."""
    for svg_path in sorted(ICONS_DIR.glob("*.svg")):
        assert 'stroke="currentColor"' in svg_path.read_text(encoding="utf-8"), (
            f"{svg_path.name} no longer uses stroke=\"currentColor\"; "
            "ui/icons.py's tinting will silently stop working for it"
        )
