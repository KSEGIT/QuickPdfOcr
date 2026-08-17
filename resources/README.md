# Resources Directory

This directory contains application resources, including icons and other assets.

## Icons

The application icon represents a terminal window scanning a document with OCR:
- **icon.svg** - Detailed vector master (1024x1024 viewBox); feeds the 128/256/512/1024px outputs
- **icon_small.svg** - Simplified vector master; feeds the 16/32/48/64px outputs
- **icon.png** - Standard PNG icon (256x256) for general use
- **icon.ico** - Windows icon file (multi-size: 16, 32, 48, 64, 128, 256)
- **icon.icns** - macOS icon file (contains all required sizes for macOS)
- **icon_512.png** - High-resolution PNG (512x512) for large displays
- **favicon.png** - 32x32 PNG, source render for the website's favicon (the live copy
  the site actually loads is `docs/assets/favicon.png` — see "docs/assets/" below)

### Icon Design

The icon follows the brand design language in `docs/design/brand-refresh-prompts.md`:
a terminal window on a squircle background (~22% continuous corner radius), diagonal
indigo `#4F46E5` → violet `#7C3AED` gradient, dim/bright text rows crossed by a cyan
`#22D3EE` scan beam, and a `> _` prompt.

There are two SVG masters, not one, because a single 512px render downscaled to 16px
smeared the terminal detail into an unrecognizable blur:

- **icon.svg** - detailed terminal-window master; feeds the 128, 256, 512, and 1024px
  outputs, where the window chrome and text rows still read.
- **icon_small.svg** - simplified master showing only the squircle and one oversized
  cyan `> _` mark; feeds the 16, 32, 48, and 64px outputs, where the detailed master
  would just be noise.
- **favicon.png** - 32×32, rendered from `icon_small.svg`.

### `docs/assets/`

GitHub Pages publishes from `main:/docs`, so `resources/` sits outside the published
root and a relative path from `docs/index.html` cannot reach it. `docs/assets/` holds
the subset of renders the page itself needs, copied by the same pipeline run so they
cannot drift from `resources/*.png`:

- **docs/assets/favicon.png** - 32×32, same render as `resources/favicon.png`; used by
  `docs/index.html`'s `<link rel="icon">`.
- **docs/assets/logo.png** - 64×64, rendered from `icon_small.svg`; used by the header
  `.logo img`, which displays it at 36×36 — far closer to native size than the old
  256px `icon.png` it used to pull cross-origin from `main`.

### Regenerating Icons

`resources/render_icons.py` is the single entry point. It drives Playwright over both
masters, rendering every required size from the correct one, then builds every
platform container from those renders:

```bash
.venv/bin/pip install -r resources/requirements-assets.txt
.venv/bin/playwright install chromium
.venv/bin/python resources/render_icons.py   # icon.png, icon_512.png, favicon.png, icon.ico, icon.icns, docs/assets/*.png
.venv/bin/python resources/render_hero.py    # quick_pdf_hero_small.jpg
```

`requirements-assets.txt` (Playwright + Pillow) is asset-authoring tooling only and is
deliberately not part of `requirements.txt` — Playwright must never enter the shipped
application bundle.

`create_icns.py` copies each pre-rendered PNG straight into the macOS iconset (never
resizing — that would reintroduce the same smearing the two-master split exists to
avoid) and requires the macOS `iconutil` binary to assemble `icon.icns`. It has no
fallback for when `iconutil` is missing: it raises instead of writing a degraded
single-resolution `.icns`, which is what the old PIL fallback silently did.

### Customizing the Icon

To customize the icon design, edit `icon.svg` for the 128px+ outputs and/or
`icon_small.svg` for the 16-64px outputs (gradients, glyph geometry, beam styling are
all plain SVG shapes), then re-render the raster files as described above.

### Icon Usage in Build

The PyInstaller spec (`packaging/quickpdfocr.spec`) includes the appropriate icon for each platform:
- **Windows**: Uses `icon.ico`
- **macOS**: Uses `icon.icns`
- **Linux**: Uses `icon.png`

The icon is also loaded at runtime in `main.py` to ensure it appears in the application window and taskbar.

## License

The icons in this directory are part of the QuickPdfOcr project and are subject to the same license as the main project (see LICENSE file in the root directory).
