#!/usr/bin/env python3
"""
QuickPdfOcr - GUI Application Entry Point
A simple Qt6-based PDF OCR application
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow
from ui.loading_screen import LoadingScreen


def initialize_application(loading_screen):
    """
    Initialize application components with progress feedback
    
    Args:
        loading_screen: LoadingScreen instance to update with progress
    """
    # Setup bundled binaries (Poppler and Tesseract) if available
    loading_screen.set_progress("Setting up Poppler binaries...")
    QApplication.processEvents()  # Process GUI events to update the display
    
    from components.poppler_utils import setup_poppler_path
    setup_poppler_path()
    
    loading_screen.set_progress("Setting up Tesseract OCR...")
    QApplication.processEvents()
    
    from components.poppler_utils import setup_tesseract_path
    setup_tesseract_path()
    
    loading_screen.set_progress("Finalizing initialization...")
    QApplication.processEvents()


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
    
    # Create QApplication first
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
    
    # Show loading screen immediately
    loading_screen = LoadingScreen()
    loading_screen.show()
    QApplication.processEvents()  # Ensure loading screen is displayed
    
    # Initialize application components with progress feedback
    initialize_application(loading_screen)
    
    # Create and show main window
    loading_screen.set_progress("Loading main window...")
    QApplication.processEvents()
    
    window = MainWindow()
    
    # Close loading screen and show main window with a small delay for smooth transition
    def show_main_window():
        loading_screen.close_with_fade()
        window.show()
    
    QTimer.singleShot(300, show_main_window)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
