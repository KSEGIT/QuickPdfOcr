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

# The hero terminal's clamp() font-size floor stops shrinking at 11px, so the
# fixed 46-column frame stays 304.66px wide below that — narrower than 375 or
# even 320px viewports can force it to shrink further. Overflow at that width
# only shows up under ~305px, so the overflow guard needs a narrower probe
# than the three standard breakpoints above: 280px is the Galaxy Fold's outer
# (folded) screen width, a real, shipping device size, not a synthetic edge
# case.
OVERFLOW_VIEWPORTS = [(280, "fold")] + VIEWPORTS

# Shared between test_hero_terminal_lines_share_a_left_edge and
# test_ascii_icon_blocks_are_left_aligned_in_their_own_box: for a given
# .ascii-art <pre>, returns the left offset of every rendered line relative
# to the element's own left edge.
#
# A plain getBoundingClientRect() on the <pre> only gives one rect for the
# whole block, and Range.getClientRects() over the *entire* element yields
# one rect per inline fragment rather than per visual line — several of
# these blocks contain child <span> tags (.beam/.cursor/.fill), so a run of
# plain text before a span, the span itself, and any plain text after it
# each produce their own rect, most of which start mid-line and are not
# what "left edge" means here. Instead, this walks the text nodes to find
# each newline-delimited line's absolute start/end offset (regardless of
# which element owns that text), builds one Range per line, and takes the
# *leftmost* of that range's rects — text flows strictly left-to-right
# inside a single line here, so that leftmost rect is the line's true
# visual start.
LINE_LEFT_OFFSETS_JS = """
    const lineLeftOffsets = (pre) => {
        const preLeft = pre.getBoundingClientRect().left;
        const walker = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT);
        const nodes = [];
        let text = '';
        let node;
        while ((node = walker.nextNode())) {
            nodes.push({ node, start: text.length,
                         end: text.length + node.textContent.length });
            text += node.textContent;
        }
        // Throws rather than guessing a nearby position: a wrong-but-
        // plausible fallback here could silently mask a real alignment
        // regression instead of failing the assertion loudly.
        const locate = (absIndex) => {
            for (const entry of nodes) {
                if (absIndex >= entry.start && absIndex <= entry.end) {
                    return { node: entry.node, offset: absIndex - entry.start };
                }
            }
            throw new Error(
                `lineLeftOffsets: index ${absIndex} falls outside the ` +
                `walked text nodes (0..${text.length}) for ` +
                `${pre.className || pre.tagName}`);
        };
        const offsets = [];
        let idx = 0;
        for (const line of text.split('\\n')) {
            if (line.length > 0) {
                const startPos = locate(idx);
                const endPos = locate(idx + line.length);
                const range = document.createRange();
                range.setStart(startPos.node, startPos.offset);
                range.setEnd(endPos.node, endPos.offset);
                const rects = [...range.getClientRects()]
                    .filter(r => r.width > 0);
                if (rects.length) {
                    const left = Math.min(...rects.map(r => r.left));
                    offsets.push(Math.round((left - preLeft) * 10) / 10);
                }
            }
            idx += line.length + 1;
        }
        return offsets;
    };
"""

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
    // Composites the real ancestor background stack (not just the
    // nearest non-transparent layer) so a translucent tint — e.g.
    // an accent-coloured badge fill at 10% alpha over the dark page
    // background — resolves to what the browser actually paints,
    // rather than a bare rgba() string with its alpha stripped.
    const parseColor = (str) => {
        const m = str.match(/rgba?\\(([^)]+)\\)/);
        const parts = m[1].split(',').map(Number);
        // Every browser this suite has run against serializes computed
        // colour as legacy comma-separated rgb()/rgba(). If that ever
        // changes (e.g. to space-separated CSS Color 4 syntax), splitting
        // on ',' silently yields NaN channels rather than an error — and a
        // NaN contrast ratio makes every "< need" comparison downstream
        // false, dropping a real failure instead of flagging it. Fail
        // loud here instead.
        if (parts.some(Number.isNaN)) {
            throw new Error(`parseColor: could not parse channels from ${str}`);
        }
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
    // A gradient background-image paints its own colour, invisible to
    // backgroundColor — a walker that only reads backgroundColor sails
    // straight past it to whatever solid colour sits further up the
    // ancestor chain (here, body's near-black), understating how the
    // gradient's own stops affect real text contrast. Text overlays the
    // whole sweep, so every stop is a candidate background and the
    // *worst* one is the one that matters, not an average or the first.
    // A background-image this can't resolve into colour stops (e.g. a
    // url(...)) throws rather than being silently skipped — the same
    // silent-skip shape as the bug this replaces.
    const gradientStops = (bgImage) => {
        if (!bgImage || bgImage === 'none') return null;
        if (!bgImage.includes('linear-gradient')) {
            throw new Error(`bgOf: unparseable background-image (not a ` +
                             `linear-gradient we can read stops from): ${bgImage}`);
        }
        const stops = [...bgImage.matchAll(/rgba?\\([^)]+\\)/g)]
            .map(m => parseColor(m[0]));
        if (stops.length === 0) {
            throw new Error(`bgOf: linear-gradient with no parseable colour ` +
                             `stops: ${bgImage}`);
        }
        return stops;
    };
    // Returns an array of candidate composited backgrounds (rgb strings) —
    // normally just one, but a gradient ancestor branches it into one
    // candidate per colour stop so callers can evaluate against the worst.
    const bgOf = (el) => {
        const layers = [];
        for (let n = el; n; n = n.parentElement) {
            const style = getComputedStyle(n);
            const stops = gradientStops(style.backgroundImage);
            const c = parseColor(style.backgroundColor);
            if (stops) {
                // CSS paints background-color at the bottom and
                // background-image on top of it, for the *same* element —
                // both are real, simultaneous layers here, not a either/or
                // choice. Push the gradient first (it ends up on top) and
                // this same node's own colour second (underneath it),
                // rather than treating the gradient as if it were the
                // node's only background and skipping its solid colour.
                layers.push({ multi: stops });
                if (c.a > 0) layers.push({ color: c });
                if (stops.every(s => s.a >= 0.999) || c.a >= 0.999) break;
                continue;
            }
            if (c.a > 0) layers.push({ color: c });
            if (c.a >= 0.999) break;
        }
        let results = [{ r: 255, g: 255, b: 255 }];
        for (let i = layers.length - 1; i >= 0; i--) {
            const layer = layers[i];
            if (layer.multi) {
                results = layer.multi.flatMap(
                    stop => results.map(res => over(stop, res)));
            } else {
                results = results.map(res => over(layer.color, res));
            }
        }
        return results.map(r => `rgb(${Math.round(r.r)}, ` +
            `${Math.round(r.g)}, ${Math.round(r.b)})`);
    };
    // fg alpha (e.g. a translucent tagline colour) must be composited over
    // each candidate background before measuring luminance, the same way
    // bgOf() already composites the background side — otherwise translucent
    // text is scored as if it were fully opaque. bgOf() always returns an
    // array (one entry normally, one per gradient stop when it touches a
    // gradient); the Array.isArray guard just means ratio()'s second
    // argument also works if ever called with a bare rgb string directly.
    // The *worst* (lowest) ratio across candidates is the one that
    // governs, since the text really does overlay all of them.
    const ratio = (a, b) => {
        const bgs = Array.isArray(b) ? b : [b];
        return Math.min(...bgs.map(bg => {
            const blended = over(parseColor(a), parseColor(bg));
            const fgResolved = `rgb(${Math.round(blended.r)}, ` +
                `${Math.round(blended.g)}, ${Math.round(blended.b)})`;
            const [x, y] = [lum(fgResolved), lum(bg)].sort((p, q) => q - p);
            return (x + 0.05) / (y + 0.05);
        }));
    };
"""


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()


@pytest.mark.parametrize(
    "width,label", OVERFLOW_VIEWPORTS, ids=[v[1] for v in OVERFLOW_VIEWPORTS]
)
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
    An ancestor's background-image gradient (e.g. .privacy-section) is
    resolved the same way rather than skipped in favour of whatever solid
    colour sits further up the tree — every colour stop is a candidate and
    the worst one governs, since the text overlays the whole sweep.
    Foreground alpha is composited the same way, over each candidate
    background, before its luminance is measured — a translucent colour
    like .hero .tagline's isn't scored as if it were fully opaque.
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


def test_bg_of_composites_gradient_over_its_own_background_color(page):
    """Regression guard: an element's own background-color must be
    composited *beneath* its own background-image gradient, not skipped in
    favour of whatever colour sits on the next ancestor out.

    CSS paints a single element's background-color at the bottom and its
    background-image on top of it — both are real, simultaneous layers on
    that one element, not a choice between them. A walker that treats
    "this node has a gradient" as reason to stop looking at that same
    node's own backgroundColor reintroduces the exact "sails past a real
    background layer" bug this file's bgOf() rewrite exists to fix, just
    one property over. Uses two identical gradient stops so the gradient
    behaves as one flat translucent overlay, giving a single deterministic
    expected colour rather than the worst-of-N-stops branching already
    covered by the real .privacy-section walk in the test above.
    """
    page.set_content(
        """
        <!doctype html><html><body style="background:#ffffff;margin:0">
          <div id="target" style="background-color: rgb(255, 0, 0);
                                   background-image: linear-gradient(
                                       rgba(0, 0, 255, 0.5), rgba(0, 0, 255, 0.5));">
            content
          </div>
        </body></html>
        """
    )
    result = page.evaluate(
        "() => {\n" + CONTRAST_HELPERS_JS + """
            return bgOf(document.getElementById('target'));
        }"""
    )
    # bgOf() branches into one candidate per literal colour stop it finds
    # (two here, since the gradient has two identical stops) — the *set* of
    # resulting values is what matters, not how many duplicate candidates
    # a two-stop-but-one-colour gradient happens to produce.
    assert set(result) == {"rgb(128, 0, 128)"}, (
        "an element's own background-color must be composited beneath its "
        f"own gradient (expected translucent blue over opaque red = "
        f"rgb(128, 0, 128) for every candidate); got {result} — "
        "rgb(128, 128, 255) would mean the walker skipped this node's own "
        "red and composited the gradient straight over the white ancestor "
        "instead"
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

    A contrast floor alone does not guard the hover *rule*: the resting
    --frame border already clears 3:1 on its own (4.90:1), so deleting the
    :hover rule outright, or replacing it with a byte-for-byte no-op
    (`border-color: var(--frame)`, i.e. the resting value spelled out
    again), leaves the resting colour showing throughout hover, and this
    test would still pass for the wrong reason. Capturing the resting
    colour before hover() and asserting the settled hover colour differs
    from it is what catches an absent or no-op rule; the contrast check
    alone only catches a hover colour that is present but too low-contrast.

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
    resting = card.evaluate("el => getComputedStyle(el).borderTopColor")
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
    hovered = card.evaluate("el => getComputedStyle(el).borderTopColor")
    got = page.evaluate(
        "(el) => {\n" + CONTRAST_HELPERS_JS + """
            const style = getComputedStyle(el);
            return ratio(style.borderTopColor, bgOf(el));
        }""",
        card,
    )
    assert hovered != resting, (
        f"{selector}:hover settled border colour ({hovered}) is identical "
        f"to the resting border colour ({resting}) — the hover rule is "
        "missing, deleted, or a byte-for-byte no-op"
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


@pytest.mark.parametrize("width", [v[0] for v in VIEWPORTS])
def test_hero_terminal_is_legible_at_every_viewport(page, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(INDEX.as_uri())
    size = page.evaluate(
        "() => parseFloat(getComputedStyle("
        "document.querySelector('.hero-terminal')).fontSize)"
    )
    assert size >= 10, f"hero terminal is {size}px at {width}px — unreadable"


@pytest.mark.parametrize("width", [v[0] for v in VIEWPORTS])
def test_hero_terminal_lines_share_a_left_edge(page, width):
    """Every visible line of the hero terminal must be flush with the same
    left edge, at every viewport.

    The mobile/tablet media query centres .hero for its prose (h1, tagline,
    description) — intentional — but that text-align: center inherits into
    the hero terminal's <pre> too. white-space: pre turns every newline
    into its own line box, and text-align applies per line box, so each
    framed row shorter than the widest one centres independently instead of
    staying flush against the frame: the "~/Documents $ ..." prompt line and
    the trailing "> N words copied..." line are both shorter than the fixed
    46-column frame rows, so they visibly drift right of the frame's left
    edge while the frame itself stays put.

    None of the other hero tests would catch this — they check column
    counts in source (test_hero_terminal_is_fixed_46_columns), clamp()
    presence, and font-size, none of which sees rendered line position.
    See LINE_LEFT_OFFSETS_JS above for why a plain getBoundingClientRect()
    or a single whole-element Range can't measure this correctly.
    """
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(INDEX.as_uri())
    offsets = page.evaluate(
        "() => {\n" + LINE_LEFT_OFFSETS_JS + """
            return lineLeftOffsets(document.querySelector('.hero-terminal'));
        }"""
    )
    assert offsets, "no rendered line boxes found in .hero-terminal"
    bad = [o for o in offsets if abs(o) > 1]
    assert bad == [], (
        f"hero terminal lines are not flush with a common left edge at "
        f"{width}px — per-line offsets from the frame's own left edge "
        f"(px): {offsets}"
    )


def test_ascii_icon_blocks_are_left_aligned_in_their_own_box(page):
    """Every .ascii-art icon block (feature/privacy/platform icons) must
    also have its lines flush with its own left edge, not just the hero
    terminal.

    .ascii-art's text-align: left (added for the hero terminal fix above)
    also reaches these 12 icon blocks, since .privacy-section and
    .download-section both set text-align: center on themselves
    *unconditionally* — unlike .hero's centring, which only applies in the
    mobile/tablet media query. Before that fix, the privacy icon and the
    macOS download icon's multi-width rows centred independently at every
    viewport, not just mobile/tablet; nothing in this suite checked
    rendered icon line position, so it went unnoticed. This runs at a
    single viewport (desktop) since these are small, non-fluid, five-line
    fixed-width blocks whose alignment doesn't depend on viewport width the
    way the hero terminal's does.
    """
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(INDEX.as_uri())
    offenders = page.evaluate(
        "() => {\n" + LINE_LEFT_OFFSETS_JS + """
            const bad = [];
            for (const pre of document.querySelectorAll('.ascii-art.ascii-icon')) {
                const offsets = lineLeftOffsets(pre);
                if (offsets.some(o => Math.abs(o) > 1)) {
                    bad.push({ icon: pre.closest('[class*="-icon"]').className,
                               offsets });
                }
            }
            return bad;
        }"""
    )
    assert offenders == [], (
        f"icon blocks not flush with their own left edge: {offenders}"
    )
