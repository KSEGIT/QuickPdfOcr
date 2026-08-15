"""Theme-token guards for the terminal skin on docs/index.html."""
import re
from pathlib import Path

import pytest

INDEX = Path(__file__).resolve().parent.parent / "docs" / "index.html"

TERMINAL_PALETTE = {
    "--bg": "#0F172A",
    "--surface": "#111C33",
    "--frame": "#4F46E5",
    "--bar": "#7C3AED",
    "--accent": "#22D3EE",
    "--text": "#E2E8F0",
    "--dim": "#64748B",
}

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
    """The old light theme's hardcoded whites must all be gone."""
    html = read_index()
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    offenders = re.findall(
        r"(?:background|background-color)\s*:\s*[^;]*"
        r"(?:#fff\b|#ffffff\b|rgba\(255,\s*255,\s*255|\bwhite\b)[^;]*;",
        css,
        re.I,
    )
    assert offenders == [], f"hardcoded light backgrounds remain: {offenders}"


def _frame_aliases(html: str) -> set[str]:
    """Custom properties declared in :root whose value is exactly var(--frame).

    A legacy alias like ``--indigo: var(--frame);`` resolves to the same
    colour as --frame, so using the alias as a text colour is exactly as
    much of a contrast violation as using var(--frame) directly. Deriving
    the alias list from :root (rather than hardcoding "--indigo") means a
    future alias of --frame is caught automatically instead of reopening
    this hole.
    """
    root = re.search(r":root\s*\{(.*?)\}", html, re.S)
    assert root, ":root block not found"
    return {
        name
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))
        if value.strip() == "var(--frame)"
    }


def test_frame_token_never_carries_text():
    """--frame is ~3:1 on --bg: decoration only, never a text colour.

    Covers direct use of var(--frame) as well as any legacy alias declared
    in :root that resolves straight to it (e.g. --indigo).
    """
    html = read_index()
    css = html.split("<style>", 1)[1].split("</style>", 1)[0]
    tokens = _frame_aliases(html) | {"--frame"}
    alternation = "|".join(re.escape(token) for token in sorted(tokens))
    offenders = re.findall(rf"(?<!-)\bcolor\s*:\s*var\(({alternation})\)", css)
    assert offenders == [], (
        f"--frame must never be used as a text colour, directly or via an alias: {offenders}"
    )
