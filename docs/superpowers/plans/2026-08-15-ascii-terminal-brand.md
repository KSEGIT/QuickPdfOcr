# ASCII / Terminal Brand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pivot the QuickPdfOcr marketing site and brand assets to a terminal/ASCII skin — 12 ASCII icons, a live character-grid hero, and a two-master app icon whose small sizes stay legible.

**Architecture:** `docs/index.html` stays a single self-contained file; the existing CSS custom properties are *remapped* onto the new dark palette rather than rewritten, so 550 lines of existing rules reskin at once with a small diff. True character-grid ASCII is used only in fixed-size blocks (icons, hero); everything that reflows uses CSS borders with corner glyphs. The app icon splits into two SVG masters feeding different size bands through a new Playwright-driven render script.

**Tech Stack:** Plain HTML/CSS (no frameworks), Python 3.12, Playwright (Chromium) for SVG→PNG rendering, Pillow for `.ico` assembly, `iconutil` for `.icns`, pytest.

**Spec:** `docs/superpowers/specs/2026-08-15-ascii-terminal-brand-design.md`

## Global Constraints

- **Character set.** Non-ASCII characters are restricted to exactly this set. Any other non-ASCII character is a defect:
  `┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ─ │ ╔ ╗ ╚ ╝ ═ ║ ░ ▒ ▓ █ ▀ ▄ ▶ ▼ ▲ ● ○ ·`
  7-bit printable ASCII is always permitted. Rounded box-drawing (`╭ ╮ ╰ ╯`), braille, and emoji are forbidden.
- **Palette.** Each brand hue has an *ink* value you draw with and a *fill* value you put white text on. Exact hex, uppercase digits:

  | Token | Hex | On `--bg` | Role |
  |---|---|---|---|
  | `--bg` | `#0F172A` | — | page ground |
  | `--surface` | `#1E293B` | 1.22:1 vs bg | card fill |
  | `--frame` | `#818CF8` | 5.98:1 | indigo **ink** — frames, ASCII art |
  | `--frame-fill` | `#4F46E5` | 2.84:1 | indigo **fill** — background only; white on it is 6.29:1 |
  | `--bar-ink` | `#A78BFA` | 6.56:1 | violet **ink** — art strokes, `█` runs |
  | `--bar` | `#7C3AED` | 3.13:1 | violet **fill** — background only; white on it is 5.70:1 |
  | `--accent` | `#22D3EE` | 9.88:1 | scan beam, prompts, links, cursor |
  | `--text` | `#E2E8F0` | 14.48:1 | body text |
  | `--dim` | `#94A3B8` | 6.96:1 | secondary text, `░` shading |
  | `--border-color` | `#64748B` | 3.75:1 (3.07:1 vs surface) | rules, card borders |

- **Contrast.** Every token carrying text or ASCII art clears 4.5:1 on `--bg`. The two `*-fill` tokens are background-only and must never be the computed `color` of a text-bearing element, directly or through a legacy alias. Never hardcode a hex to route around a token's contrast — add or use the correct ink/fill token instead.
- **Monospace stack** (verbatim, everywhere): `ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", "Liberation Mono", monospace`
- **Reflow rule.** Fixed-width box-drawing frames only inside fixed-size blocks. Section frames, cards, and buttons use CSS borders plus `::before`/`::after` corner glyphs.
- **Copy is frozen.** No headline, paragraph, feature name, or link may be reworded. Existing `id` attributes (`#about`, `#features`, `#download`, `#developers`) and all `href`s are preserved.
- **Accessibility.** Every ASCII art block carries `aria-hidden="true"`. No text content is replaced by art.
- **Output filenames are frozen:** `resources/icon.png`, `icon_512.png`, `icon.ico`, `icon.icns`, `quick_pdf_hero_small.jpg`. Consumers at `main.py:296`, `packaging/quickpdfocr.spec:71,88`, `docs/index.html:598` must keep working untouched.
- **Single file.** `docs/index.html` stays self-contained: no external CSS, JS, or font requests.
- **Commit style:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).

---

### Task 1: Terminal skin CSS foundation

Remap the existing palette tokens onto the terminal palette so the whole page inverts at once, then fix the hardcoded colours the remap can't reach.

**Files:**
- Modify: `docs/index.html:33-54` (`:root` block and `body`)
- Modify: `docs/index.html:63-72` (header background — hardcoded white)
- Create: `tests/test_site_theme.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the seven CSS custom properties `--bg --surface --frame --bar --accent --text --dim` and `--mono`, referenced by every later site task. Also `tests/test_site_theme.py::read_index()` — a module-level helper returning `docs/index.html` as a `str`, imported by later test modules.

- [ ] **Step 1: Write the failing test**

Create `tests/test_site_theme.py`:

```python
"""Theme-token guards for the terminal skin on docs/index.html."""
import re
from pathlib import Path

import pytest

INDEX = Path(__file__).resolve().parent.parent / "docs" / "index.html"

TERMINAL_PALETTE = {
    "--bg": "#0F172A",
    "--surface": "#1E293B",
    "--frame": "#818CF8",
    "--bar": "#7C3AED",
    "--accent": "#22D3EE",
    "--text": "#E2E8F0",
    "--dim": "#94A3B8",
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


def test_frame_token_never_carries_text():
    """--frame is ~3:1 on --bg: decoration only, never a text colour."""
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    offenders = re.findall(r"(?<!-)\bcolor\s*:\s*var\(--frame\)", css)
    assert offenders == [], "--frame must never be used as a text colour"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_site_theme.py -v`
Expected: FAIL — the palette tokens, `--mono`, and the dark `body` rule do not exist yet, and `test_no_hardcoded_white_backgrounds` reports the header's `rgba(255, 255, 255, 0.92)`.

- [ ] **Step 3: Replace the `:root` block**

Replace `docs/index.html:33-46` with:

```css
        :root {
            /* Terminal palette — docs/superpowers/specs/2026-08-15-ascii-terminal-brand-design.md */
            --bg: #0F172A;
            --surface: #1E293B;
            --frame: #818CF8;
            --bar: #7C3AED;
            --accent: #22D3EE;
            --text: #E2E8F0;
            --dim: #94A3B8;
            --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", "Liberation Mono", monospace;

            /* Legacy token names remapped onto the terminal palette, so the
               pre-existing rules below reskin without being rewritten. */
            --indigo: var(--frame);
            --indigo-hover: #6366F1;
            --violet: var(--bar);
            --cyan: var(--accent);
            --slate-dark: var(--text);
            --slate-light: var(--surface);
            --text-gray: var(--dim);
            --bg-white: var(--bg);
            --border-color: #1E293B;
            --shadow-md: 0 4px 12px -2px rgb(0 0 0 / 0.5);
            --shadow-lg: 0 12px 28px -6px rgb(0 0 0 / 0.6);
            --radius: 0;
        }
```

- [ ] **Step 4: Switch `body` to the mono stack**

Replace `docs/index.html:48-54` with:

```css
        body {
            font-family: var(--mono);
            line-height: 1.7;
            font-size: 15px;
            color: var(--text);
            background: var(--bg);
            -webkit-font-smoothing: antialiased;
        }
```

- [ ] **Step 5: Audit every legacy-token use for inversion bugs**

The remap flips meaning wherever a token was used as a *background* rather than a foreground. Find them:

```bash
grep -n -- "--slate-dark\|--slate-light\|--bg-white\|--text-gray\|--border-color" docs/index.html
```

For each hit, read the surrounding rule. The rule is correct if the token appears in `color:` and it used to be a dark-on-light pairing. It is **wrong** if the token appears in `background`/`background-color` — those need swapping to `var(--surface)` (cards, raised areas) or `var(--bg)` (page-level areas). Fix each one.

- [ ] **Step 6: Fix the header's hardcoded white**

At `docs/index.html:63-72`, replace `background: rgba(255, 255, 255, 0.92);` with:

```css
            background: rgb(15 23 42 / 0.92);
```

Then sweep for any remaining hardcoded light colours and convert each to the matching token:

```bash
grep -n -i "#fff\b\|#ffffff\|rgba(255\|: white" docs/index.html
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_site_theme.py -v`
Expected: PASS (11 tests).

- [ ] **Step 8: Commit**

```bash
git add docs/index.html tests/test_site_theme.py
git commit -m "feat: remap site palette to the terminal skin"
```

---

### Task 2: The 12 ASCII icons

**Files:**
- Modify: `docs/index.html:242-296` (`/* Features Grid */` — icon sizing rules), `:297-337` (privacy icon), `:338-405` (platform icon)
- Modify: `docs/index.html:647-734` (8 feature cards), `:742-747` (privacy), `:765-801` (3 platform cards)
- Create: `tests/test_ascii_art.py`

**Interfaces:**
- Consumes: `--frame`, `--accent`, `--dim`, `--mono` from Task 1; `read_index()` from `tests/test_site_theme.py`.
- Produces: the CSS class `.ascii-art` (shared block styling, reused verbatim by the hero in Task 3) and `.ascii-art .beam` (cyan inner span). Produces `tests/test_ascii_art.py::ALLOWED_NON_ASCII` and `::ascii_blocks()`, reused by Task 3.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ascii_art.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_ascii_art.py -v`
Expected: FAIL — `test_twelve_icons_present` reports 0 found, `test_no_svg_icons_remain` reports remaining `<svg`.

- [ ] **Step 3: Add the shared ASCII block CSS**

Insert immediately after the `/* Features Grid */` comment at `docs/index.html:242`:

```css
        /* Shared character-grid ASCII blocks (icons + hero) */
        .ascii-art {
            font-family: var(--mono);
            line-height: 1.15;
            white-space: pre;
            margin: 0;
            color: var(--frame);
            -webkit-font-smoothing: none;
        }

        .ascii-art .beam { color: var(--accent); }
        .ascii-art .fill { color: var(--bar-ink); }
        .ascii-art .dim  { color: var(--dim); }

        .ascii-icon {
            font-size: 15px;
            letter-spacing: 0;
            display: inline-block;
        }

        .icon-indigo { color: var(--frame); }
        .icon-violet { color: var(--bar-ink); }
        .icon-cyan   { color: var(--accent); }
```

- [ ] **Step 4: Replace the 8 feature icons**

For each feature card at `docs/index.html:647-734`, replace the `<svg>...</svg>` element inside `<div class="feature-icon icon-*">` with a `<pre>`. Keep the wrapping `<div>` and its colour class exactly as-is. Keep the cards in their current order.

Card 1 — Drag & Drop:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true"> ┌─────┐
 │ ░░░ │
 └──┬──┘
    ▼
┌ ─ ─ ─ ┐</pre>
```

Card 2 — File Picker:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌─────────┐
│ ▶ a.pdf │
│   b.pdf │
│   c.pdf │
└─────────┘</pre>
```

Card 3 — Native OCR Engines (the brand motif; the beam span is cyan):

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌─────────┐
│ ░░░░░░░ │
│<span class="beam">═════════</span>│
│ ▓▓▓▓▓▓▓ │
└─────────┘</pre>
```

Card 4 — Progress & Status Updates:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌─────────┐
│ scan... │
│ <span class="fill">████</span>░░░ │
│   57%   │
└─────────┘</pre>
```

Card 5 — One-Click Copy to Clipboard:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true"> ┌──────┐
┌┴─────┐│
│ ░░░░ ├┘
│ ░░░░ │
└──────┘</pre>
```

Card 6 — Error Recovery:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌─────────┐
│  ! err  │
│ ──────▶ │
│ [retry] │
└─────────┘</pre>
```

Card 7 — Modern UI:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌─┬───────┐
│●│ ░░░░░ │
│░│ ░░░░░ │
│░│ ░░░░░ │
└─┴───────┘</pre>
```

Card 8 — Fully Standalone:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">  ┌─────┐
 ┌┴────┐│
 │ ▓▓▓ ││
 │ ▓▓▓ ├┘
 └─────┘</pre>
```

- [ ] **Step 5: Replace the privacy icon**

At `docs/index.html:742-747`, replace the `<svg>` inside `<div class="privacy-icon">` with a padlock — a shield's diagonals do not survive the charset restriction:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">  ┌───┐
 ┌┴───┴┐
 │ ███ │
 │ █▀█ │
 └─────┘</pre>
```

- [ ] **Step 6: Replace the 3 platform icons**

At `docs/index.html:765-801`, in card order Windows / macOS / Linux:

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌───┬───┐
│░░░│░░░│
├───┼───┤
│░░░│░░░│
└───┴───┘</pre>
```

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌───────┐
│ ░░░░░ │
│ ░░░░░ │
└───────┘
 ▀▀▀▀▀▀▀</pre>
```

```html
<pre class="ascii-art ascii-icon" aria-hidden="true">┌───────┐
│ <span class="beam">&gt; _</span>   │
│ ░░░░  │
│ ░░    │
└───────┘</pre>
```

Note the `&gt;` escape — a literal `>` inside markup is legal here but escaping keeps the parse unambiguous. The test strips tags and resolves nothing, so keep `&gt;` out of any block the 5-line test counts by using it only inside spans as shown.

- [ ] **Step 7: Remove the now-dead SVG sizing rules**

The old rules `.feature-icon svg` (`docs/index.html:275`), `.privacy-icon svg` (`:333`), and `.download-card .platform-icon svg` (`:377`) no longer match anything. Delete those three rule blocks. Leave the parent `.feature-icon` / `.privacy-icon` / `.platform-icon` rules in place, but remove any `background`, `border-radius`, or fixed `width`/`height` that boxed the old SVG — the `<pre>` sizes itself.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_ascii_art.py tests/test_site_theme.py -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add docs/index.html tests/test_ascii_art.py
git commit -m "feat: replace inline SVG icons with ASCII character-grid art"
```

---

### Task 3: Live ASCII hero

**Files:**
- Modify: `docs/index.html:120-214` (`/* Hero Section */` CSS)
- Modify: `docs/index.html:612-629` (hero markup)
- Modify: `tests/test_ascii_art.py` (append hero tests)

**Interfaces:**
- Consumes: `.ascii-art` and `.beam`/`.fill` from Task 2; `ascii_blocks()` from `tests/test_ascii_art.py`.
- Produces: the CSS class `.hero-terminal`; the hero image is no longer rendered on-page, which Task 7 relies on.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ascii_art.py`:

```python
HERO_RE = re.compile(
    r'<pre[^>]*class="[^"]*\bhero-terminal\b[^"]*"[^>]*>(.*?)</pre>', re.S
)


def _hero_text() -> str:
    match = HERO_RE.search(read_index())
    assert match, "no .hero-terminal block found"
    return re.sub(r"<[^>]+>", "", match.group(1)).strip("\n")


def test_hero_terminal_is_fixed_46_columns():
    """Every framed row is exactly 46 columns, or the box will not close."""
    framed = [ln for ln in _hero_text().split("\n")
              if ln.startswith(("┌", "│", "└"))]
    assert framed, "hero has no framed rows"
    widths = {len(ln) for ln in framed}
    assert widths == {46}, f"hero framed rows must all be 46 cols, got {widths}"


def test_hero_uses_clamped_font_size():
    """clamp() keeps the fixed grid inside narrow viewports."""
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    rule = re.search(r"\.hero-terminal\s*\{(.*?)\}", css, re.S)
    assert rule, ".hero-terminal rule not found"
    assert "clamp(" in rule.group(1), "hero font-size must use clamp()"


def test_hero_background_image_removed():
    """The hero no longer paints quick_pdf_hero_small.jpg; it is og:image only."""
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    assert "quick_pdf_hero_small" not in css


def test_cursor_blink_respects_reduced_motion():
    css = read_index().split("<style>", 1)[1].split("</style>", 1)[0]
    assert "prefers-reduced-motion" in css
    reduced = re.search(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\s{8}\}",
        css, re.S,
    )
    assert reduced, "no prefers-reduced-motion block"
    assert "animation" in reduced.group(1), (
        "reduced-motion block must disable the cursor animation"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_ascii_art.py -v -k hero`
Expected: FAIL — no `.hero-terminal` block exists.

- [ ] **Step 3: Replace the hero CSS**

In the `/* Hero Section */` block at `docs/index.html:120-214`: delete every `background-image` / `background` declaration that references `quick_pdf_hero_small.jpg` and any gradient overlay that existed only to darken that photo. The page ground is already `--bg`. Then append:

```css
        .hero-terminal {
            /* .ascii-art is color:inherit so the per-card .icon-* classes can
               tint each icon; the hero has no such wrapper, so it states its
               own ink here. */
            color: var(--frame);
            font-size: clamp(6px, 1.55vw, 15px);
            margin: 2rem auto 0;
            width: max-content;
            max-width: 100%;
        }

        .hero-prompt { color: var(--dim); }

        .cursor {
            color: var(--accent);
            animation: blink 1.1s step-end infinite;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        @media (prefers-reduced-motion: reduce) {
            .cursor { animation: none; }
        }
```

- [ ] **Step 4: Replace the hero markup**

Inside `<div class="hero-content">` at `docs/index.html:614`, keep the existing `<h1>`, the existing subtitle paragraph, and the existing CTA buttons exactly as they are. Insert this block after the CTA buttons:

```html
<pre class="ascii-art hero-terminal" aria-hidden="true"><span class="hero-prompt">~/Documents $</span> quickpdfocr scan report.pdf

┌─ QuickPdfOcr ────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  <span class="beam">══════════════════════════════════════</span>  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│                                          │
│  [<span class="fill">████████████████</span>░░░░░░] 71%            │
│  page 12/17  ·  vision.framework         │
└──────────────────────────────────────────┘

<span class="beam">&gt;</span> 4,812 words copied to clipboard<span class="cursor">_</span></pre>
```

Count the framed rows before saving: `┌`, four `│` rows, the blank `│` row, two `│` rows, `└` — each must be exactly 46 characters wide once tags are stripped. The test enforces this.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_ascii_art.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/index.html tests/test_ascii_art.py
git commit -m "feat: replace hero image with live ASCII terminal"
```

---

### Task 4: Terminal chrome — nav, section titles, buttons

**Files:**
- Modify: `docs/index.html:215-241` (section title CSS), `:594-610` (header), `:220-241` + button CSS
- Modify: `tests/test_site_theme.py` (append chrome tests)

**Interfaces:**
- Consumes: palette tokens from Task 1.
- Produces: CSS classes `.boxed` (reflow-safe faked frame) and `.cmd` (section-title prompt), used by no later task but asserted in Task 9's screenshots.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_site_theme.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_site_theme.py -v -k "command or reflow or bracket or shell"`
Expected: FAIL — none of `.cmd::before`, `.boxed`, `.btn::before`, or the prompt string exist.

- [ ] **Step 3: Add the chrome CSS**

Insert after the `/* Section Styles */` comment at `docs/index.html:215`:

```css
        /* Reflow-safe faked box-drawing: CSS borders + corner glyphs.
           True character frames are reserved for fixed-size .ascii-art blocks. */
        .boxed {
            position: relative;
            border: 1px solid var(--frame);
            background: var(--surface);
            padding: 1.5rem;
        }

        .boxed::before,
        .boxed::after {
            position: absolute;
            color: var(--frame);
            font-family: var(--mono);
            line-height: 1;
            pointer-events: none;
        }

        .boxed::before { content: "┌"; top: -1px; left: -1px; }
        .boxed::after  { content: "┘"; bottom: -1px; right: -1px; }

        /* Section titles as shell commands */
        .cmd::before {
            content: "$ ";
            color: var(--accent);
        }

        /* Buttons as bracketed terminal affordances */
        .btn::before { content: "[ "; color: var(--dim); }
        .btn::after  { content: " ]"; color: var(--dim); }
```

- [ ] **Step 4: Apply the classes**

- Add `cmd` to every `<h2 class="section-title">` — it becomes `class="section-title cmd"`. There are four, at `docs/index.html:633`, `:645`, `:759`, and in the developer section around `:812`. Do not change the title text.
- Add `boxed` to the `.feature-card` and `.download-card` elements' class lists.
- In the header nav at `docs/index.html:601`, insert this as the first child of `<nav class="header-links">`:

```html
<span class="hero-prompt" aria-hidden="true">~/quickpdfocr $</span>
```

- [ ] **Step 5: Verify the reflow rule holds**

Confirm no character-drawn frame was introduced into a reflowing container:

```bash
grep -n "┌\|└\|─" docs/index.html | grep -v "ascii-art\|ascii-icon\|hero-terminal\|content:"
```

Expected: only lines *inside* `<pre>` blocks (which the grep shows without their opening tag) and the `.boxed::before/::after` `content:` declarations. Any hit inside a `<div>`, `<h2>`, or `<p>` is a defect — move it into a `<pre class="ascii-art">` or convert it to a CSS border.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: PASS, including the pre-existing app test modules.

- [ ] **Step 7: Commit**

```bash
git add docs/index.html tests/test_site_theme.py
git commit -m "feat: add terminal chrome to nav, section titles and buttons"
```

---

### Task 5: The two icon masters

**Files:**
- Modify: `resources/icon.svg` (full rewrite)
- Create: `resources/icon_small.svg`
- Create: `tests/test_icon_masters.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `resources/icon.svg` and `resources/icon_small.svg`, both 1024×1024 viewBox, consumed by `render_icons.py` in Task 6 via the `SIZE_SOURCES` map.

- [ ] **Step 1: Write the failing test**

Create `tests/test_icon_masters.py`:

```python
"""Structural guards for the two SVG icon masters."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
DETAILED = RESOURCES / "icon.svg"
SIMPLE = RESOURCES / "icon_small.svg"
SVG_NS = "{http://www.w3.org/2000/svg}"


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_master_exists_and_parses(master):
    assert master.exists(), f"{master.name} is missing"
    ET.parse(master)


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_master_is_1024_square(master):
    root = ET.parse(master).getroot()
    assert root.get("viewBox") == "0 0 1024 1024"


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_glyphs_are_paths_not_text(master):
    """Font-independent: rendering must not depend on installed fonts."""
    root = ET.parse(master).getroot()
    texts = list(root.iter(f"{SVG_NS}text"))
    assert texts == [], (
        f"{master.name} uses <text>; glyphs must be vector paths"
    )


@pytest.mark.parametrize("master", [DETAILED, SIMPLE], ids=["detailed", "simple"])
def test_master_shares_squircle_and_gradient(master):
    """Both masters must read as one icon across the size bands."""
    source = master.read_text(encoding="utf-8")
    assert 'rx="230"' in source, "squircle corner radius missing"
    assert "#4F46E5" in source and "#7C3AED" in source, "brand gradient missing"
    assert "#22D3EE" in source, "cyan accent missing"


def test_simple_master_is_substantially_simpler():
    """The small master must carry far fewer drawing ops, or it will still mush."""
    def ops(path):
        root = ET.parse(path).getroot()
        return sum(1 for el in root.iter()
                   if el.tag in {f"{SVG_NS}rect", f"{SVG_NS}path",
                                 f"{SVG_NS}circle"})

    assert ops(SIMPLE) < ops(DETAILED) / 2, (
        "icon_small.svg must be at least 2x simpler than icon.svg"
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_icon_masters.py -v`
Expected: FAIL — `icon_small.svg` does not exist, and the current `icon.svg` is the document-page design.

- [ ] **Step 3: Rewrite `resources/icon.svg` as the terminal window**

Replace the entire file. Every glyph is a `<rect>` — no `<text>`, so no font dependency:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4F46E5"/>
      <stop offset="1" stop-color="#7C3AED"/>
    </linearGradient>
    <radialGradient id="topLight" cx="0.5" cy="0.08" r="0.9">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.16"/>
      <stop offset="0.55" stop-color="#FFFFFF" stop-opacity="0.05"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <filter id="winShadow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="18"/>
    </filter>
  </defs>

  <!-- Squircle background -->
  <rect x="0" y="0" width="1024" height="1024" rx="230" fill="url(#bgGrad)"/>
  <rect x="0" y="0" width="1024" height="1024" rx="230" fill="url(#topLight)"/>

  <!-- Terminal window shadow, then body -->
  <rect x="176" y="232" width="672" height="560" rx="28" fill="#1E1B4B"
        opacity="0.34" filter="url(#winShadow)" transform="translate(6 18)"/>
  <rect x="176" y="216" width="672" height="560" rx="28" fill="#0F172A"/>
  <rect x="176" y="216" width="672" height="560" rx="28" fill="none"
        stroke="#334155" stroke-width="6"/>

  <!-- Title bar + traffic-light dots -->
  <path d="M 176 244 Q 176 216 204 216 L 820 216 Q 848 216 848 244 L 848 300 L 176 300 Z"
        fill="#1E293B"/>
  <circle cx="232" cy="258" r="15" fill="#475569"/>
  <circle cx="286" cy="258" r="15" fill="#475569"/>
  <circle cx="340" cy="258" r="15" fill="#475569"/>

  <!-- Unrecognized text rows (dim) -->
  <g fill="#475569">
    <rect x="232" y="356" width="440" height="26" rx="13"/>
    <rect x="232" y="416" width="380" height="26" rx="13"/>
  </g>

  <!-- Cyan scan beam: halo, mid glow, bright core, hot centre -->
  <rect x="196" y="466" width="632" height="72" rx="36" fill="#22D3EE" opacity="0.15"/>
  <rect x="210" y="482" width="604" height="40" rx="20" fill="#22D3EE" opacity="0.30"/>
  <rect x="224" y="494" width="576" height="16" rx="8" fill="#22D3EE"/>
  <rect x="224" y="499" width="576" height="6" rx="3" fill="#CFFAFE" opacity="0.95"/>

  <!-- Recognized text rows (bright) -->
  <g fill="#E2E8F0">
    <rect x="232" y="566" width="440" height="26" rx="13"/>
    <rect x="232" y="626" width="360" height="26" rx="13"/>
  </g>

  <!-- Prompt: ">" chevron drawn as two strokes, plus the cursor block -->
  <path d="M 232 688 L 268 712 L 232 736" fill="none" stroke="#22D3EE"
        stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="298" y="700" width="72" height="22" rx="8" fill="#22D3EE"/>
</svg>
```

- [ ] **Step 4: Create `resources/icon_small.svg`**

The same squircle and gradient, carrying only a large cyan `> _` — this is what survives at 16px:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4F46E5"/>
      <stop offset="1" stop-color="#7C3AED"/>
    </linearGradient>
  </defs>

  <rect x="0" y="0" width="1024" height="1024" rx="230" fill="url(#bgGrad)"/>

  <!-- Oversized ">" chevron -->
  <path d="M 300 356 L 508 512 L 300 668" fill="none" stroke="#22D3EE"
        stroke-width="96" stroke-linecap="round" stroke-linejoin="round"/>
  <!-- Cursor underscore -->
  <rect x="576" y="600" width="188" height="68" rx="26" fill="#22D3EE"/>
</svg>
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_icon_masters.py -v`
Expected: PASS (11 tests).

- [ ] **Step 6: Commit**

```bash
git add resources/icon.svg resources/icon_small.svg tests/test_icon_masters.py
git commit -m "feat: re-author icon masters as terminal window plus small-size mark"
```

---

### Task 6: Multi-resolution render pipeline

**Files:**
- Create: `resources/requirements-assets.txt`
- Create: `resources/render_icons.py`
- Modify: `resources/create_icns.py` (replace `create_icns_from_png` with `create_icns_from_pngs`)
- Delete: `resources/generate_icon.py`
- Create: `tests/test_icon_outputs.py`

**Interfaces:**
- Consumes: `resources/icon.svg`, `resources/icon_small.svg` from Task 5.
- Produces: `create_icns.create_icns_from_pngs(png_by_size: dict[int, Path], output_icns_path: str | Path) -> None`, called by `render_icons.main()`. Produces `render_icons.SIZE_SOURCES: dict[int, Path]` and `render_icons.ICO_SIZES: list[int]`, read by `tests/test_icon_outputs.py`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_icon_outputs.py`:

```python
"""Guards on the rendered icon artefacts and the size->master mapping."""
import sys
from pathlib import Path

import pytest

RESOURCES = Path(__file__).resolve().parent.parent / "resources"
sys.path.insert(0, str(RESOURCES))

Image = pytest.importorskip("PIL.Image", reason="Pillow is asset tooling")
render_icons = pytest.importorskip(
    "render_icons", reason="asset tooling not installed"
)

ICO = RESOURCES / "icon.ico"
ICNS = RESOURCES / "icon.icns"
PNG_256 = RESOURCES / "icon.png"
PNG_512 = RESOURCES / "icon_512.png"
FAVICON = RESOURCES / "favicon.png"


def test_small_sizes_come_from_the_simple_master():
    for size in (16, 32, 48, 64):
        assert render_icons.SIZE_SOURCES[size].name == "icon_small.svg"


def test_large_sizes_come_from_the_detailed_master():
    for size in (128, 256, 512, 1024):
        assert render_icons.SIZE_SOURCES[size].name == "icon.svg"


@pytest.mark.parametrize(
    "path,expected",
    [(PNG_256, (256, 256)), (PNG_512, (512, 512)), (FAVICON, (32, 32))],
    ids=["icon.png", "icon_512.png", "favicon.png"],
)
def test_png_outputs_exist_at_expected_size(path, expected):
    assert path.exists(), f"{path.name} not rendered"
    with Image.open(path) as im:
        assert im.size == expected


def test_ico_carries_all_six_sizes():
    assert ICO.exists(), "icon.ico not rendered"
    with Image.open(ICO) as im:
        sizes = {s[0] for s in im.info["sizes"]}
    assert sizes == set(render_icons.ICO_SIZES), (
        f"icon.ico sizes {sorted(sizes)} != {render_icons.ICO_SIZES}"
    )


def test_icns_exists_and_is_non_trivial():
    assert ICNS.exists(), "icon.icns not rendered"
    assert ICNS.stat().st_size > 50_000, "icon.icns looks truncated"


def test_16px_is_not_a_downscale_of_the_detailed_art():
    """The whole point of two masters: the 16px slot must be distinct art."""
    small = RESOURCES / "_render" / "icon_16.png"
    large = RESOURCES / "_render" / "icon_256.png"
    if not (small.exists() and large.exists()):
        pytest.skip("intermediate renders not retained; run render_icons.py")
    with Image.open(small) as a, Image.open(large) as b:
        a = a.convert("RGBA")
        downscaled = b.convert("RGBA").resize((16, 16), Image.Resampling.LANCZOS)
        diff = sum(
            abs(p - q)
            for pa, pb in zip(a.getdata(), downscaled.getdata())
            for p, q in zip(pa, pb)
        )
    assert diff > 5000, "16px render is indistinguishable from a downscale"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_icon_outputs.py -v`
Expected: all tests SKIP — Pillow and `render_icons` are not importable yet. Skips are the correct failing state here; they turn into passes once Step 3–6 land.

- [ ] **Step 3: Add the asset tooling requirements**

`requirements.txt:19` gates Pillow to `sys_platform != 'darwin'`, so it is deliberately absent on macOS and must not be added to the runtime requirements — it would bloat the shipped bundle. Create `resources/requirements-assets.txt`:

```
# Asset-authoring tooling only. NOT a runtime dependency of QuickPdfOcr —
# do not merge into requirements.txt (Pillow is deliberately excluded on
# macOS there, and Playwright must never enter the shipped bundle).
playwright>=1.49.0
Pillow>=12.3.0
```

Install it:

```bash
.venv/bin/pip install -r resources/requirements-assets.txt
.venv/bin/playwright install chromium
```

- [ ] **Step 4: Refactor `create_icns.py` to consume pre-rendered PNGs**

Replace `create_icns_from_png` (`resources/create_icns.py:12-103`) and `main` (`:106-124`) with:

```python
ICONSET_SLOTS = [
    (16, 1, 'icon_16x16.png'),
    (16, 2, 'icon_16x16@2x.png'),
    (32, 1, 'icon_32x32.png'),
    (32, 2, 'icon_32x32@2x.png'),
    (64, 1, 'icon_64x64.png'),
    (128, 1, 'icon_128x128.png'),
    (128, 2, 'icon_128x128@2x.png'),
    (256, 1, 'icon_256x256.png'),
    (256, 2, 'icon_256x256@2x.png'),
    (512, 1, 'icon_512x512.png'),
    (512, 2, 'icon_512x512@2x.png'),
]


def create_icns_from_pngs(png_by_size, output_icns_path):
    """Build a macOS .icns from PNGs already rendered at each exact size.

    Every slot is copied, never resized: the point of the two-master
    pipeline is that a 16pt slot carries different art from a 512pt slot,
    which downscaling would destroy.

    Args:
        png_by_size: {pixel_size: Path} covering every size in ICONSET_SLOTS.
        output_icns_path: destination .icns path.
    """
    iconset_dir = Path(output_icns_path).with_suffix('.iconset')
    iconset_dir.mkdir(exist_ok=True)

    for size, scale, filename in ICONSET_SLOTS:
        pixels = size * scale
        source = png_by_size.get(pixels)
        if source is None:
            raise KeyError(
                f"no rendered PNG for {pixels}px (slot {filename}); "
                f"have {sorted(png_by_size)}"
            )
        shutil.copyfile(source, iconset_dir / filename)
        print(f"  - {filename} ({pixels}x{pixels}) <- {Path(source).name}")

    result = subprocess.run(
        ['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(output_icns_path)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        shutil.rmtree(iconset_dir)
        print(f"Created: {output_icns_path}")
        return

    raise RuntimeError(
        f"iconutil failed ({result.returncode}): {result.stderr.strip()}\n"
        f"Iconset retained at {iconset_dir} for manual conversion on macOS."
    )
```

Add `import subprocess` to the module imports and drop the now-unused `from PIL import Image` and `import os`. Delete the old `main()` and the `if __name__ == '__main__'` block — `render_icons.py` is the entry point now.

Note the deliberate behaviour change: the old code silently fell back to a PIL-written `.icns` when `iconutil` was unavailable, producing a single-resolution file that looked fine locally and shipped wrong. It now raises. `.icns` is a macOS-only artefact built on macOS.

- [ ] **Step 5: Create `resources/render_icons.py`**

```python
#!/usr/bin/env python3
"""Render every raster icon artefact from the two SVG masters.

The detailed master (icon.svg) feeds 128px and above; the simplified
master (icon_small.svg) feeds 64px and below, so Dock, taskbar and
favicon sizes stay legible instead of becoming a smear of the large art.

Requires resources/requirements-assets.txt (Playwright + Pillow) and
`playwright install chromium`. This is asset tooling, not a runtime
dependency of the app.

Usage:  python3 resources/render_icons.py
"""

import shutil
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from create_icns import create_icns_from_pngs

RESOURCES = Path(__file__).resolve().parent
DETAILED = RESOURCES / "icon.svg"
SIMPLE = RESOURCES / "icon_small.svg"
RENDER_DIR = RESOURCES / "_render"

SIZE_SOURCES = {
    16: SIMPLE,
    32: SIMPLE,
    48: SIMPLE,
    64: SIMPLE,
    128: DETAILED,
    256: DETAILED,
    512: DETAILED,
    1024: DETAILED,
}

ICO_SIZES = [16, 32, 48, 64, 128, 256]

_WRAPPER = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; padding: 0; background: transparent; }
svg { display: block; width: 100vw; height: 100vh; }
</style></head><body>%s</body></html>"""


def render_all(out_dir: Path) -> dict[int, Path]:
    """Render each size from its designated master. Returns {size: png_path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: dict[int, Path] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for size, master in sorted(SIZE_SOURCES.items()):
                page = browser.new_page(
                    viewport={"width": size, "height": size},
                    device_scale_factor=1,
                )
                page.set_content(_WRAPPER % master.read_text(encoding="utf-8"))
                target = out_dir / f"icon_{size}.png"
                page.screenshot(path=str(target), omit_background=True)
                page.close()
                rendered[size] = target
                print(f"  rendered {size:>4}px from {master.name}")
        finally:
            browser.close()

    return rendered


def main() -> int:
    for master in (DETAILED, SIMPLE):
        if not master.exists():
            print(f"Error: master not found: {master}")
            return 1

    print("Rendering icon sizes...")
    pngs = render_all(RENDER_DIR)

    shutil.copyfile(pngs[256], RESOURCES / "icon.png")
    shutil.copyfile(pngs[512], RESOURCES / "icon_512.png")
    shutil.copyfile(pngs[32], RESOURCES / "favicon.png")
    print("Wrote icon.png, icon_512.png, favicon.png")

    images = [Image.open(pngs[s]).convert("RGBA") for s in ICO_SIZES]
    images[-1].save(
        RESOURCES / "icon.ico",
        format="ICO",
        append_images=images[:-1],
        sizes=[(s, s) for s in ICO_SIZES],
    )
    for image in images:
        image.close()
    print(f"Wrote icon.ico ({len(ICO_SIZES)} sizes)")

    create_icns_from_pngs(pngs, RESOURCES / "icon.icns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run the pipeline and delete the dead generator**

```bash
.venv/bin/python resources/render_icons.py
git rm resources/generate_icon.py
```

`generate_icon.py` is the PIL-drawn placeholder generator already documented as deprecated in `resources/README.md:52-53`. It has no callers — confirm before removing:

```bash
grep -rn "generate_icon" --include="*.py" --include="*.md" --include="*.spec" . | grep -v "^./.worktrees\|^./.venv"
```

Expected: only `resources/README.md`, which Task 8 rewrites.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_icon_outputs.py -v`
Expected: PASS (9 tests, none skipped).

- [ ] **Step 8: Commit**

```bash
git add resources/render_icons.py resources/create_icns.py \
        resources/requirements-assets.txt resources/icon.png \
        resources/icon_512.png resources/favicon.png resources/icon.ico \
        resources/icon.icns tests/test_icon_outputs.py
git rm --cached resources/generate_icon.py 2>/dev/null || true
git add -u
git commit -m "feat: render icons from two masters so small sizes stay legible"
```

Note: `resources/_render/` holds intermediates. Add it to `.gitignore` in this commit rather than committing 8 loose PNGs:

```bash
echo "resources/_render/" >> .gitignore
```

---

### Task 7: Regenerate the hero as the og:image

**Files:**
- Modify: `resources/hero.svg` (full rewrite)
- Modify: `resources/quick_pdf_hero_small.jpg` (regenerated)
- Create: `resources/render_hero.py`

**Interfaces:**
- Consumes: the Playwright tooling installed in Task 6.
- Produces: `resources/quick_pdf_hero_small.jpg` at 1920×1080, referenced unchanged by `docs/index.html:16` and `:22`.

- [ ] **Step 1: Rewrite `resources/hero.svg`**

Depict the same terminal scene the live hero shows, at 1920×1080. Unlike the icon masters this may use `<text>` — it is rendered once through Chromium, so the font is baked into the JPEG. Use the mono stack so the render matches the site.

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0F172A"/>
      <stop offset="1" stop-color="#1E1B4B"/>
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
  </defs>

  <rect width="1920" height="1080" fill="url(#bg)"/>

  <!-- Terminal window -->
  <rect x="360" y="210" width="1200" height="660" rx="18" fill="#0B1220"
        stroke="#4F46E5" stroke-width="3"/>
  <path d="M 360 228 Q 360 210 378 210 L 1542 210 Q 1560 210 1560 228 L 1560 282 L 360 282 Z"
        fill="#1E293B"/>
  <circle cx="410" cy="246" r="11" fill="#475569"/>
  <circle cx="450" cy="246" r="11" fill="#475569"/>
  <circle cx="490" cy="246" r="11" fill="#475569"/>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
     font-size="30">
    <text x="540" y="256" fill="#64748B">QuickPdfOcr</text>
    <text x="410" y="360" fill="#475569">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</text>
    <text x="410" y="426" fill="#22D3EE" filter="url(#glow)">══════════════════════════════════</text>
    <text x="410" y="426" fill="#22D3EE">══════════════════════════════════</text>
    <text x="410" y="492" fill="#E2E8F0">▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓</text>
    <text x="410" y="606" fill="#7C3AED">████████████████</text>
    <text x="722" y="606" fill="#334155">░░░░░░</text>
    <text x="880" y="606" fill="#E2E8F0">71%</text>
    <text x="410" y="672" fill="#64748B">page 12/17  ·  vision.framework</text>
    <text x="360" y="960" fill="#22D3EE">&gt;</text>
    <text x="400" y="960" fill="#E2E8F0">4,812 words copied to clipboard</text>
  </g>
</svg>
```

Remove the duplicated `x` attribute on the progress-bar remainder `<text>` — split it into its own element positioned at `x="722"`. An element with two `x` attributes is malformed XML and will fail to parse.

- [ ] **Step 2: Create `resources/render_hero.py`**

```python
#!/usr/bin/env python3
"""Render resources/hero.svg to the og:image JPEG.

The hero is no longer displayed on the page — docs/index.html draws a live
ASCII terminal. This JPEG exists solely as the Open Graph / Twitter card
preview referenced by docs/index.html:16 and :22.

Usage:  python3 resources/render_hero.py
"""

from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

RESOURCES = Path(__file__).resolve().parent
SOURCE = RESOURCES / "hero.svg"
TARGET = RESOURCES / "quick_pdf_hero_small.jpg"
MAX_BYTES = 350_000

_WRAPPER = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; padding: 0; }
svg { display: block; width: 100vw; height: 100vh; }
</style></head><body>%s</body></html>"""


def main() -> int:
    if not SOURCE.exists():
        print(f"Error: {SOURCE} not found")
        return 1

    png = RESOURCES / "_render" / "hero.png"
    png.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.set_content(_WRAPPER % SOURCE.read_text(encoding="utf-8"))
        page.screenshot(path=str(png))
        browser.close()

    with Image.open(png) as image:
        image.convert("RGB").save(TARGET, "JPEG", quality=85, optimize=True)

    size = TARGET.stat().st_size
    print(f"Wrote {TARGET.name}: {size:,} bytes")
    if size > MAX_BYTES:
        print(f"Error: exceeds {MAX_BYTES:,} byte budget")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Render it**

Run: `.venv/bin/python resources/render_hero.py`
Expected: exit 0, and a reported size under 350,000 bytes.

- [ ] **Step 4: Verify the result visually**

Open `resources/quick_pdf_hero_small.jpg` and confirm: the box-drawing rows align (no ragged right edge), the cyan beam glows, and no glyph rendered as a tofu box. If any row is ragged, the `<text>` elements are not landing on a shared grid — set an explicit `letter-spacing` or `textLength` on the affected rows.

- [ ] **Step 5: Commit**

```bash
git add resources/hero.svg resources/render_hero.py resources/quick_pdf_hero_small.jpg
git commit -m "feat: regenerate hero image as terminal scene for og:image"
```

---

### Task 8: Favicon repoint and documentation

**Files:**
- Modify: `docs/index.html:25` (favicon link)
- Modify: `resources/README.md` (pipeline section)
- Modify: `docs/design/brand-refresh-prompts.md` (full rewrite)
- Modify: `docs/README.md` (asset pipeline references)

**Interfaces:**
- Consumes: `resources/favicon.png` from Task 6.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Repoint the favicon**

`docs/index.html:25` points `rel="icon"` at the 256px `icon.png`, leaving browsers to downscale detailed art to 16px — the exact problem the two-master pipeline exists to solve. Replace that line with:

```html
    <link rel="icon" type="image/png" sizes="32x32" href="https://raw.githubusercontent.com/KSEGIT/QuickPdfOcr/main/resources/favicon.png">
```

Leave the logo `<img>` at `docs/index.html:598` pointing at `icon.png` — it renders at 36px, where the detailed art still reads.

- [ ] **Step 2: Rewrite `docs/design/brand-refresh-prompts.md`**

The file currently describes the superseded indigo-squircle direction as the source of truth. Replace its body with the ASCII/terminal brief: the shared design language (charset, palette table, monospace stack, reflow rule) copied from the Global Constraints of this plan, then three sections — App icon (two masters, size bands, deliverables), Hero (og:image only, 1920×1080), Website (terminal skin, 12 ASCII icons, live hero). Add a line at the top: `Supersedes the indigo-squircle / photographic-hero direction shipped in a642a3f.` Point the reader at `docs/superpowers/specs/2026-08-15-ascii-terminal-brand-design.md` as the full spec.

- [ ] **Step 3: Rewrite the `resources/README.md` pipeline section**

Replace the "Icon Design", "Regenerating Icons", and "Icon Generation Scripts" sections (`resources/README.md:14-59`). The new content must state:

- `icon.svg` — detailed terminal-window master, feeds 128/256/512/1024
- `icon_small.svg` — simplified `> _` master, feeds 16/32/48/64
- `favicon.png` — new 32px output, used by the site
- Regeneration is one command, replacing the old heredoc:

```bash
.venv/bin/pip install -r resources/requirements-assets.txt
.venv/bin/playwright install chromium
.venv/bin/python resources/render_icons.py   # icon.png, icon_512.png, favicon.png, icon.ico, icon.icns
.venv/bin/python resources/render_hero.py    # quick_pdf_hero_small.jpg
```

- `create_icns.py` copies pre-rendered PNGs into the iconset and requires macOS `iconutil`; it no longer downscales and no longer falls back silently.
- Delete the `generate_icon.py` bullet — the file is gone.

- [ ] **Step 4: Check `docs/README.md` for stale references**

```bash
grep -n "hero\|icon\|generate_icon\|svg" docs/README.md
```

Update any line describing the old asset pipeline or the photographic hero. If the hero is described as a page background, correct it to og:image only.

- [ ] **Step 5: Verify no stale references remain**

```bash
grep -rn "generate_icon" --include="*.md" --include="*.py" . | grep -v "^./.worktrees\|^./.venv"
```

Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add docs/index.html docs/README.md docs/design/brand-refresh-prompts.md resources/README.md
git commit -m "docs: repoint favicon and update brand brief for the terminal direction"
```

---

### Task 9: Cross-viewport verification

The spec's verification gate. Nothing here is optional — this task is what proves the charset restriction and the reflow rule actually held in a browser rather than only in a regex.

**Files:**
- Create: `tests/test_site_rendering.py`
- Create: `docs/design/screenshots/` (three PNGs, committed as review evidence)

**Interfaces:**
- Consumes: everything from Tasks 1–8; Playwright from Task 6.

- [ ] **Step 1: Write the rendering test**

Create `tests/test_site_rendering.py`:

```python
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
            const bgOf = (el) => {
                for (let n = el; n; n = n.parentElement) {
                    const bg = getComputedStyle(n).backgroundColor;
                    if (bg && !/rgba?\\(0,\\s*0,\\s*0,\\s*0\\)/.test(bg)) return bg;
                }
                return 'rgb(255, 255, 255)';
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
```

- [ ] **Step 2: Run it**

Run: `.venv/bin/python -m pytest tests/test_site_rendering.py -v`
Expected: every test PASSES.

If `test_every_text_element_clears_aa_against_its_real_background` fails, fix the colour pairing — do not raise the threshold or add elements to the skip list. This test exists precisely because the earlier static guards could not see real foreground/background pairings and let a 2.84:1 token and a 2.98:1 button through.

If `test_no_tofu_glyphs` fails, the mitigation is stated in the spec's risk table: escalate to an inlined base64 subset webfont in `docs/index.html`. Do not silence the test.

If `test_no_horizontal_overflow` fails at 375px, the hero `clamp()` lower bound is too high — lower the `6px` floor or the `1.55vw` slope. Do not add `overflow-x: hidden`; that hides the defect rather than fixing it.

- [ ] **Step 3: Review the screenshots**

Open all three of `docs/design/screenshots/*.png`. Confirm by eye: icon frames close cleanly, the hero terminal is centred and unclipped, cards read against the dark ground, and no section still looks like the old light theme.

- [ ] **Step 4: Run the full suite**

Run: `.venv/bin/python -m pytest -q`

**Known baseline, measured at `69bc25e` before any of this work landed:**
`1 failed, 67 passed, 8 skipped, 2 errors`

- FAILED `tests/test_selftest.py::test_selftest_detects_ocr_error_markers` — `main` has no attribute `PdfOcrProcessor`
- ERROR `tests/test_main_window.py::test_open_file_works_after_a_thread_is_destroyed`
- ERROR `tests/test_main_window.py::test_is_ocr_running_treats_a_deleted_thread_as_not_running`

These three are pre-existing application-code failures, unrelated to the brand work. **Do not fix them — they are outside this plan's scope.** Expected after this plan: the same three, plus every new site/icon test passing. Any *additional* failure is a regression from this branch and must be investigated.

- [ ] **Step 5: Confirm the app still loads its icon**

Run: `.venv/bin/python main.py`
Expected: the window opens and stdout shows `Loaded icon from: .../resources/icon.png` — not `Warning: Icon not found`. Close the window.

- [ ] **Step 6: Commit**

```bash
git add tests/test_site_rendering.py docs/design/screenshots
git commit -m "test: verify terminal skin renders across viewports without tofu or overflow"
```

---

## Self-Review

**Spec coverage:** Design language → Task 1 + Global Constraints. 12 site icons → Task 2. Hero → Tasks 3 (live) and 7 (og:image). App icon two masters → Task 5. Render pipeline including `create_icns.py` refactor, `favicon.png`, and `generate_icon.py` deletion → Task 6. Consumer compatibility → asserted in Task 6's tests and Task 9 Step 5. Favicon repoint → Task 8 Step 1. Documentation → Task 8. All five spec verification items → Task 9 (viewports 1, contrast 2, icon output 3 via Task 6, pytest 4, app launch 5).

**Known gap, deliberately accepted:** the spec's chrome details (nav prompt, `$` section titles, bracketed buttons) are one task (4) rather than being folded into Task 1, because they are independently rejectable — a reviewer might accept the palette remap and reject the prompt styling.

**Type consistency:** `create_icns_from_pngs(png_by_size, output_icns_path)` is defined in Task 6 Step 4 and called in Task 6 Step 5 with `(pngs, RESOURCES / "icon.icns")` — matching. `SIZE_SOURCES` and `ICO_SIZES` are defined in `render_icons.py` and read by `tests/test_icon_outputs.py` under those exact names. `read_index()` is defined in `tests/test_site_theme.py` (Task 1) and imported by `tests/test_ascii_art.py` (Task 2). `.ascii-art` is defined in Task 2 and reused by `.hero-terminal` in Task 3. `ascii_blocks()` and `ALLOWED_NON_ASCII` are defined in Task 2 and extended in Task 3.
