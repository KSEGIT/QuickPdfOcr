#!/usr/bin/env python3
"""
PDF OCR Component - Extract text from PDF files using OCR
Uses pytesseract (Tesseract OCR) - the most popular open-source OCR engine
"""

import sys
from pathlib import Path
from typing import Optional, Callable

# Setup bundled binaries (Poppler and Tesseract) if available
from components.poppler_utils import setup_bundled_binaries
setup_bundled_binaries()

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError
    import pytesseract
    from PIL import Image
    import PyPDF2
except ImportError as e:
    print(f"Error: Missing required library - {e}")
    print("\nPlease install required packages:")
    print("  pip install pytesseract pdf2image pillow PyPDF2")
    print("\nAlso install system dependencies:")
    print("  macOS: brew install tesseract poppler")
    print("  Linux: sudo apt-get install tesseract-ocr poppler-utils")
    sys.exit(1)


class PdfOcrProcessor:
    """PDF OCR Processor Component"""
    
    def __init__(self, lang='eng'):
        """
        Initialize the PDF OCR processor
        
        Args:
            lang (str): Tesseract language code (default: 'eng' for English)
        """
        self.lang = lang
        self.dpi = None
    
    def detect_optimal_dpi(self, pdf_path: Path) -> int:
        """
        Auto-detect optimal DPI based on PDF characteristics
        
        Args:
            pdf_path (Path): Path to the PDF file
        
        Returns:
            int: Recommended DPI value
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Get first page to analyze
                if len(pdf_reader.pages) == 0:
                    return 300  # Default fallback
                
                page = pdf_reader.pages[0]
                
                # Get page dimensions (in points, 1 point = 1/72 inch)
                if '/MediaBox' in page:
                    media_box = page.mediabox
                    width_points = float(media_box.width)
                    height_points = float(media_box.height)
                    
                    # Convert to inches
                    width_inches = width_points / 72
                    height_inches = height_points / 72
                    
                    # Determine DPI based on page size
                    # Small pages (like receipts) need higher DPI
                    # Standard letter/A4 can use medium DPI
                    # Large pages can use lower DPI
                    
                    max_dimension = max(width_inches, height_inches)
                    
                    if max_dimension < 6:  # Small document (receipt, card, etc.)
                        dpi = 400
                        reason = "small document detected"
                    elif max_dimension < 10:  # Standard size (letter, A4)
                        dpi = 300
                        reason = "standard document size"
                    elif max_dimension < 14:  # Legal, A3
                        dpi = 250
                        reason = "large document detected"
                    else:  # Very large documents
                        dpi = 200
                        reason = "very large document detected"
                    
                    print(f"Auto-detected DPI: {dpi} ({reason})")
                    print(f"  Page size: {width_inches:.1f}\" × {height_inches:.1f}\"")
                    return dpi
                
        except Exception as e:
            print(f"Warning: Could not auto-detect DPI ({e}), using default 300")
        
        return 300  # Default fallback
    
    def process(
        self, 
        pdf_path: str, 
        output_file: Optional[str] = None, 
        dpi: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Extract text from PDF using OCR
        
        Args:
            pdf_path (str): Path to the PDF file
            output_file (str, optional): Path to save extracted text. If None, doesn't save to file
            dpi (int, optional): Resolution for PDF to image conversion. If None, auto-detects optimal DPI
            progress_callback (callable, optional): Function to call with progress updates
        
        Returns:
            str: Extracted text
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a PDF
            RuntimeError: If PDF conversion or OCR fails
        """
        # Validate input file
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF: {pdf_path}")
        
        self._log(f"Processing PDF: {pdf_path.name}", progress_callback)
        
        # Auto-detect DPI if not specified
        if dpi is None:
            dpi = self.detect_optimal_dpi(pdf_path)
        
        self.dpi = dpi
        self._log(f"Converting PDF to images (DPI: {dpi})...", progress_callback)
        
        # Convert PDF to images
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")
        
        self._log(f"Found {len(images)} page(s)", progress_callback)
        
        # Extract text from each page
        all_text = []
        for i, image in enumerate(images, 1):
            self._log(f"Processing page {i}/{len(images)}...", progress_callback)
            try:
                # Perform OCR on the image
                text = pytesseract.image_to_string(image, lang=self.lang)
                all_text.append(f"--- Page {i} ---\n{text}\n")
            except Exception as e:
                print(f"Warning: Failed to process page {i}: {e}")
                all_text.append(f"--- Page {i} ---\n[OCR Error]\n")
        
        # Combine all text
        final_text = "\n".join(all_text)
        
        # Save results if output file specified
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(final_text, encoding='utf-8')
            self._log(f"Text extracted and saved to: {output_path}", progress_callback)
        
        return final_text
    
    def _log(self, message: str, callback: Optional[Callable[[str], None]] = None):
        """
        Log a message, either via callback or print
        
        Args:
            message (str): Message to log
            callback (callable, optional): Progress callback function
        """
        if callback:
            callback(message)
        else:
            print(message)


# Backward compatibility function
def ocr_pdf(pdf_path, output_file=None, dpi=None, lang='eng'):
    """
    Legacy function for backward compatibility
    Extract text from PDF using OCR
    
    Args:
        pdf_path (str): Path to the PDF file
        output_file (str, optional): Path to save extracted text. If None, prints to stdout
        dpi (int, optional): Resolution for PDF to image conversion. If None, auto-detects optimal DPI
        lang (str): Tesseract language code (default: 'eng' for English)
    
    Returns:
        str: Extracted text
    """
    processor = PdfOcrProcessor(lang=lang)
    final_text = processor.process(pdf_path, output_file=output_file, dpi=dpi)
    
    if not output_file:
        print("\n" + "="*60)
        print("EXTRACTED TEXT:")
        print("="*60)
        print(final_text)
    
    return final_text


def main():
    """Main entry point for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python pdf_ocr.py <pdf_file> [output_file] [--dpi DPI] [--lang LANG]")
        print("\nExamples:")
        print("  python pdf_ocr.py document.pdf                      # Auto-detect DPI")
        print("  python pdf_ocr.py document.pdf output.txt")
        print("  python pdf_ocr.py document.pdf --dpi 400 --lang eng # Manual DPI")
        print("  python pdf_ocr.py document.pdf output.txt --lang fra")
        print("\nCommon language codes:")
        print("  eng = English, fra = French, deu = German, spa = Spanish")
        print("  chi_sim = Chinese Simplified, jpn = Japanese")
        print("\nNote: DPI is auto-detected by default based on document size")
        sys.exit(1)
    
    # Parse arguments
    pdf_path = sys.argv[1]
    output_file = None
    dpi = None  # Auto-detect by default
    lang = 'eng'
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--dpi' and i + 1 < len(sys.argv):
            dpi = int(sys.argv[i + 1])
            i += 2
        elif arg == '--lang' and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('--'):
            output_file = arg
            i += 1
        else:
            i += 1
    
    # Run OCR
    try:
        ocr_pdf(pdf_path, output_file, dpi=dpi, lang=lang)
        print("\n✓ OCR completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
