"""Tests for OCR engines.

EngineContractTests is subclassed once per engine so both are held to the same
contract. Assertions are substring-based on purpose: Vision and Tesseract will
never agree character for character.
"""

import sys
from types import SimpleNamespace

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


class _FakeCandidate:
    """Stands in for a VNRecognizedText's top candidate."""

    def __init__(self, text):
        self._text = text

    def string(self):
        return self._text


class _FakeObservation:
    """Stands in for a VNRecognizedTextObservation.

    _read_in_order only ever calls boundingBox() and topCandidates_(n) on a
    real observation, so a fake exposing just those two is enough to test the
    grouping/sorting logic without depending on what Vision actually returns
    for any given image.
    """

    def __init__(self, x, y, height, text):
        self._box = SimpleNamespace(
            origin=SimpleNamespace(x=x, y=y),
            size=SimpleNamespace(height=height),
        )
        self._text = text

    def boundingBox(self):
        return self._box

    def topCandidates_(self, n):
        return [_FakeCandidate(self._text)]


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

    def test_read_in_order_sorts_shuffled_observations_top_to_bottom(self, engine):
        """The sort must do the work: feed it out of order and check it fixes it."""
        top = _FakeObservation(x=0.1, y=0.8, height=0.05, text="top")
        middle = _FakeObservation(x=0.1, y=0.5, height=0.05, text="middle")
        bottom = _FakeObservation(x=0.1, y=0.2, height=0.05, text="bottom")

        lines = engine._read_in_order([middle, bottom, top])

        assert lines == ["top", "middle", "bottom"]

    def test_read_in_order_sorts_same_line_left_to_right(self, engine):
        """Two boxes on one visual line rarely share an identical origin.y --
        heights and baselines differ slightly -- so the tiebreak must trigger
        on near-equal y, not only exact equality."""
        left = _FakeObservation(x=0.1, y=0.500, height=0.05, text="Netto:")
        right = _FakeObservation(x=0.5, y=0.505, height=0.05, text="VAT:")

        lines = engine._read_in_order([right, left])

        assert lines == ["Netto: VAT:"]

    def test_read_in_order_separates_distinct_lines(self, engine):
        top = _FakeObservation(x=0.1, y=0.9, height=0.05, text="line one")
        bottom = _FakeObservation(x=0.1, y=0.1, height=0.05, text="line two")

        lines = engine._read_in_order([top, bottom])

        assert lines == ["line one", "line two"]


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
