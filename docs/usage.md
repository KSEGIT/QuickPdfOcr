# Usage

[← Back to the README](../README.md)

## The app

1. Drag a PDF onto the window, or click **Open PDF File** to pick one.
2. Click **Start OCR**. A progress bar shows which page it's working on.
3. Click **Copy to Clipboard** when it finishes.

If something goes wrong, the app offers **Try Again** or **Start Over** rather
than leaving you stuck.

## Getting better results

OCR quality depends almost entirely on the quality of the scan.

- **Start with a good scan.** Text that's blurry, skewed, or faint on paper will
  be blurry, skewed, or faint to the recognizer too.
- **Raise the DPI for small text.** QuickPdfOcr picks a DPI automatically from
  the page size, which suits most documents. For dense or small print, try 400
  on the command line (see below).
- **Set the language.** The recognizer is much more accurate when it knows which
  language to expect.

## Languages

Language codes differ by platform, because the two engines use different
standards.

| Platform | Engine | Code style | Examples |
| --- | --- | --- | --- |
| macOS | Apple Vision | BCP-47 | `en-US`, `fr-FR`, `de-DE` |
| Windows, Linux | Tesseract | ISO 639-2 | `eng`, `fra`, `deu` |

Common Tesseract codes:

| Code | Language |
| --- | --- |
| `eng` | English |
| `fra` | French |
| `deu` | German |
| `spa` | Spanish |
| `chi_sim` | Chinese (Simplified) |
| `jpn` | Japanese |

Tesseract only recognizes a language if you've installed its data file. On
Ubuntu or Debian, `sudo apt-get install tesseract-ocr-fra` adds French.

## Command line

The OCR processor also runs on its own, without the window. This is the older
interface and it is kept for scripting.

```bash
python components/pdf_ocr.py document.pdf output.txt
```

If you leave the output file out, the text goes to standard output.

**Options**

| Option | What it does |
| --- | --- |
| `--dpi <value>` | Render pages at this DPI. Default: picked automatically from page size. |
| `--lang <code>` | Recognize this language. Default: whatever the engine uses. |

**Examples**

```bash
# Let it pick the DPI
python components/pdf_ocr.py document.pdf

# Write to a file at 400 DPI
python components/pdf_ocr.py document.pdf output.txt --dpi 400

# French on Windows or Linux
python components/pdf_ocr.py document.pdf --lang fra

# French on macOS
python components/pdf_ocr.py document.pdf --lang fr-FR
```

The command line runs from a source checkout. See [Building from
source](building.md) to set that up.
