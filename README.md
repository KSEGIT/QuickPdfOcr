# QuickPdfOcr — free offline PDF OCR for Mac, Windows, and Linux

Turn scanned PDFs into searchable, copyable text on your own computer. No upload, no cloud, no account.

[![Latest release](https://img.shields.io/github/v/release/KSEGIT/QuickPdfOcr)](https://github.com/KSEGIT/QuickPdfOcr/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Download

| Platform | Download | Also needed |
| --- | --- | --- |
| macOS 13 or later | [QuickPdfOcr-macOS-universal2.zip](https://github.com/KSEGIT/QuickPdfOcr/releases/latest) | Nothing |
| Windows 10/11 | [QuickPdfOcr-Windows-x64.zip](https://github.com/KSEGIT/QuickPdfOcr/releases/latest) | [Tesseract OCR](docs/installation.md#windows) |
| Linux (x86_64) | [QuickPdfOcr-Linux-x86_64.tar.gz](https://github.com/KSEGIT/QuickPdfOcr/releases/latest) | [Tesseract OCR](docs/installation.md#linux) |

On macOS the first launch needs one extra click, because the app isn't
notarized yet. See [Installation](docs/installation.md#macos).

## What it does

You have a scanned PDF. The text inside it is really a picture, so you can't
select it, search it, or copy it. QuickPdfOcr reads that picture and hands you
the text back.

Everything runs on your machine. Your documents are never uploaded anywhere.

- **Drag and drop** — drop a PDF on the window, or pick one with the file browser.
- **Watch it work** — a progress bar tells you which page it's on.
- **Copy the result** — one click puts the text on your clipboard.
- **Open from Finder** — on macOS, right-click a PDF and choose QuickPdfOcr.

On macOS, text recognition uses Apple's Vision framework, which is already part
of the operating system — so there is nothing extra to install. On Windows and
Linux it uses [Tesseract](https://github.com/tesseract-ocr/tesseract), which you
install once.

## How to use it

1. Drag a PDF onto the window, or click **Open PDF File**.
2. Click **Start OCR**.
3. Click **Copy to Clipboard** when it finishes.

That's the whole app. For language settings, scan quality, and the command
line, see [Usage](docs/usage.md).

## Documentation

- [Installation](docs/installation.md) — per-platform setup, including Tesseract
- [Usage](docs/usage.md) — languages, image quality, command-line options
- [Troubleshooting](docs/troubleshooting.md) — when something doesn't work
- [Building from source](docs/building.md) — run the code, build your own binary

## Contributing

Pull requests are welcome. To run QuickPdfOcr from source:

```bash
git clone https://github.com/KSEGIT/QuickPdfOcr.git
cd QuickPdfOcr
pip install -r requirements.txt
python main.py
```

Full build instructions, the project layout, and how releases are made are in
[Building from source](docs/building.md).

## License

MIT — see [LICENSE](LICENSE).

Third-party components (PDFium, Tesseract, Qt, and others) keep their own
licenses; see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
