# QuickPdfOcr — TODO

## User-Facing Features

### OCR Language Selection
- [x] Add a language dropdown/selector in the UI (default: English)
- [x] Download Tesseract language packs on demand from the app
- [x] Show download progress and store downloaded packs locally
- [x] Remember the user's last-used language between sessions

### Batch / Multi-File Processing
- [ ] Allow dropping or selecting multiple PDFs at once
- [ ] Process files in sequence with a combined progress view
- [ ] Export all results to individual text files or a single merged file

### Output Options
- [x] Save extracted text to file (txt, docx, markdown)
- [ ] Search within extracted text (Ctrl+F)
- [ ] Page-by-page navigation instead of one long text block
- [ ] Syntax/format preservation (tables, columns) where possible

### Image-to-Text Support
- [ ] Accept image files (PNG, JPG, TIFF) in addition to PDFs
- [ ] Drag-and-drop or file dialog for images

### Settings / Preferences
- [x] Persistent settings (language, DPI override, output format, theme)
- [ ] Manual DPI override option in the UI
- [ ] Dark mode / light mode toggle
- [x] Configurable default output directory

### UX Polish
- [x] Cancel button to abort in-progress OCR
- [ ] Estimated time remaining during OCR processing
- [x] Page-level progress bar (e.g., "Page 3/12") in addition to text status
- [ ] Keyboard shortcuts (Ctrl+O open, Ctrl+C copy, Ctrl+V paste PDF path)
- [ ] Recent files list
- [ ] Drag-and-drop feedback: preview the PDF filename before dropping
- [ ] System tray / notification when OCR finishes (for large jobs)

### Accessibility
- [ ] Screen reader support for all UI elements
- [ ] High-contrast mode
- [ ] Resizable / scalable fonts in the output area

---

## Developer / Code Quality

### Testing
- [x] Add unit tests for `PdfOcrProcessor` (DPI detection, empty text, error paths)
- [x] Add unit tests for `OCRWorker` (stop flag, signal emission, edge cases)
- [ ] Add UI tests for `MainWindow` (file selection, state transitions, button visibility)
- [ ] Add integration test with a small sample PDF
- [x] Set up pytest with CI integration
- [ ] Add test coverage reporting

### Architecture
- [ ] Extract hardcoded stylesheet strings into a central theme/style module
- [x] Separate OCR language config from `OCRWorker` (currently hardcoded to `'eng'`)
- [x] Add a settings/config module (QSettings or JSON) for persistent preferences
- [ ] Add structured logging (replace scattered `print()` calls)
- [x] Move inline `import traceback` in `ocr_worker.py` to module level

### CI / Build
- [ ] Add a linter step to CI (ruff or flake8)
- [ ] Add type checking step (mypy)
- [ ] Add automated test step to all build workflows
- [ ] Pin dependency versions in `requirements.txt` for reproducible builds
- [ ] Add dependabot or renovate for dependency updates
- [ ] Automate release notes generation from commit history

### Documentation
- [ ] Add contributing guide (CONTRIBUTING.md)
- [ ] Add inline docstrings to `DropZoneLabel` public methods
- [ ] Document the architecture (component diagram, data flow)
- [ ] Add troubleshooting section for common Tesseract/Poppler path issues on each OS
