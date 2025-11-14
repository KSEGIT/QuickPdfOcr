# QuickPdfOcr

A simple and intuitive PDF OCR application built with PySide6 (Qt6) and Tesseract OCR.

## Features

- 📄 **Drag & Drop Interface** - Simply drag PDF files into the window
- 📁 **File Browser** - Or use the file picker to select PDFs
- 🔍 **OCR Processing** - Extract text from scanned PDFs using Tesseract
- 📊 **Progress Feedback** - Real-time status updates during processing
- 📋 **Copy to Clipboard** - One-click copy functionality (macOS/Linux/Windows)
- 🔄 **Error Recovery** - Retry or start over options on failure
- 🎨 **Modern UI** - Clean, user-friendly interface with visual feedback

## Prerequisites

### System Dependencies

**macOS:**
```bash
brew install tesseract poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Install [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/KSEGIT/QuickPdfOcr.git
cd QuickPdfOcr
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

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

See `requirements.txt` for Python package versions:
- pytesseract>=0.3.10
- pdf2image>=1.16.0
- Pillow>=10.0.0
- PyPDF2>=3.0.0
- PySide6>=6.6.0

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

**Issue: "Tesseract not found"**
- Make sure Tesseract is installed and in your system PATH
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

**Issue: "Failed to convert PDF to images"**
- Ensure Poppler is installed
- macOS: `brew install poppler`
- Linux: `sudo apt-get install poppler-utils`

**Issue: Poor OCR quality**
- Try increasing DPI (e.g., `--dpi 400`)
- Ensure the PDF has good scan quality
- The system auto-detects optimal DPI based on page size

## Author

Created by [KSEGIT](https://github.com/KSEGIT)
