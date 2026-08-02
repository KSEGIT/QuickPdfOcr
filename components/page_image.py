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
BYTES_PER_PIXEL = 4


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
        if self.stride < self.width * BYTES_PER_PIXEL:
            raise ValueError(
                f"stride {self.stride} is too small for width {self.width} * "
                f"{BYTES_PER_PIXEL} bytes/pixel = {self.width * BYTES_PER_PIXEL}"
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
