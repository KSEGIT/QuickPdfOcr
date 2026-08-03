"""Tests for MainWindow's OCR-thread lifecycle bookkeeping.

CRITICAL bug found in the whole-branch review: _start_ocr() wires
`self.ocr_thread.finished.connect(self.ocr_thread.deleteLater)`, but nothing
ever reset `self.ocr_thread` (or `self.ocr_worker`) back to None once a run
completed. `_is_ocr_running()` -- which sits at the top of `open_file()`, the
single entry point for drag-drop, the file picker, Finder double-click, Dock
drop, and Services -- then called `isRunning()` on a Python wrapper whose
underlying C++ QThread had already been deleted by that same deleteLater().
PySide raises:

    RuntimeError: libshiboken: Internal C++ object (PySide6.QtCore.QThread)
    already deleted.

Since this happened inside a Qt slot, PySide only printed the traceback to
stderr (invisible inside a packaged .app) and the UI did not change at all --
every open_file() call after the first completed OCR run silently did
nothing, permanently, until the app was relaunched.

tests/test_file_open.py's `_StubRunningThread` stand-in cannot catch this
class of bug: it is a plain Python object, never a real QThread, so it has
no C++ side to delete. This test uses a genuine QThread -- started, quit,
waited, and deleteLater()-processed through the event loop -- to reproduce
the actual deleted-wrapper condition before asserting open_file() still
works.
"""

import time

import pytest
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app() -> QApplication:
    """The process-wide QApplication.

    QApplication is a singleton per process, so this reuses whatever
    instance already exists (from another GUI test module) instead of
    constructing a second one, which Qt does not allow.
    """
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    """A fresh MainWindow, torn down after each test so state from one test
    cannot leak into the next."""
    win = MainWindow()
    yield win
    win.deleteLater()


class _TrivialWorker(QObject):
    """A worker whose run() does nothing but announce completion -- enough
    to drive a real QThread through its full started -> finished lifecycle
    without doing any actual OCR work."""

    done = Signal()

    def run(self):
        self.done.emit()


def _destroyed_thread(app: QApplication) -> QThread:
    """Build a real QThread wired exactly like _start_ocr() wires
    self.ocr_thread, run it to completion, and pump the event loop until its
    deleteLater() call has actually been processed -- reproducing a wrapper
    whose underlying C++ QThread object is gone, not merely a thread that
    has stopped running.

    Deliberately does NOT use QThread.wait() to detect completion: wait()
    blocks the calling (main) thread without pumping its event queue, but
    worker.done.connect(thread.quit) is a cross-thread queued connection --
    delivering it requires the main thread's event loop to actually run.
    Blocking in wait() before ever calling processEvents() would deadlock
    the two threads against each other (this was verified experimentally:
    wait() reliably timed out). The production app never hits this because
    QApplication.exec() is already pumping events continuously; a test
    without that must pump explicitly instead of blocking.
    """
    thread = QThread()
    worker = _TrivialWorker()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.done.connect(thread.quit)
    worker.done.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()

    deadline = time.monotonic() + 5
    while thread.isRunning() and time.monotonic() < deadline:
        app.processEvents()
    assert not thread.isRunning(), "worker thread did not finish in time"

    # isRunning() becoming False only means the thread function returned;
    # both deleteLater() calls (worker's and the thread's own) are queued
    # events that still need further event-loop turns to actually process.
    for _ in range(50):
        app.processEvents()

    # Confirm the C++ object is really gone, not just stopped -- otherwise
    # this test would not be exercising the bug at all.
    with pytest.raises(RuntimeError):
        thread.isRunning()

    return thread


def test_open_file_works_after_a_thread_is_destroyed(app, window, sample_pdf):
    """Regression test for the CRITICAL bug described above: open_file()
    must succeed even when self.ocr_thread references a QThread wrapper
    whose underlying C++ object has already been deleted."""
    window.ocr_thread = _destroyed_thread(app)
    window.ocr_worker = None

    window.open_file(str(sample_pdf))

    assert window.current_file == str(sample_pdf)


def test_is_ocr_running_treats_a_deleted_thread_as_not_running(app, window):
    """Direct unit test of the defensive catch in _is_ocr_running(), so the
    behavior is pinned independently of open_file()'s other side effects."""
    window.ocr_thread = _destroyed_thread(app)

    assert window._is_ocr_running() is False


def test_start_ocr_wires_a_thread_finished_clearer(window, sample_pdf, monkeypatch):
    """The other half of the fix: _start_ocr() must wire something that
    clears self.ocr_thread once QThread.finished fires, or the same
    deleted-wrapper condition reappears the next time _is_ocr_running() (or
    _start_ocr()'s own guard) is evaluated.

    Deliberately does not spin a real background thread to observe this:
    running a second genuine QThread lifecycle through app.exec() in the
    same process as _destroyed_thread()'s real QThread(s) was found,
    empirically, to segfault intermittently (roughly one run in three) --
    reproducible with a fake OCR engine too, so it is unrelated to Vision or
    pdfium specifically, and looks like a PySide/Qt interaction between
    successive QThread create/destroy cycles within one process rather than
    anything wrong with the fix. QThread.start() is patched to a no-op so
    _start_ocr() runs its real wiring/connection code -- the thing being
    tested -- without ever creating an actual OS thread; QThread.finished
    is then emitted manually to simulate genuine completion.
    """
    monkeypatch.setattr(QThread, "start", lambda self: None)
    window.current_file = str(sample_pdf)

    window._start_ocr()
    thread = window.ocr_thread
    assert thread is not None, "_start_ocr() did not create self.ocr_thread"

    thread.finished.emit()

    assert window.ocr_thread is None, "ocr_thread was not cleared once finished fired"
