# Resources Directory

This directory contains application resources, including icons and other assets.

## Icons

The application icon represents a PDF document with OCR scanning functionality:
- **icon.png** - Standard PNG icon (256x256) for general use
- **icon.ico** - Windows icon file (multi-size: 16, 32, 48, 64, 128, 256, 512)
- **icon.icns** - macOS icon file (contains all required sizes for macOS)
- **icon_512.png** - High-resolution PNG (512x512) for large displays

### Icon Design

The icon features:
- A white document with a blue border
- Gray text lines representing document content
- Blue scanning arrows showing OCR processing
- A red "PDF" badge in the top-right corner

### Regenerating Icons

If you need to modify or regenerate the icons:

```bash
# Navigate to the resources directory
cd resources

# Generate new icons
python3 generate_icon.py

# Create macOS .icns file
python3 create_icns.py
```

#### Icon Generation Scripts

- **generate_icon.py** - Creates the base icon design and generates PNG and ICO files
- **create_icns.py** - Converts PNG to macOS .icns format

### Customizing the Icon

To customize the icon design, edit `generate_icon.py` and modify the `create_icon()` function. The icon is drawn programmatically using PIL (Pillow), so you can adjust:
- Colors
- Shapes and proportions
- Text and badges
- Special effects

After making changes, run the generation scripts again to create new icon files.

### Icon Usage in Build

The build process (`build.py`) automatically includes the appropriate icon for each platform:
- **Windows**: Uses `icon.ico`
- **macOS**: Uses `icon.icns`
- **Linux**: Uses `icon.png`

The icon is also loaded at runtime in `main.py` to ensure it appears in the application window and taskbar.

## License

The icons in this directory are part of the QuickPdfOcr project and are subject to the same license as the main project (see LICENSE file in the root directory).
