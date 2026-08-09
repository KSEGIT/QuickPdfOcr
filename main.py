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

    try:
        engine = get_engine()
        loading_screen.set_progress(f"Using {engine.name}...")
        QApplication.processEvents()
    except Exception as exc:
        loading_screen.set_progress(f"Error: {exc}")
        QApplication.processEvents()
        QTimer.singleShot(3000, lambda: sys.exit(1))
        return

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

    # Detect OCR error markers that PdfOcrProcessor._process_page() produces
    # when OCR processing fails on a page.
    if "[OCR Error:" in text:
        print("self-test FAILED: OCR error marker present in output", file=sys.stderr)
        return 1

    print(f"self-test PASSED, {len(stripped)} characters extracted")
    print(text)
    return 0


# Lazily-built, process-wide cache for the Services provider's Objective-C
# class. PyObjC raises if two distinct Python classes are ever registered
# under the same Objective-C class name in one process, so the class itself
# must be defined exactly once -- see _get_services_provider_class().
_pdf_services_provider_class = None


def _pdf_path_from_pasteboard(pasteboard):
    """Extract the first usable PDF path from a Cocoa Services pasteboard.

    Modern senders put NSURL objects on the pasteboard; NSSendFileTypes in
    packaging/quickpdfocr.spec restricts Finder to offering this Service for
    PDFs only, but a deleted-since-selected or otherwise-wrong path is still
    checked defensively rather than trusted, the same as main()'s argv
    handling does for double-clicked files. Some senders instead put a bare
    path string on the pasteboard, so that is tried as a fallback.
    """
    import AppKit

    def _is_usable_pdf(path) -> bool:
        return bool(path) and path.lower().endswith(".pdf") and Path(path).exists()

    urls = pasteboard.readObjectsForClasses_options_([AppKit.NSURL], None) or []
    for url in urls:
        path = url.path()
        if _is_usable_pdf(path):
            return path

    text = pasteboard.stringForType_(AppKit.NSPasteboardTypeString)
    if _is_usable_pdf(text):
        return text

    return None


def _get_services_provider_class():
    """Lazily define, once, the NSObject subclass implementing the Cocoa
    Services 'openFile:userData:error:' selector declared by NSServices in
    packaging/quickpdfocr.spec's Info.plist.

    AppKit is imported here, inside this macOS-only code path, rather than
    at module top -- Windows and Linux cannot import it at all, and
    --selftest must stay free of GUI/AppKit imports.
    """
    global _pdf_services_provider_class
    if _pdf_services_provider_class is not None:
        return _pdf_services_provider_class

    import AppKit

    class _PdfServicesProvider(AppKit.NSObject):
        """A Services invocation is delivered via distributed objects, not
        a QEvent.FileOpen -- Finder's Services menu never produces the
        event QuickPdfOcrApplication.event() handles below. This is a
        second, required delivery path for the same PDF-opening behavior;
        `.app` is set on each instance after construction and is the
        QuickPdfOcrApplication to forward opened files to.
        """

        def openFile_userData_error_(self, pasteboard, userData, error):
            app = getattr(self, "app", None)
            if app is None:
                return None
            path = _pdf_path_from_pasteboard(pasteboard)
            if path:
                app._open_pdf_path(path)
            return None

    _pdf_services_provider_class = _PdfServicesProvider
    return _pdf_services_provider_class


class QuickPdfOcrApplication(QApplication):
    """QApplication that accepts files opened from Finder, the Dock, or the
    Finder Services menu.

    macOS does not pass double-clicked files in argv -- it sends a FileOpen
    event, which may arrive before the main window exists. Early events are
    queued and replayed once the window is ready. A Finder Services
    invocation ("Right-click a PDF -> Services -> OCR with QuickPdfOcr")
    arrives through a completely different mechanism -- see
    _register_services_provider() -- but converges on the same
    queue-or-open-immediately logic in _open_pdf_path().
    """

    def __init__(self, argv):
        super().__init__(argv)
        self._window = None
        self._pending_file = None
        self._services_provider = None  # see _register_services_provider()

    def set_window(self, window):
        """Attach the main window, replay any queued file, and register the
        Finder Services provider now that there is a window to deliver to."""
        self._window = window
        if self._pending_file:
            window.open_file(self._pending_file)
            self._pending_file = None
        self._register_services_provider()

    def _open_pdf_path(self, path):
        """Shared delivery point for a PDF path arriving via QEvent.FileOpen
        or a Finder Services invocation: queue it if the window is not
        attached yet (mirroring the FileOpen behavior above), otherwise hand
        it straight to MainWindow.open_file(), which itself refuses the
        file while an OCR run is already in progress."""
        if self._window is not None:
            self._window.open_file(path)
        else:
            self._pending_file = path

    def event(self, event):
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.FileOpen:
            path = event.file()
            if path.lower().endswith(".pdf"):
                self._open_pdf_path(path)
            return True
        return super().event(event)

    def _build_services_provider(self):
        """Construct, but do not register, the NSObject implementing the
        Cocoa Services selector. Split out from _register_services_provider
        so tests can build a provider and call its method directly without
        touching the real, process-wide NSApplication services
        registration. Callers must only invoke this on macOS."""
        provider_class = _get_services_provider_class()
        provider = provider_class.alloc().init()
        provider.app = self
        return provider

    def _register_services_provider(self):
        """Register the Finder Services entry declared by NSServices in
        packaging/quickpdfocr.spec, so 'Right-click a PDF -> Services ->
        OCR with QuickPdfOcr' actually calls into the app instead of
        silently doing nothing.

        A no-op off macOS and idempotent (registration only needs to happen
        once). Best-effort: any import or registration failure is logged
        and swallowed rather than raised -- a broken Service must not
        prevent the app from launching.
        """
        if sys.platform != "darwin" or self._services_provider is not None:
            return
        try:
            provider = self._build_services_provider()
            # setServicesProvider_ does NOT retain its argument (unlike most
            # AppKit setters). A provider that only lived in a local
            # variable here would be garbage-collected as soon as this
            # method returns, and the Service would then silently do
            # nothing the next time Finder invokes it. Storing it on self
            # keeps it alive for the app's lifetime.
            self._services_provider = provider

            import AppKit

            AppKit.NSApplication.sharedApplication().setServicesProvider_(provider)
        except Exception as exc:
            print(f"Warning: could not register Finder Services provider: {exc}")


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
