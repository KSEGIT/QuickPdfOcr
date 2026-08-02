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
