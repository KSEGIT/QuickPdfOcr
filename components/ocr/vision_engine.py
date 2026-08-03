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

# Two observations count as sharing a visual line when their vertical centres
# are within half a box height of each other. Real text lines are rarely
# bit-for-bit aligned -- baselines and box heights differ slightly even for
# words that a human reads as "the same row".
LINE_OVERLAP_RATIO = 0.5


def page_image_to_cgimage(page: PageImage):
    """Wrap a PageImage's raw buffer in a CGImage.

    Requires 4-byte pixels. CoreGraphics cannot consume 24-bit RGB: it returns
    a 0x0 image, and Vision then reports failure with a None result rather than
    raising. PageImage rejects non-RGBX modes to make that unrepresentable.
    """
    # PyObjC retains its own strong reference to the Python buffer passed here,
    # so the CGImage (and anything derived from it) does not depend on the
    # PageImage outliving this call. Verified experimentally with a __del__
    # canary on the buffer object.
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

    def recognize(self, page: PageImage, languages: list[str] | None = None) -> str:
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
        """Group observations into visual lines and read each line left to right.

        Vision does not guarantee ordering. Bounding boxes are normalized with
        the origin at the bottom-left, so descending vertical centre is
        top-to-bottom. A single sort by (y, x) is not enough: two observations
        on the same printed line rarely share an identical origin.y (box
        heights and baselines differ), so an x tiebreak that only applies on
        exact y equality never fires on real documents -- rows like
        "Netto: 1000,00    VAT: 234,56" can come out reversed. Grouping by
        vertical proximity first, then sorting each group by x, fixes that.
        """
        def vertical_center(observation):
            box = observation.boundingBox()
            return box.origin.y + box.size.height / 2

        ordered = sorted(observations, key=vertical_center, reverse=True)

        groups = []
        for observation in ordered:
            box = observation.boundingBox()
            center = box.origin.y + box.size.height / 2
            if groups:
                group_center, _ = groups[-1]
                threshold = LINE_OVERLAP_RATIO * box.size.height
                if abs(center - group_center) <= threshold:
                    groups[-1][1].append(observation)
                    continue
            groups.append((center, [observation]))

        lines = []
        for _, members in groups:
            members.sort(key=lambda observation: observation.boundingBox().origin.x)
            words = []
            for observation in members:
                candidates = observation.topCandidates_(1)
                if candidates:
                    words.append(candidates[0].string())
            if words:
                lines.append(" ".join(words))
        return lines
