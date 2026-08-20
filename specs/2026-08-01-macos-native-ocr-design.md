# Self-contained macOS app: native rendering + OCR

**Date:** 2026-08-01
**Status:** Proposed
**Closes:** #26 (poppler error on macOS)

## Problem

Issue #26 reports the bundled macOS app failing on every PDF:

```
OCR failed: Poppler utilities not found.
dyld[55364]: Library not loaded: @rpath/libpoppler.158.dylib
  Referenced from: /private/var/folders/.../T/_MEIxcaSMZ/poppler/bin/pdfinfo
  Reason: tried: .../poppler/bin/../../libpoppler.158.dylib (no such file)
```

### Root cause (verified)

Three defects compound:

1. **`.github/workflows/build-macos.yml:29`** copies `/opt/homebrew/bin/pdf*` — the CLI
   executables only, none of their shared libraries.
2. Those executables link against Homebrew dylibs by `@rpath`. Measured locally:

   ```
   $ otool -L $(which pdfinfo)
       @rpath/libpoppler.162.dylib
   ```

   Walking the transitive closure yields **24 third-party dylibs, 10.9 MB** — libpoppler,
   freetype, fontconfig, libjpeg, libtiff, libpng, lcms2, nspr/nss, gpgme, libassuan and more.
   None are copied into the bundle.
3. **`build.py:141`** uses `--onefile`, so the app unpacks to `/var/folders/…/T/_MEIxxxx/` at
   launch. `@rpath` there resolves to `poppler/bin/../../libpoppler.158.dylib`, which does
   not exist. Hence the dyld failure.

**Tesseract has the identical latent defect.** `build.py:274` bundles `bin/tesseract` alone,
without libtesseract or libleptonica. It simply fails after poppler does.

**Secondary issue:** poppler is GPL-licensed. Shipping it inside a distributed `.app` carries
obligations that `THIRD_PARTY_LICENSES.md` does not currently discharge.

## Decision

Stop shipping foreign binaries on macOS. Use what the OS already provides.

| Platform | PDF → bitmap | bitmap → text |
|---|---|---|
| macOS | pypdfium2 (bundled wheel) | **Apple Vision** (`VNRecognizeTextRequest`) |
| Windows / Linux | pypdfium2 (bundled wheel) | Tesseract (unchanged) |

Poppler is removed on **all** platforms. Tesseract is removed on **macOS only**.

### Why this over the alternatives

- **Fixing the dylib bundling** (`dylibbundler` + `install_name_tool`) works, but leaves 25
  dylibs to keep re-pointing and re-signing on every Homebrew bump, and keeps the GPL exposure.
- **pypdfium2 alone** fixes the crash in the issue but still requires correctly bundling
  Tesseract's own dylib tree on macOS — the same class of bug, one layer down.

Vision is already installed on every supported Mac, is GPU-accelerated on Apple Silicon, and
needs no language data files at all.

### Verified proof of concept

An end-to-end run on macOS 26.5.2 (`scratchpad/poc_nopil.py`), with neither poppler,
tesseract, nor Pillow present:

```
pypdfium2 raw bitmap: 2480x3509 stride=9920 format=3 mode=RGBX
CGImage created: 2480 x 3509
Vision OCR (no PIL) ok=True in 0.29s
  1.00  FAKTURA VAT PL6972514
  1.00  Kwota brutto: 1234,56 PLN
  1.00  NIP 527-10-26-863
  1.00  Termin platnosci: 2026-08-14

Pillow imported? False
```

Vision reports **30 OS-provided recognition languages**, including `pl-PL` — matching the
Polish invoice in the issue screenshot:

```
en-US, fr-FR, it-IT, de-DE, es-ES, pt-BR, zh-Hans, zh-Hant, yue-Hans, yue-Hant, ko-KR,
ja-JP, ru-RU, uk-UA, th-TH, vi-VT, ar-SA, ars-SA, tr-TR, id-ID, cs-CZ, da-DK, nl-NL,
no-NO, nn-NO, nb-NO, ms-MY, pl-PL, ro-RO, sv-SE
```

## Architecture

Two narrow interfaces, each with one job, so platform differences stay behind a boundary
instead of spreading through `pdf_ocr.py`.

```
components/
  page_image.py            PageImage dataclass — the boundary type
  rendering/
    base.py                PdfRenderer protocol
    pdfium_renderer.py     pypdfium2; all platforms
  ocr/
    base.py                OcrEngine protocol
    vision_engine.py       macOS; PyObjC Vision
    tesseract_engine.py    Windows/Linux; pytesseract
    __init__.py            get_engine() — platform selection, single place
```

### `PageImage` — the boundary

```python
@dataclass(frozen=True)
class PageImage:
    width: int
    height: int
    stride: int       # bytes per row
    buffer: bytes     # raw pixels
    mode: str         # "RGBX"
```

A plain buffer, not a PIL image. Each engine adapts it on its own side:

- `vision_engine` → `CGImageCreate` → `VNImageRequestHandler`
- `tesseract_engine` → `PIL.Image.frombuffer` → `pytesseract`

This is what keeps **Pillow out of the macOS import graph entirely**, which matters for
universal2 (below).

### Interfaces

```python
class PdfRenderer(Protocol):
    def page_count(self) -> int: ...
    def page_size_inches(self, index: int) -> tuple[float, float]: ...   # for DPI autodetect
    def render_page(self, index: int, dpi: int) -> PageImage: ...

class OcrEngine(Protocol):
    def supported_languages(self) -> list[str]: ...
    def recognize(self, page: PageImage, lang: str) -> str: ...
```

`PdfOcrProcessor.process()` becomes orchestration only — open, loop, render, recognize, join.
It shrinks from 323 lines to roughly 120, and stops containing any knowledge of poppler,
tessdata, or environment variables.

### Rendering flags that matter

`page.render(scale=dpi/72, rev_byteorder=True, prefer_bgrx=True)`.

Both flags are load-bearing: pypdfium2 defaults to 24-bit RGB, which `CGImageCreate` rejects
(it returns a 0×0 image and Vision then fails with a bare `None` result — the first PoC hit
exactly this). `prefer_bgrx` forces 4-byte pixels; `rev_byteorder` gives RGBx rather than BGRx.
Pair with `kCGImageAlphaNoneSkipLast`.

## What this deletes

| Removed | Why |
|---|---|
| `components/poppler_utils.py` (196 lines) | No bundled binaries left to locate |
| `PdfOcrProcessor._get_tessdata_config()` | No tessdata on macOS |
| `TESSDATA_PREFIX` / `TESSDATA_DIR` handling | Same |
| `test_bundled_deps.py`, `test_tessdata_path.py` | Test machinery that no longer exists |
| `pdf2image` dependency | Replaced by pypdfium2 |
| `PyPDF2` dependency | `page.get_size()` covers DPI autodetect |
| `pytesseract`, `Pillow` **on macOS** | Vision path needs neither |
| `poppler_binaries` / `tesseract_binaries` CI steps | Nothing to copy |

Expected app size: **~250 MB → ~60 MB**.

## DPI auto-detection

`detect_optimal_dpi()` keeps its current thresholds (400/300/250/200 by page size) but sources
page dimensions from `pypdfium2`'s `page.get_size()` (points) instead of `PyPDF2`'s mediabox.
Behaviour is unchanged; one dependency disappears.

## Language handling

Tesseract uses ISO 639-2 (`eng`, `pol`); Vision uses BCP-47 (`en-US`, `pl-PL`). A mapping table
lives in `ocr/__init__.py`.

The language dropdown must be **populated at runtime** from
`engine.supported_languages()`, not hardcoded — Vision's language list grows with the OS
version, and a Mac on macOS 13 offers fewer than the 30 listed above.

## Packaging

Scope per decision: bundle fixes, universal2, PDF association, Finder Services.
**Signing and notarization are out of scope** — see Risks.

### 1. `--onedir` `.app` instead of `--onefile`

`build.py:133` drops `--onefile`; PyInstaller emits `QuickPdfOcr.app` directly. This is also a
correctness fix: the `/var/folders/…/T/_MEI…` temp extraction is precisely where issue #26's
`@rpath` lookup went wrong. It removes a ~250 MB re-extract on every launch.

### 2. universal2

Wheel survey:

| Package | universal2? |
|---|---|
| PySide6 6.11.1 | ✅ `pyside6-6.11.1-cp310-abi3-macosx_13_0_universal2.whl` |
| pyobjc-framework-Vision / Quartz 12.2.1 | ✅ universal2 |
| pypdfium2 5.12.1 | ❌ separate arm64 / x86_64 |
| Pillow 12.3.0 | ❌ separate arm64 / x86_64 — **not needed on macOS** |

Dropping Pillow reduces the problem to a single file, `pypdfium2_raw/libpdfium.dylib`, which
merges cleanly. Verified:

```
$ lipo -create armx/.../libpdfium.dylib x86x/.../libpdfium.dylib -output libpdfium_universal.dylib
$ lipo -info libpdfium_universal.dylib
Architectures in the fat file: x86_64 arm64
```

CI step: build on `macos-14`, download the opposite-arch pypdfium2 wheel, `lipo -create` the
two dylibs over the bundled one, then re-sign (below).

### 3. Ad-hoc code signing — required, not optional

`lipo` invalidates any existing signature, and **arm64 binaries will not execute unsigned on
Apple Silicon.** After the merge the build must run:

```
codesign --force --deep --sign - dist/QuickPdfOcr.app
```

Ad-hoc signing (`--sign -`) is free and needs no Apple Developer account. It is a hard
requirement for the app to launch at all, independent of the notarization decision.

### 4. PDF file-type association

Add `CFBundleDocumentTypes` to the `.app` Info.plist (PyInstaller `--osx-bundle-identifier`
plus an `info_plist` dict in the spec file) declaring `com.adobe.pdf` as `LSItemContentTypes`
with `CFBundleTypeRole: Viewer`.

Handling requires one addition on the Qt side: macOS delivers double-clicked and
dragged-to-Dock files as `QEvent.Type.FileOpen` on the `QApplication`, **not** as `argv`. A
`QApplication.event()` override routes it into the existing file-selection path in
`ui/main_window.py`.

### 5. Finder right-click

Use **`NSServices` in the main app's Info.plist**, not a separate Quick Action app extension.
An `NSServices` entry with `NSSendFileTypes: [com.adobe.pdf]` puts "OCR with QuickPdfOcr" in
the Finder context menu with no second build target, no separate bundle, and no additional
signing identity. Launch Services registers it the first time the app runs.

## Testing

- **Engine contract tests** — one shared suite run against both `VisionOcrEngine` and
  `TesseractOcrEngine`, asserting the `OcrEngine` protocol holds for each.
- **Golden-file test** — a committed fixture PDF, asserting extracted text contains known
  strings. Thresholded, not exact-match: Vision and Tesseract will not agree character for
  character.
- **Renderer test** — page count, page size, and bitmap dimensions at a known DPI.
- **Smoke test in CI** — run the built `.app` headless against the fixture PDF. This is the
  check that would have caught issue #26 before release; the current CI builds the artifact
  but never executes it.

## Risks and open items

1. **No notarization (accepted).** Ad-hoc-signed apps downloaded from GitHub still carry the
   quarantine bit. Users will get a Gatekeeper prompt and must use System Settings → Privacy &
   Security → "Open Anyway" on first launch. A Developer ID ($99/yr) is the only way to remove
   this. Recommend documenting the workaround prominently in the README.
2. **Minimum macOS rises to 13 (Ventura).** Both the PySide6 and pypdfium2 wheels are tagged
   `macosx_13_0`. This should be stated in the release notes.
3. **Vision offers no PSM/whitelist equivalent.** Tesseract's page-segmentation modes have no
   counterpart. For ordinary documents Vision is generally stronger; for unusual layouts
   results will differ from the current build in ways that are tuned differently, not
   necessarily worse.
4. **Two OCR engines means two output shapes.** The golden tests must tolerate this rather
   than pin exact strings.
5. **Windows/Linux still bundle Tesseract** with the same un-copied-dylib pattern
   (`build.py:232-342`). Out of scope here, but it is the same latent defect and should get
   its own issue.

## Phasing

| Phase | Content | Closes #26? |
|---|---|---|
| 1 | `PageImage`, renderer abstraction, pypdfium2; delete pdf2image/PyPDF2/poppler_utils | Yes — removes the crashing code path |
| 2 | `OcrEngine` abstraction, `VisionOcrEngine`, runtime language list | Removes Tesseract from macOS |
| 3 | `--onedir` `.app`, universal2 lipo, ad-hoc signing, CI smoke test | Makes the artifact launchable |
| 4 | `CFBundleDocumentTypes`, `QEvent.FileOpen`, `NSServices` | Mac-native UX |

Phase 1 alone resolves the reported bug. Phases 2–4 deliver the self-contained, zero-install
app.

## Corrections after implementation

This section records three places where implementation proved this design wrong. The body
above is left as originally written, as a record of what was designed and why; corrections
live here rather than being edited in-place.

1. **universal2 does not reduce to lipo-merging one dylib.** The "2. universal2" section
   above describes fattening `pypdfium2_raw/libpdfium.dylib` and treats that as sufficient.
   In practice, PyInstaller also freezes the *host Python interpreter* into the app, and
   `target_arch="universal2"` fails outright if any collected binary — including that
   interpreter — is thin. Neither Homebrew nor `uv` publish universal2 CPython interpreters
   for Apple Silicon (both ship arm64-only), so a normal local dev venv cannot supply one at
   all. The actual pipeline (see `.github/workflows/build-macos.yml`) installs python.org's
   own `macos11.pkg` installer (universal2 through a release's bugfix-support window) and
   builds the venv from that interpreter specifically — a whole extra CI step this design
   did not anticipate, not just a dylib merge.
2. **Size estimate was off by nearly 2x.** "Expected app size: ~250 MB → ~60 MB" under
   "What this deletes" did not hold up. The actual built bundle is **109 MB** (confirmed via
   `du -sh dist/QuickPdfOcr.app` during Task 11's verification) — still a large reduction
   from the ~250 MB baseline, just not to the ~60 MB this document projected.
3. **The NSServices section understated what "Finder right-click" requires.** "5. Finder
   right-click" above describes only the `Info.plist` `NSServices` declaration
   (`NSSendFileTypes`, the menu item) and does not mention that this is a distinct delivery
   mechanism from `QEvent.FileOpen`. A Cocoa Services invocation never produces a
   `QFileOpenEvent` — it calls the `openFile:userData:error:` selector directly, via
   distributed objects, delivering the selected file on an `NSPasteboard`. Declaring
   `NSServices` in the `Info.plist` alone is not sufficient; the app must also call
   `NSApplication.setServicesProvider_(provider)` with a real Objective-C object implementing
   that selector, or the Services menu item appears in Finder but does nothing when clicked.
   This was missed in the original implementation pass and only caught in code review (see
   `.superpowers/sdd/2026-08-01-macos-native-ocr/task-11-report.md`, "Fix round 2"), which
   added `main.py`'s `_build_services_provider()` / `_register_services_provider()` and the
   `pyobjc-framework-Cocoa` dependency this section's plan never listed.
