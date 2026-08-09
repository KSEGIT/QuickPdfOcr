"""
OCR Worker - Background thread for PDF OCR processing
"""

import re

from PySide6.QtCore import QObject, Signal
from components.ocr.base import OcrEngineUnavailable
from components.pdf_ocr import PdfOcrProcessor


class OCRWorker(QObject):
    """Worker class to run OCR in a background thread"""

    progress = Signal(str)  # Progress message
    finished = Signal(str)  # Completed with extracted text
    error = Signal(str)     # Error message

    def __init__(self, pdf_path: str, languages: list[str] | None = None):
        super().__init__()
        self.pdf_path = pdf_path
        self.languages = languages
        self._stop_requested = False

    def request_stop(self):
        """Request the worker to stop processing at the next opportunity."""
        self._stop_requested = True

    def run(self):
        """Execute OCR processing"""
        try:
            # Create OCR processor
            processor = PdfOcrProcessor(languages=self.languages)

            # Wrap the progress callback to check for stop requests between
            # pages.  The processor calls this once per page, giving us a
            # cooperative cancellation point without modifying PdfOcrProcessor.
            def progress_callback(message):
                if self._stop_requested:
                    raise InterruptedError("OCR processing was cancelled")
                self.progress.emit(message)

            # Run OCR with progress callback
            text = processor.process(
                self.pdf_path,
                output_file=None,
                progress_callback=progress_callback,
            )

            # Check if we got any meaningful text beyond page headers
            # The processor always adds "--- Page N ---" headers, so we must
            # strip those before checking for actual content
            content_only = re.sub(r'---\s*Page\s+\d+\s*---', '', text).strip()
            if not content_only:
                self.error.emit("No text could be extracted from the PDF")
                return

            # Success!
            self.finished.emit(text)

        except InterruptedError:
            # Worker was asked to stop — exit silently without emitting signals
            return
        except FileNotFoundError as e:
            self.error.emit(f"File not found: {str(e)}")
        except ValueError as e:
            self.error.emit(f"Invalid file: {str(e)}")
        except OcrEngineUnavailable as e:
            # A whole-document failure (missing OCR engine/language data),
            # not a bug in this app -- report it plainly, like the other
            # expected-failure branches above, rather than falling through
            # to the generic handler's full traceback dump.
            self.error.emit(str(e))
        except Exception as e:
            # Provide more detailed error information
            import traceback
            error_details = traceback.format_exc()
            self.error.emit(f"OCR failed: {str(e)}\n\nDetails:\n{error_details}")
