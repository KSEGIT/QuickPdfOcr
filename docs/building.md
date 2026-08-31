# Building from source

[← Back to the README](../README.md)

## Run it from source

```bash
git clone https://github.com/KSEGIT/QuickPdfOcr.git
cd QuickPdfOcr
pip install -r requirements.txt
python main.py
```

On Windows and Linux you also need Tesseract installed — see
[Installation](installation.md). On macOS there's nothing extra: text
recognition uses the Vision framework built into macOS 13+, and PDF rendering
ships inside the `pypdfium2` wheel.

## Run the tests

```bash
python -m pytest
```

## Build your own binary

```bash
python build.py
```

The result lands in `dist/`.

On macOS you must ad-hoc sign the bundle before it will launch, even for local
testing:

```bash
python packaging/verify_universal.py
```

There is no Poppler step on any platform. PDF rendering is inside the
`pypdfium2` wheel and needs no system binary.

## Project layout

```
QuickPdfOcr/
├── main.py                          # Entry point: argv + macOS FileOpen handling
├── build.py                         # Build entry point (drives PyInstaller)
├── components/
│   ├── pdf_ocr.py                   # OCR orchestration (PdfOcrProcessor)
│   ├── ocr_worker.py                # Background worker for the GUI
│   ├── page_image.py                # Rendered-page pixel buffer
│   ├── rendering/                   # PDF rendering backend (pypdfium2)
│   └── ocr/                         # OCR backends (Apple Vision / Tesseract)
├── ui/
│   ├── main_window.py               # Main application window
│   └── loading_screen.py            # Startup loading screen
├── packaging/
│   ├── quickpdfocr.spec             # PyInstaller spec (incl. macOS Info.plist)
│   ├── prepare_universal_deps.py    # Fattens pypdfium2's dylib for universal2
│   └── verify_universal.py          # Architecture census + ad-hoc signing
├── resources/                       # Icon masters and the render pipeline
├── docs/                            # This documentation and the project website
├── tests/                           # pytest suite
└── requirements.txt                 # Python dependencies
```

## What it's built with

| Piece | What it does |
| --- | --- |
| [PySide6](https://doc.qt.io/qtforpython-6/) | Qt 6 GUI framework |
| [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) | PDF rendering, bundled on every platform |
| [Apple Vision](https://developer.apple.com/documentation/vision) | Text recognition on macOS |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | Text recognition on Windows and Linux |
| [Pillow](https://python-pillow.org/) | Image handling (Windows and Linux only) |
| [PyInstaller](https://pyinstaller.org/) | Packaging into a standalone app |

Exact versions live in [`requirements.txt`](../requirements.txt).

## How releases are built

Three GitHub Actions workflows build for Windows, Linux, and macOS. Each one
runs the test suite before it builds.

PyInstaller produces a directory (onedir) bundle on every platform, so each
workflow archives that directory as a single asset:

- `QuickPdfOcr-Windows-x64.zip`
- `QuickPdfOcr-Linux-x86_64.tar.gz`
- `QuickPdfOcr-macOS-universal2.zip`

The macOS workflow does extra work: it builds a universal2 binary for both
Apple Silicon and Intel, runs a self-test OCR pass against the built bundle,
and ad-hoc signs the result.

To cut a release, run the **Create Release** workflow from the Actions tab with
the version you want to tag. The artifacts appear on the resulting GitHub
release.
