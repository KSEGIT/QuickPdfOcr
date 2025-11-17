# Third-Party Licenses

This application uses several open-source components. Below are the licenses for each:

## Poppler

**License:** GPL-2.0 or GPL-3.0 (user's choice)

Poppler is a PDF rendering library based on the xpdf-3.0 code base.

- Website: https://poppler.freedesktop.org/
- Source Code: https://gitlab.freedesktop.org/poppler/poppler

When distributed in binary form with this application, you may choose to comply with either GPL-2.0 or GPL-3.0 terms.

**GPL-2.0 License Text:** https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
**GPL-3.0 License Text:** https://www.gnu.org/licenses/gpl-3.0.html

**Important Note:** Since Poppler is licensed under GPL, and this application distributes Poppler binaries, users who redistribute this application must comply with the GPL terms. The source code for Poppler is available at the links above.

---

## Tesseract OCR

**License:** Apache License 2.0

Tesseract is an open-source OCR engine.

- Website: https://github.com/tesseract-ocr/tesseract
- License: https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE

When distributed in binary form with this application, Tesseract binaries and tessdata (language data files) are included. The Apache 2.0 license allows free redistribution.

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

### pdf2image

**License:** MIT License

- Website: https://github.com/Belval/pdf2image
- License: https://github.com/Belval/pdf2image/blob/master/LICENSE

### Pillow (PIL Fork)

**License:** HPND (Historical Permission Notice and Disclaimer)

- Website: https://python-pillow.org/
- License: https://github.com/python-pillow/Pillow/blob/main/LICENSE

### PyPDF2

**License:** BSD 3-Clause License

- Website: https://github.com/py-pdf/pypdf
- License: https://github.com/py-pdf/pypdf/blob/main/LICENSE

### PyInstaller

**License:** GPL-2.0 with a special exception for bundled applications

- Website: https://pyinstaller.org/
- License: https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt

PyInstaller's license includes an exception that allows you to distribute the bootloader and bundled applications under any license you choose, as long as you don't modify PyInstaller itself.

---

## Compliance Notes

1. **GPL Components:** This application bundles Poppler, which is licensed under GPL. This means:
   - The complete source code must be made available (see https://github.com/KSEGIT/QuickPdfOcr)
   - Any modifications must also be distributed under GPL terms
   - The GPL license text must be included with distributions

2. **LGPL Components:** PySide6 (Qt) is licensed under LGPL, which allows dynamic linking with proprietary software. Since we bundle it as a library, this is compliant.

3. **Other Licenses:** All other components use permissive licenses (MIT, Apache, BSD, HPND) that allow free redistribution.

---

## Source Code Availability

The complete source code for this application is available at:
**https://github.com/KSEGIT/QuickPdfOcr**

The source code for Poppler is available at:
**https://gitlab.freedesktop.org/poppler/poppler**

---

## Windows Poppler Build

For Windows builds, we use pre-compiled Poppler binaries from:
**https://github.com/oschwartz10612/poppler-windows**

These binaries are built from the official Poppler source code and are subject to the same GPL-2.0/GPL-3.0 license terms.
