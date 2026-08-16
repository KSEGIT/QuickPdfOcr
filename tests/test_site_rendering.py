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
VIEWPORTS = [(375, "mobile"), (768, "tablet"), (1440, "desktop")]

# Shared verbatim between test_every_text_element_clears_aa_against_its_real_background
# and test_contrast_helper_composites_translucent_backgrounds below, so the
# regression guard exercises the real code path rather than a copy that can
# silently drift from it. If this ever regresses to reading a translucent
# background's raw rgba() string with its alpha discarded — the bug that
# produced a false 1:1 reading on this site's own badge and secondary
# button — the synthetic test below fails.
CONTRAST_HELPERS_JS = """
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
"""


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
def test_capture_screenshot(page, width, label, tmp_path):
    # Writes into pytest's tmp_path, not the tracked docs/design/screenshots/
    # directory: those committed PNGs are review evidence, refreshed
    # deliberately by a human, not regenerated as a side effect of running
    # the suite (a different Chromium build or font set would otherwise
    # produce a spurious binary diff on every run).
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(INDEX.as_uri())
    shot = tmp_path / f"{label}-{width}.png"
    page.screenshot(path=str(shot), full_page=True)
    assert shot.exists()


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
        "() => {\n" + CONTRAST_HELPERS_JS + """
            const bad = [];
            for (const el of document.querySelectorAll(
                    'h1,h2,h3,h4,p,a,li,span,button,pre,strong,em')) {
                if (!el.textContent.trim()) continue;
                const own = [...el.childNodes].some(
                    n => n.nodeType === 3 && n.textContent.trim());
                if (!own) continue;
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


def test_contrast_helper_composites_translucent_backgrounds(page):
    """Regression guard for the bgOf() alpha-compositing bug.

    Feeds the exact helper used by
    test_every_text_element_clears_aa_against_its_real_background (imported
    via CONTRAST_HELPERS_JS, not copied) two synthetic pairings on a
    minimal page:

    - "opaque": a plain, fully-opaque low-contrast pairing. Sanity check
      that the underlying WCAG relative-luminance math still works.
    - "translucent": a pairing that is genuinely low-contrast once its
      translucent background is composited over its opaque ancestor
      (rgba(0,0,0,0.05) over rgb(240,240,240) composites to rgb(228,228,228),
      barely distinguishable from the rgb(230,230,230) text) — but whose
      *raw* rgba() string, alpha discarded, reads as flat black, a totally
      different colour. A helper that reads that raw string — the exact bug
      this task's contrast test surfaced and fixed on the site's own badge
      and secondary button — scores this ~16.8:1 and silently passes a real
      failure. Only a helper that actually composites the ancestor stack
      catches it, at ~1.02:1.
    """
    page.set_content(
        """
        <!doctype html><html><body style="background:#0F172A;margin:0">
          <p id="opaque" style="color:#334155;background:#0F172A">
            opaque low-contrast text
          </p>
          <div style="background:rgb(240,240,240)">
            <span id="translucent"
                  style="color:rgb(230,230,230);
                         background:rgba(0,0,0,0.05)">
              translucent low-contrast text
            </span>
          </div>
        </body></html>
        """
    )
    results = page.evaluate(
        "() => {\n" + CONTRAST_HELPERS_JS + """
            const out = {};
            for (const id of ['opaque', 'translucent']) {
                const el = document.getElementById(id);
                const style = getComputedStyle(el);
                out[id] = ratio(style.color, bgOf(el));
            }
            return out;
        }"""
    )
    assert results["opaque"] < 4.5, (
        f"opaque sanity pairing should read low contrast: {results}"
    )
    assert results["translucent"] < 4.5, (
        "translucent pairing should read low contrast once composited "
        f"over its ancestor — a helper reading the raw rgba() string "
        f"would score this ~16.8:1 and miss it: {results}"
    )


@pytest.mark.parametrize("selector", [".feature-card", ".download-card"])
def test_card_hover_border_clears_ui_contrast(page, selector):
    """A card's border must stay visible — not vanish or no-op — on hover.

    Neither the rest-state contrast walker above nor any static test reads
    a :hover pseudo-class, so a hover rule that composites to near-1:1 (the
    card dissolving into its section) or one that is a byte-for-byte no-op
    (declaring the same colour the border already has) is invisible to
    every other guard in this suite. Borders are non-text UI components
    (WCAG 1.4.11), so the floor here is 3:1, evaluated against the same
    real, alpha-composited background bgOf() resolves everywhere else.

    Both card rules carry `transition: border-color 0.2s`, so a read taken
    immediately after hover() lands mid-transition and reports the resting
    colour, not the hover colour — a broken hover rule would still measure
    as the (fine) resting value and the test would pass for the wrong
    reason. wait_for_function polls (via requestAnimationFrame, not a
    hardcoded sleep) until borderTopColor stops changing across several
    consecutive frames before the ratio is read, so the assertion reflects
    the settled hover state regardless of how long the transition actually
    takes.
    """
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(INDEX.as_uri())
    card = page.query_selector(selector)
    assert card is not None, f"{selector} not found on page"
    card.hover()
    page.wait_for_function(
        """(el) => {
            const current = getComputedStyle(el).borderTopColor;
            if (current === el.__lastBorderColor) {
                el.__stableFrames = (el.__stableFrames || 0) + 1;
            } else {
                el.__stableFrames = 0;
                el.__lastBorderColor = current;
            }
            return el.__stableFrames >= 5;
        }""",
        arg=card,
    )
    got = page.evaluate(
        "(el) => {\n" + CONTRAST_HELPERS_JS + """
            const style = getComputedStyle(el);
            return ratio(style.borderTopColor, bgOf(el));
        }""",
        card,
    )
    assert got >= 3.0, (
        f"{selector}:hover border is only {got:.2f}:1 against its "
        "composited background, needs >= 3.0:1"
    )


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
