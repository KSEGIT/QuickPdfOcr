import pytest
from pathlib import Path
from components.pdf_ocr import PdfOcrProcessor


class TestPdfOcrProcessor:
    def test_init_default_language(self):
        processor = PdfOcrProcessor()
        assert processor.lang == "eng"

    def test_init_custom_language(self):
        processor = PdfOcrProcessor(lang="fra")
        assert processor.lang == "fra"

    def test_process_file_not_found(self):
        processor = PdfOcrProcessor()
        with pytest.raises(FileNotFoundError):
            processor.process("/nonexistent/file.pdf")

    def test_process_not_pdf(self, tmp_path):
        fake = tmp_path / "not_a_pdf.txt"
        fake.write_text("hello")
        processor = PdfOcrProcessor()
        with pytest.raises(ValueError, match="must be a PDF"):
            processor.process(str(fake))

    def test_detect_optimal_dpi_corrupt_fallback(self, tmp_path):
        """DPI detection on a corrupt file should return 300 default."""
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_bytes(b"%PDF-1.4 garbage")
        processor = PdfOcrProcessor()
        dpi = processor.detect_optimal_dpi(bad_pdf)
        assert dpi == 300
