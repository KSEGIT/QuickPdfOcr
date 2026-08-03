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
    constructing a second one, which Qt does not allow.
    """
    return QApplication.instance() or QuickPdfOcrApplication([])


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

    app.event(FakeFileOpenEvent(path))
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

    app.event(FakeFileOpenEvent(path))

    assert window.current_file == path
    assert app._pending_file is None


def test_non_pdf_file_open_is_ignored(app, window):
    """A FileOpen event for a non-PDF path must be neither queued nor
    opened -- only .pdf paths are meaningful to this app."""
    app.set_window(window)
    window.current_file = None
    app._pending_file = None

    app.event(FakeFileOpenEvent("/some/document.txt"))

    assert window.current_file is None, "non-PDF path was opened"
    assert app._pending_file is None, "non-PDF path was queued"
