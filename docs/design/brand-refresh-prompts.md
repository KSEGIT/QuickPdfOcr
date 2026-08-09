# QuickPdfOcr Brand Refresh — Asset Prompts

These briefs are the source of truth for the regenerated brand assets (app icon, hero
image, website). Assets are hand-authored as vector SVG and rendered to raster with a
headless browser, so they stay crisp at every size. No AI-image model is involved; the
old PIL-drawn placeholder icon is retired.

## Shared design language

- **Mood**: fast, precise, trustworthy, offline-first. Desktop-utility professionalism,
  not startup-playful.
- **Primary gradient**: indigo `#4F46E5` → violet `#7C3AED` (replaces the previous site
  accent gradient `#667eea` → `#764ba2`).
- **Scan accent**: cyan `#22D3EE` — used only for the OCR "scan beam" motif and small
  highlights.
- **Neutrals**: slate `#0F172A` (dark), `#F8FAFC` (light), `#475569` (body text).
- **Motif**: a document page with text lines being crossed by a glowing horizontal
  scan beam — the product in one image.
- **Typography on web**: system font stack (unchanged), headings 700–800 weight.

## Prompt 1 — App icon (`resources/`)

> A modern macOS/iOS-style app icon on a squircle (continuous-corner rounded rect,
> ~22% corner radius). Background: diagonal gradient from indigo #4F46E5 (top-left) to
> violet #7C3AED (bottom-right), with a very subtle radial lightening toward the top.
> Centered glyph: a clean white document page (slightly rounded corners, folded top-right
> corner) with 4–5 slate-gray text lines. Across the middle of the document, a glowing
> cyan #22D3EE horizontal scan beam (thin bright core + soft outer glow) with a faint
> translucent cyan wash above it, evoking OCR scanning in progress. Flat vector style,
> crisp edges, soft inner depth only — no skeuomorphism, no text, no red "PDF" badge.
> Must read clearly at 16×16.

Deliverables (rendered from one master `resources/icon.svg`):

- `resources/icon.png` — 256×256
- `resources/icon_512.png` — 512×512
- `resources/icon.ico` — multi-size 16/32/48/64/128/256
- `resources/icon.icns` — via existing `resources/create_icns.py`
- `resources/icon.svg` — master vector (new, kept for future edits)

`generate_icon.py` is superseded by the SVG master; keep the script but note in
`resources/README.md` that the SVG is now the source of truth.

## Prompt 2 — Hero image (`resources/quick_pdf_hero_small.jpg`)

> Wide 1920×1080 website hero background, dark premium look. Deep indigo-violet gradient
> backdrop (#312E81 → #4C1D95 diagonal) with a faint dot-grid texture. Floating in the
> right two-thirds: a stylized white document card, tilted slightly in 3D perspective,
> text lines visible; a bright cyan scan beam sweeps across it with a soft glow and a
> subtle light trail. Behind/around it, 2–3 smaller ghosted document cards at varying
> depths and low opacity for parallax feel. Left third kept visually calm (headline text
> overlays there). Soft cinematic lighting, gentle vignette, abstract flat-3D vector
> style — not a photo. No words or letters anywhere in the image.

Deliverable: `resources/quick_pdf_hero_small.jpg` (quality ~85, ≤ 350 KB) replacing the
current stock-photo hero.

## Prompt 3 — Website (`docs/index.html`)

> Rebuild the single-page marketing site around the new assets. Same sections and copy
> hierarchy as today (hero, what-it-does, features, privacy, download, developers,
> footer), but a cleaner contemporary look: hero uses the new hero image with a dark
> gradient overlay for text contrast; feature/platform icons become inline SVG icons in
> brand colors instead of emoji; privacy section keeps the indigo→violet gradient;
> favicon/logo point at the new icon. Keep it one self-contained HTML file, responsive,
> no external CSS/JS frameworks. Preserve all existing links (GitHub, releases) and
> meta/OG tags (update OG image to the new hero).

Deliverable: updated `docs/index.html`.
