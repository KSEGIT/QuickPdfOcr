# Self-Contained macOS App (Vision + pypdfium2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the macOS build of QuickPdfOcr fully self-contained — no Homebrew, no poppler, no Tesseract, no tessdata — so issue #26 cannot recur, and ship it as a Mac-native `.app`.

**Architecture:** Two narrow interfaces behind which platform differences hide. `PdfRenderer` turns a PDF page into a raw `PageImage` buffer (pypdfium2, all platforms). `OcrEngine` turns a `PageImage` into text (Apple Vision on macOS, Tesseract elsewhere). `PdfOcrProcessor` becomes pure orchestration and stops knowing anything about binaries, dylibs, or environment variables.

**Tech Stack:** Python 3.12, PySide6 6.11.x, pypdfium2 5.12.x, pyobjc-framework-Vision / -Quartz 12.2.x (macOS only), pytesseract + Pillow (Windows/Linux only), PyInstaller 6.x, pytest.

## Global Constraints

- **Minimum macOS is 13.0 (Ventura).** Both the PySide6 and pypdfium2 wheels are tagged `macosx_13_0`. Do not add a dependency with a higher floor.
- **Pillow and pytesseract must never be imported on macOS.** They have no universal2 wheels; importing them anywhere in the macOS code path breaks the universal2 build. Import them *inside* `components/ocr/tesseract_engine.py` only, never at module top level of shared code.
- **Poppler is removed from every platform.** No new reference to `pdf2image`, `pdftoppm`, `pdfinfo`, or `poppler` may be introduced.
- **`PyPDF2` is removed.** Page geometry comes from pypdfium2.
- **Never call `page.render()` without both `rev_byteorder=True` and `prefer_bgrx=True`.** pypdfium2 defaults to 24-bit RGB; `CGImageCreate` silently returns a 0×0 image for 24-bit input and Vision then fails with a bare `None` result rather than an exception.
- **Ad-hoc code signing is mandatory, not cosmetic.** `lipo` invalidates signatures and arm64 binaries do not execute unsigned on Apple Silicon. Every build that runs `lipo` must be followed by `codesign --force --deep --sign -`.
- **Tests must run on all three platforms.** Guard macOS-only tests with `@pytest.mark.skipif(sys.platform != "darwin", ...)`.
- Existing code style: 4-space indent, docstrings on public functions, f-strings for interpolation. Match it.

## File Structure

**Created:**

| Path | Responsibility |
|---|---|
| `components/page_image.py` | `PageImage` dataclass — the one type crossing the render→OCR boundary |
| `components/rendering/__init__.py` | `get_renderer()` factory |
| `components/rendering/base.py` | `PdfRenderer` protocol |
| `components/rendering/pdfium_renderer.py` | pypdfium2 implementation, all platforms |
| `components/ocr/__init__.py` | `get_engine()` platform selection + language code mapping |
| `components/ocr/base.py` | `OcrEngine` protocol |
| `components/ocr/vision_engine.py` | Apple Vision implementation, macOS only |
| `components/ocr/tesseract_engine.py` | pytesseract implementation, Windows/Linux |
| `tests/conftest.py` | pytest fixtures |
| `tests/fixtures/sample_invoice.pdf` | committed golden-test input |
| `tests/fixtures/make_fixture.py` | how that PDF was generated (documentation, not run in CI) |
| `tests/test_page_image.py`, `tests/test_pdfium_renderer.py`, `tests/test_ocr_engines.py`, `tests/test_pdf_ocr.py` | test suites |
| `packaging/quickpdfocr.spec` | PyInstaller spec file (replaces CLI-flag build) |
| `packaging/prepare_universal_deps.py` | lipo-merges pdfium and other universal2 dependencies |
| `packaging/verify_universal.py` | checks universal2 binary architecture and ad-hoc signs the app |

**Modified:** `components/pdf_ocr.py`, `components/ocr_worker.py`, `ui/main_window.py`, `main.py`, `build.py`, `requirements.txt`, `.github/workflows/build-macos.yml`, `README.md`, `THIRD_PARTY_LICENSES.md`

**Deleted:** `components/poppler_utils.py`, `test_bundled_deps.py`, `test_tessdata_path.py`, `docs/OCR_ERROR_FIX.md`

---

## Phase 1 — Renderer abstraction (closes #26)

### Task 1: Test infrastructure and the `PageImage` boundary type

**Files:**
- Create: `components/page_image.py`
- Create: `tests/__init__.py` (empty), `tests/conftest.py`, `tests/fixtures/make_fixture.py`, `tests/fixtures/sample_invoice.pdf`
- Create: `tests/test_page_image.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `PageImage(width: int, height: int, stride: int, buffer: bytes, mode: str)` — frozen dataclass with property `expected_size: int` returning `stride * height`, and `__post_init__` validation. Every later task uses this type as the render→OCR boundary.

- [ ] **Step 1: Add the new dependencies**

Replace `requirements.txt` entirely with:

```
# Core GUI
PySide6>=6.6.0

# PDF rendering — self-contained wheel, no system binaries
pypdfium2>=5.12.0

# macOS: native OCR via Apple Vision (no Tesseract, no tessdata)
pyobjc-framework-Vision>=12.0; sys_platform == 'darwin'
pyobjc-framework-Quartz>=12.0; sys_platform == 'darwin'

# Windows/Linux: Tesseract OCR
pytesseract>=0.3.10; sys_platform != 'darwin'
Pillow>=10.0.0; sys_platform != 'darwin'

# Build + test
pyinstaller>=6.0.0
pytest>=8.0.0
```

Note what left: `pdf2image` and `PyPDF2` are gone, and `Pillow`/`pytesseract` are now
platform-conditional.

- [ ] **Step 2: Write the failing test**

Create `tests/test_page_image.py`:

```python
"""Tests for the PageImage boundary type."""

import pytest

from components.page_image import PageImage


def test_page_image_holds_raw_buffer():
    """PageImage carries raw pixel bytes, not a library-specific image object."""
    page = PageImage(width=2, height=2, stride=8, buffer=b"\x00" * 16, mode="RGBX")

    assert page.width == 2
    assert page.height == 2
    assert page.stride == 8
    assert page.mode == "RGBX"
    assert isinstance(page.buffer, bytes)


def test_expected_size_is_stride_times_height():
    page = PageImage(width=2, height=2, stride=8, buffer=b"\x00" * 16, mode="RGBX")

    assert page.expected_size == 16


def test_rejects_buffer_that_does_not_match_stride_and_height():
    """A short buffer means a rendering bug; fail loudly rather than hand
    CoreGraphics a truncated image that it renders as garbage."""
    with pytest.raises(ValueError, match="buffer size"):
        PageImage(width=2, height=2, stride=8, buffer=b"\x00" * 15, mode="RGBX")


def test_rejects_unsupported_mode():
    """Only 4-byte RGBX is supported; 24-bit RGB silently produces a 0x0
    CGImage on macOS, so reject it at the boundary."""
    with pytest.raises(ValueError, match="mode"):
        PageImage(width=2, height=2, stride=6, buffer=b"\x00" * 12, mode="RGB")


def test_is_immutable():
    page = PageImage(width=2, height=2, stride=8, buffer=b"\x00" * 16, mode="RGBX")

    with pytest.raises(Exception):
        page.width = 5
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest tests/test_page_image.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'components.page_image'`

- [ ] **Step 4: Write the implementation**

Create `components/page_image.py`:

```python
#!/usr/bin/env python3
"""The single data type that crosses the rendering -> OCR boundary.

Deliberately a raw buffer rather than a PIL image: on macOS neither Pillow nor
pytesseract is installed, so nothing here may depend on them.
"""

from dataclasses import dataclass

# Only 4-byte-per-pixel RGBX is supported. CoreGraphics cannot build a CGImage
# from 24-bit RGB -- it returns a 0x0 image and Vision then fails with a bare
# None result rather than an error, which is very hard to debug.
SUPPORTED_MODES = ("RGBX",)


@dataclass(frozen=True)
class PageImage:
    """One rasterized PDF page.

    Attributes:
        width: Pixel width.
        height: Pixel height.
        stride: Bytes per row. May exceed width * 4 due to row padding.
        buffer: Raw pixel bytes, stride * height long.
        mode: Pixel format; see SUPPORTED_MODES.
    """

    width: int
    height: int
    stride: int
    buffer: bytes
    mode: str

    def __post_init__(self):
        if self.mode not in SUPPORTED_MODES:
            raise ValueError(
                f"Unsupported mode {self.mode!r}; expected one of {SUPPORTED_MODES}"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"Invalid dimensions {self.width}x{self.height}; both must be positive"
            )
        if len(self.buffer) != self.expected_size:
            raise ValueError(
                f"buffer size {len(self.buffer)} does not match "
                f"stride {self.stride} * height {self.height} = {self.expected_size}"
            )

    @property
    def expected_size(self) -> int:
        """Number of bytes a correctly sized buffer holds."""
        return self.stride * self.height
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m pytest tests/test_page_image.py -v`
Expected: PASS, 5 passed

- [ ] **Step 6: Create the test fixture PDF**

Create `tests/fixtures/make_fixture.py`. This documents how the committed PDF was
produced; it is not run by CI and only works on macOS.

```python
#!/usr/bin/env python3
"""Regenerate tests/fixtures/sample_invoice.pdf. macOS only; run manually.

    python tests/fixtures/make_fixture.py

The content deliberately mirrors issue #26: a Polish invoice, which exercises
non-ASCII-adjacent text and the pl-PL recognition language.
"""

from pathlib import Path

import Quartz
from Foundation import NSURL

LINES = [
    b"FAKTURA VAT PL6972514",
    b"Kwota brutto: 1234,56 PLN",
    b"NIP 527-10-26-863",
    b"Termin platnosci: 2026-08-14",
]

out = Path(__file__).parent / "sample_invoice.pdf"
url = NSURL.fileURLWithPath_(str(out))
ctx = Quartz.CGPDFContextCreateWithURL(url, Quartz.CGRectMake(0, 0, 595, 842), None)
Quartz.CGPDFContextBeginPage(ctx, None)
Quartz.CGContextSelectFont(ctx, b"Helvetica", 24.0, Quartz.kCGEncodingMacRoman)
Quartz.CGContextSetTextDrawingMode(ctx, Quartz.kCGTextFill)
for i, line in enumerate(LINES):
    Quartz.CGContextShowTextAtPoint(ctx, 60, 700 - i * 40, line, len(line))
Quartz.CGPDFContextEndPage(ctx)
Quartz.CGPDFContextClose(ctx)
print(f"wrote {out}")
```

Run it to produce the fixture:

```bash
python tests/fixtures/make_fixture.py
```

Verify the file exists and is a real PDF:

```bash
file tests/fixtures/sample_invoice.pdf
```

Expected: `tests/fixtures/sample_invoice.pdf: PDF document, version 1.x`

- [ ] **Step 7: Write the shared fixtures**

Create `tests/conftest.py`:

```python
"""Shared pytest fixtures."""

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"

# Strings the fixture PDF is known to contain. Used for golden assertions that
# tolerate engine-specific differences -- Vision and Tesseract will not agree
# character for character, so never assert on the full extracted text.
EXPECTED_SUBSTRINGS = ["FAKTURA", "1234,56", "527-10-26-863"]


@pytest.fixture
def sample_pdf() -> Path:
    """Path to the committed single-page Polish invoice fixture."""
    path = FIXTURE_DIR / "sample_invoice.pdf"
    if not path.exists():
        pytest.skip(f"fixture missing: {path}; run tests/fixtures/make_fixture.py")
    return path
```

Also create an empty `tests/__init__.py`.

- [ ] **Step 8: Commit**

```bash
git add requirements.txt components/page_image.py tests/
git commit -m "feat: add PageImage boundary type and pytest infrastructure

Introduces the raw-buffer type that will cross the render->OCR boundary,
deliberately avoiding PIL so macOS never imports Pillow. Adds the test
fixture PDF mirroring issue #26's Polish invoice."
```

---

### Task 2: pypdfium2 renderer

**Files:**
- Create: `components/rendering/__init__.py`, `components/rendering/base.py`, `components/rendering/pdfium_renderer.py`
- Create: `tests/test_pdfium_renderer.py`

**Interfaces:**
- Consumes: `PageImage` from Task 1.
- Produces:
  - `PdfRenderer` protocol with `page_count() -> int`, `page_size_inches(index: int) -> tuple[float, float]`, `render_page(index: int, dpi: int) -> PageImage`, `close() -> None`.
  - `PdfiumRenderer(pdf_path: str | Path)` implementing it, usable as a context manager.
  - `get_renderer(pdf_path) -> PdfRenderer` from `components.rendering`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_pdfium_renderer.py`:

```python
"""Tests for the pypdfium2-backed renderer."""

import pytest

from components.page_image import PageImage
from components.rendering import get_renderer
from components.rendering.pdfium_renderer import PdfiumRenderer


def test_reports_page_count(sample_pdf):
    with PdfiumRenderer(sample_pdf) as renderer:
        assert renderer.page_count() == 1


def test_reports_page_size_in_inches(sample_pdf):
    """A4 is 595x842 points; at 72 points/inch that is ~8.27 x 11.69 inches."""
    with PdfiumRenderer(sample_pdf) as renderer:
        width, height = renderer.page_size_inches(0)

    assert width == pytest.approx(8.27, abs=0.05)
    assert height == pytest.approx(11.69, abs=0.05)


def test_renders_page_at_requested_dpi(sample_pdf):
    """595 points wide at 300 DPI is 595/72*300 = 2479.2 -> 2480 px."""
    with PdfiumRenderer(sample_pdf) as renderer:
        page = renderer.render_page(0, dpi=300)

    assert isinstance(page, PageImage)
    assert page.width == pytest.approx(2480, abs=2)
    assert page.height == pytest.approx(3509, abs=2)


def test_renders_four_byte_pixels(sample_pdf):
    """24-bit output silently breaks CoreGraphics; the renderer must force RGBX."""
    with PdfiumRenderer(sample_pdf) as renderer:
        page = renderer.render_page(0, dpi=72)

    assert page.mode == "RGBX"
    assert page.stride >= page.width * 4


def test_lower_dpi_produces_smaller_image(sample_pdf):
    with PdfiumRenderer(sample_pdf) as renderer:
        small = renderer.render_page(0, dpi=72)
        large = renderer.render_page(0, dpi=144)

    assert large.width > small.width


def test_rejects_out_of_range_page_index(sample_pdf):
    with PdfiumRenderer(sample_pdf) as renderer:
        with pytest.raises(IndexError):
            renderer.render_page(99, dpi=72)


def test_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        PdfiumRenderer(tmp_path / "nope.pdf")


def test_factory_returns_a_renderer(sample_pdf):
    with get_renderer(sample_pdf) as renderer:
        assert renderer.page_count() == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_pdfium_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'components.rendering'`

- [ ] **Step 3: Write the protocol**

Create `components/rendering/base.py`:

```python
#!/usr/bin/env python3
"""The rendering interface. One job: PDF page -> raw pixels."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from components.page_image import PageImage


@runtime_checkable
class PdfRenderer(Protocol):
    """Rasterizes pages of a single PDF document."""

    def page_count(self) -> int:
        """Number of pages in the document."""
        ...

    def page_size_inches(self, index: int) -> tuple[float, float]:
        """(width, height) of a page in inches, used for DPI auto-detection."""
        ...

    def render_page(self, index: int, dpi: int) -> PageImage:
        """Rasterize one page at the given resolution."""
        ...

    def close(self) -> None:
        """Release the underlying document."""
        ...

    def __enter__(self) -> "PdfRenderer":
        """Renderers are context managers; callers should prefer `with`."""
        ...

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        ...
```

- [ ] **Step 4: Write the implementation**

Create `components/rendering/pdfium_renderer.py`:

```python
#!/usr/bin/env python3
"""PDF rendering via pypdfium2.

pypdfium2 ships PDFium inside the wheel, so there is no external binary and no
dynamic library to locate at runtime. This is what replaced poppler, whose
Homebrew binaries linked 24 uncopied dylibs by @rpath and produced issue #26.
"""

from pathlib import Path

import pypdfium2 as pdfium

from components.page_image import PageImage

# 1 PDF canvas unit is 1/72 inch.
POINTS_PER_INCH = 72


class PdfiumRenderer:
    """Renders pages of one PDF document. Works on macOS, Windows and Linux."""

    def __init__(self, pdf_path):
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        self._path = path
        self._doc = pdfium.PdfDocument(str(path))

    def __enter__(self) -> "PdfiumRenderer":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def page_count(self) -> int:
        """Number of pages in the document."""
        return len(self._doc)

    def page_size_inches(self, index: int) -> tuple[float, float]:
        """(width, height) of a page in inches."""
        self._check_index(index)
        width_points, height_points = self._doc[index].get_size()
        return width_points / POINTS_PER_INCH, height_points / POINTS_PER_INCH

    def render_page(self, index: int, dpi: int) -> PageImage:
        """Rasterize one page to a 4-byte-per-pixel RGBX buffer.

        Both render flags are load-bearing. prefer_bgrx forces 4-byte pixels,
        without which pypdfium2 emits 24-bit RGB and CoreGraphics builds a 0x0
        image. rev_byteorder gives RGBx rather than BGRx byte order.
        """
        self._check_index(index)
        bitmap = self._doc[index].render(
            scale=dpi / POINTS_PER_INCH,
            rev_byteorder=True,
            prefer_bgrx=True,
        )
        return PageImage(
            width=bitmap.width,
            height=bitmap.height,
            stride=bitmap.stride,
            buffer=bytes(bitmap.buffer),
            mode="RGBX",
        )

    def close(self) -> None:
        """Release the underlying document."""
        self._doc.close()

    def _check_index(self, index: int) -> None:
        if not 0 <= index < len(self._doc):
            raise IndexError(
                f"Page index {index} out of range for {self._path.name} "
                f"({len(self._doc)} page(s))"
            )
```

Create `components/rendering/__init__.py`:

```python
#!/usr/bin/env python3
"""Rendering backend selection."""

from components.rendering.base import PdfRenderer
from components.rendering.pdfium_renderer import PdfiumRenderer

__all__ = ["PdfRenderer", "PdfiumRenderer", "get_renderer"]


def get_renderer(pdf_path) -> PdfRenderer:
    """Return a renderer for the given PDF.

    pypdfium2 works identically on every supported platform, so unlike
    get_engine() this makes no platform decision. It exists so callers depend
    on the interface rather than the concrete class.
    """
    return PdfiumRenderer(pdf_path)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_pdfium_renderer.py -v`
Expected: PASS, 8 passed

- [ ] **Step 6: Commit**

```bash
git add components/rendering/ tests/test_pdfium_renderer.py
git commit -m "feat: add pypdfium2 renderer behind a PdfRenderer interface

Replaces poppler's pdftoppm/pdfinfo with a self-contained wheel. Forces
4-byte RGBX output, which CoreGraphics requires and pypdfium2 does not
produce by default."
```

---

### Task 3: OCR engine interface and the Tesseract engine

**Files:**
- Create: `components/ocr/base.py`, `components/ocr/tesseract_engine.py`
- Create: `tests/test_ocr_engines.py`

**Interfaces:**
- Consumes: `PageImage` from Task 1.
- Produces:
  - `OcrEngine` protocol: `name: str` property, `supported_languages() -> list[str]`, `default_languages() -> list[str]`, `recognize(page: PageImage, languages: list[str] | None = None) -> str`.
  - `TesseractOcrEngine()` implementing it. Language codes are ISO 639-2 (`eng`, `pol`).
- Task 5 adds `VisionOcrEngine` against this same protocol; Task 6 adds the factory.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ocr_engines.py`. The shared-contract test class is the point —
Task 5 subclasses it so both engines are held to identical behaviour.

```python
"""Tests for OCR engines.

EngineContractTests is subclassed once per engine so both are held to the same
contract. Assertions are substring-based on purpose: Vision and Tesseract will
never agree character for character.
"""

import sys

import pytest

from components.ocr.base import OcrEngine
from components.rendering import get_renderer
from tests.conftest import EXPECTED_SUBSTRINGS


class EngineContractTests:
    """Shared contract. Subclasses set `engine_factory`."""

    engine_factory = None

    @pytest.fixture
    def engine(self):
        return self.engine_factory()

    def test_satisfies_the_protocol(self, engine):
        assert isinstance(engine, OcrEngine)

    def test_has_a_name(self, engine):
        assert isinstance(engine.name, str)
        assert engine.name

    def test_reports_supported_languages(self, engine):
        languages = engine.supported_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0
        assert all(isinstance(code, str) for code in languages)

    def test_default_languages_are_supported(self, engine):
        supported = set(engine.supported_languages())

        assert set(engine.default_languages()) <= supported

    def test_recognizes_text_from_the_fixture(self, engine, sample_pdf):
        with get_renderer(sample_pdf) as renderer:
            page = renderer.render_page(0, dpi=300)

        text = engine.recognize(page)

        for expected in EXPECTED_SUBSTRINGS:
            assert expected in text, f"{expected!r} missing from: {text!r}"

    def test_returns_a_string_for_a_blank_page(self, engine):
        from components.page_image import PageImage

        blank = PageImage(
            width=100, height=100, stride=400, buffer=b"\xff" * 40000, mode="RGBX"
        )

        assert isinstance(engine.recognize(blank), str)


@pytest.mark.skipif(
    sys.platform == "darwin", reason="Tesseract is not installed on macOS builds"
)
class TestTesseractEngine(EngineContractTests):
    @staticmethod
    def engine_factory():
        from components.ocr.tesseract_engine import TesseractOcrEngine

        return TesseractOcrEngine()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ocr_engines.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'components.ocr'`

(On macOS the Tesseract class is skipped; the collection error still fails the run,
which is the failure we want to see.)

- [ ] **Step 3: Write the protocol**

Create `components/ocr/base.py`:

```python
#!/usr/bin/env python3
"""The OCR interface. One job: raw pixels -> text."""

from typing import Protocol, runtime_checkable

from components.page_image import PageImage


@runtime_checkable
class OcrEngine(Protocol):
    """Recognizes text in a rasterized page.

    Language codes are engine-specific: Tesseract uses ISO 639-2 ('eng'),
    Vision uses BCP-47 ('en-US'). Callers should treat the strings returned by
    supported_languages() as opaque and pass them straight back to recognize().
    """

    @property
    def name(self) -> str:
        """Human-readable engine name, shown in the UI."""
        ...

    def supported_languages(self) -> list[str]:
        """Language codes this engine can recognize, in engine-native form."""
        ...

    def default_languages(self) -> list[str]:
        """Languages to use when the caller expresses no preference."""
        ...

    def recognize(self, page: PageImage, languages: list[str] | None = None) -> str:
        """Extract text from one page. Returns '' when nothing is found."""
        ...
```

- [ ] **Step 4: Write the Tesseract engine**

Create `components/ocr/tesseract_engine.py`. Note that Pillow and pytesseract
are imported at module level here and **only** here — this module is never
imported on macOS.

```python
#!/usr/bin/env python3
"""OCR via Tesseract. Windows and Linux only.

macOS uses components/ocr/vision_engine.py instead, which is why Pillow and
pytesseract may be imported at module level here: this file is never reached on
darwin. Keep it that way -- neither package publishes universal2 wheels.
"""

from PIL import Image
import pytesseract

from components.page_image import PageImage

DEFAULT_LANGUAGES = ["eng"]

# Fallback list used when Tesseract cannot be queried (e.g. not yet installed
# during a packaging step). Keeps the UI populated rather than empty.
FALLBACK_LANGUAGES = ["eng"]


class TesseractOcrEngine:
    """Tesseract-backed OCR. Language codes are ISO 639-2, e.g. 'eng', 'pol'."""

    @property
    def name(self) -> str:
        return "Tesseract"

    def supported_languages(self) -> list[str]:
        """Languages for which a .traineddata file is installed."""
        try:
            languages = list(pytesseract.get_languages(config=""))
        except Exception:
            return list(FALLBACK_LANGUAGES)
        # 'osd' is orientation/script detection, not a text language.
        languages = sorted(code for code in languages if code != "osd")
        return languages or list(FALLBACK_LANGUAGES)

    def default_languages(self) -> list[str]:
        supported = set(self.supported_languages())
        chosen = [code for code in DEFAULT_LANGUAGES if code in supported]
        return chosen or self.supported_languages()[:1]

    def recognize(self, page: PageImage, languages: list[str] | None = None) -> str:
        """Extract text from one page."""
        codes = languages or self.default_languages()
        image = Image.frombuffer(
            "RGBX",
            (page.width, page.height),
            page.buffer,
            "raw",
            "RGBX",
            page.stride,
            1,
        ).convert("RGB")
        return pytesseract.image_to_string(image, lang="+".join(codes))
```

Create `components/ocr/__init__.py` as a stub for now — Task 6 fills it in:

```python
#!/usr/bin/env python3
"""OCR backend selection."""

from components.ocr.base import OcrEngine

__all__ = ["OcrEngine"]
```

- [ ] **Step 5: Run the tests**

On Windows/Linux, run: `python -m pytest tests/test_ocr_engines.py -v`
Expected: PASS, 6 passed

On macOS, run: `python -m pytest tests/test_ocr_engines.py -v`
Expected: 6 skipped (`Tesseract is not installed on macOS builds`), 0 failed.
The suite must **collect** cleanly — that is what this step verifies on macOS.

- [ ] **Step 6: Commit**

```bash
git add components/ocr/ tests/test_ocr_engines.py
git commit -m "feat: add OcrEngine interface and Tesseract implementation

Pillow and pytesseract are imported only inside tesseract_engine, which is
never loaded on macOS -- neither ships universal2 wheels."
```

---

### Task 4: Rewire `PdfOcrProcessor` onto the two interfaces

**Files:**
- Modify: `components/pdf_ocr.py` (rewrite; currently 323 lines)
- Create: `tests/test_pdf_ocr.py`

**Interfaces:**
- Consumes: `get_renderer` (Task 2), `OcrEngine` (Task 3).
- Produces: `PdfOcrProcessor(engine: OcrEngine | None = None, languages: list[str] | None = None)` with `process(pdf_path, output_file=None, dpi=None, progress_callback=None) -> str` and `detect_optimal_dpi(pdf_path) -> int`. The `engine` parameter is dependency injection for tests; production callers leave it `None` and get the platform default from Task 6.

- [ ] **Step 1: Write the failing test**

Create `tests/test_pdf_ocr.py`:

```python
"""Tests for the OCR orchestration layer."""

import pytest

from components.page_image import PageImage
from components.pdf_ocr import PdfOcrProcessor


class FakeEngine:
    """Records what it was asked to recognize, returns canned text."""

    def __init__(self, text="fake text"):
        self.text = text
        self.calls = []

    @property
    def name(self) -> str:
        return "Fake"

    def supported_languages(self) -> list[str]:
        return ["xx", "yy"]

    def default_languages(self) -> list[str]:
        return ["xx"]

    def recognize(self, page: PageImage, languages=None) -> str:
        self.calls.append((page, languages))
        return self.text


def test_extracts_text_from_every_page(sample_pdf):
    engine = FakeEngine("hello")
    processor = PdfOcrProcessor(engine=engine)

    text = processor.process(sample_pdf)

    assert len(engine.calls) == 1
    assert "hello" in text


def test_labels_each_page(sample_pdf):
    processor = PdfOcrProcessor(engine=FakeEngine("body"))

    text = processor.process(sample_pdf)

    assert "--- Page 1 ---" in text


def test_passes_configured_languages_to_the_engine(sample_pdf):
    engine = FakeEngine()
    processor = PdfOcrProcessor(engine=engine, languages=["yy"])

    processor.process(sample_pdf)

    _page, languages = engine.calls[0]
    assert languages == ["yy"]


def test_reports_progress_per_page(sample_pdf):
    messages = []
    processor = PdfOcrProcessor(engine=FakeEngine())

    processor.process(sample_pdf, progress_callback=messages.append)

    assert any("page 1" in m.lower() for m in messages)


def test_writes_output_file_when_requested(sample_pdf, tmp_path):
    out = tmp_path / "out.txt"
    processor = PdfOcrProcessor(engine=FakeEngine("written"))

    processor.process(sample_pdf, output_file=out)

    assert "written" in out.read_text(encoding="utf-8")


def test_detects_250_dpi_for_a4(sample_pdf):
    """A4's long edge is 11.69in, which falls in the 10-14in band -> 250 DPI."""
    processor = PdfOcrProcessor(engine=FakeEngine())

    assert processor.detect_optimal_dpi(sample_pdf) == 250


def test_rejects_a_missing_file(tmp_path):
    processor = PdfOcrProcessor(engine=FakeEngine())

    with pytest.raises(FileNotFoundError):
        processor.process(tmp_path / "nope.pdf")


def test_rejects_a_non_pdf(tmp_path):
    other = tmp_path / "notes.txt"
    other.write_text("hi")
    processor = PdfOcrProcessor(engine=FakeEngine())

    with pytest.raises(ValueError, match="must be a PDF"):
        processor.process(other)


def test_one_failing_page_does_not_abort_the_document(sample_pdf):
    class ExplodingEngine(FakeEngine):
        def recognize(self, page, languages=None):
            raise RuntimeError("boom")

    processor = PdfOcrProcessor(engine=ExplodingEngine())

    text = processor.process(sample_pdf)

    assert "OCR Error" in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_pdf_ocr.py -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'engine'`

- [ ] **Step 3: Rewrite the implementation**

Replace `components/pdf_ocr.py` entirely:

```python
#!/usr/bin/env python3
"""PDF OCR orchestration.

Deliberately knows nothing about binaries, dylibs, PATH, or TESSDATA_PREFIX.
It renders pages through a PdfRenderer and recognizes them through an
OcrEngine; which concrete implementations those are is decided in
components/rendering/__init__.py and components/ocr/__init__.py.
"""

import sys
from pathlib import Path
from typing import Callable, Optional

from components.ocr.base import OcrEngine
from components.rendering import get_renderer

# DPI bands keyed on the page's longest edge in inches. Small pages (receipts)
# need more pixels per inch to resolve small type; very large pages do not.
DPI_BANDS = (
    (6, 400, "small document detected"),
    (10, 300, "standard document size"),
    (14, 250, "large document detected"),
)
FALLBACK_DPI = 200
DEFAULT_DPI = 300


class PdfOcrProcessor:
    """Extracts text from a PDF, one page at a time."""

    def __init__(
        self,
        engine: Optional[OcrEngine] = None,
        languages: Optional[list[str]] = None,
    ):
        """
        Args:
            engine: OCR backend. Defaults to the platform's engine.
            languages: Engine-native language codes. Defaults to the engine's own.
        """
        if engine is None:
            from components.ocr import get_engine

            engine = get_engine()
        self.engine = engine
        self.languages = languages
        self.dpi = None

    def detect_optimal_dpi(self, pdf_path) -> int:
        """Pick a rendering resolution from the first page's physical size."""
        try:
            with get_renderer(pdf_path) as renderer:
                if renderer.page_count() == 0:
                    return DEFAULT_DPI
                width_in, height_in = renderer.page_size_inches(0)
        except Exception as exc:
            print(f"Warning: could not auto-detect DPI ({exc}), using {DEFAULT_DPI}")
            return DEFAULT_DPI

        longest_edge = max(width_in, height_in)
        for limit, dpi, reason in DPI_BANDS:
            if longest_edge < limit:
                print(f"Auto-detected DPI: {dpi} ({reason})")
                print(f'  Page size: {width_in:.1f}" x {height_in:.1f}"')
                return dpi

        print(f"Auto-detected DPI: {FALLBACK_DPI} (very large document detected)")
        return FALLBACK_DPI

    def process(
        self,
        pdf_path,
        output_file: Optional[str] = None,
        dpi: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Extract text from every page of a PDF.

        Args:
            pdf_path: Path to the PDF.
            output_file: If given, the extracted text is also written here.
            dpi: Rendering resolution. Auto-detected when None.
            progress_callback: Called with a status string per page.

        Returns:
            The extracted text, with a '--- Page N ---' header per page.

        Raises:
            FileNotFoundError: The PDF does not exist.
            ValueError: The path is not a PDF.
            RuntimeError: The document could not be opened.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF: {pdf_path}")

        self._log(f"Processing PDF: {pdf_path.name}", progress_callback)

        if dpi is None:
            dpi = self.detect_optimal_dpi(pdf_path)
        self.dpi = dpi

        try:
            renderer = get_renderer(pdf_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to open PDF: {exc}") from exc

        try:
            total = renderer.page_count()
            self._log(f"Found {total} page(s)", progress_callback)

            sections = []
            for index in range(total):
                self._log(f"Processing page {index + 1}/{total}...", progress_callback)
                sections.append(self._process_page(renderer, index, dpi))
        finally:
            renderer.close()

        final_text = "\n".join(sections)

        if output_file:
            output_path = Path(output_file)
            output_path.write_text(final_text, encoding="utf-8")
            self._log(f"Text extracted and saved to: {output_path}", progress_callback)

        return final_text

    def _process_page(self, renderer, index: int, dpi: int) -> str:
        """Render and recognize one page. A page-level failure is recorded in
        the output rather than aborting the whole document."""
        try:
            page = renderer.render_page(index, dpi=dpi)
            text = self.engine.recognize(page, languages=self.languages)
        except Exception as exc:
            print(f"Warning: failed to process page {index + 1}: {exc}")
            return f"--- Page {index + 1} ---\n[OCR Error: {exc}]\n"
        return f"--- Page {index + 1} ---\n{text}\n"

    def _log(self, message: str, callback: Optional[Callable[[str], None]] = None):
        """Report progress via the callback if given, else stdout."""
        if callback:
            callback(message)
        else:
            print(message)


def ocr_pdf(pdf_path, output_file=None, dpi=None, languages=None) -> str:
    """Convenience wrapper for command-line use."""
    processor = PdfOcrProcessor(languages=languages)
    final_text = processor.process(pdf_path, output_file=output_file, dpi=dpi)

    if not output_file:
        print("\n" + "=" * 60)
        print("EXTRACTED TEXT:")
        print("=" * 60)
        print(final_text)

    return final_text


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_ocr.py <pdf_file> [output_file] [--dpi DPI] [--lang LANG]")
        print("\nExamples:")
        print("  python pdf_ocr.py document.pdf")
        print("  python pdf_ocr.py document.pdf output.txt --dpi 400")
        print("  python pdf_ocr.py document.pdf --lang pl-PL   # macOS (Vision)")
        print("  python pdf_ocr.py document.pdf --lang pol      # Windows/Linux")
        print("\nDPI is auto-detected by default based on page size.")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_file = None
    dpi = None
    languages = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--dpi" and i + 1 < len(sys.argv):
            dpi = int(sys.argv[i + 1])
            i += 2
        elif arg == "--lang" and i + 1 < len(sys.argv):
            languages = sys.argv[i + 1].split("+")
            i += 2
        elif not arg.startswith("--"):
            output_file = arg
            i += 1
        else:
            i += 1

    try:
        ocr_pdf(pdf_path, output_file, dpi=dpi, languages=languages)
        print("\n[OK] OCR completed successfully!")
    except Exception as exc:
        print(f"\n[FAIL] Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_pdf_ocr.py -v`
Expected: PASS, 9 passed

- [ ] **Step 5: Run the whole suite for regressions**

Run: `python -m pytest tests/ -v`
Expected: all pass (Tesseract contract tests skipped on macOS)

- [ ] **Step 6: Commit**

```bash
git add components/pdf_ocr.py tests/test_pdf_ocr.py
git commit -m "refactor: drive PdfOcrProcessor through renderer and engine interfaces

Drops pdf2image and PyPDF2. Page geometry now comes from pypdfium2, and
all tessdata/TESSDATA_PREFIX handling is gone from the orchestration layer.
Closes the code path that produced issue #26."
```

---

## Phase 2 — Vision engine on macOS

### Task 5: Apple Vision OCR engine

**Files:**
- Create: `components/ocr/vision_engine.py`
- Modify: `tests/test_ocr_engines.py` (append a subclass)

**Interfaces:**
- Consumes: `PageImage` (Task 1), `OcrEngine` protocol (Task 3).
- Produces: `VisionOcrEngine()` implementing `OcrEngine`. Language codes are BCP-47 (`en-US`, `pl-PL`). Also exports `page_image_to_cgimage(page: PageImage)` for reuse.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ocr_engines.py`:

```python
@pytest.mark.skipif(sys.platform != "darwin", reason="Vision is macOS-only")
class TestVisionEngine(EngineContractTests):
    @staticmethod
    def engine_factory():
        from components.ocr.vision_engine import VisionOcrEngine

        return VisionOcrEngine()

    def test_supports_polish(self, engine):
        """Issue #26's document is a Polish invoice."""
        assert "pl-PL" in engine.supported_languages()

    def test_language_codes_are_bcp47(self, engine):
        assert all("-" in code for code in engine.supported_languages())

    def test_orders_lines_top_to_bottom(self, engine, sample_pdf):
        """Vision returns observations in no guaranteed order; the engine must
        sort them, or multi-line documents come out scrambled."""
        from components.rendering import get_renderer

        with get_renderer(sample_pdf) as renderer:
            page = renderer.render_page(0, dpi=300)

        text = engine.recognize(page)

        assert text.index("FAKTURA") < text.index("1234,56")
        assert text.index("1234,56") < text.index("527-10-26-863")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ocr_engines.py -v -k Vision`
Expected: FAIL — `ModuleNotFoundError: No module named 'components.ocr.vision_engine'`

- [ ] **Step 3: Write the implementation**

Create `components/ocr/vision_engine.py`:

```python
#!/usr/bin/env python3
"""OCR via Apple's Vision framework. macOS only.

Vision ships with the OS, so there is no binary to bundle, no dylib to
re-point, and no .traineddata to install. This is what replaced Tesseract on
macOS and, together with pypdfium2, is why the app no longer needs Homebrew.

Do not import Pillow or pytesseract here -- neither is installed on macOS.
"""

import Quartz
import Vision

from components.page_image import PageImage

# Preferred when the caller expresses no preference. Vision accepts several
# languages at once and picks per text region, so listing more than one costs
# little and handles mixed-language documents.
DEFAULT_LANGUAGES = ["en-US", "pl-PL", "de-DE", "fr-FR"]

# Used if the OS query fails, which should not happen on a supported system.
FALLBACK_LANGUAGES = ["en-US"]


def page_image_to_cgimage(page: PageImage):
    """Wrap a PageImage's raw buffer in a CGImage.

    Requires 4-byte pixels. CoreGraphics cannot consume 24-bit RGB: it returns
    a 0x0 image, and Vision then reports failure with a None result rather than
    raising. PageImage rejects non-RGBX modes to make that unrepresentable.
    """
    provider = Quartz.CGDataProviderCreateWithData(
        None, page.buffer, len(page.buffer), None
    )
    color_space = Quartz.CGColorSpaceCreateDeviceRGB()
    cgimage = Quartz.CGImageCreate(
        page.width,
        page.height,
        8,   # bits per component
        32,  # bits per pixel
        page.stride,
        color_space,
        Quartz.kCGImageAlphaNoneSkipLast | Quartz.kCGBitmapByteOrderDefault,
        provider,
        None,
        False,
        Quartz.kCGRenderingIntentDefault,
    )
    if cgimage is None or Quartz.CGImageGetWidth(cgimage) == 0:
        raise RuntimeError(
            f"CoreGraphics rejected a {page.width}x{page.height} "
            f"{page.mode} buffer with stride {page.stride}"
        )
    return cgimage


class VisionOcrEngine:
    """Vision-backed OCR. Language codes are BCP-47, e.g. 'en-US', 'pl-PL'."""

    @property
    def name(self) -> str:
        return "Apple Vision"

    def supported_languages(self) -> list[str]:
        """Recognition languages this macOS version provides.

        The list grows with the OS, so it is queried rather than hardcoded --
        macOS 13 offers fewer than macOS 26's 30.
        """
        request = Vision.VNRecognizeTextRequest.alloc().init()
        result = request.supportedRecognitionLanguagesAndReturnError_(None)
        languages = result[0] if result and result[0] else None
        return list(languages) if languages else list(FALLBACK_LANGUAGES)

    def default_languages(self) -> list[str]:
        supported = set(self.supported_languages())
        chosen = [code for code in DEFAULT_LANGUAGES if code in supported]
        return chosen or self.supported_languages()[:1]

    def recognize(self, page: PageImage, languages=None) -> str:
        """Extract text from one page, in top-to-bottom reading order."""
        codes = languages or self.default_languages()
        cgimage = page_image_to_cgimage(page)

        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
            cgimage, None
        )
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setRecognitionLanguages_(codes)
        request.setUsesLanguageCorrection_(True)

        succeeded, error = handler.performRequests_error_([request], None)
        if not succeeded:
            raise RuntimeError(f"Vision text recognition failed: {error}")

        observations = request.results()
        if not observations:
            return ""

        return "\n".join(self._read_in_order(observations))

    @staticmethod
    def _read_in_order(observations) -> list[str]:
        """Sort observations into reading order and take the best candidate.

        Vision does not guarantee ordering. Bounding boxes are normalized with
        the origin at the bottom-left, so descending y is top-to-bottom.
        """
        def position(observation):
            box = observation.boundingBox()
            return -box.origin.y, box.origin.x

        lines = []
        for observation in sorted(observations, key=position):
            candidates = observation.topCandidates_(1)
            if candidates:
                lines.append(candidates[0].string())
        return lines
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ocr_engines.py -v -k Vision`
Expected: PASS, 9 passed

- [ ] **Step 5: Confirm no Pillow leaked into the macOS path**

Run:

```bash
python -c "
import sys
from components.ocr.vision_engine import VisionOcrEngine
from components.rendering import get_renderer
from components.pdf_ocr import PdfOcrProcessor
assert 'PIL' not in sys.modules, 'Pillow was imported on macOS'
assert 'pytesseract' not in sys.modules, 'pytesseract was imported on macOS'
print('clean: no Pillow, no pytesseract')
"
```

Expected: `clean: no Pillow, no pytesseract`

This guards the universal2 build; if it fails, an import crept into shared code.

- [ ] **Step 6: Commit**

```bash
git add components/ocr/vision_engine.py tests/test_ocr_engines.py
git commit -m "feat: add Apple Vision OCR engine for macOS

Uses the OS's own text recognition -- no bundled binary, no tessdata.
Sorts observations into reading order, which Vision does not guarantee."
```

---

### Task 6: Platform engine selection and language plumbing

**Files:**
- Modify: `components/ocr/__init__.py`
- Modify: `components/ocr_worker.py:31`
- Modify: `ui/main_window.py` (add language selector)
- Modify: `tests/test_ocr_engines.py` (append factory tests)

**Interfaces:**
- Consumes: `VisionOcrEngine` (Task 5), `TesseractOcrEngine` (Task 3).
- Produces:
  - `get_engine() -> OcrEngine` — returns `VisionOcrEngine` on darwin, `TesseractOcrEngine` elsewhere.
  - `describe_language(code: str) -> str` — human-readable label for the dropdown.
  - `OCRWorker(pdf_path: str, languages: list[str] | None = None)` — the second parameter is new.

**Why the UI change is in scope:** `ocr_worker.py:31` currently hardcodes `lang='eng'`.
Issue #26's document is a Polish invoice, so even after the crash is fixed that user
gets poor results. Language selection is part of resolving the reported problem.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ocr_engines.py`:

```python
def test_factory_returns_the_platform_engine():
    from components.ocr import get_engine

    engine = get_engine()

    if sys.platform == "darwin":
        assert engine.name == "Apple Vision"
    else:
        assert engine.name == "Tesseract"


def test_describe_language_is_human_readable():
    from components.ocr import describe_language

    assert describe_language("pl-PL") == "Polish"
    assert describe_language("pol") == "Polish"
    assert describe_language("en-US") == "English"
    assert describe_language("eng") == "English"


def test_describe_language_falls_back_to_the_raw_code():
    from components.ocr import describe_language

    assert describe_language("zz-ZZ") == "zz-ZZ"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ocr_engines.py -v -k "factory or describe"`
Expected: FAIL — `ImportError: cannot import name 'get_engine'`

- [ ] **Step 3: Write the factory**

Replace `components/ocr/__init__.py`:

```python
#!/usr/bin/env python3
"""OCR backend selection.

macOS uses Apple Vision, which the OS provides. Every other platform uses
Tesseract. The two use different language-code schemes, so codes are treated as
opaque strings outside the engines; describe_language() maps either scheme to a
label for display.
"""

import sys

from components.ocr.base import OcrEngine

__all__ = ["OcrEngine", "get_engine", "describe_language"]

# Maps both BCP-47 (Vision) and ISO 639-2 (Tesseract) codes to display names,
# so the UI can label whichever engine is active.
_LANGUAGE_NAMES = {
    "ar": "Arabic", "ara": "Arabic",
    "cs": "Czech", "ces": "Czech",
    "da": "Danish", "dan": "Danish",
    "de": "German", "deu": "German",
    "en": "English", "eng": "English",
    "es": "Spanish", "spa": "Spanish",
    "fr": "French", "fra": "French",
    "id": "Indonesian", "ind": "Indonesian",
    "it": "Italian", "ita": "Italian",
    "ja": "Japanese", "jpn": "Japanese",
    "ko": "Korean", "kor": "Korean",
    "ms": "Malay", "msa": "Malay",
    "nb": "Norwegian", "nn": "Norwegian", "no": "Norwegian", "nor": "Norwegian",
    "nl": "Dutch", "nld": "Dutch",
    "pl": "Polish", "pol": "Polish",
    "pt": "Portuguese", "por": "Portuguese",
    "ro": "Romanian", "ron": "Romanian",
    "ru": "Russian", "rus": "Russian",
    "sv": "Swedish", "swe": "Swedish",
    "th": "Thai", "tha": "Thai",
    "tr": "Turkish", "tur": "Turkish",
    "uk": "Ukrainian", "ukr": "Ukrainian",
    "vi": "Vietnamese", "vie": "Vietnamese",
    "yue": "Cantonese",
    "zh": "Chinese", "chi_sim": "Chinese", "chi_tra": "Chinese",
}


def get_engine() -> OcrEngine:
    """Return the OCR engine for this platform."""
    if sys.platform == "darwin":
        from components.ocr.vision_engine import VisionOcrEngine

        return VisionOcrEngine()

    from components.ocr.tesseract_engine import TesseractOcrEngine

    return TesseractOcrEngine()


def describe_language(code: str) -> str:
    """Human-readable name for an engine-native language code.

    Accepts BCP-47 ('pl-PL') and ISO 639-2 ('pol'). Unknown codes are returned
    unchanged so the UI degrades to showing the raw code.
    """
    if code in _LANGUAGE_NAMES:
        return _LANGUAGE_NAMES[code]
    base = code.split("-")[0]
    return _LANGUAGE_NAMES.get(base, code)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ocr_engines.py -v -k "factory or describe"`
Expected: PASS, 3 passed

- [ ] **Step 5: Thread languages through the worker**

In `components/ocr_worker.py`, change the constructor and the processor
construction. Replace lines 18-31 (`def __init__` through `processor = PdfOcrProcessor(lang='eng')`) with:

```python
    def __init__(self, pdf_path: str, languages: list[str] | None = None):
        super().__init__()
        self.pdf_path = pdf_path
        self.languages = languages
        self._stop_requested = False

    def request_stop(self):
        """Request the worker to stop processing at the next opportunity."""
        self._stop_requested = True

    def run(self):
        """Execute OCR processing"""
        try:
            # Create OCR processor
            processor = PdfOcrProcessor(languages=self.languages)
```

Leave the rest of `run()` unchanged.

- [ ] **Step 6: Add the language selector to the UI**

In `ui/main_window.py`, add to the imports at line 8-13:

```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QComboBox
)
```

and after the existing `from components.ocr_worker import OCRWorker`:

```python
from components.ocr import describe_language, get_engine
```

In `MainWindow.__init__`, after `self.ocr_worker = None` (line 113), add:

```python
        # Query the platform engine once; the language list depends on the OS
        # version, so it is never hardcoded.
        self.engine = get_engine()
```

In `_setup_ui`, insert this immediately after the `layout.addWidget(self.open_btn)`
line (line 154):

```python
        # Language selector, populated from whichever engine this platform uses
        language_layout = QHBoxLayout()
        language_layout.setSpacing(10)

        language_caption = QLabel("Language:")
        language_caption.setStyleSheet("color: #333;")
        language_layout.addWidget(language_caption)

        self.language_combo = QComboBox()
        self.language_combo.setMinimumHeight(30)
        self._populate_languages()
        language_layout.addWidget(self.language_combo, 1)

        layout.addLayout(language_layout)
```

Add these two methods to `MainWindow`, after `_setup_ui`:

```python
    def _populate_languages(self):
        """Fill the language dropdown from the active engine.

        Vision's language list grows with the macOS version and Tesseract's
        depends on installed .traineddata, so this is queried at runtime.
        """
        self.language_combo.addItem(f"Automatic ({self.engine.name})", None)

        for code in self.engine.supported_languages():
            self.language_combo.addItem(f"{describe_language(code)} ({code})", code)

    def _selected_languages(self):
        """Language codes for the current selection, or None for automatic."""
        code = self.language_combo.currentData()
        return [code] if code else None
```

In `_start_ocr`, change the worker construction (line 376) to pass the selection:

```python
        self.ocr_worker = OCRWorker(self.current_file, languages=self._selected_languages())
```

Also disable the dropdown during processing. In `_start_ocr`, after
`self.drop_zone.setAcceptDrops(False)` (line 359):

```python
        self.language_combo.setEnabled(False)
```

and re-enable it in both `_on_ocr_success` (after line 419) and `_on_ocr_error`
(after line 441):

```python
        self.language_combo.setEnabled(True)
```

- [ ] **Step 7: Verify the app launches and the dropdown is populated**

Run:

```bash
python -c "
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
app = QApplication([])
w = MainWindow()
count = w.language_combo.count()
print(f'engine: {w.engine.name}')
print(f'languages offered: {count}')
print(f'first three: {[w.language_combo.itemText(i) for i in range(min(3, count))]}')
assert count > 1, 'dropdown not populated'
"
```

Expected on macOS: `engine: Apple Vision`, `languages offered: 31`, and the first
three reading `Automatic (Apple Vision)`, `English (en-US)`, `French (fr-FR)`.

- [ ] **Step 8: Run the full suite**

Run: `python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 9: Commit**

```bash
git add components/ocr/__init__.py components/ocr_worker.py ui/main_window.py tests/test_ocr_engines.py
git commit -m "feat: select OCR engine by platform and add a language picker

The dropdown is populated at runtime from the active engine, since Vision's
language list depends on the macOS version. Replaces the hardcoded lang='eng'
that would have mis-read issue #26's Polish invoice even after the crash fix."
```

---

### Task 7: Delete the poppler/tesseract bundling machinery

**Files:**
- Delete: `components/poppler_utils.py`, `test_bundled_deps.py`, `test_tessdata_path.py`, `docs/OCR_ERROR_FIX.md`
- Modify: `main.py:14`, `main.py:20-36`
- Modify: `THIRD_PARTY_LICENSES.md`

**Interfaces:**
- Consumes: nothing new.
- Produces: `main.py` no longer imports `setup_bundled_binaries`; `initialize_application(loading_screen)` keeps its signature so the loading-screen flow is unchanged.

- [ ] **Step 1: Confirm nothing still references the deleted modules**

Run:

```bash
grep -rn "poppler_utils\|setup_bundled_binaries\|pdf2image\|PyPDF2\|TESSDATA" \
  --include="*.py" --include="*.yml" --include="*.md" . | grep -v "^./docs/superpowers/"
```

Expected: matches only in `main.py`, `build.py`, the workflow files, `README.md`,
`THIRD_PARTY_LICENSES.md`, and the files being deleted. If any other module
matches, fix it before continuing.

- [ ] **Step 2: Update the application entry point**

In `main.py`, delete line 14 (`from components.poppler_utils import setup_bundled_binaries`).

Replace `initialize_application` (lines 20-36) with:

```python
def initialize_application(loading_screen):
    """
    Initialize application components with progress feedback

    Args:
        loading_screen: LoadingScreen instance to update with progress
    """
    # There are no external binaries to locate any more: PDF rendering is
    # bundled in the pypdfium2 wheel and OCR comes from the OS on macOS.
    loading_screen.set_progress("Preparing OCR engine...")
    QApplication.processEvents()

    # Instantiating the engine here surfaces any platform problem on the
    # loading screen rather than on the first OCR run.
    from components.ocr import get_engine

    engine = get_engine()
    loading_screen.set_progress(f"Using {engine.name}...")
    QApplication.processEvents()

    loading_screen.set_progress("Finalizing initialization...")
    QApplication.processEvents()
```

- [ ] **Step 3: Delete the obsolete files**

```bash
git rm components/poppler_utils.py test_bundled_deps.py test_tessdata_path.py docs/OCR_ERROR_FIX.md
```

`test_bundled_deps.py` and `test_tessdata_path.py` are standalone diagnostic
scripts for bundled binaries that no longer exist. `docs/OCR_ERROR_FIX.md`
documents the Tesseract-path workaround the Vision engine makes obsolete.

- [ ] **Step 4: Update the license inventory**

In `THIRD_PARTY_LICENSES.md`, remove the Poppler and Tesseract sections for macOS
and add:

```markdown
## PDFium (via pypdfium2)

- **License:** BSD-3-Clause (PDFium), Apache-2.0 (pypdfium2 bindings)
- **Used for:** rendering PDF pages to bitmaps on all platforms
- **Source:** https://github.com/pypdfium2-team/pypdfium2

## Apple Vision framework (macOS only)

- **License:** part of macOS; used via public API, not redistributed
- **Used for:** on-device text recognition on macOS
- **Bindings:** PyObjC (MIT), https://github.com/ronaldoussoren/pyobjc

## Tesseract OCR (Windows and Linux only)

- **License:** Apache-2.0
- **Used for:** text recognition on non-macOS platforms
- **Source:** https://github.com/tesseract-ocr/tesseract
```

Note in the file that Poppler (GPL) is no longer distributed with any build.

- [ ] **Step 5: Verify the app still starts**

Run:

```bash
python -c "
from PySide6.QtWidgets import QApplication
import main
app = QApplication([])
from ui.loading_screen import LoadingScreen
screen = LoadingScreen()
main.initialize_application(screen)
print('initialization completed without poppler_utils')
"
```

Expected: `initialization completed without poppler_utils`

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: delete poppler/tesseract bundling machinery

Removes poppler_utils.py (196 lines of binary path-hunting), the two
standalone bundle-diagnostic scripts, and the tessdata workaround doc.
Poppler (GPL) is no longer distributed with any build."
```

---

## Phase 3 — macOS packaging

### Task 8: Build a real `.app` instead of a `--onefile` executable

**Files:**
- Create: `packaging/quickpdfocr.spec`
- Modify: `build.py` (rewrite; currently 420 lines)
- Modify: `main.py` (add `--selftest`)

**Interfaces:**
- Consumes: nothing new.
- Produces: `python build.py` emits `dist/QuickPdfOcr.app` on macOS and `dist/QuickPdfOcr/` elsewhere. `python main.py --selftest <pdf>` runs OCR headless, prints the text, and exits non-zero on failure — this is the hook Task 9's CI smoke test calls.

- [ ] **Step 1: Add the headless self-test entry point**

In `main.py`, insert at the top of `main()` (before the startup banner at line 42):

```python
    # Headless self-test, used by CI to prove the packaged app can actually OCR.
    # The existing build produced artifacts that were never executed, which is
    # why issue #26 shipped.
    if "--selftest" in sys.argv:
        sys.exit(_run_selftest(sys.argv))
```

and add this function above `main()`:

```python
def _run_selftest(argv) -> int:
    """Run OCR on a PDF without starting the GUI. Returns a process exit code."""
    index = argv.index("--selftest")
    if index + 1 >= len(argv):
        print("--selftest requires a PDF path", file=sys.stderr)
        return 2

    pdf_path = argv[index + 1]
    from components.ocr import get_engine
    from components.pdf_ocr import PdfOcrProcessor

    engine = get_engine()
    print(f"self-test: engine={engine.name} file={pdf_path}")

    try:
        text = PdfOcrProcessor().process(pdf_path)
    except Exception as exc:
        print(f"self-test FAILED: {exc}", file=sys.stderr)
        return 1

    stripped = text.replace("--- Page 1 ---", "").strip()
    if not stripped:
        print("self-test FAILED: no text extracted", file=sys.stderr)
        return 1

    print(f"self-test PASSED, {len(stripped)} characters extracted")
    print(text)
    return 0
```

- [ ] **Step 2: Verify the self-test works from source**

Run: `python main.py --selftest tests/fixtures/sample_invoice.pdf`
Expected: exits 0, prints `self-test PASSED` and the invoice text including `FAKTURA VAT PL6972514`.

- [ ] **Step 3: Write the PyInstaller spec**

Create `packaging/quickpdfocr.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for QuickPdfOcr.

Builds a directory-mode bundle, not --onefile. --onefile unpacks the whole app
to /var/folders/.../T/_MEIxxxx on every launch; that temp directory is where
issue #26's @rpath lookup failed, and re-extracting the bundle each run is slow.

There are no external binaries to bundle any more.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent
IS_MACOS = sys.platform == "darwin"

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / "resources"), "resources"),
        (str(PROJECT_ROOT / "LICENSE"), "."),
        (str(PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"), "."),
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "pypdfium2",
    ] + ([
        "Vision",
        "Quartz",
        "Foundation",
    ] if IS_MACOS else [
        "pytesseract",
        "PIL",
        "PIL.Image",
    ]),
    hookspath=[],
    runtime_hooks=[],
    # Keep the non-macOS OCR stack out of the macOS bundle entirely. Pillow has
    # no universal2 wheel, so its presence would break the universal2 build.
    excludes=["PIL", "pytesseract", "pdf2image", "PyPDF2"] if IS_MACOS else [],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="QuickPdfOcr",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(PROJECT_ROOT / "resources" / ("icon.icns" if IS_MACOS else "icon.ico")),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="QuickPdfOcr",
)

if IS_MACOS:
    app = BUNDLE(
        coll,
        name="QuickPdfOcr.app",
        icon=str(PROJECT_ROOT / "resources" / "icon.icns"),
        bundle_identifier="com.quickpdfocr.app",
        info_plist={
            "CFBundleName": "QuickPdfOcr",
            "CFBundleDisplayName": "QuickPdfOcr",
            "CFBundleShortVersionString": "2.0.0",
            "CFBundleVersion": "2.0.0",
            "LSMinimumSystemVersion": "13.0",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "See THIRD_PARTY_LICENSES.md",
        },
    )
```

- [ ] **Step 4: Rewrite the build script**

Replace `build.py` entirely:

```python
#!/usr/bin/env python3
"""Build the standalone application.

There is nothing to hunt for on disk any more. PDF rendering ships inside the
pypdfium2 wheel and macOS OCR comes from the operating system, so this script
just drives PyInstaller against packaging/quickpdfocr.spec.

On macOS the result is dist/QuickPdfOcr.app in directory mode. See
packaging/make_universal.py for the universal2 and code-signing steps.
"""

import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SPEC_FILE = PROJECT_ROOT / "packaging" / "quickpdfocr.spec"


def build() -> None:
    """Run PyInstaller and report what was produced."""
    system = platform.system()
    print(f"Building for {system} ({platform.machine()})...")

    if not SPEC_FILE.exists():
        print(f"Spec file not found: {SPEC_FILE}", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", str(SPEC_FILE)]

    print("\n" + "=" * 60)
    print("STARTING PYINSTALLER BUILD")
    print("=" * 60)
    print("This may take several minutes...\n")

    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"\nBuild failed: {exc}", file=sys.stderr)
        sys.exit(1)

    artifact = (
        PROJECT_ROOT / "dist" / "QuickPdfOcr.app"
        if system == "Darwin"
        else PROJECT_ROOT / "dist" / "QuickPdfOcr"
    )

    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL")
    print("=" * 60)
    print(f"\nArtifact: {artifact}")
    print("\nBUNDLED COMPONENTS:")
    print("  [OK] Python interpreter")
    print("  [OK] PySide6")
    print("  [OK] PDFium (via pypdfium2) -- no Poppler needed")
    if system == "Darwin":
        print("  [OK] OCR via the OS's Vision framework -- no Tesseract needed")
        print("\nNEXT STEP: python packaging/make_universal.py")
        print("  (required -- arm64 binaries will not launch unsigned)")
    else:
        print("  [!!] Tesseract must be installed on the target system")


if __name__ == "__main__":
    build()
```

- [ ] **Step 5: Build and verify the bundle shape**

Run:

```bash
python build.py
ls -d dist/QuickPdfOcr.app && du -sh dist/QuickPdfOcr.app
```

Expected: the `.app` exists. Size should be well under the previous ~250 MB —
roughly 60-90 MB.

- [ ] **Step 6: Verify no poppler or tesseract leaked into the bundle**

Run:

```bash
find dist/QuickPdfOcr.app \( -name "*poppler*" -o -name "pdftoppm" -o -name "pdfinfo" \
  -o -name "tesseract*" -o -name "*.traineddata" \) -print | head
```

Expected: no output. Any hit means the old bundling path is still active.

- [ ] **Step 7: Commit**

```bash
git add build.py packaging/quickpdfocr.spec main.py
git commit -m "build: produce a directory-mode .app via a PyInstaller spec

Replaces --onefile, whose /var/folders temp extraction is where issue #26's
@rpath lookup failed. Adds main.py --selftest so CI can execute the built
artifact instead of only producing it."
```

---

### Task 9: universal2 merge, ad-hoc signing, and a CI smoke test

**Files:**
- Create: `packaging/make_universal.py`
- Modify: `.github/workflows/build-macos.yml` (rewrite)

**Interfaces:**
- Consumes: `dist/QuickPdfOcr.app` from Task 8.
- Produces: a universal2, ad-hoc-signed `.app`. `python packaging/make_universal.py` exits non-zero if the merge or signature verification fails.

- [ ] **Step 1: Write the universal2 script**

Create `packaging/make_universal.py`:

```python
#!/usr/bin/env python3
"""Make dist/QuickPdfOcr.app universal2, then ad-hoc sign it.

Wheel arch survey as of pypdfium2 5.12 / PySide6 6.11:

    PySide6                 universal2 wheel     -- nothing to do
    pyobjc Vision/Quartz    universal2 wheels    -- nothing to do
    pypdfium2               arm64 and x86_64     -- must be lipo-merged

Pillow is the other non-universal2 dependency, which is why the macOS build
excludes it entirely; if it reappears in the bundle this script will say so.

Signing is not optional. lipo invalidates any existing signature, and arm64
binaries do not execute unsigned on Apple Silicon. Ad-hoc signing (--sign -)
needs no Apple Developer account. It does NOT notarize: users downloading from
GitHub will still see a Gatekeeper prompt on first launch.
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APP = PROJECT_ROOT / "dist" / "QuickPdfOcr.app"
PDFIUM_NAME = "libpdfium.dylib"
PYPDFIUM2_VERSION = "5.12.1"


def run(cmd, **kwargs) -> subprocess.CompletedProcess:
    """Run a command, echoing it, and raise on failure."""
    print(f"  $ {' '.join(str(part) for part in cmd)}")
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def find_pdfium() -> Path:
    """Locate the bundled libpdfium.dylib inside the .app."""
    matches = list(APP.rglob(PDFIUM_NAME))
    if not matches:
        raise SystemExit(f"{PDFIUM_NAME} not found in {APP}")
    if len(matches) > 1:
        raise SystemExit(f"Multiple {PDFIUM_NAME} found: {matches}")
    return matches[0]


def architectures(binary: Path) -> set:
    """Architectures present in a Mach-O file."""
    output = run(["lipo", "-info", str(binary)]).stdout
    return set(output.strip().split(":")[-1].split())


def download_other_arch(target: str, into: Path) -> Path:
    """Download the opposite-architecture pypdfium2 wheel and extract its dylib."""
    run([
        sys.executable, "-m", "pip", "download",
        f"pypdfium2=={PYPDFIUM2_VERSION}",
        "--only-binary=:all:",
        f"--platform=macosx_13_0_{target}",
        "--python-version=3.12",
        "--no-deps",
        "-d", str(into),
    ])
    wheels = list(into.glob("*.whl"))
    if not wheels:
        raise SystemExit(f"No pypdfium2 wheel downloaded for {target}")

    extracted = into / "extracted"
    with zipfile.ZipFile(wheels[0]) as archive:
        archive.extractall(extracted)

    dylibs = list(extracted.rglob(PDFIUM_NAME))
    if not dylibs:
        raise SystemExit(f"No {PDFIUM_NAME} inside {wheels[0].name}")
    return dylibs[0]


def check_no_thin_dependencies() -> None:
    """Fail loudly if a non-universal2 package slipped into the bundle."""
    strays = [p for p in APP.rglob("*") if p.is_dir() and p.name == "PIL"]
    if strays:
        raise SystemExit(
            f"Pillow is present in the bundle ({strays[0]}); it has no "
            "universal2 wheel. Check that nothing imports PIL on macOS."
        )


def main() -> int:
    if not APP.exists():
        raise SystemExit(f"{APP} not found; run python build.py first")

    print("Checking for non-universal2 dependencies...")
    check_no_thin_dependencies()

    pdfium = find_pdfium()
    present = architectures(pdfium)
    print(f"Bundled {PDFIUM_NAME} architectures: {sorted(present)}")

    if {"arm64", "x86_64"} <= present:
        print("Already universal2; skipping merge.")
    else:
        missing = "x86_64" if "arm64" in present else "arm64"
        print(f"Merging in {missing}...")
        with tempfile.TemporaryDirectory() as tmp:
            other = download_other_arch(missing, Path(tmp))
            merged = Path(tmp) / "merged.dylib"
            run(["lipo", "-create", str(pdfium), str(other), "-output", str(merged)])
            shutil.copy2(merged, pdfium)

        merged_arches = architectures(pdfium)
        if not {"arm64", "x86_64"} <= merged_arches:
            raise SystemExit(f"Merge failed; got {sorted(merged_arches)}")
        print(f"Merged: {sorted(merged_arches)}")

    # lipo strips the signature, and unsigned arm64 code will not run.
    print("Ad-hoc signing the bundle...")
    run(["codesign", "--force", "--deep", "--sign", "-", str(APP)])
    run(["codesign", "--verify", "--deep", "--strict", str(APP)])
    print("Signature verified.")

    print("\nDone. Note: ad-hoc signing is not notarization -- users will still")
    print("need Privacy & Security -> 'Open Anyway' on first launch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it and verify the result**

Run:

```bash
python packaging/make_universal.py
```

Expected: prints `Merged: ['arm64', 'x86_64']` then `Signature verified.`

- [ ] **Step 3: Verify the built app actually runs OCR**

Run:

```bash
./dist/QuickPdfOcr.app/Contents/MacOS/QuickPdfOcr --selftest tests/fixtures/sample_invoice.pdf
echo "exit code: $?"
```

Expected: `self-test PASSED`, the invoice text, and `exit code: 0`.

**This is the check that would have caught issue #26.** If it fails, stop and
diagnose before proceeding — do not adjust the test to pass.

- [ ] **Step 4: Rewrite the macOS workflow**

Replace `.github/workflows/build-macos.yml`:

```yaml
name: Build macOS

on:
  workflow_dispatch:
    inputs:
      release_tag:
        description: 'Tag to build (e.g. v1.0.0)'
        required: false
        type: string

permissions:
  contents: read

jobs:
  build-macos:
    runs-on: macos-14  # Apple Silicon
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.release_tag || github.ref }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # No Homebrew step. Poppler and Tesseract are not used on macOS:
      # rendering ships inside the pypdfium2 wheel and OCR comes from the OS.

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest tests/ -v

      - name: Build .app
        run: python build.py

      - name: Make universal2 and sign
        run: python packaging/make_universal.py

      - name: Smoke test the built app
        run: |
          ./dist/QuickPdfOcr.app/Contents/MacOS/QuickPdfOcr \
            --selftest tests/fixtures/sample_invoice.pdf

      - name: Verify no Poppler or Tesseract in the bundle
        run: |
          if find dist/QuickPdfOcr.app \
               \( -name "*poppler*" -o -name "pdfinfo" -o -name "pdftoppm" \
                  -o -name "tesseract*" -o -name "*.traineddata" \) \
               -print | grep .; then
            echo "::error::External OCR binaries leaked into the bundle"
            exit 1
          fi
          echo "Bundle is clean"

      - name: Create ZIP archive
        run: |
          cd dist
          ditto -c -k --keepParent QuickPdfOcr.app QuickPdfOcr-macOS-universal2.zip

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: QuickPdfOcr-macOS-universal2
          path: dist/QuickPdfOcr-macOS-universal2.zip
```

Two changes beyond the obvious: the Homebrew step is gone entirely, and `ditto`
replaces `zip` because `zip` does not preserve the extended attributes and
symlinks a signed `.app` needs.

- [ ] **Step 5: Commit**

```bash
git add packaging/make_universal.py .github/workflows/build-macos.yml
git commit -m "build: universal2 merge, ad-hoc signing, and a CI smoke test

lipo-merges pdfium's two arch-specific dylibs, then re-signs -- lipo strips
signatures and unsigned arm64 code will not launch. CI now executes the built
app against the fixture PDF, which is the check that would have caught #26."
```

---

## Phase 4 — Mac-native integration

### Task 10: Open PDFs directly from Finder and the Dock

**Files:**
- Modify: `packaging/quickpdfocr.spec` (extend `info_plist`)
- Modify: `main.py` (handle `QEvent.FileOpen`)
- Modify: `ui/main_window.py` (public method for external file opening)

**Interfaces:**
- Consumes: `MainWindow` from Task 6.
- Produces: `MainWindow.open_file(path: str) -> None` — public entry point for externally supplied files. `_on_file_dropped` delegates to it.

- [ ] **Step 1: Declare the document type**

In `packaging/quickpdfocr.spec`, add to the `info_plist` dictionary:

```python
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "PDF Document",
                    "CFBundleTypeRole": "Viewer",
                    "LSItemContentTypes": ["com.adobe.pdf"],
                    "LSHandlerRank": "Alternate",
                }
            ],
```

`LSHandlerRank: Alternate` asks to appear in "Open With" without displacing
Preview as the default PDF handler.

- [ ] **Step 2: Expose a public file-opening method**

In `ui/main_window.py`, rename `_on_file_dropped` to `open_file` and make the old
name delegate. Replace the `def _on_file_dropped(self, file_path: str):` line and
its docstring with:

```python
    def open_file(self, file_path: str):
        """Load a PDF for OCR. Public entry point used by drag-drop, the file
        picker, and macOS 'Open With' / Dock-drop events."""
```

Then add immediately after that method's body ends (before `_start_ocr`):

```python
    def _on_file_dropped(self, file_path: str):
        """Slot for the drop zone's file_dropped signal."""
        self.open_file(file_path)
```

- [ ] **Step 3: Handle the macOS file-open event**

In `main.py`, add this class above `main()`:

```python
class QuickPdfOcrApplication(QApplication):
    """QApplication that accepts files opened from Finder or the Dock.

    macOS does not pass double-clicked files in argv -- it sends a FileOpen
    event, which may arrive before the main window exists. Early events are
    queued and replayed once the window is ready.
    """

    def __init__(self, argv):
        super().__init__(argv)
        self._window = None
        self._pending_file = None

    def set_window(self, window):
        """Attach the main window and replay any queued file."""
        self._window = window
        if self._pending_file:
            window.open_file(self._pending_file)
            self._pending_file = None

    def event(self, event):
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.FileOpen:
            path = event.file()
            if path.lower().endswith(".pdf"):
                if self._window is not None:
                    self._window.open_file(path)
                else:
                    self._pending_file = path
            return True
        return super().event(event)
```

In `main()`, replace `app = QApplication(sys.argv)` (line 57) with:

```python
    app = QuickPdfOcrApplication(sys.argv)
```

and after `window = MainWindow()` (line 89) add:

```python
    app.set_window(window)
```

Finally, accept a PDF passed on the command line, which is how Windows and Linux
deliver it. After `app.set_window(window)`:

```python
    # Windows and Linux pass the file in argv; macOS uses the FileOpen event above.
    for argument in sys.argv[1:]:
        if argument.lower().endswith(".pdf") and Path(argument).exists():
            window.open_file(argument)
            break
```

- [ ] **Step 4: Verify the event plumbing**

Run:

```bash
python -c "
from PySide6.QtCore import QEvent
from main import QuickPdfOcrApplication
from ui.main_window import MainWindow

app = QuickPdfOcrApplication([])

class FakeFileOpenEvent(QEvent):
    def __init__(self, path):
        super().__init__(QEvent.Type.FileOpen)
        self._path = path
    def file(self):
        return self._path

# Event arriving before the window exists must be queued, not dropped.
app.event(FakeFileOpenEvent('tests/fixtures/sample_invoice.pdf'))
assert app._pending_file == 'tests/fixtures/sample_invoice.pdf', 'early event lost'

window = MainWindow()
app.set_window(window)
assert window.current_file == 'tests/fixtures/sample_invoice.pdf', 'queued file not replayed'
assert app._pending_file is None

# And one arriving afterwards must go straight through.
app.event(FakeFileOpenEvent('tests/fixtures/sample_invoice.pdf'))
assert window.current_file == 'tests/fixtures/sample_invoice.pdf'
print('FileOpen handling verified, both before and after window creation')
"
```

Expected: `FileOpen handling verified, both before and after window creation`

- [ ] **Step 5: Rebuild and verify the declaration landed**

Run:

```bash
python build.py && python packaging/make_universal.py
plutil -extract CFBundleDocumentTypes xml1 -o - dist/QuickPdfOcr.app/Contents/Info.plist
```

Expected: XML listing `com.adobe.pdf`.

- [ ] **Step 6: Commit**

```bash
git add packaging/quickpdfocr.spec main.py ui/main_window.py
git commit -m "feat: open PDFs from Finder, the Dock, and the command line

macOS delivers double-clicked files as QEvent.FileOpen rather than argv, and
the event can arrive before the window exists, so early events are queued."
```

---

### Task 11: Finder right-click via `NSServices`

**Files:**
- Modify: `packaging/quickpdfocr.spec` (extend `info_plist`)
- Modify: `README.md`

**Interfaces:**
- Consumes: the `--selftest`-style argv handling and `open_file` from Task 10.
- Produces: no new Python API. The Services entry reuses the existing argv path.

**Why `NSServices` rather than a Quick Action:** an app extension needs a second
build target, its own bundle, and its own signing identity. An `NSServices` entry
in the main app's Info.plist needs none of those and is registered by Launch
Services the first time the app runs.

- [ ] **Step 1: Declare the service**

In `packaging/quickpdfocr.spec`, add to `info_plist`:

```python
            "NSServices": [
                {
                    "NSMenuItem": {"default": "OCR with QuickPdfOcr"},
                    "NSMessage": "openFile",
                    "NSPortName": "QuickPdfOcr",
                    "NSSendFileTypes": ["com.adobe.pdf"],
                }
            ],
```

- [ ] **Step 2: Rebuild and verify the declaration**

Run:

```bash
python build.py && python packaging/make_universal.py
plutil -extract NSServices xml1 -o - dist/QuickPdfOcr.app/Contents/Info.plist
```

Expected: XML containing `OCR with QuickPdfOcr` and `com.adobe.pdf`.

- [ ] **Step 3: Register and confirm Launch Services sees it**

Run:

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
  -f dist/QuickPdfOcr.app
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
  -dump | grep -A2 -i "quickpdfocr" | head -20
```

Expected: the bundle appears in the dump with `com.quickpdfocr.app`.

Manual confirmation (cannot be automated): copy the `.app` to `/Applications`,
launch it once, then right-click a PDF in Finder and look under Services for
"OCR with QuickPdfOcr". Note in the commit whether this worked — Services
registration can take a minute or need a Finder restart.

- [ ] **Step 4: Document installation and the Gatekeeper prompt**

In `README.md`, replace the macOS installation section with:

```markdown
### macOS

1. Download `QuickPdfOcr-macOS-universal2.zip` from the
   [latest release](../../releases/latest).
2. Unzip it and drag `QuickPdfOcr.app` to your Applications folder.
3. **First launch only:** macOS will refuse to open the app because it is not
   notarized. Go to **System Settings → Privacy & Security**, scroll to the
   message about QuickPdfOcr, and click **Open Anyway**. Subsequent launches
   work normally.

There is nothing else to install. No Homebrew, no Poppler, no Tesseract —
PDF rendering is built into the app and text recognition uses macOS's own
Vision framework.

**Requires macOS 13 (Ventura) or later.**

Once installed you can also:
- Right-click any PDF in Finder → **Services → OCR with QuickPdfOcr**
- Drag a PDF onto the app's Dock icon
- Right-click a PDF → **Open With → QuickPdfOcr**
```

Also update the requirements section elsewhere in the README to remove the
`brew install poppler tesseract` instructions for macOS. Keep them for Linux
and Windows, which still use Tesseract.

- [ ] **Step 5: Run the full suite one last time**

Run: `python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add packaging/quickpdfocr.spec README.md
git commit -m "feat: add 'OCR with QuickPdfOcr' to the Finder Services menu

Uses NSServices in the main app's Info.plist rather than a Quick Action
extension, which would need a second build target and signing identity.
Documents the first-launch Gatekeeper step, since the app is not notarized."
```

---

## Verification checklist

Before opening the PR, confirm each of these and paste the output:

- [ ] `python -m pytest tests/ -v` — all pass
- [ ] `python build.py && python packaging/make_universal.py` — succeeds
- [ ] `lipo -info $(find dist/QuickPdfOcr.app -name libpdfium.dylib)` — shows both arches
- [ ] `codesign --verify --deep --strict dist/QuickPdfOcr.app` — silent (success)
- [ ] `./dist/QuickPdfOcr.app/Contents/MacOS/QuickPdfOcr --selftest tests/fixtures/sample_invoice.pdf` — exit 0
- [ ] `find dist/QuickPdfOcr.app \( -name "*poppler*" -o -name "tesseract*" -o -name "*.traineddata" \)` — no output
- [ ] `grep -rn "pdf2image\|PyPDF2\|poppler_utils" --include="*.py" .` — no output outside `docs/superpowers/`
- [ ] `du -sh dist/QuickPdfOcr.app` — substantially under the previous ~250 MB
- [ ] Manual: launch the app, drop the fixture PDF, confirm text appears and the
      language dropdown is populated

## Deliberately out of scope

- **Notarization and Developer ID signing.** Decided against; requires a $99/yr
  account. Consequence documented in the README.
- **Windows/Linux Tesseract dylib bundling.** `build.py`'s old Windows and Linux
  paths bundled `tesseract` without libtesseract or libleptonica — the same
  defect as issue #26, one platform over. The spec's Risk 5. File a separate issue.
- **DMG with a drag-to-Applications background.** A signed ZIP via `ditto` is
  sufficient; a styled DMG is cosmetic.
