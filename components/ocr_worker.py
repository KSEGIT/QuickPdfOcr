"""OCR Worker - Background thread for PDF OCR processing"""

import re
import traceback

from PySide6.QtCore import QObject, Signal
from components.pdf_ocr import PdfOcrProcessor


class OCRWorker(QObject):
    """Worker class to run OCR in a background thread"""

    progress = Signal(str)          # Progress message
    page_progress = Signal(int, int)  # (current_page, total_pages)
    finished = Signal(str)          # Completed with extracted text
    error = Signal(str)             # Error message

    def __init__(self, pdf_path: str, lang: str = "eng"):
        super().__init__()
        self.pdf_path = pdf_path
        self.lang = lang
        self._stop_requested = False

    def request_stop(self):
        """Request the worker to stop processing at the next opportunity."""
        self._stop_requested = True

    def run(self):
        """Execute OCR processing"""
        try:
            processor = PdfOcrProcessor(lang=self.lang)

            def progress_callback(message):
                if self._stop_requested:
                    raise InterruptedError("OCR processing was cancelled")
                self.progress.emit(message)
                # Parse "Processing page X/Y..." messages for progress bar
                match = re.match(r'Processing page (\d+)/(\d+)', message)
                if match:
                    self.page_progress.emit(int(match.group(1)), int(match.group(2)))

            text = processor.process(
                self.pdf_path,
                output_file=None,
                progress_callback=progress_callback,
            )

            content_only = re.sub(r'---\s*Page\s+\d+\s*---', '', text).strip()
            if not content_only:
                self.error.emit("No text could be extracted from the PDF")
                return

            self.finished.emit(text)

        except InterruptedError:
            return
        except FileNotFoundError as e:
            self.error.emit(f"File not found: {str(e)}")
        except ValueError as e:
            self.error.emit(f"Invalid file: {str(e)}")
        except Exception as e:
            error_details = traceback.format_exc()
            self.error.emit(f"OCR failed: {str(e)}\n\nDetails:\n{error_details}")
