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
