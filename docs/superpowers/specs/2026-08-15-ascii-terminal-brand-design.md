# ASCII / Terminal Brand Design

**Date:** 2026-08-15
**Status:** Approved, ready for planning
**Supersedes:** `docs/design/brand-refresh-prompts.md` (the indigo-squircle / photographic-hero direction shipped in `a642a3f`)

## Problem

Commit `a642a3f` replaced the site's emoji with 12 inline SVG icons and shipped a
vector app icon and hero. The direction is competent but generic — it reads like any
other utility landing page. QuickPdfOcr is a fast, local, no-cloud document tool, and a
terminal aesthetic states that identity in a way a rounded-rect icon set cannot.

This spec pivots the **web presence and brand assets** to a terminal/ASCII skin: the
marketing site, the app icon, and the hero. The palette established in `a642a3f` is
retained so the pivot reads as a sharpening of the brand, not a replacement.

## Scope

**In scope**

- `docs/index.html` — full terminal skin (chrome, typography, 12 ASCII icons, live ASCII hero)
- `resources/icon.svg` — re-authored as a terminal-window icon
- `resources/icon_small.svg` — **new** simplified master for small sizes
- `resources/render_icons.py` — **new** single-command render pipeline
- `resources/create_icns.py` — consume pre-rendered per-size PNGs instead of downscaling one
- `resources/hero.svg` → `resources/quick_pdf_hero_small.jpg` — regenerated; now serves the `og:image` only
- `resources/favicon.png` — **new**, 32px, from the small master
- `resources/generate_icon.py` — **deleted** (already deprecated dead code)
- `docs/design/brand-refresh-prompts.md` — rewritten as the ASCII/terminal brief of record
- `resources/README.md` — updated for the two-master pipeline

**Out of scope**

- The PySide6 desktop UI (`ui/main_window.py`, `ui/loading_screen.py`) keeps its current
  look. Reskinning the app itself is a separate spec.
- Application behaviour, OCR engines, packaging logic, CI workflows.
- Copy rewriting. All existing site copy, sections, and links are preserved verbatim.

## Design language

### Character set (hard constraint)

Only the cp437/DEC-derived subset, which every mainstream monospace font carries, plus
7-bit ASCII:

```
┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ─ │      box, single
╔ ╗ ╚ ╝ ═ ║                 box, double (emphasis only)
░ ▒ ▓ █ ▀ ▄                 shading / bars
▶ ▼ ▲ ● ○ · > _ [ ] ~ $     accents, prompts, buttons
```

Explicitly excluded: rounded box-drawing (`╭ ╮ ╰ ╯`), braille, emoji, half-width forms.
Rounded corners are the least widely supported box-drawing set and are the most likely
source of tofu; sharp corners are used everywhere instead.

### Palette

| Token | Hex | Contrast on `--bg` | Use |
|---|---|---|---|
| `--bg` | `#0F172A` | — | page background |
| `--surface` | `#1E293B` | 1.22:1 vs bg | card fill (a visible lift, not a text pairing) |
| `--frame` | `#818CF8` | 5.98:1 | indigo **ink** — box-drawing frames, ASCII art strokes |
| `--frame-fill` | `#4F46E5` | 2.84:1 | indigo **fill** — background only; white on it is 6.29:1 |
| `--bar-ink` | `#A78BFA` | 6.56:1 | violet **ink** — art strokes, `█` runs |
| `--bar` | `#7C3AED` | 3.13:1 | violet **fill** — background only; white on it is 5.70:1 |
| `--border-color` | `#64748B` | 3.75:1 (3.07:1 vs surface) | header rule (`border-bottom`) — its only consumer |
| `--accent` | `#22D3EE` | 9.88:1 | scan beam, prompts, links, cursor |
| `--text` | `#E2E8F0` | 14.48:1 | body text |
| `--dim` | `#94A3B8` | 6.96:1 | secondary text, `░` shading |

**Contrast rule.** Every token that carries text *or ASCII art* must clear WCAG AA
4.5:1 against `--bg`. `--bar` is the sole exception at 3.13:1: it is used only as a
solid fill (progress bars, `█` runs), which is a non-text UI component and needs only
3:1. `--bar` must never be a text colour.

**Palette correction, 2026-08-15.** The first draft of this table used
`--frame: #4F46E5` and `--dim: #64748B`, carried over unchanged from the light-theme
brand. Measured against `#0F172A` those are **2.84:1** and **3.75:1** — `--frame` fails
even the 3:1 non-text floor, which would have made the ASCII icon frames barely visible,
and `--dim` fails the 4.5:1 text floor while being assigned to secondary text. Both were
moved one step lighter within the same hue family (indigo-400, slate-400). The hues and
the brand reading are unchanged; only the shades lift enough to survive the dark ground.
`--surface` moved from `#111C33` to `#1E293B` for the same reason — at 1.05:1 against
`--bg` the card fill was invisible.

### Typography

Monospace throughout:

```css
font-family: ui-monospace, SFMono-Regular, Menlo, Consolas,
             "DejaVu Sans Mono", "Liberation Mono", monospace;
```

Body copy stays at 15–16px with `line-height: 1.7`. Authentic 80-column terminal metrics
are deliberately not applied to paragraphs — readability wins over purity.

### The reflow rule

A fixed-width `┌────┐` frame cannot reflow; at 375px it wraps and shatters. Therefore:

- **True character-grid ASCII** is used only where the box has a fixed size: the 12
  icons, the hero terminal, progress bars.
- **CSS-faked box-drawing** is used everywhere that must reflow: section frames, cards,
  buttons. Implemented as `border: 1px solid var(--frame)` plus `::before` / `::after`
  corner glyphs — it looks drawn and behaves like CSS.

This rule is the single most important implementation constraint in this spec.

### Chrome

- Nav renders as a prompt line: `~/quickpdfocr $ ` followed by the existing links.
- Section titles gain a `$ ` prompt prefix via `.cmd::before`, so "Key Features" reads as "$ Key Features". The prefix comes from CSS; the heading text itself is never edited, because copy is frozen.
- Buttons render as `[ Download ]`.
- A single `_` cursor blinks in the hero, wrapped in
  `@media (prefers-reduced-motion: reduce)` to hold steady.

### Accessibility

Every ASCII art block is `aria-hidden="true"`. No text content is replaced by art — each
icon already sits beside a real `<h3>`, and the hero's information is duplicated in the
adjacent headline and copy. A screen reader loses nothing.

## Component 1 — Site icons (`docs/index.html`)

The 12 inline `<svg>` blocks are replaced by `<pre class="ascii-icon" aria-hidden="true">`
elements containing literal characters. Each icon is a 5-line block on a consistent grid.

Icons are two-tone: the frame inherits the card's existing `icon-indigo` / `icon-violet` /
`icon-cyan` class, and inner `<span>` elements take `--accent` for beams and prompts. The
existing class names and card markup are preserved.

**Features (8)**

```
Drag & Drop        File Picker        Native OCR         Progress & Status
 ┌─────┐           ┌─────────┐        ┌─────────┐        ┌─────────┐
 │ ░░░ │           │ ▶ a.pdf │        │ ░░░░░░░ │        │ scan... │
 └──┬──┘           │   b.pdf │        │═════════│        │ ████░░░ │
    ▼              │   c.pdf │        │ ▓▓▓▓▓▓▓ │        │   57%   │
┌ ─ ─ ─ ┐          └─────────┘        └─────────┘        └─────────┘

Copy to Clipboard  Error Recovery     Modern UI          Fully Standalone
 ┌──────┐          ┌─────────┐        ┌─┬───────┐          ┌─────┐
┌┴─────┐│          │  ! err  │        │●│ ░░░░░ │         ┌┴────┐│
│ ░░░░ ├┘          │ ──────▶ │        │░│ ░░░░░ │         │ ▓▓▓ ││
│ ░░░░ │           │ [retry] │        │░│ ░░░░░ │         │ ▓▓▓ ├┘
└──────┘           └─────────┘        └─┴───────┘         └─────┘
```

The **Native OCR** icon is the brand motif in miniature — `░` unrecognized above, cyan
`═` scan beam, `▓` recognized below.

**Privacy (1)** — a padlock. A shield's diagonals do not survive the charset restriction;
a padlock does.

```
  ┌───┐
 ┌┴───┴┐
 │ ███ │
 │ █▀█ │
 └─────┘
```

**Platforms (3)**

```
Windows            macOS              Linux
┌───┬───┐          ┌───────┐          ┌───────┐
│░░░│░░░│          │ ░░░░░ │          │ > _   │
├───┼───┤          │ ░░░░░ │          │ ░░░░  │
│░░░│░░░│          └───────┘          │ ░░    │
└───┴───┘           ▀▀▀▀▀▀▀           └───────┘
```

Linux remains a terminal prompt rather than a penguin — the same call the current SVG
makes.

## Component 2 — Hero

The hero becomes **live ASCII in the HTML**, not an image:

```
~/Documents $ quickpdfocr scan report.pdf

┌─ QuickPdfOcr ────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ══════════════════════════════════════  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│                                          │
│  [████████████████░░░░░░] 71%            │
│  page 12/17  ·  vision.framework         │
└──────────────────────────────────────────┘

> 4,812 words copied to clipboard_
```

Fixed at 46 columns, sized with `font-size: clamp(6px, 1.55vw, 15px)` so the block always
fits without horizontal scroll. One variant only — no per-breakpoint markup duplicates.

`resources/hero.svg` is re-authored to depict this same scene and rendered to
`resources/quick_pdf_hero_small.jpg` (quality ~85, ≤ 350 KB). Its only remaining job is
the `og:image` social preview; the page itself no longer displays it.

## Component 3 — App icon

Two SVG masters. Glyphs are authored as **vector paths, not `<text>`**, so the masters
render identically regardless of installed fonts.

| Master | Feeds sizes | Art |
|---|---|---|
| `resources/icon.svg` | 1024, 512, 256, 128 | terminal window: `● ● ●` title dots, `░` lines, cyan `═` beam, `▓` lines, `> _` prompt |
| `resources/icon_small.svg` *(new)* | 64, 48, 32, 16 | squircle + gradient + a single large cyan `> _` |

Both share the squircle silhouette (~22% continuous corner radius) and the indigo `#4F46E5`
→ violet `#7C3AED` diagonal gradient, so the transition across sizes reads as one icon
rather than two.

## Component 4 — Render pipeline

`create_icns.py` currently opens one 512px PNG and downscales it into all 11 iconset
slots — precisely the mush this spec exists to avoid. It changes to consume a
pre-rendered `{size: png_path}` map.

Its non-macOS PIL fallback is **removed**, not retained. That fallback wrote a
single-resolution `.icns` whenever `iconutil` was missing — producing exactly the
smeared-at-small-sizes artefact this spec exists to eliminate, silently and while
appearing to succeed. `create_icns_from_pngs` now raises instead. This is safe:
`.icns` is consumed only under `IS_MACOS` (`packaging/quickpdfocr.spec:71,88`) and
built only on `macos-14` runners, so nothing off-macOS ever needed the fallback.

`resources/render_icons.py` becomes the single entry point:

1. Drive Playwright over both masters, rendering each required size from the correct one
   (`omitBackground: true` to preserve corner transparency).
2. Emit `icon.png` (256), `icon_512.png`, and `favicon.png` (32, from the small master).
3. Assemble multi-size `icon.ico` (16/32/48/64/128/256) via Pillow.
4. Call `create_icns.py` with the per-size map to build `icon.icns`.

This replaces the ad-hoc heredoc currently documented in `resources/README.md`.
`resources/generate_icon.py` is deleted.

### Consumer compatibility

All output filenames are unchanged, so no consumer needs edits:

- `main.py:296` — loads `resources/icon.png` at runtime
- `packaging/quickpdfocr.spec:71,88` — `icon.icns` (macOS) / `icon.ico` (Windows)
- `docs/index.html:598` — logo `<img>` continues to use `icon.png`

One deliberate change: `docs/index.html:25` currently points `rel="icon"` at the 256px
`icon.png`, leaving the browser to downscale detailed art to 16px. It is repointed at the
new `favicon.png`.

## Documentation

- `docs/design/brand-refresh-prompts.md` is rewritten as the ASCII/terminal brief of
  record. Leaving it describing the superseded direction would actively mislead.
- `resources/README.md` is updated for the two-master pipeline and the single render
  command.

## Verification

Work is not complete until all of the following have been run and their output shown:

1. **Cross-viewport render** — Playwright screenshots of `docs/index.html` at 375px,
   768px, and 1440px. Assert: no tofu glyphs, no misaligned frames, no horizontal
   document overflow.
2. **Contrast** — assert the `--text`/`--bg` and `--accent`/`--bg` pairs meet WCAG AA,
   and confirm no rule applies `--frame` to a text-bearing element.
3. **Icon output** — `icon.ico` carries all 6 sizes; the 16/32/48/64 slots derive from
   `icon_small.svg` and the 128/256 slots from `icon.svg`; `icon.icns` builds via
   `iconutil`.
4. **Test suite** — `pytest` green.
5. **App launch** — start the app and confirm `main.py` still loads its icon without the
   "Icon not found" warning.

## Risks

| Risk | Mitigation |
|---|---|
| Monospace fonts vary in box-drawing coverage; a missing glyph renders as tofu | Restricted charset (no rounded corners); verified by cross-viewport Playwright screenshots. If breakage appears, escalate to an inlined base64 subset webfont (~30–60 KB) — decided against up front on page-weight grounds, but the fallback stands. |
| Terminal aesthetic may read as "CLI for hackers" for a click-and-go GUI app | Body copy stays sans-metrics and plainly worded; no section requires terminal literacy to understand. Chosen with this tradeoff stated and accepted. |
| Fixed-grid hero overflowing narrow viewports | `clamp()`-scaled font-size on a single 46-column block; explicitly asserted in verification step 1. |
