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
