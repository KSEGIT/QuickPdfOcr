"""Shared pytest fixtures."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

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
        pytest.fail(f"fixture missing: {path}; run tests/fixtures/make_fixture.py")
    return path


@pytest.fixture
def multipage_pdf() -> Path:
    """Path to the committed three-page fixture (pages read 'STRONA 1/2/3')."""
    path = FIXTURE_DIR / "sample_multipage.pdf"
    if not path.exists():
        pytest.fail(f"fixture missing: {path}; run tests/fixtures/make_fixture.py")
    return path


@pytest.fixture
def blank_pdf() -> Path:
    """Path to the committed two-page fixture with no drawn text on either page."""
    path = FIXTURE_DIR / "sample_blank.pdf"
    if not path.exists():
        pytest.fail(f"fixture missing: {path}; run tests/fixtures/make_fixture.py")
    return path


@pytest.fixture(scope="session")
def qapp():
    """The process-wide QApplication instance.

    QApplication is a singleton per process, so this reuses whatever
    instance already exists (from another GUI test module) instead of
    constructing a second one, which Qt does not allow.
    """
    import sys
    if sys.platform == "darwin":
        from main import QuickPdfOcrApplication
        instance = QApplication.instance()
        if instance is None:
            return QuickPdfOcrApplication([])
        if not isinstance(instance, QuickPdfOcrApplication):
            pytest.fail(
                "QApplication.instance() is a plain QApplication, not "
                "QuickPdfOcrApplication -- some other test module must have "
                "constructed it first. Some tests need the QuickPdfOcrApplication "
                "subclass to exercise set_window()/event()."
            )
        return instance
    else:
        return QApplication.instance() or QApplication([])
