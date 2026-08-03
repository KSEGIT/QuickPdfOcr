#!/usr/bin/env python3
"""
QuickPdfOcr - GUI Application Entry Point
A simple Qt6-based PDF OCR application
"""

import re
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


def _run_selftest(argv) -> int:
    """Run OCR on a PDF without starting the GUI.

    Exit codes:
        0 -- OCR ran and produced text beyond the page headers.
        1 -- OCR raised an exception (missing file, unreadable PDF, engine failure).
        2 -- usage error: --selftest was given with no path following it.
        3 -- OCR completed without error but extracted no text.
    """
    index = argv.index("--selftest")
    if index + 1 >= len(argv):
        print("--selftest requires a PDF path", file=sys.stderr)
        return 2

    pdf_path = argv[index + 1]
    from components.ocr import get_engine
    from components.pdf_ocr import PdfOcrProcessor

    engine = get_engine()
    print(f"self-test: engine={engine.name} file={pdf_path}")

    try:
        text = PdfOcrProcessor().process(pdf_path)
    except Exception as exc:
        print(f"self-test FAILED: {exc}", file=sys.stderr)
        return 1

    # The processor always adds "--- Page N ---" headers, so every one of them
    # must be stripped before checking for actual content -- not just the
    # first, or a multi-page document with zero OCR text still "passes" on
    # the strength of its own page headers.
    stripped = re.sub(r'---\s*Page\s+\d+\s*---', '', text).strip()
    if not stripped:
        print("self-test FAILED: no text extracted", file=sys.stderr)
        return 3

    print(f"self-test PASSED, {len(stripped)} characters extracted")
    print(text)
    return 0


class QuickPdfOcrApplication(QApplication):
    """QApplication that accepts files opened from Finder or the Dock.

    macOS does not pass double-clicked files in argv -- it sends a FileOpen
    event, which may arrive before the main window exists. Early events are
    queued and replayed once the window is ready.
    """

    def __init__(self, argv):
        super().__init__(argv)
        self._window = None
        self._pending_file = None

    def set_window(self, window):
        """Attach the main window and replay any queued file."""
        self._window = window
        if self._pending_file:
            window.open_file(self._pending_file)
            self._pending_file = None

    def event(self, event):
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.FileOpen:
            path = event.file()
            if path.lower().endswith(".pdf"):
                if self._window is not None:
                    self._window.open_file(path)
                else:
                    self._pending_file = path
            return True
        return super().event(event)


def main():
    """Main application entry point"""
    # Headless self-test, used by CI to prove the packaged app can actually OCR.
    # The existing build produced artifacts that were never executed, which is
    # why issue #26 shipped.
    if "--selftest" in sys.argv:
        sys.exit(_run_selftest(sys.argv))

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
    app = QuickPdfOcrApplication(sys.argv)
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
    app.set_window(window)

    # Windows and Linux pass the file in argv; macOS uses the FileOpen event above.
    for argument in sys.argv[1:]:
        if argument.lower().endswith(".pdf") and Path(argument).exists():
            window.open_file(argument)
            break

    # Close loading screen and show main window after fade-out completes
    def on_initialization_complete():
        """Handle transition from loading screen to main window"""
        loading_screen.close_with_fade(on_finished=lambda: window.show())
    
    QTimer.singleShot(LOADING_TO_MAIN_DELAY, on_initialization_complete)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
