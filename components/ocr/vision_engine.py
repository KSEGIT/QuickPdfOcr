#!/usr/bin/env python3
"""OCR via Apple's Vision framework. macOS only.

Vision ships with the OS, so there is no binary to bundle, no dylib to
re-point, and no .traineddata to install. This is what replaced Tesseract on
macOS and, together with pypdfium2, is why the app no longer needs Homebrew.

Do not import Pillow or pytesseract here -- neither is installed on macOS.
"""

import Quartz
import Vision

from components.page_image import PageImage

# Preferred when the caller expresses no preference. Vision accepts several
# languages at once and picks per text region, so listing more than one costs
# little and handles mixed-language documents.
DEFAULT_LANGUAGES = ["en-US", "pl-PL", "de-DE", "fr-FR"]

# Used if the OS query fails, which should not happen on a supported system.
FALLBACK_LANGUAGES = ["en-US"]


def page_image_to_cgimage(page: PageImage):
    """Wrap a PageImage's raw buffer in a CGImage.

    Requires 4-byte pixels. CoreGraphics cannot consume 24-bit RGB: it returns
    a 0x0 image, and Vision then reports failure with a None result rather than
    raising. PageImage rejects non-RGBX modes to make that unrepresentable.
    """
    provider = Quartz.CGDataProviderCreateWithData(
        None, page.buffer, len(page.buffer), None
    )
    color_space = Quartz.CGColorSpaceCreateDeviceRGB()
    cgimage = Quartz.CGImageCreate(
        page.width,
        page.height,
        8,   # bits per component
        32,  # bits per pixel
        page.stride,
        color_space,
        Quartz.kCGImageAlphaNoneSkipLast | Quartz.kCGBitmapByteOrderDefault,
        provider,
        None,
        False,
        Quartz.kCGRenderingIntentDefault,
    )
    if cgimage is None or Quartz.CGImageGetWidth(cgimage) == 0:
        raise RuntimeError(
            f"CoreGraphics rejected a {page.width}x{page.height} "
            f"{page.mode} buffer with stride {page.stride}"
        )
    return cgimage


class VisionOcrEngine:
    """Vision-backed OCR. Language codes are BCP-47, e.g. 'en-US', 'pl-PL'."""

    @property
    def name(self) -> str:
        return "Apple Vision"

    def supported_languages(self) -> list[str]:
        """Recognition languages this macOS version provides.

        The list grows with the OS, so it is queried rather than hardcoded --
        macOS 13 offers fewer than macOS 26's 30.
        """
        request = Vision.VNRecognizeTextRequest.alloc().init()
        result = request.supportedRecognitionLanguagesAndReturnError_(None)
        languages = result[0] if result and result[0] else None
        return list(languages) if languages else list(FALLBACK_LANGUAGES)

    def default_languages(self) -> list[str]:
        supported = set(self.supported_languages())
        chosen = [code for code in DEFAULT_LANGUAGES if code in supported]
        return chosen or self.supported_languages()[:1]

    def recognize(self, page: PageImage, languages=None) -> str:
        """Extract text from one page, in top-to-bottom reading order."""
        codes = languages or self.default_languages()
        cgimage = page_image_to_cgimage(page)

        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
            cgimage, None
        )
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setRecognitionLanguages_(codes)
        request.setUsesLanguageCorrection_(True)

        succeeded, error = handler.performRequests_error_([request], None)
        if not succeeded:
            raise RuntimeError(f"Vision text recognition failed: {error}")

        observations = request.results()
        if not observations:
            return ""

        return "\n".join(self._read_in_order(observations))

    @staticmethod
    def _read_in_order(observations) -> list[str]:
        """Sort observations into reading order and take the best candidate.

        Vision does not guarantee ordering. Bounding boxes are normalized with
        the origin at the bottom-left, so descending y is top-to-bottom.
        """
        def position(observation):
            box = observation.boundingBox()
            return -box.origin.y, box.origin.x

        lines = []
        for observation in sorted(observations, key=position):
            candidates = observation.topCandidates_(1)
            if candidates:
                lines.append(candidates[0].string())
        return lines
