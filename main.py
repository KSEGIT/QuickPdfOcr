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

# Constants
LOADING_TO_MAIN_DELAY = 300  # Delay in milliseconds before showing main window


def initialize_application(loading_screen):
    """
    Initialize application components with progress feedback

    Args:
        loading_screen: LoadingScreen instance to update with progress
    """
    # There are no external binaries to locate any more: PDF rendering is
    # bundled in the pypdfium2 wheel and OCR comes from the OS on macOS.
    loading_screen.set_progress("Preparing OCR engine...")
    QApplication.processEvents()

    # Instantiating the engine here surfaces any platform problem on the
    # loading screen rather than on the first OCR run.
    from components.ocr import get_engine

    engine = get_engine()
    loading_screen.set_progress(f"Using {engine.name}...")
    QApplication.processEvents()

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
        loading_screen.close_with_fade(on_finished=lambda: window.show())
    
    QTimer.singleShot(LOADING_TO_MAIN_DELAY, on_initialization_complete)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
