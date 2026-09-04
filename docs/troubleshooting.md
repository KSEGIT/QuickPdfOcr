# Troubleshooting

[← Back to the README](../README.md)

## macOS won't open the app

macOS blocks the app on first launch because it isn't notarized yet. Open
**System Settings → Privacy & Security**, scroll to the message about
QuickPdfOcr, and click **Open Anyway**. This is a one-time step — see
[Installation](installation.md#macos).

## "Tesseract not found"

This affects Windows and Linux only. macOS uses Apple's Vision framework and
never needs Tesseract.

Tesseract is installed separately from QuickPdfOcr, and it has to be on your
system PATH.

- **Linux:** `sudo apt-get install tesseract-ocr`
- **Windows:** `winget install --id UB-Mannheim.TesseractOCR`, or use the [UB
  Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki)

If you installed it and still see this message, the installer probably didn't
add it to your PATH. Open a new terminal and run `tesseract --version` to
check.

## "Failed to open/render PDF"

There is no separate PDF library to install — rendering is bundled on every
platform — so this is almost always about the file itself. The usual causes:

- The PDF is corrupted or was only partly downloaded.
- The PDF is password-protected.
- The file isn't actually a PDF, despite its `.pdf` name.

Try opening it in a normal PDF viewer first. If that fails too, the file is the
problem.

## The text comes out wrong or garbled

- **Check the language.** A recognizer expecting English will mangle French. See
  [Languages](usage.md#languages).
- **Check the scan.** Faint, skewed, or low-resolution scans produce poor text.
  Rescanning at a higher quality helps more than any setting.
- **Raise the DPI.** For small or dense print, try `--dpi 400` on the [command
  line](usage.md#command-line).

## The app runs but the buttons have no icons

This means the icon files didn't make it into the build. Report it as a bug —
it's a packaging problem, not something you can fix locally.

## Something else

Please [open an issue](https://github.com/KSEGIT/QuickPdfOcr/issues) and
include your operating system, the QuickPdfOcr version, and what you were doing
when it went wrong.
