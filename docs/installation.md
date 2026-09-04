# Installation

[← Back to the README](../README.md)

All downloads are on the [latest release
page](https://github.com/KSEGIT/QuickPdfOcr/releases/latest).

## macOS

**Requires macOS 13 (Ventura) or later.**

1. Download `QuickPdfOcr-macOS-universal2.zip`.
2. Unzip it and drag `QuickPdfOcr.app` into your Applications folder.
3. **On the first launch only:** macOS refuses to open the app, because it
   isn't notarized. Open **System Settings → Privacy & Security**, scroll down
   to the message about QuickPdfOcr, and click **Open Anyway**. Every launch
   after that works normally.

There is nothing else to install — no Homebrew, no Poppler, no Tesseract. PDF
rendering is built into the app, and text recognition uses the Vision framework
that ships with macOS.

Once it's installed you can also:

- Drag a PDF onto the app's Dock icon.
- Right-click a PDF and choose **Open With → QuickPdfOcr**.
- Right-click a PDF and choose **Services → OCR with QuickPdfOcr**. macOS only
  registers Services entries after an app has run once, so launch QuickPdfOcr
  at least one time before you look for it. You may also need to wait a moment
  or restart Finder.

## Windows

1. Download `QuickPdfOcr-Windows-x64.zip`.
2. Extract it. You get a `QuickPdfOcr` folder holding `QuickPdfOcr.exe` next to
   an `_internal` folder that it needs — keep the two together.
3. Install Tesseract OCR (see below). It is the one thing the download does not
   include.
4. Run `QuickPdfOcr.exe` from inside the extracted folder.

### Install Tesseract on Windows

The quickest way is winget:

```powershell
winget install --id UB-Mannheim.TesseractOCR
```

You can also download the installer from the [UB Mannheim Tesseract
page](https://github.com/UB-Mannheim/tesseract/wiki).

## Linux

1. Download `QuickPdfOcr-Linux-x86_64.tar.gz`.
2. Extract it: `tar -xzf QuickPdfOcr-Linux-x86_64.tar.gz`. You get a
   `QuickPdfOcr` folder holding the `QuickPdfOcr` executable next to an
   `_internal` folder that it needs — keep the two together.
3. Install Tesseract OCR (see below).
4. Make it executable and run it from inside the extracted folder:

```bash
chmod +x QuickPdfOcr/QuickPdfOcr
./QuickPdfOcr/QuickPdfOcr
```

### Install Tesseract on Linux

On Ubuntu or Debian:

```bash
sudo apt-get install tesseract-ocr
```

## Why Windows and Linux need Tesseract

QuickPdfOcr needs two things: something to turn PDF pages into images, and
something to read text out of those images.

The first part is bundled everywhere. QuickPdfOcr uses `pypdfium2`, which ships
inside the app on all three platforms, so there is no Poppler to install.

The second part differs by platform. macOS has a text recognizer built into the
operating system (Apple's Vision framework), so the app just uses it. Windows
and Linux have no equivalent, so they use Tesseract. Windows and Linux release
artifacts do not bundle Tesseract, so you must install it separately.

## Running from source instead

If you'd rather run the Python code directly, see [Building from
source](building.md).
