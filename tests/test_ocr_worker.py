"""Tests for OCRWorker's exception-to-signal mapping.

IMPORTANT bug found in the whole-branch review: PdfOcrProcessor._process_page()
used to catch every exception, including a missing OCR engine, and record it
as ordinary page text (`[OCR Error: tesseract is not installed...]`).
OCRWorker.run() then saw non-empty extracted text and emitted `finished`, so
the UI reported "OCR completed successfully!" on every page of a document
that was never actually OCR'd.

components/ocr/base.py's OcrEngineUnavailable now lets that specific class of
failure -- the OCR backend itself being unusable, not a single bad page --
propagate out of PdfOcrProcessor.process() entirely (see
components/pdf_ocr.py's _process_page()). These tests exercise the other
half of that fix: OCRWorker.run()'s existing exception handling must turn an
escaped OcrEngineUnavailable into an `error` signal, not a `finished` one,
while a plain per-page exception (already covered at the PdfOcrProcessor
level in test_pdf_ocr.py) still results in a successful, contained run here
too.

No QThread is used -- OCRWorker.run() is called directly, synchronously, in
the test's own thread. Its signal connections are then plain same-thread
(direct) connections, so no event loop is needed to observe them.
"""

from PySide6.QtWidgets import QApplication

from components.ocr.base import OcrEngineUnavailable
from components.ocr_worker import OCRWorker
from tests.test_pdf_ocr import FakeEngine


class _PageFailureThenOkEngine(FakeEngine):
    """First page raises a plain (per-page) exception; the rest succeed."""

    def recognize(self, page, languages=None):
        self.calls.append((page, languages))
        if len(self.calls) == 1:
            raise RuntimeError("boom")
        return f"recovered text {len(self.calls)}"


class _UnavailableEngine(FakeEngine):
    """Every call raises OcrEngineUnavailable, as a missing Tesseract
    install or missing language data would."""

    def recognize(self, page, languages=None):
        self.calls.append((page, languages))
        raise OcrEngineUnavailable("tesseract is not installed or not in PATH")


def _run_worker(pdf_path, engine, monkeypatch):
    """Run OCRWorker.run() synchronously against `engine` and capture which
    of its two terminal signals fired.

    Patches components.ocr.get_engine rather than passing engine directly:
    OCRWorker has no constructor parameter for it (matching production,
    where it always uses the platform's real engine via
    PdfOcrProcessor(languages=...)'s own internal `from components.ocr
    import get_engine` -- a fresh, function-scoped import each call, so
    patching the module attribute here is picked up correctly).
    """
    monkeypatch.setattr("components.ocr.get_engine", lambda: engine)

    worker = OCRWorker(str(pdf_path))
    results = {"finished": None, "error": None}
    worker.finished.connect(lambda text: results.__setitem__("finished", text))
    worker.error.connect(lambda msg: results.__setitem__("error", msg))

    worker.run()

    return results


def test_a_page_level_failure_is_contained_and_the_run_still_succeeds(
    multipage_pdf, monkeypatch
):
    QApplication.instance() or QApplication([])

    results = _run_worker(multipage_pdf, _PageFailureThenOkEngine(), monkeypatch)

    assert results["error"] is None, "a contained per-page failure must not be reported as a run error"
    assert results["finished"] is not None
    assert "[OCR Error" in results["finished"]
    assert "recovered text" in results["finished"]


def test_engine_unavailable_aborts_the_run_and_reports_an_error(sample_pdf, monkeypatch):
    QApplication.instance() or QApplication([])

    results = _run_worker(sample_pdf, _UnavailableEngine(), monkeypatch)

    assert results["finished"] is None, (
        "an unavailable OCR engine must never be reported as a successful run"
    )
    assert results["error"] is not None
    assert "tesseract is not installed" in results["error"].lower()
