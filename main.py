#!/usr/bin/env python3
"""
QuickPdfOcr - GUI Application Entry Point
A simple Qt6-based PDF OCR application
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Setup bundled Poppler binaries if available
from components.poppler_utils import setup_poppler_path
setup_poppler_path()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("QuickPdfOcr")
    app.setOrganizationName("QuickPdfOcr")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
