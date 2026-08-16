# QuickPdfOcr Brand — ASCII / Terminal Direction

Supersedes the indigo-squircle / photographic-hero direction shipped in a642a3f.

This is the brief of record for the app icon, the hero, and the marketing site. For the
full rationale — why a terminal aesthetic, the accessibility argument, the risks
considered and accepted — see
`docs/superpowers/specs/2026-08-15-ascii-terminal-brand-design.md`. This document
describes the assets as built.

All three surfaces share one design language: a dark terminal skin, monospace
typography, and hand-authored ASCII/box-drawing art rendered from vector SVG masters,
not screenshotted or AI-generated.

## Shared design language

### Character set

Restricted to the subset every mainstream monospace font reliably carries, plus 7-bit
ASCII:

```
┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ─ │      box, single
╔ ╗ ╚ ╝ ═ ║                 box, double (emphasis only)
░ ▒ ▓ █ ▀ ▄                 shading / bars
▶ ▼ ▲ ● ○ ·                 accents
```

plus plain ASCII (`> _ [ ] ~ $` and so on). Rounded box-drawing (`╭ ╮ ╰ ╯`) is
deliberately excluded — it is the least widely supported box-drawing set and the most
likely source of tofu glyphs on an uncommon font.

### Palette

Each brand hue carries two values: an *ink* for drawing strokes and art directly on
`--bg`, and a *fill* for solid backgrounds that then carry white text. A single
light-theme value cannot do both jobs on a dark ground — a fill-weight indigo reads
fine as a button background but is too dim to draw a legible icon frame with, and an
ink-weight indigo is too light for white text on top of it to stay readable.

| Token | Hex | On `--bg` | Role |
|---|---|---|---|
| `--bg` | `#0F172A` | — | page ground |
| `--surface` | `#1E293B` | 1.22:1 vs bg | card fill |
| `--border-color` | `#64748B` | 3.75:1 on `--bg`, 3.07:1 vs `--surface` | header rule (border-bottom) |
| `--frame` | `#818CF8` | 5.98:1 | indigo ink — frames, ASCII art |
| `--frame-fill` | `#4F46E5` | 2.84:1 | indigo fill — background only |
| `--bar-ink` | `#A78BFA` | 6.56:1 | violet ink |
| `--bar` | `#7C3AED` | 3.13:1 | violet fill — background only |
| `--accent` | `#22D3EE` | 9.88:1 | scan beam, prompts, links |
| `--text` | `#E2E8F0` | 14.48:1 | body text |
| `--dim` | `#94A3B8` | 6.96:1 | secondary text, `░` shading |

Every token used for text or art clears WCAG AA (4.5:1 for text, 3:1 for non-text UI).
The two fill tokens (`--frame-fill`, `--bar-ink`'s counterpart `--bar`) fall below 4.5:1
against `--bg` and must never be used to draw text or ASCII art directly on the page
background — they exist only as solid fills with white content on top of them.

`--border-color` sits at `#64748B` rather than a value closer to `--surface` because an
earlier value collided with `--surface` byte-for-byte, making the header rule
invisible, and the next candidate (`#475569`) still only reached 1.93:1 against
`--surface` — under the 3:1 non-text floor. It was lifted to `#64748B` to clear both
floors at once.

### Typography

Monospace throughout, including body copy:

```css
font-family: ui-monospace, SFMono-Regular, Menlo, Consolas,
             "DejaVu Sans Mono", "Liberation Mono", monospace;
```

### The reflow rule

A fixed-width block like `┌────┐` cannot reflow — narrow its container and the
corners no longer line up with the sides. So:

- **True character-grid ASCII** — literal box-drawing characters in a `<pre>` — is
  used only inside fixed-size blocks: the 12 site icons and the hero terminal.
- **Everything that must reflow** — section frames, cards, buttons — is CSS borders
  plus `::before`/`::after` corner-glyph pseudo-elements. It reads as hand-drawn but
  behaves like ordinary responsive CSS.

This is the single most important implementation constraint in the whole direction.

## App icon (`resources/`)

Two SVG masters, because one 512px render downscaled into a 16px slot smears into an
unrecognizable blur — the terminal window's title bar, text rows, and scan beam simply
don't survive that much reduction. Each master is authored for the size band it feeds,
not merely resized from the other.

| Master | Feeds | Content |
|---|---|---|
| `resources/icon.svg` | 128, 256, 512, 1024 | Full terminal window: squircle body, title bar with three dots, dim unrecognized text rows, a cyan horizontal scan beam, bright recognized text rows, and a `>` prompt with cursor block |
| `resources/icon_small.svg` | 16, 32, 48, 64 | Simplified to the squircle background and one oversized cyan `> _` mark — legible at a glance where the detailed master would just be noise |

Both share the same squircle silhouette (~22% continuous corner radius) and the
indigo `#4F46E5` → violet `#7C3AED` diagonal gradient, so the two masters read as one
icon across the size range rather than two different marks.

Deliverables, all rendered from the masters by `resources/render_icons.py`:

- `resources/icon.png` — 256×256
- `resources/icon_512.png` — 512×512
- `resources/favicon.png` — 32×32, rendered from `icon_small.svg`; used by the site's
  `<link rel="icon">`
- `resources/icon.ico` — multi-size Windows icon (16/32/48/64/128/256)
- `resources/icon.icns` — macOS icon, assembled by `resources/create_icns.py`

## Hero (`resources/quick_pdf_hero_small.jpg`)

The hero is no longer displayed on the page — `docs/index.html` renders a live ASCII
terminal scene directly in the HTML instead. `resources/quick_pdf_hero_small.jpg` now
serves exactly one purpose: the `og:image`/`twitter:image` social-card preview.

It is rendered by `resources/render_hero.py` from `resources/hero.svg` at 1920×1080,
depicting the same terminal-scan scene as the on-page ASCII hero (deep indigo-violet
gradient backdrop, a document card mid-scan with the cyan beam), exported as JPEG at
quality ~85 and kept under 350 KB.

## Website (`docs/index.html`)

A dark terminal skin over the existing sections, copy, and links — nothing about the
page's structure or wording changed, only its visual language:

- The 12 feature/platform/privacy icons that were inline `<svg>` are now
  `<pre class="ascii-art ascii-icon" aria-hidden="true">` blocks of literal
  box-drawing characters, tinted per-card via `icon-indigo` / `icon-violet` /
  `icon-cyan` classes.
- The hero is a live `<pre class="ascii-art hero-terminal">` block — a terminal
  session scanning a PDF, with a blinking `_` cursor (held steady under
  `prefers-reduced-motion: reduce`) — sized with `clamp()` so the fixed-column art
  never forces horizontal scroll.
- Section titles get a `$ ` prompt prefix via a `.cmd::before` rule (e.g. `$ Key
  Features`), buttons render as bracketed affordances (`[ Download ]`), and the nav
  logo sits beside a `~/quickpdfocr $` prompt line.
- Every ASCII art block is `aria-hidden="true"`; the information it depicts is always
  also present as ordinary text nearby, so nothing is lost to screen readers.
- The favicon points at `resources/favicon.png` (32px, rendered from the small
  master); the header logo `<img>` still points at `resources/icon.png` — at the 36px
  it renders on the page, the detailed master still reads clearly.
- The page remains one self-contained HTML file: no external CSS, JS, font, or image
  requests.
