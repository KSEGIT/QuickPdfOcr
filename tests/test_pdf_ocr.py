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


def test_detect_optimal_dpi_propagates_missing_file(tmp_path):
    processor = PdfOcrProcessor(engine=FakeEngine())

    with pytest.raises(FileNotFoundError):
        processor.detect_optimal_dpi(tmp_path / "nope.pdf")


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


def test_one_failing_page_does_not_abort_the_document(multipage_pdf):
    class FirstPageExplodingEngine(FakeEngine):
        def recognize(self, page, languages=None):
            self.calls.append((page, languages))
            if len(self.calls) == 1:
                raise RuntimeError("boom")
            return f"good text {len(self.calls)}"

    engine = FirstPageExplodingEngine()
    processor = PdfOcrProcessor(engine=engine)

    text = processor.process(multipage_pdf)

    assert "--- Page 1 ---\n[OCR Error" in text
    assert "good text 2" in text
    assert "good text 3" in text
    assert len(engine.calls) == 3
