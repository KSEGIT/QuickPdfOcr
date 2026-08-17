"""Tests for main._run_selftest, the headless entry point CI uses to prove the
packaged app can actually OCR (see main.py's --selftest handling).

These call main._run_selftest directly rather than shelling out to
`python main.py --selftest ...`, and never construct a QApplication --
_run_selftest never touches Qt.
"""

import main
from unittest.mock import patch


def test_selftest_passes_on_a_document_with_text(sample_pdf):
    argv = ["main.py", "--selftest", str(sample_pdf)]

    assert main._run_selftest(argv) == 0


def test_selftest_reports_no_text_on_a_blank_multipage_pdf(blank_pdf):
    """Regression test for a false pass: PdfOcrProcessor always adds a
    "--- Page N ---" header per page, so a naive check that only strips the
    first page's header still sees non-empty text on page 2+ of a blank
    document. A CI gate built on that check reports success on a document it
    extracted nothing from.
    """
    argv = ["main.py", "--selftest", str(blank_pdf)]

    assert main._run_selftest(argv) == 3


def test_selftest_reports_failure_on_a_missing_file():
    argv = ["main.py", "--selftest", "/nonexistent/does-not-exist.pdf"]

    assert main._run_selftest(argv) == 1


def test_selftest_reports_usage_error_without_a_path():
    argv = ["main.py", "--selftest"]

    assert main._run_selftest(argv) == 2


def test_selftest_detects_ocr_error_markers(sample_pdf):
    """When PdfOcrProcessor.process() returns text containing an OCR error
    marker ("[OCR Error: ...]"), _run_selftest must return exit code 1
    rather than treating it as successful non-empty output."""
    argv = ["main.py", "--selftest", str(sample_pdf)]

    with patch("components.pdf_ocr.PdfOcrProcessor") as mock_processor_class:
        mock_instance = mock_processor_class.return_value
        mock_instance.process.return_value = "--- Page 1 ---\n[OCR Error: something went wrong]"

        result = main._run_selftest(argv)

    assert result == 1
