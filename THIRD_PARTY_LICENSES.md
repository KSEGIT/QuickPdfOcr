# Third-Party Licenses

This application uses several open-source components. Below are the licenses for each:

**Poppler is no longer distributed with any build.** Earlier releases bundled
Poppler (GPL-2.0/GPL-3.0) binaries for PDF rendering; PDF rendering is now
provided by the pypdfium2 wheel (BSD-3-Clause/Apache-2.0), so no GPL-licensed
component ships with this application.

## PDFium (via pypdfium2)

- **License:** BSD-3-Clause (PDFium), Apache-2.0 (pypdfium2 bindings)
- **Used for:** rendering PDF pages to bitmaps on all platforms
- **Source:** https://github.com/pypdfium2-team/pypdfium2

---

## Apple Vision framework (macOS only)

- **License:** part of macOS; used via public API, not redistributed
- **Used for:** on-device text recognition on macOS
- **Bindings:** PyObjC (MIT), https://github.com/ronaldoussoren/pyobjc

---

## Tesseract OCR (Windows and Linux only)

**License:** Apache License 2.0

- **Used for:** text recognition on non-macOS platforms
- Website: https://github.com/tesseract-ocr/tesseract
- License: https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE

Windows and Linux users must install Tesseract and tessdata (language data files) separately; they are not bundled with the binaries. The Apache 2.0 license allows free redistribution. macOS builds do not include Tesseract; they use the Apple Vision framework instead.

**Source Code:** https://github.com/tesseract-ocr/tesseract

---

## Python Dependencies

### PySide6 (Qt for Python)

**License:** LGPL-3.0

- Website: https://www.qt.io/qt-for-python
- License: https://www.gnu.org/licenses/lgpl-3.0.html

### pytesseract

**License:** Apache License 2.0

- Website: https://github.com/madmaze/pytesseract
- License: https://github.com/madmaze/pytesseract/blob/master/LICENSE

### Pillow (PIL Fork)

**License:** HPND (Historical Permission Notice and Disclaimer)

- Website: https://python-pillow.org/
- License: https://github.com/python-pillow/Pillow/blob/main/LICENSE

### PyInstaller

**License:** GPL-2.0 with a special exception for bundled applications

- Website: https://pyinstaller.org/
- License: https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt

PyInstaller's license includes an exception that allows you to distribute the bootloader and bundled applications under any license you choose, as long as you don't modify PyInstaller itself.

---

## Compliance Notes

1. **No GPL Components:** This application no longer bundles any GPL-licensed
   component. Poppler (GPL-2.0/GPL-3.0) has been removed; PDF rendering is
   provided by pypdfium2 (BSD-3-Clause/Apache-2.0) instead.

2. **LGPL Components:** PySide6 (Qt) is licensed under LGPL, which allows dynamic linking with proprietary software. Since we bundle it as a library, this is compliant.

3. **Other Licenses:** All other components use permissive licenses (MIT, Apache, BSD, HPND) that allow free redistribution.

---

## Source Code Availability

The complete source code for this application is available at:
**https://github.com/KSEGIT/QuickPdfOcr**
