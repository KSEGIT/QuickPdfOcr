"""Tests for QuickPdfOcrApplication's FileOpen event handling.

macOS delivers a double-clicked, Dock-dropped, or "Open With"-launched PDF as
a QEvent.FileOpen rather than via argv, and that event can arrive *before*
the main window exists (Qt processes it as soon as the event loop starts,
which can be ahead of MainWindow() finishing construction). An
implementation that only forwards FileOpen to an already-existing window
silently drops the file the user just opened.

QuickPdfOcrApplication (see main.py) handles this by queuing the path in
_pending_file when no window is attached yet, and replaying it in
set_window() once the window shows up. These tests cover all three delivery
paths so that behavior cannot regress silently:

  1. FileOpen before set_window() -- queued, then replayed.
  2. FileOpen after set_window() -- delivered immediately.
  3. A non-PDF FileOpen -- ignored outright (neither queued nor opened).

A fourth test covers a related bug found in review: QuickPdfOcrApplication
calls window.open_file() unconditionally, with no gate against an OCR run
already in progress -- unlike the drop zone and file-picker button, which
_set_controls_enabled(False) disables while a run is active. Without a
guard in MainWindow.open_file() itself, an OS-delivered FileOpen event
mid-run would silently swap current_file out from under the in-flight
OCRWorker, misattributing its result (or a "Try Again" retry) to the wrong
document.
"""

import pytest
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

from main import QuickPdfOcrApplication
from ui.main_window import MainWindow


class FakeFileOpenEvent(QEvent):
    """A stand-in for the QFileOpenEvent macOS sends on file-open.

    PySide6 does not expose a public constructor for real QFileOpenEvent
    objects from Python, so tests build a minimal QEvent subclass exposing
    the same file() accessor QuickPdfOcrApplication.event() reads.
    """

    def __init__(self, path: str):
        super().__init__(QEvent.Type.FileOpen)
        self._path = path

    def file(self):
        return self._path


@pytest.fixture(scope="module")
def app() -> QuickPdfOcrApplication:
    """The process-wide QApplication.

    QApplication is a singleton per process, so this reuses whatever
    instance already exists (from another GUI test module) instead of
    constructing a second one, which Qt does not allow. If some other
    module got there first with a plain QApplication instead of
    QuickPdfOcrApplication, fail loudly here rather than let every test in
    this module die with a bare AttributeError on ._window/._pending_file
    that gives no hint why.
    """
    instance = QApplication.instance()
    if instance is None:
        return QuickPdfOcrApplication([])
    if not isinstance(instance, QuickPdfOcrApplication):
        pytest.fail(
            "QApplication.instance() is a plain QApplication, not "
            "QuickPdfOcrApplication -- some other test module must have "
            "constructed it first. tests/test_file_open.py needs the "
            "QuickPdfOcrApplication subclass to exercise set_window()/event()."
        )
    return instance


@pytest.fixture
def window(app):
    """A fresh MainWindow, detached from the shared app after each test so
    state from one test cannot leak into the next."""
    win = MainWindow()
    yield win
    app._window = None
    app._pending_file = None
    win.deleteLater()


def test_file_open_before_window_is_queued_then_replayed(app, window, sample_pdf):
    """An event arriving before the window is attached must be queued, not
    dropped, and replayed onto the window once set_window() runs."""
    app._window = None
    app._pending_file = None
    path = str(sample_pdf)

    result = app.event(FakeFileOpenEvent(path))
    assert result is True, "FileOpen event must be reported as handled"
    assert app._pending_file == path, "early FileOpen event was lost"

    app.set_window(window)

    assert window.current_file == path, "queued file was not replayed onto the window"
    assert app._pending_file is None


def test_file_open_after_window_goes_straight_through(app, window, sample_pdf):
    """An event arriving once the window is already attached must be
    delivered immediately, bypassing the pending-file queue entirely."""
    app.set_window(window)
    app._pending_file = None
    path = str(sample_pdf)

    result = app.event(FakeFileOpenEvent(path))

    assert result is True, "FileOpen event must be reported as handled"
    assert window.current_file == path
    assert app._pending_file is None


def test_non_pdf_file_open_is_ignored(app, window):
    """A FileOpen event for a non-PDF path must be neither queued nor
    opened -- only .pdf paths are meaningful to this app."""
    app.set_window(window)
    window.current_file = None
    app._pending_file = None

    result = app.event(FakeFileOpenEvent("/some/document.txt"))

    assert result is True, "FileOpen event must be reported as handled even when ignored"
    assert window.current_file is None, "non-PDF path was opened"
    assert app._pending_file is None, "non-PDF path was queued"


def test_file_open_is_refused_while_ocr_is_running(app, window, sample_pdf, multipage_pdf):
    """Regression test: before this task, MainWindow.open_file()'s only entry
    points (drop zone, file-picker button) were disabled during an OCR run
    via _set_controls_enabled(False). QuickPdfOcrApplication.event() calls
    window.open_file() unconditionally, so an OS-delivered FileOpen event
    arriving mid-run must be refused by open_file() itself, or it would
    silently swap current_file out from under the in-flight OCRWorker.
    """
    app.set_window(window)
    window.open_file(str(sample_pdf))
    assert window.current_file == str(sample_pdf)

    class _StubRunningThread:
        """Lightweight stand-in for a QThread that is still running -- no
        real QThread is started, only isRunning() is queried by the guard."""

        def isRunning(self):
            return True

    window.ocr_thread = _StubRunningThread()

    result = app.event(FakeFileOpenEvent(str(multipage_pdf)))

    assert result is True, "FileOpen event must be reported as handled even when refused"
    assert window.current_file == str(sample_pdf), (
        "file-open delivered while OCR is running must not replace current_file"
    )
