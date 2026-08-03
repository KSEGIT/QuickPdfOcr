# QuickPdfOcr

A simple and intuitive PDF OCR application built with PySide6 (Qt6). Text
recognition uses Apple's Vision framework on macOS (built into the OS) and
Tesseract OCR on Windows and Linux. PDF rendering uses the bundled
`pypdfium2` library on every platform — there is no Poppler anywhere.

## 🚀 Quick Start for End Users

**Download and run!**

The pre-built executables include:
- ✅ Python interpreter
- ✅ All Python packages
- ✅ PDF rendering (bundled `pypdfium2` — no Poppler, on any platform)
- ✅ **macOS: OCR via the Vision framework built into the OS — nothing else to install**
- ⚠️ **Windows/Linux: Tesseract OCR is *not* bundled** — install it separately, see [Prerequisites](#prerequisites)

See [Installation](#installation) below for download links. The macOS build
is ad-hoc signed but not notarized, so the first launch needs one extra
step — see the [macOS installation instructions](#macos).

## Features

- 📄 **Drag & Drop Interface** - Simply drag PDF files into the window
- 📁 **File Browser** - Or use the file picker to select PDFs
- 🔍 **OCR Processing** - Extract text from scanned PDFs (Apple Vision on macOS, Tesseract on Windows/Linux)
- 📊 **Progress Feedback** - Real-time status updates during processing
- 📋 **Copy to Clipboard** - One-click copy functionality (macOS/Linux/Windows)
- 🔄 **Error Recovery** - Retry or start over options on failure
- 🎨 **Modern UI** - Clean, user-friendly interface with visual feedback
- 📦 **No Poppler, ever** - PDF rendering is bundled on every platform; macOS needs nothing else installed

## Prerequisites

### For Pre-built Binaries

**macOS:** Nothing required. PDF rendering is bundled and OCR uses the
Vision framework built into the OS.

**Windows/Linux:** Install Tesseract OCR (see below) — it is the one thing
the pre-built executables do not bundle.

### For Running from Source

**macOS:**
Nothing to install. PDF rendering ships inside the `pypdfium2` wheel and OCR
uses the Vision framework built into macOS 13+.

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
- Install Tesseract OCR:
  - **Recommended:** Using winget: `winget install --id UB-Mannheim.TesseractOCR`
  - Or download from [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- *Optional:* For WSL users, you can also install via: `wsl sudo apt-get install tesseract-ocr`

## Installation

### macOS

1. Download `QuickPdfOcr-macOS-universal2.zip` from the
   [latest release](../../releases/latest).
2. Unzip it and drag `QuickPdfOcr.app` to your Applications folder.
3. **First launch only:** macOS will refuse to open the app because it is not
   notarized. Go to **System Settings → Privacy & Security**, scroll to the
   message about QuickPdfOcr, and click **Open Anyway**. Subsequent launches
   work normally.

There is nothing else to install. No Homebrew, no Poppler, no Tesseract —
PDF rendering is built into the app and text recognition uses macOS's own
Vision framework.

**Requires macOS 13 (Ventura) or later.**

Once installed you can also:
- Drag a PDF onto the app's Dock icon
- Right-click a PDF → **Open With → QuickPdfOcr**
- Right-click a PDF → **Services → OCR with QuickPdfOcr**, once the item
  appears — macOS registers Services menu entries the first time the app
  runs, so launch QuickPdfOcr at least once before checking Finder's
  Services submenu (a Finder restart or a short wait may also be needed)

### Windows

1. Download `QuickPdfOcr.exe` from the
   [latest release](https://github.com/KSEGIT/QuickPdfOcr/releases).
2. Install Tesseract OCR — it is not bundled (see [Prerequisites](#prerequisites)).
3. Run `QuickPdfOcr.exe`.

### Linux

1. Download `QuickPdfOcr` from the
   [latest release](https://github.com/KSEGIT/QuickPdfOcr/releases).
2. Install Tesseract OCR — it is not bundled (see [Prerequisites](#prerequisites)).
3. Make it executable and run it: `chmod +x QuickPdfOcr && ./QuickPdfOcr`.

### Run from Source

1. Clone the repository:
```bash
git clone https://github.com/KSEGIT/QuickPdfOcr.git
cd QuickPdfOcr
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies (see [Prerequisites](#prerequisites))

### Build Your Own Binary

1. Clone and install dependencies (see above)

2. Build the executable:
```bash
python build.py
```

3. On macOS, ad-hoc sign the bundle — required before it will launch, even
   for local testing:
```bash
python packaging/verify_universal.py
```

4. Find your executable in the `dist/` folder

## Usage

### GUI Application

Run the graphical interface:
```bash
python main.py
```

**Workflow:**
1. Drag and drop a PDF file or click "Open PDF File"
2. Click "Start OCR" to begin text extraction
3. Wait for processing (progress updates shown)
4. Copy extracted text or start over with a new file

### Command Line (Legacy)

You can also use the OCR processor directly from command line:
```bash
python components/pdf_ocr.py document.pdf output.txt
```

**Options:**
- `--dpi <value>` - Set DPI for conversion (default: auto-detect)
- `--lang <code>` - Set language for OCR (default: the engine's own default)

Language codes are engine-specific: Tesseract (Windows/Linux) uses ISO 639-2
codes like `eng`/`fra`; Vision (macOS) uses BCP-47 codes like `en-US`/`fr-FR`.

**Examples:**
```bash
# Auto-detect DPI
python components/pdf_ocr.py document.pdf

# Manual DPI and output file
python components/pdf_ocr.py document.pdf output.txt --dpi 400

# French language (Windows/Linux, Tesseract)
python components/pdf_ocr.py document.pdf --lang fra

# French language (macOS, Vision)
python components/pdf_ocr.py document.pdf --lang fr-FR
```

**Common Tesseract language codes:**
- `eng` - English
- `fra` - French
- `deu` - German
- `spa` - Spanish
- `chi_sim` - Chinese Simplified
- `jpn` - Japanese

## Project Structure

```
QuickPdfOcr/
├── main.py                     # Entry point: argv + macOS FileOpen handling
├── build.py                    # Build entry point (drives PyInstaller)
├── components/
│   ├── __init__.py
│   ├── pdf_ocr.py             # OCR orchestration (PdfOcrProcessor)
│   ├── ocr_worker.py          # Background worker for the GUI
│   ├── page_image.py          # Rendered-page pixel buffer
│   ├── rendering/             # PDF rendering backend (pypdfium2)
│   └── ocr/                   # OCR backends (Apple Vision / Tesseract)
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   └── loading_screen.py      # Startup loading screen
├── packaging/
│   ├── quickpdfocr.spec       # PyInstaller spec (incl. macOS Info.plist)
│   ├── prepare_universal_deps.py  # Fattens pypdfium2's dylib for universal2
│   └── verify_universal.py    # Architecture census + ad-hoc signing
├── tests/                      # pytest suite
└── requirements.txt             # Python dependencies
```

## Technologies Used

- **PySide6** - Qt6 framework for Python (GUI)
- **Apple Vision** - OCR engine on macOS, built into the OS
- **Tesseract OCR** - OCR engine on Windows and Linux
- **pypdfium2** - PDF rendering, bundled on every platform (no Poppler)
- **Pillow** - Image processing (Windows/Linux only)

## Requirements

### System Requirements
- **macOS:** None. OCR uses the Vision framework built into macOS 13+.
- **Windows/Linux:** **Tesseract OCR** must be installed on your system — it
  is not bundled, even in the pre-built binaries.

### Python Dependencies (for source installation)
See `requirements.txt` for Python package versions:
- PySide6>=6.6.0
- pypdfium2>=5.12.0 (PDF rendering, all platforms)
- pyobjc-framework-Vision>=12.0, pyobjc-framework-Quartz>=12.0 (macOS only)
- pytesseract>=0.3.10, Pillow>=10.0.0 (Windows/Linux only)
- pyinstaller>=6.0.0 (for building binaries)
- pytest>=8.0.0 (for running the test suite)

## License

This project is open source and available under the MIT License.

See the [LICENSE](LICENSE) file for details.

For third-party component licenses (PDFium/pypdfium2, Tesseract, PySide6/Qt,
and others), see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Building & Releases

### Local Build

Build for your current platform:
```bash
pip install -r requirements.txt
python build.py
```

The executable will be in the `dist/` folder. On macOS, sign it before
launching it — even for local testing — with `python packaging/verify_universal.py`.

There is no Poppler step: PDF rendering ships inside the `pypdfium2` wheel
and needs no system binary on any platform.

### Automated Builds (GitHub Actions)

The project includes GitHub Actions workflows that build executables for
Windows, Linux, and macOS. The macOS workflow builds a universal2 (Apple
Silicon + Intel) app, runs the test suite and a self-test OCR pass, ad-hoc
signs the result, and uploads `QuickPdfOcr-macOS-universal2.zip`.

To create a release, run the "Create Release" workflow from the Actions tab
with the version you want to tag. Artifacts will be available in the
resulting GitHub release.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

**Issue: "Tesseract not found"** (Windows/Linux only — macOS uses Vision, not Tesseract)
- Make sure Tesseract is installed and in your system PATH
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: `winget install --id UB-Mannheim.TesseractOCR` or download from [here](https://github.com/UB-Mannheim/tesseract/wiki)

**Issue: "Failed to open/render PDF"**
- PDF rendering is bundled (`pypdfium2`) on every platform, so there is no
  separate Poppler install to check.
- This usually means the PDF itself is corrupted, password-protected, or not
  actually a PDF despite its extension.

**Issue: Poor OCR quality**
- Try increasing DPI (e.g., `--dpi 400`)
- Ensure the PDF has good scan quality
- The system auto-detects optimal DPI based on page size

## Author

Created by [KSEGIT](https://github.com/KSEGIT)
