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
from components.poppler_utils import setup_bundled_binaries

# Constants
LOADING_TO_MAIN_DELAY = 300  # Delay in milliseconds before showing main window


def initialize_application(loading_screen):
    """
    Initialize application components with progress feedback
    
    Args:
        loading_screen: LoadingScreen instance to update with progress
    """
    # Setup bundled binaries (Poppler and Tesseract) if available
    def progress_callback(message):
        """Update loading screen with progress message"""
        loading_screen.set_progress(message)
        QApplication.processEvents()  # Process GUI events to update the display
    
    setup_bundled_binaries(progress_callback=progress_callback)
    
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
    
    # Close loading screen and show main window after fade-out completes
    def on_initialization_complete():
        """Handle transition from loading screen to main window"""
        loading_screen.close_with_fade(on_finished=window.show)
    
    QTimer.singleShot(LOADING_TO_MAIN_DELAY, on_initialization_complete)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
