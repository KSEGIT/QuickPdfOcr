# QuickPdfOcr

A simple and intuitive PDF OCR application built with PySide6 (Qt6) and Tesseract OCR.

## 🚀 Quick Start for End Users

**Download and run - no installation required!**

The pre-built executables are **100% standalone** and include:
- ✅ Python interpreter
- ✅ All Python packages
- ✅ Poppler (PDF processing)
- ✅ **Tesseract OCR (text recognition)**

**No additional software installation needed!** Just download and run.

See [Installation](#installation) below for download links.

## Features

- 📄 **Drag & Drop Interface** - Simply drag PDF files into the window
- 📁 **File Browser** - Or use the file picker to select PDFs
- 🔍 **OCR Processing** - Extract text from scanned PDFs using Tesseract
- 📊 **Progress Feedback** - Real-time status updates during processing
- 📋 **Copy to Clipboard** - One-click copy functionality (macOS/Linux/Windows)
- 🔄 **Error Recovery** - Retry or start over options on failure
- 🎨 **Modern UI** - Clean, user-friendly interface with visual feedback
- 📦 **Fully Standalone** - Zero dependencies, zero installation required

## Prerequisites

### For Pre-built Binaries (Recommended)

**Nothing required!** The executable includes everything you need - Python, Poppler, and Tesseract OCR are all bundled.

Just download and run! 🎉

### For Running from Source

**macOS:**
```bash
brew install tesseract poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Install Tesseract OCR:
  - **Recommended:** Using winget: `winget install --id UB-Mannheim.TesseractOCR`
  - Or download from [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Install [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/)
- *Optional:* For WSL users, you can also install via: `wsl sudo apt-get install tesseract-ocr poppler-utils`

## Installation

### Option 1: Download Pre-built Binary (Recommended)

**100% Standalone - No installation required!**

1. Download the latest release for your platform from [Releases](https://github.com/KSEGIT/QuickPdfOcr/releases)
   - **Windows**: `QuickPdfOcr.exe`
   - **macOS**: `QuickPdfOcr.app` (ARM64 or Intel)
   - **Linux**: `QuickPdfOcr`

2. Run the application! That's it! 🎉

**What's Included:**
- ✅ Python interpreter (no Python installation needed)
- ✅ All Python packages (PySide6, pytesseract, pdf2image, Pillow, PyPDF2)
- ✅ Poppler binaries (for PDF processing)
- ✅ Tesseract OCR with English language data (for text recognition)

**Note:** The bundled Tesseract includes English language data by default. For other languages, you can still install Tesseract system-wide and the app will use it instead.

### Option 2: Run from Source

1. Clone the repository:
```bash
git clone https://github.com/KSEGIT/QuickPdfOcr.git
cd QuickPdfOcr
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies (see above)

### Option 3: Build Your Own Binary

1. Clone and install dependencies (see Option 2)

2. Build executable:
```bash
python build.py
```

3. Find your executable in the `dist/` folder

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
- `--lang <code>` - Set language for OCR (default: eng)

**Examples:**
```bash
# Auto-detect DPI
python components/pdf_ocr.py document.pdf

# Manual DPI and output file
python components/pdf_ocr.py document.pdf output.txt --dpi 400

# French language
python components/pdf_ocr.py document.pdf --lang fra
```

**Common language codes:**
- `eng` - English
- `fra` - French
- `deu` - German
- `spa` - Spanish
- `chi_sim` - Chinese Simplified
- `jpn` - Japanese

## Project Structure

```
QuickPdfOcr/
├── main.py                    # Application entry point
├── components/
│   ├── __init__.py
│   ├── pdf_ocr.py            # OCR processor component
│   └── ocr_worker.py         # Background worker for GUI
├── ui/
│   ├── __init__.py
│   └── main_window.py        # Main application window
└── requirements.txt          # Python dependencies
```

## Technologies Used

- **PySide6** - Qt6 framework for Python (GUI)
- **Tesseract OCR** - Open-source OCR engine
- **pdf2image** - PDF to image conversion
- **PyPDF2** - PDF manipulation and analysis
- **Pillow** - Image processing

## Requirements

### System Requirements
- **Tesseract OCR** (must be installed on your system)
- **Poppler** (bundled with pre-built binaries, or install separately if running from source)

### Python Dependencies (for source installation)
See `requirements.txt` for Python package versions:
- pytesseract>=0.3.10
- pdf2image>=1.16.0
- Pillow>=10.0.0
- PyPDF2>=3.0.0
- PySide6>=6.6.0
- pyinstaller>=6.0.0 (for building binaries)

## License

This project is open source and available under the MIT License.

See the [LICENSE](LICENSE) file for details.

For third-party component licenses (including Poppler), see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Building & Releases

### Local Build

Build for your current platform:
```bash
pip install -r requirements.txt
python build.py
```

The executable will be in the `dist/` folder.

**Note:** If you want to bundle Poppler with your local build, you need to:
1. Install Poppler on your system (see Prerequisites above)
2. The build script will automatically detect and bundle it

Alternatively, you can manually create a `poppler_binaries` directory in the project root and place the Poppler binaries there before building.

### Automated Builds (GitHub Actions)

The project includes GitHub Actions workflow that automatically builds executables for all platforms when you:
1. Push a tag starting with `v` (e.g., `v1.0.0`)
2. Manually trigger the workflow

The workflow automatically downloads and bundles Poppler for each platform.

To create a release:
```bash
git tag v1.0.0
git push origin v1.0.0
```

Artifacts will be available in the GitHub release.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

**Issue: "Tesseract not found"**
- Make sure Tesseract is installed and in your system PATH
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: `winget install --id UB-Mannheim.TesseractOCR` or download from [here](https://github.com/UB-Mannheim/tesseract/wiki)

**Issue: "Failed to convert PDF to images"**
- If using pre-built binary: This should not occur as Poppler is bundled
- If running from source: Ensure Poppler is installed
  - macOS: `brew install poppler`
  - Linux: `sudo apt-get install poppler-utils`
  - Windows: Install from [here](https://github.com/oschwartz10612/poppler-windows/releases/)

**Issue: Poor OCR quality**
- Try increasing DPI (e.g., `--dpi 400`)
- Ensure the PDF has good scan quality
- The system auto-detects optimal DPI based on page size

## Author

Created by [KSEGIT](https://github.com/KSEGIT)
