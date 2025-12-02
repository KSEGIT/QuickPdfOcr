#!/usr/bin/env python3
"""
QuickPdfOcr - GUI Application Entry Point
A simple Qt6-based PDF OCR application
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow

# Setup bundled binaries (Poppler and Tesseract) if available
from components.poppler_utils import setup_bundled_binaries
setup_bundled_binaries()


def main():
    """Main application entry point"""
    # Print startup diagnostics
    print("\n" + "="*60)
    print("QuickPdfOcr - Starting Application")
    print("="*60)
    
    # Check if running from bundle
    import os
    if getattr(sys, 'frozen', False):
        print(f"Running from PyInstaller bundle")
        print(f"Bundle directory: {sys._MEIPASS}")
    else:
        print(f"Running from Python interpreter")
    
    print("="*60 + "\n")
    
    app = QApplication(sys.argv)
    app.setApplicationName("QuickPdfOcr")
    app.setOrganizationName("QuickPdfOcr")
    
    # Set application icon
    icon_path = None
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source
        base_path = Path(__file__).parent
    
    # Try to load the icon
    icon_file = base_path / "resources" / "icon.png"
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))
        print(f"Loaded icon from: {icon_file}")
    else:
        print(f"Warning: Icon not found at {icon_file}")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
