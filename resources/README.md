# Resources Directory

This directory contains application resources, including icons and other assets.

## Icons

The application icon represents a PDF document with OCR scanning functionality:
- **icon.svg** - Master vector source (1024x1024 viewBox); all raster icons are rendered from this file
- **icon.png** - Standard PNG icon (256x256) for general use
- **icon.ico** - Windows icon file (multi-size: 16, 32, 48, 64, 128, 256)
- **icon.icns** - macOS icon file (contains all required sizes for macOS)
- **icon_512.png** - High-resolution PNG (512x512) for large displays

### Icon Design

The icon follows the brand design language in `docs/design/brand-refresh-prompts.md`:

- A macOS/iOS-style squircle (rounded rect with ~22% continuous corner radius)
- Background: diagonal gradient from indigo `#4F46E5` (top-left) to violet `#7C3AED`
  (bottom-right), with a subtle radial lightening toward the top
- Centered white document page glyph with slightly rounded corners and a folded
  top-right corner, containing slate-gray (`#475569`) text lines
- A glowing cyan (`#22D3EE`) horizontal scan beam across the middle of the document
  (thin bright core + soft outer glow) with a faint translucent cyan wash above it,
  evoking OCR scanning in progress
- Flat vector style, crisp edges, no text or badges; reads clearly down to 16x16

### Regenerating Icons

`icon.svg` is the source of truth. To regenerate the raster icons, render the SVG at
the required sizes with a headless browser (e.g. Playwright: set the viewport to the
target size, load the SVG, screenshot with `omitBackground: true` to preserve corner
transparency), then build the platform containers:

```bash
# Build the Windows multi-size .ico from the rendered size PNGs (Pillow)
python3 - <<'EOF'
from PIL import Image
sizes = [16, 32, 48, 64, 128, 256]
imgs = [Image.open(f'/tmp/icon_{s}.png').convert('RGBA') for s in sizes]
imgs[-1].save('icon.ico', format='ICO', append_images=imgs[:-1],
              sizes=[(s, s) for s in sizes])
EOF

# Create macOS .icns file (reads icon_512.png, uses iconutil)
python3 create_icns.py
```

#### Icon Generation Scripts

- **icon.svg** - Master vector source of truth for the icon (new)
- **generate_icon.py** - Legacy/deprecated PIL-drawn icon generator, kept for
  reference only; superseded by `icon.svg`. Do not use for new icon builds.
- **create_icns.py** - Converts `icon_512.png` to macOS .icns format (still in use)

### Customizing the Icon

To customize the icon design, edit `icon.svg` (gradients, glyph geometry, beam
styling are all plain SVG shapes) and re-render the raster files as described above.

### Icon Usage in Build

The PyInstaller spec (`packaging/quickpdfocr.spec`) includes the appropriate icon for each platform:
- **Windows**: Uses `icon.ico`
- **macOS**: Uses `icon.icns`
- **Linux**: Uses `icon.png`

The icon is also loaded at runtime in `main.py` to ensure it appears in the application window and taskbar.

## License

The icons in this directory are part of the QuickPdfOcr project and are subject to the same license as the main project (see LICENSE file in the root directory).
