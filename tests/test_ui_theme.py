"""Palette + contrast guards for the desktop UI's dark terminal theme.

Mirrors tests/test_site_theme.py's approach for the web half of the same
design system: pin the palette's exact hex values, then re-derive the
contrast ratio of every foreground/background pair the UI actually paints
from those constants rather than a hardcoded expectation. That is the check
whose absence let docs/index.html originally ship a --bar/--bar-ink
confusion (2.84:1 used as a text colour) before it was measured -- "measure;
do not eyeball" is the standing directive this file follows for the desktop
half.
"""
import pytest

from ui import theme

TEXT_CONTRAST_MIN = 4.5
FILL_CONTRAST_MIN = 3.0

# The eleven palette tokens this task's brief specified, exact hex. Eight of
# them (BG, SURFACE, FRAME, ACCENT, BAR, BAR_INK, TEXT, DIM) also appear in
# specs/2026-08-15-ascii-terminal-brand-design.md and docs/index.html's
# :root -- this test does not re-read those files, so it cannot itself prove
# ui/theme.py agrees with them (tests/test_site_theme.py is what pins the
# site's own copies). OK, WARN, and ERR are new semantic-state colours this
# desktop UI task introduced, with no prior spec-doc or site-CSS value to
# check against at all -- see ui/theme.py's module docstring for the full
# provenance breakdown. For all eleven, what this test *does* prove is that
# ui/theme.py's declared value has not silently drifted from the exact hex
# specified for it.
SPEC_PALETTE = {
    "BG": "#0F172A",
    "SURFACE": "#1E293B",
    "FRAME": "#818CF8",
    "ACCENT": "#22D3EE",
    "BAR": "#7C3AED",
    "BAR_INK": "#A78BFA",
    "TEXT": "#E2E8F0",
    "DIM": "#94A3B8",
    "OK": "#22C55E",
    "WARN": "#F59E0B",
    "ERR": "#EF4444",
}


@pytest.mark.parametrize("name,value", sorted(SPEC_PALETTE.items()))
def test_palette_constant_matches_spec(name, value):
    """Each of the eleven tokens is declared in ui/theme.py with its exact
    hex (see the SPEC_PALETTE comment above for what "spec" means for each
    one -- it is not the same claim for all eleven)."""
    actual = getattr(theme, name)
    assert actual == value, f"ui.theme.{name} is {actual!r}, spec requires {value!r}"


def _hex_to_rgb(hex_value: str) -> tuple:
    hex_value = hex_value.lstrip("#")
    return tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))


def _relative_luminance(rgb: tuple) -> float:
    def channel(c: int) -> float:
        c_srgb = c / 255
        return c_srgb / 12.92 if c_srgb <= 0.03928 else ((c_srgb + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG 2.x contrast ratio between two hex colours, always >= 1.0.

    Same maths as tests/test_site_theme.py's _contrast_ratio helper,
    reimplemented locally rather than imported across test modules.
    """
    luminance_a = _relative_luminance(_hex_to_rgb(hex_a))
    luminance_b = _relative_luminance(_hex_to_rgb(hex_b))
    lighter, darker = max(luminance_a, luminance_b), min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


# Every text-bearing foreground/background pair ui/main_window.py and
# ui/loading_screen.py actually paint. Each row names the call site(s) it
# covers -- see .superpowers/sdd/2026-08-15-ascii-terminal-brand/
# desktop-ui-report.md for the full pairing-by-pairing writeup.
TEXT_PAIRS = [
    ("TEXT", "BG"),        # file_label
    ("DIM", "BG"),         # language caption; loading screen subtitle/progress
    ("TEXT", "SURFACE"),   # text_area real text, language combo popup, progress_label (error)
    ("DIM", "SURFACE"),    # drop zone idle text; text_area placeholder; disabled button text+icon
    ("ACCENT", "SURFACE"), # drop zone drag-hover text; progress_label (active)
    ("ACCENT", "BG"),      # loading screen title
    ("WARN", "SURFACE"),   # drop zone warning text
    ("OK", "SURFACE"),     # drop zone accepted text; progress_label (success)
    ("BG", "FRAME"),         # button rest state: dark ink on light-indigo fill
    ("BG", "FRAME_HOVER"),   # button hover state
    ("BG", "FRAME_PRESSED"), # button pressed state
]

# Non-text UI (borders, left-border accents): only the 3:1 floor applies.
FILL_PAIRS = [
    ("FRAME", "SURFACE"),  # drop zone idle / text_area / combo borders
    ("FRAME", "BG"),       # loading screen card border
    ("ERR", "SURFACE"),    # progress_label error-state left border
]


@pytest.mark.parametrize("fg,bg", TEXT_PAIRS)
def test_text_pair_clears_contrast_floor(fg, bg):
    fg_hex, bg_hex = getattr(theme, fg), getattr(theme, bg)
    ratio = _contrast_ratio(fg_hex, bg_hex)
    assert ratio >= TEXT_CONTRAST_MIN, (
        f"{fg} ({fg_hex}) on {bg} ({bg_hex}) is only {ratio:.2f}:1, "
        f"needs >= {TEXT_CONTRAST_MIN}:1 for text"
    )


@pytest.mark.parametrize("fg,bg", FILL_PAIRS)
def test_fill_pair_clears_contrast_floor(fg, bg):
    fg_hex, bg_hex = getattr(theme, fg), getattr(theme, bg)
    ratio = _contrast_ratio(fg_hex, bg_hex)
    assert ratio >= FILL_CONTRAST_MIN, (
        f"{fg} ({fg_hex}) on {bg} ({bg_hex}) is only {ratio:.2f}:1, "
        f"needs >= {FILL_CONTRAST_MIN}:1 even as a non-text fill/border"
    )


def test_err_would_fail_the_text_floor_on_surface():
    """Regression guard for a deliberately-avoided combination, not a
    hypothetical one: ERR (#EF4444) measures 3.89:1 on SURFACE, clearing
    the 3:1 non-text floor (see test_fill_pair_clears_contrast_floor above)
    but failing the 4.5:1 text floor. ui/main_window.py's error-state
    styling therefore keeps TEXT as the message-body colour and confines
    ERR to the left-border accent (see tests/test_main_window_theme.py).
    This pins the numeric fact that decision depends on, so a future
    palette change silently invalidating it is caught here rather than
    only showing up as a contrast regression nobody measured.
    """
    ratio = _contrast_ratio(theme.ERR, theme.SURFACE)
    assert ratio < TEXT_CONTRAST_MIN, (
        f"ERR on SURFACE is now {ratio:.2f}:1, which clears the text floor -- "
        "if intentional, ui/main_window.py's error-state text colour could "
        "use ERR directly instead of TEXT; if not, this caught a palette "
        "drift that changes that tradeoff"
    )
