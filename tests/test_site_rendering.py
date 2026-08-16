"""Browser-level verification of the terminal skin.

Regex guards prove the markup says the right thing; only a real render
proves the fonts resolved, the frames aligned, and nothing overflowed.
"""
from pathlib import Path

import pytest

sync_playwright = pytest.importorskip(
    "playwright.sync_api", reason="asset tooling not installed"
).sync_playwright

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "index.html"
SHOTS = ROOT / "docs" / "design" / "screenshots"
VIEWPORTS = [(375, "mobile"), (768, "tablet"), (1440, "desktop")]


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()


@pytest.mark.parametrize("width,label", VIEWPORTS, ids=[v[1] for v in VIEWPORTS])
def test_no_horizontal_overflow(page, width, label):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(INDEX.as_uri())
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - "
        "document.documentElement.clientWidth"
    )
    assert overflow <= 0, (
        f"{label} ({width}px) overflows horizontally by {overflow}px"
    )


@pytest.mark.parametrize("width,label", VIEWPORTS, ids=[v[1] for v in VIEWPORTS])
def test_capture_screenshot(page, width, label):
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(INDEX.as_uri())
    page.screenshot(path=str(SHOTS / f"{label}-{width}.png"), full_page=True)
    assert (SHOTS / f"{label}-{width}.png").exists()


def test_no_tofu_glyphs(page):
    """Every ASCII block must render with all glyphs present in the font.

    A missing glyph collapses to the .notdef box, which measures differently
    from a real character. Compare each block's rendered width against the
    width a same-length run of a known-present character occupies.
    """
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(INDEX.as_uri())
    bad = page.evaluate(
        """() => {
            const probe = document.createElement('pre');
            const bad = [];
            for (const el of document.querySelectorAll('.ascii-art')) {
                const style = getComputedStyle(el);
                probe.style.cssText = `position:absolute;visibility:hidden;
                    white-space:pre;margin:0;font-family:${style.fontFamily};
                    font-size:${style.fontSize};letter-spacing:${style.letterSpacing}`;
                document.body.appendChild(probe);
                for (const line of el.textContent.split('\\n')) {
                    if (!line.trim()) continue;
                    probe.textContent = line;
                    const actual = probe.getBoundingClientRect().width;
                    probe.textContent = 'M'.repeat(line.length);
                    const expected = probe.getBoundingClientRect().width;
                    if (Math.abs(actual - expected) > 1.5) {
                        bad.push(line.slice(0, 40));
                    }
                }
                probe.remove();
            }
            return bad;
        }"""
    )
    assert bad == [], f"non-monospaced or tofu glyphs in: {bad}"


def test_every_text_element_clears_aa_against_its_real_background(page):
    """The general guard: computed foreground vs computed background, AA 4.5:1.

    Static CSS tests cannot resolve which background a rule actually pairs
    with — that is why the palette shipped with a 2.84:1 frame token and a
    2.98:1 button. This walks the rendered tree and checks real pairings.
    Elements inside .ascii-art are checked at the 3:1 non-text threshold:
    the art is aria-hidden decoration, but it still has to be visible.

    Backgrounds are alpha-composited over the full ancestor stack rather
    than read off the nearest non-transparent layer as a raw rgba() string:
    a naive read discards alpha, so a translucent accent-tinted chip (fill
    and text sharing a hue at low alpha over the dark page background — a
    valid, common pattern here) collapses to a spurious foreground-equals-
    background 1:1 reading instead of the ~8-11:1 it actually renders at.
    """
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(INDEX.as_uri())
    offenders = page.evaluate(
        """() => {
            const lum = (rgb) => {
                const [r, g, b] = rgb.match(/\\d+/g).slice(0, 3).map(Number)
                    .map(v => v / 255)
                    .map(v => v <= 0.04045 ? v / 12.92
                                           : Math.pow((v + 0.055) / 1.055, 2.4));
                return 0.2126 * r + 0.7152 * g + 0.0722 * b;
            };
            const ratio = (a, b) => {
                const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
                return (x + 0.05) / (y + 0.05);
            };
            // Composites the real ancestor background stack (not just the
            // nearest non-transparent layer) so a translucent tint — e.g.
            // an accent-coloured badge fill at 10% alpha over the dark page
            // background — resolves to what the browser actually paints,
            // rather than a bare rgba() string with its alpha stripped.
            const parseColor = (str) => {
                const m = str.match(/rgba?\\(([^)]+)\\)/);
                const parts = m[1].split(',').map(Number);
                return {
                    r: parts[0], g: parts[1], b: parts[2],
                    a: parts.length > 3 ? parts[3] : 1,
                };
            };
            const over = (fg, bg) => ({
                r: fg.r * fg.a + bg.r * (1 - fg.a),
                g: fg.g * fg.a + bg.g * (1 - fg.a),
                b: fg.b * fg.a + bg.b * (1 - fg.a),
            });
            const bgOf = (el) => {
                const layers = [];
                for (let n = el; n; n = n.parentElement) {
                    const c = parseColor(getComputedStyle(n).backgroundColor);
                    if (c.a > 0) layers.push(c);
                    if (c.a >= 0.999) break;
                }
                let result = { r: 255, g: 255, b: 255 };
                for (let i = layers.length - 1; i >= 0; i--) {
                    result = over(layers[i], result);
                }
                return `rgb(${Math.round(result.r)}, ${Math.round(result.g)}, ` +
                       `${Math.round(result.b)})`;
            };
            const bad = [];
            for (const el of document.querySelectorAll(
                    'h1,h2,h3,h4,p,a,li,span,button,pre,strong,em')) {
                if (!el.textContent.trim()) continue;
                if ([...el.children].some(c => c.textContent.trim())) continue;
                const style = getComputedStyle(el);
                const art = el.closest('.ascii-art');
                const need = art ? 3.0 : 4.5;
                const got = ratio(style.color, bgOf(el));
                if (got < need) {
                    bad.push(`${el.tagName}${art ? '(art)' : ''} ` +
                             `${got.toFixed(2)}:1 < ${need} — ` +
                             `"${el.textContent.trim().slice(0, 30)}"`);
                }
            }
            return bad;
        }"""
    )
    assert offenders == [], "contrast failures:\n  " + "\n  ".join(offenders)


def test_fills_only_token_is_not_a_text_colour(page):
    """--bar is 3.13:1 on --bg; assert no text element computed to it."""
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(INDEX.as_uri())
    offenders = page.evaluate(
        """() => {
            const bar = getComputedStyle(document.documentElement)
                .getPropertyValue('--bar').trim();
            const toRgb = (hex) => {
                const n = parseInt(hex.slice(1), 16);
                return `rgb(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255})`;
            };
            const target = toRgb(bar);
            const bad = [];
            for (const el of document.querySelectorAll('h1,h2,h3,p,a,li,span')) {
                if (el.closest('.ascii-art')) continue;
                if (!el.textContent.trim()) continue;
                if (getComputedStyle(el).color === target) {
                    bad.push(el.tagName + ': ' + el.textContent.trim().slice(0, 30));
                }
            }
            return bad;
        }"""
    )
    assert offenders == [], f"--bar used as text colour on: {offenders}"


@pytest.mark.parametrize("width", [375, 768, 1440])
def test_hero_terminal_is_legible_at_every_viewport(page, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(INDEX.as_uri())
    size = page.evaluate(
        "() => parseFloat(getComputedStyle("
        "document.querySelector('.hero-terminal')).fontSize)"
    )
    assert size >= 10, f"hero terminal is {size}px at {width}px — unreadable"
