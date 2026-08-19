"""Theme-token guards for the terminal skin on docs/index.html."""
import re
from pathlib import Path

import pytest

INDEX = Path(__file__).resolve().parent.parent / "docs" / "index.html"

TERMINAL_PALETTE = {
    "--bg": "#0F172A",
    "--surface": "#1E293B",
    "--frame": "#818CF8",
    "--frame-fill": "#4F46E5",
    "--bar": "#7C3AED",
    "--bar-ink": "#A78BFA",
    "--accent": "#22D3EE",
    "--text": "#E2E8F0",
    "--dim": "#94A3B8",
}

# WCAG 2.x minimums this palette is measured against: 4.5:1 for body text,
# 3:1 for the "fills only, never text" decorative tier (borders, chip fills,
# large-scale UI graphics).
TEXT_CONTRAST_MIN = 4.5
FILL_CONTRAST_MIN = 3.0

MONO_STACK = (
    'ui-monospace, SFMono-Regular, Menlo, Consolas, '
    '"DejaVu Sans Mono", "Liberation Mono", monospace'
)


def read_index() -> str:
    return INDEX.read_text(encoding="utf-8")


@pytest.mark.parametrize("token,value", sorted(TERMINAL_PALETTE.items()))
def test_palette_token_declared(token, value):
    """Each terminal palette token is declared with its exact spec hex."""
    assert re.search(rf"{re.escape(token)}\s*:\s*{value}\s*;", read_index()), (
        f"{token} must be declared as {value}"
    )


def test_mono_stack_declared():
    assert MONO_STACK in read_index()


def test_body_uses_mono_and_terminal_background():
    """body must render monospace on the dark ground, not the old white sans."""
    html = read_index()
    body = re.search(r"\n\s*body\s*\{(.*?)\}", html, re.S)
    assert body, "body rule not found"
    rule = body.group(1)
    assert "var(--mono)" in rule
    assert "var(--bg)" in rule


def test_no_hardcoded_white_backgrounds():
    """The old light theme's hardcoded whites must all be gone.

    The white-rgb alternative matches both legacy comma-separated syntax
    (`rgba(255, 255, 255, ...)`) and CSS Color 4 space-separated syntax
    (`rgb(255 255 255 / 0.9)`) -- the latter is what this file's own
    `header` and `--shadow` tokens use, so a regex blind to it would miss
    the most likely shape of a real regression. `[^;{}]*` (rather than
    `[^;]*`) keeps each wildcard span inside the single declaration it
    started in: `[^;]*` alone crosses `}` into the next rule when a
    declaration is missing its trailing semicolon (valid CSS for the last
    declaration in a block), which can misattribute an unrelated later
    value to this property.
    """
    html = read_index()
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    offenders = re.findall(
        r"(?:background|background-color)\s*:\s*[^;{}]*"
        r"(?:#fff\b|#ffffff\b|rgba?\(\s*255(?:\s*,\s*|\s+)255(?:\s*,\s*|\s+)255\b"
        r"|\bwhite\b)[^;{}]*;",
        css,
        re.I,
    )
    assert offenders == [], f"hardcoded light backgrounds remain: {offenders}"


def test_no_hardcoded_border_radius():
    """--radius is 0 for the sharp-corners terminal skin.

    A hardcoded px/% radius bypasses that token the same way a hardcoded
    background colour bypasses the palette above -- it looks fine today and
    silently drifts from --radius the next time the token changes.
    """
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    declarations = re.findall(r"border-radius\s*:\s*([^;]+);", css)
    offenders = [d for d in declarations if d.strip() != "var(--radius)"]
    assert offenders == [], f"hardcoded border-radius remains: {offenders}"


FILLS_ONLY_TOKEN = "--bar"


def _aliases_of(html: str, target: str) -> set[str]:
    """Custom properties declared in :root whose value is exactly var(target).

    A legacy alias like ``--violet: var(--bar);`` resolves to the same
    colour as --bar, so using the alias as a text colour is exactly as much
    of a contrast violation as using var(--bar) directly. Deriving the
    alias list from :root (rather than hardcoding "--violet") means a
    future alias of the fills-only token is caught automatically instead of
    reopening this hole.
    """
    root = re.search(r":root\s*\{(.*?)\}", html, re.S)
    assert root, ":root block not found"
    return {
        name
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))
        if value.strip() == f"var({target})"
    }


def test_bar_token_never_carries_text():
    """--bar is ~3:1 on --bg: fills only, never a text colour.

    --frame was the fills-only token in the original spec, but the
    corrected palette lifted it to 5.98:1 (legible as text). --bar
    (#7C3AED, 3.13:1) is the token that still fails the 4.5:1 text floor,
    so it — and any legacy alias declared in :root that resolves straight
    to it (e.g. --violet) — must never carry text.
    """
    html = read_index()
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    tokens = _aliases_of(html, FILLS_ONLY_TOKEN) | {FILLS_ONLY_TOKEN}
    alternation = "|".join(re.escape(token) for token in sorted(tokens))
    offenders = re.findall(rf"(?<!-)\bcolor\s*:\s*var\(({alternation})\)", css)
    assert offenders == [], (
        f"{FILLS_ONLY_TOKEN} must never be used as a text colour, directly or via an alias: {offenders}"
    )


def _hex_to_rgb(hex_value: str) -> tuple[int, int, int]:
    hex_value = hex_value.lstrip("#")
    return tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.x relative luminance (the L in the contrast-ratio formula)."""
    def channel(c: int) -> float:
        c_srgb = c / 255
        return c_srgb / 12.92 if c_srgb <= 0.03928 else ((c_srgb + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG 2.x contrast ratio between two hex colours, always >= 1.0."""
    luminance_a = _relative_luminance(_hex_to_rgb(hex_a))
    luminance_b = _relative_luminance(_hex_to_rgb(hex_b))
    lighter, darker = max(luminance_a, luminance_b), min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def _declared_tokens(html: str) -> dict[str, str]:
    """The literal value of every custom property declared in :root."""
    root = re.search(r":root\s*\{(.*?)\}", html, re.S)
    assert root, ":root block not found"
    return {
        name: value.strip()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))
    }


@pytest.mark.parametrize("token", ["--text", "--accent", "--dim", "--frame"])
def test_text_token_clears_contrast_floor_against_bg(token):
    """Text-bearing tokens must clear WCAG's 4.5:1 floor against --bg.

    Computed from the hex values actually declared in :root, not asserted
    against a hardcoded expectation — this is the check whose absence let
    the original spec ship a --frame/--dim/--surface combination that
    failed these floors.
    """
    tokens = _declared_tokens(read_index())
    ratio = _contrast_ratio(tokens[token], tokens["--bg"])
    assert ratio >= TEXT_CONTRAST_MIN, (
        f"{token} ({tokens[token]}) is only {ratio:.2f}:1 against --bg "
        f"({tokens['--bg']}), needs >= {TEXT_CONTRAST_MIN}:1 for text"
    )


def test_bar_token_clears_fill_contrast_floor_against_bg():
    """--bar is fills-only, so it only needs WCAG's 3:1 non-text floor."""
    tokens = _declared_tokens(read_index())
    ratio = _contrast_ratio(tokens[FILLS_ONLY_TOKEN], tokens["--bg"])
    assert ratio >= FILL_CONTRAST_MIN, (
        f"{FILLS_ONLY_TOKEN} ({tokens[FILLS_ONLY_TOKEN]}) is only {ratio:.2f}:1 against --bg "
        f"({tokens['--bg']}), needs >= {FILL_CONTRAST_MIN}:1 even as a fill"
    )


# Rules whose background AND foreground are both declared together in a
# single CSS rule, so a rule-local regex can resolve the pairing without
# guessing which background a colour actually renders on. --frame flipped
# from a dark fill (white-on-it read at 6.29:1) to a light one (5.98:1
# against --bg) when the palette was corrected, so these two "filled"
# .btn-primary variants were inverted to dark ink on the light fill.
#
# Their :hover variants (`.download-card .btn-primary:hover`,
# `.developer-section .btn-primary:hover`) only swap `background` and rely
# on the cascade to keep the `color` declared here — that inheritance
# across two separate rules isn't something a rule-local regex can see
# without effectively reimplementing CSS cascade resolution, so it is
# deliberately not asserted here (see docstring below).
FILLED_BUTTON_SELECTORS = [
    ".download-card .btn-primary",
    ".developer-section .btn-primary",
]


def _resolve_token(tokens: dict[str, str], value: str) -> str:
    """Resolve a declared value down to a literal hex, walking var() chains.

    Follows however many var() hops it takes to bottom out at a literal
    value (e.g. --indigo -> var(--frame) -> #818CF8), raising if a name
    isn't declared in :root or a chain loops back on itself.
    """
    value = value.strip()
    seen = set()
    while value.startswith("var(") and value.endswith(")"):
        name = value[4:-1].strip()
        assert name not in seen, f"circular alias resolving {value!r}"
        assert name in tokens, f"{name!r} is not declared in :root"
        seen.add(name)
        value = tokens[name].strip()
    return value


@pytest.mark.parametrize("selector", FILLED_BUTTON_SELECTORS)
def test_filled_btn_primary_pairing_clears_text_contrast(selector):
    """The declared background/foreground pair on each filled .btn-primary
    variant's rest state must clear 4.5:1, resolved from :root rather than
    hardcoded.

    Deliberately does not cover the :hover state: it only overrides
    `background`, and its `color` comes from the cascade (the plain,
    non-hover rule above it) rather than anything declared in the hover
    rule itself. A rule-local regex has no principled way to resolve that
    without reimplementing CSS's cascade — a later task adds a
    browser-level check that reads the real computed style instead.
    """
    html = read_index()
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    tokens = _declared_tokens(html)
    rule = re.search(rf"{re.escape(selector)}\s*\{{(.*?)\}}", css, re.S)
    assert rule, f"{selector} rule not found"
    body = rule.group(1)
    background = re.search(r"background\s*:\s*([^;]+);", body)
    color = re.search(r"(?<!-)\bcolor\s*:\s*([^;]+);", body)
    assert background and color, f"{selector} must declare both background and color together"
    bg_hex = _resolve_token(tokens, background.group(1))
    fg_hex = _resolve_token(tokens, color.group(1))
    ratio = _contrast_ratio(bg_hex, fg_hex)
    assert ratio >= TEXT_CONTRAST_MIN, (
        f"{selector}: {color.group(1).strip()} on {background.group(1).strip()} "
        f"({fg_hex} on {bg_hex}) is only {ratio:.2f}:1, needs >= {TEXT_CONTRAST_MIN}:1"
    )


def test_privacy_gradient_stops_clear_text_contrast():
    """Every colour stop in .privacy-section's gradient background must
    stay legible under its own text.

    --frame-fill and --bar are the *fill* tier of their hue (dark enough
    to hold light text) as opposed to --frame/--bar-ink (the *ink* tier,
    drawable on the dark ground). Before this token split, the gradient's
    first stop reused --indigo/--frame directly; once that token was
    lifted to the ink value, the stop silently went from a dark fill to a
    light one and the text on top of it failed contrast. This is the test
    that would have caught that drift.

    Resolves the section's own declared `color` from :root rather than
    assuming it's literally "white", so the assertion tracks whatever ink
    the rule actually declares, not a hardcoded expectation.
    """
    html = read_index()
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    tokens = _declared_tokens(html)
    rule = re.search(r"\.privacy-section\s*\{(.*?)\}", css, re.S)
    assert rule, ".privacy-section rule not found"
    body = rule.group(1)
    background = re.search(r"background\s*:\s*([^;]+);", body)
    assert background, ".privacy-section must declare a background"
    assert "linear-gradient" in background.group(1), ".privacy-section must declare a linear-gradient background"
    stops = re.findall(r"(var\(--[\w-]+\)|#[0-9A-Fa-f]{6})", background.group(1))
    assert len(stops) >= 2, f".privacy-section gradient needs at least 2 colour stops, found {stops}"
    color = re.search(r"(?<!-)\bcolor\s*:\s*([^;]+);", body)
    assert color, ".privacy-section must declare a color"
    ink_hex = _resolve_token(tokens, color.group(1))
    for stop in stops:
        stop_hex = _resolve_token(tokens, stop)
        ratio = _contrast_ratio(stop_hex, ink_hex)
        assert ratio >= TEXT_CONTRAST_MIN, (
            f".privacy-section: {color.group(1).strip()} ({ink_hex}) on gradient stop "
            f"{stop} ({stop_hex}) is only {ratio:.2f}:1, needs >= {TEXT_CONTRAST_MIN}:1"
        )


def test_section_titles_render_as_commands():
    """Section titles carry a shell-prompt prefix via .cmd::before."""
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    rule = re.search(r"\.cmd::before\s*\{(.*?)\}", css, re.S)
    assert rule, ".cmd::before rule not found"
    assert "content:" in rule.group(1)


def test_reflowing_frames_use_css_borders_not_characters():
    """The reflow rule: cards/sections are CSS-framed, never character-framed."""
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    rule = re.search(r"\.boxed\s*\{(.*?)\}", css, re.S)
    assert rule, ".boxed rule not found"
    assert "border:" in rule.group(1)
    assert "var(--frame)" in rule.group(1)


def test_buttons_are_bracketed():
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    before = re.search(r"\.btn::before\s*\{(.*?)\}", css, re.S)
    after = re.search(r"\.btn::after\s*\{(.*?)\}", css, re.S)
    assert before and after, "btn bracket pseudo-elements not found"
    assert '"[' in before.group(1) or "'[" in before.group(1)
    assert ']"' in after.group(1) or "]'" in after.group(1)


def test_nav_has_shell_prompt():
    assert "~/quickpdfocr" in read_index()
