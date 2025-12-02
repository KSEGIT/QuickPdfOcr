# GitHub Copilot Instructions for QuickPdfOcr

## Project Overview

QuickPdfOcr is a cross-platform desktop application for extracting text from PDF files using OCR (Optical Character Recognition). It features a modern Qt6-based GUI built with PySide6 and uses Tesseract OCR for text extraction.

**Key Technologies:**
- **PySide6** (Qt6 for Python) - GUI framework
- **Tesseract OCR** - Text recognition engine
- **Poppler** - PDF processing utilities
- **PyInstaller** - Standalone executable bundling
- **Python 3.12** - Core language (CI uses 3.12, likely works with 3.10+)
- **pdf2image** - PDF to image conversion
- **pytesseract** - Python wrapper for Tesseract
- **Pillow (PIL)** - Image processing
- **PyPDF2** - PDF metadata and analysis

## Build and Test Commands

### Running the Application
```bash
# Run from source
python main.py

# Run command-line interface (legacy)
python components/pdf_ocr.py document.pdf output.txt
```

### Building Executables
```bash
# Install dependencies
pip install -r requirements.txt

# Build standalone executable for current platform
python build.py

# Output will be in dist/ directory
```

### Testing
```bash
# Test bundled dependencies (for built executables)
python test_bundled_deps.py
```

**Note:** This project does not currently have a comprehensive test suite. When adding new features, consider adding appropriate tests if it makes sense for the feature.

## Project Structure

```
QuickPdfOcr/
├── main.py                    # Application entry point
├── __main__.py                # Module entry point (currently empty placeholder)
├── build.py                   # PyInstaller build script
├── requirements.txt           # Python dependencies
├── test_bundled_deps.py      # Test script for bundled binaries
├── components/
│   ├── __init__.py
│   ├── pdf_ocr.py            # Core OCR processor (PdfOcrProcessor class)
│   ├── ocr_worker.py         # Qt background worker thread
│   └── poppler_utils.py      # Poppler binary detection and setup
├── ui/
│   ├── __init__.py
│   └── main_window.py        # Main GUI window (MainWindow class)
├── docs/                      # Documentation files
└── .github/
    └── workflows/             # CI/CD build workflows
```

## Code Style and Conventions

### General Python Style
- **Follow PEP 8** conventions for Python code
- Use **4 spaces** for indentation (not tabs)
- Use **double quotes** for strings consistently
- Maximum line length: ~100 characters (flexible for readability, slightly relaxed from PEP 8's 79)
- Use **type hints** for function parameters and return values where practical

### Docstrings
```python
def function_name(param: str) -> bool:
    """
    Brief description of function
    
    Args:
        param (str): Description of parameter
    
    Returns:
        bool: Description of return value
    """
```

### Class Organization
- Group related methods together
- Use leading underscore for private/internal methods (e.g., `_setup_ui()`)
- Add docstrings to classes and public methods

### Qt/PySide6 Patterns
- Use **Signal/Slot** mechanism for event handling
- Prefix Qt widget member variables meaningfully (e.g., `self.ocr_button` not `self.btn1`)
- Use Qt enums with full namespace (e.g., `Qt.AlignmentFlag.AlignCenter`)
- Implement drag-and-drop with proper event handling (`dragEnterEvent`, `dropEvent`)
- Run long operations in **QThread** with **QObject** workers (see `OCRWorker` example)

### File Handling
- Always use **pathlib.Path** for file paths (not string concatenation)
- Validate file extensions and existence before processing
- Use context managers (`with` statements) for file operations

### Error Handling
- Catch specific exceptions rather than broad `except Exception`
- Provide meaningful error messages to users
- Use `progress_callback` pattern for long-running operations to provide feedback

## Platform-Specific Considerations

### Binary Bundling
- The application bundles **Poppler** and **Tesseract** for standalone executables
- `setup_bundled_binaries()` must be called early in startup
- Use `getattr(sys, 'frozen', False)` to detect PyInstaller bundle
- Access bundled resources via `sys._MEIPASS` when frozen

### Cross-Platform Paths
- Homebrew paths differ on ARM64 (`/opt/homebrew/`) vs Intel (`/usr/local/`) macOS
- Windows uses backslashes - always use `Path` objects to handle this
- Linux typically has Poppler in `/usr/bin/`

## Key Components and Patterns

### PdfOcrProcessor (`components/pdf_ocr.py`)
- Main OCR processing class
- Auto-detects optimal DPI based on PDF page size
- Supports progress callbacks: `progress_callback(message: str)`
- Returns extracted text as string

### OCRWorker (`components/ocr_worker.py`)
- QObject-based worker for background processing
- Emits three signals: `progress`, `finished`, `error`
- Always run in a `QThread`, never in the main GUI thread

### MainWindow (`ui/main_window.py`)
- Main GUI with drag-and-drop support
- Uses custom `DropZoneLabel` widget for file drops
- Manages OCR thread lifecycle (create, start, cleanup)

## Dependencies and Security

### Adding New Dependencies
- Add to `requirements.txt` with version constraints
- Ensure compatibility with PyInstaller bundling
- Test on all three platforms (Windows, macOS, Linux)
- Check licenses for bundling compatibility

### Security Considerations
- **Never commit secrets** or API keys
- Validate file paths to prevent directory traversal
- Sanitize user inputs before displaying in UI
- Be cautious with `eval()` or `exec()` - avoid if possible
- The bundled Tesseract/Poppler binaries come from trusted sources

## Git Workflow

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (e.g., "Add", "Fix", "Update", "Refactor")
- Keep first line under 72 characters
- Add details in subsequent lines if needed

### Branch Strategy
- `main` branch is the stable release branch
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Copilot branches: `copilot/*` (automatically created)

### Pull Requests
- Ensure code builds successfully on all platforms
- Update README.md if adding user-facing features
- Add or update docstrings for new functions/classes
- Test manually with the GUI if UI changes are involved

## Common Patterns and Examples

### Processing a PDF with Progress Updates
```python
from components.pdf_ocr import PdfOcrProcessor

processor = PdfOcrProcessor(lang='eng')
text = processor.process(
    pdf_path,
    output_file=None,  # or specify a path to save
    progress_callback=lambda msg: print(msg)
)
```

### Creating a Qt Background Worker
```python
from PySide6.QtCore import QThread, QObject, Signal

# Create worker and thread
self.ocr_thread = QThread()
self.ocr_worker = OCRWorker(pdf_path)
self.ocr_worker.moveToThread(self.ocr_thread)

# Connect signals
self.ocr_thread.started.connect(self.ocr_worker.run)
self.ocr_worker.finished.connect(self.on_ocr_finished)
self.ocr_worker.error.connect(self.on_ocr_error)

# Start processing
self.ocr_thread.start()
```

### Detecting Bundled vs Source Execution
```python
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    binary_path = bundle_dir / "poppler" / "bin"
else:
    # Running from source - use platform-specific paths
    # See poppler_utils.py for actual cross-platform detection
    binary_path = Path("/usr/local/bin")  # macOS/Linux example
```

## Boundaries and Restrictions

### Do NOT Modify
- `.github/workflows/` files without understanding CI/CD implications
- `LICENSE` or `THIRD_PARTY_LICENSES.md` files
- Binary files or bundled dependencies in `dist/` (these are build artifacts)

### Be Careful With
- PyInstaller spec file generation in `build.py`
- Binary paths and platform detection logic
- Qt Signal/Slot connections (easy to create memory leaks)
- Thread cleanup (always stop threads properly)

### Always Consider
- Cross-platform compatibility (Windows, macOS Intel/ARM, Linux)
- User experience - provide feedback for long operations
- Error messages should be user-friendly, not just technical
- Memory usage - OCR can be memory-intensive with large PDFs

## Troubleshooting Common Issues

### "Tesseract not found" Error
- Bundled executables include Tesseract - check `setup_bundled_binaries()`
- For source: Ensure Tesseract is installed and in PATH
- Build artifacts bundle Tesseract in `tesseract_binaries/` directory

### "Poppler not found" Error
- Ensure `poppler_utils.py` is correctly setting up paths
- Check `poppler_binaries/` directory for bundled version
- Verify `pdf2image` can find the Poppler binaries

### GUI Freezing
- Long operations must run in QThread, not main thread
- Check that worker is properly moved to thread with `moveToThread()`
- Ensure `QThread.start()` is called, not `worker.run()` directly

### Build Failures
- Verify all dependencies in `requirements.txt` are installed
- Check platform-specific binary paths in `build.py`
- Ensure Poppler/Tesseract are available during build

## Development Tips

1. **Test on target platform**: Each OS has quirks - test builds on actual hardware
2. **Use Qt Designer sparingly**: This project uses programmatic UI for better control
3. **Check binary size**: Bundled executables can be large (100+ MB) - this is expected
4. **Monitor memory**: OCR processes can use significant RAM with large/high-DPI PDFs
5. **Provide user feedback**: Always show progress for operations taking >1 second
6. **Handle edge cases**: Empty PDFs, corrupted files, non-text PDFs, etc.

## Useful Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Tesseract OCR Documentation](https://github.com/tesseract-ocr/tesseract)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [pdf2image Documentation](https://github.com/Belval/pdf2image)

---

**For questions or clarifications**, refer to existing code patterns in `components/` and `ui/` directories, or check the README.md for user-facing documentation.
