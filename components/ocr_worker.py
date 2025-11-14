"""
OCR Worker - Background thread for PDF OCR processing
"""

from PySide6.QtCore import QObject, Signal
from components.pdf_ocr import PdfOcrProcessor


class OCRWorker(QObject):
    """Worker class to run OCR in a background thread"""
    
    progress = Signal(str)  # Progress message
    finished = Signal(str)  # Completed with extracted text
    error = Signal(str)     # Error message
    
    def __init__(self, pdf_path: str):
        super().__init__()
        self.pdf_path = pdf_path
    
    def run(self):
        """Execute OCR processing"""
        try:
            # Create OCR processor
            processor = PdfOcrProcessor(lang='eng')
            
            # Run OCR with progress callback
            text = processor.process(
                self.pdf_path, 
                output_file=None,
                progress_callback=self.progress.emit
            )
            
            # Check if we got any text
            if not text or text.strip() == "":
                self.error.emit("No text could be extracted from the PDF")
                return
            
            # Success!
            self.finished.emit(text)
            
        except FileNotFoundError as e:
            self.error.emit(f"File not found: {str(e)}")
        except ValueError as e:
            self.error.emit(f"Invalid file: {str(e)}")
        except Exception as e:
            self.error.emit(f"OCR failed: {str(e)}")
