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
