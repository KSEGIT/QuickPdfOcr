"""Behavior-level guards that MainWindow/DropZoneLabel reach for the
*intended* palette token in each visual state.

tests/test_ui_theme.py proves the tokens themselves clear their contrast
floors; these prove the code actually applies the right one, so a future
edit that swaps (say) TEXT and ERR in _on_ocr_error() -- both individually
valid theme.py constants -- is still caught.
"""
from pathlib import Path

import pytest
from PySide6.QtGui import QIcon

from ui.main_window import DropZoneLabel, MainWindow
from ui.theme import BG, DIM, ERR, FRAME_PRESSED, OK, TEXT, WARN


@pytest.fixture
def window(qapp):
    """A fresh MainWindow, torn down after each test.

    Also resets qapp._window/_pending_file (as tests/test_file_open.py's
    fixture does) even though no test in this file currently calls
    qapp.set_window() itself: MainWindow.__init__() does not touch either
    attribute, so this is a no-op today, but it keeps this fixture safe by
    construction if a future test here does start calling set_window() --
    forgetting that reset is exactly what test_file_open.py's fixture
    comment warns leaks a deleted MainWindow into a later, unrelated test
    via the session-scoped QApplication.
    """
    win = MainWindow()
    yield win
    qapp._window = None
    qapp._pending_file = None
    win.deleteLater()


class _StubRunningThread:
    """Lightweight stand-in for a QThread that is still running -- no real
    QThread is started, only isRunning() is queried by the guard. Mirrors
    tests/test_file_open.py's identically-named, identically-shaped class;
    duplicated locally rather than imported across test modules (test
    modules importing test-scoped helpers from each other is more coupling
    than this one four-line class is worth avoiding)."""

    def isRunning(self):
        return True


class _FakeUrl:
    """Stand-in for a QUrl: dropEvent only ever calls toLocalFile()."""

    def __init__(self, path: str):
        self._path = path

    def toLocalFile(self):
        return self._path


class _FakeMimeData:
    def __init__(self, urls):
        self._urls = urls

    def urls(self):
        return self._urls

    def hasUrls(self):
        return bool(self._urls)


class _FakeDropEvent:
    """Stand-in for QDropEvent: dropEvent() only calls mimeData() and
    acceptProposedAction(), so a real QDropEvent (fiddly to construct
    off-screen) is unnecessary -- mirrors tests/test_file_open.py's
    FakeFileOpenEvent approach for the same reason."""

    def __init__(self, urls):
        self._mime = _FakeMimeData(urls)

    def mimeData(self):
        return self._mime

    def acceptProposedAction(self):
        pass


def test_drop_zone_invalid_drop_shows_warning_style(qapp):
    """Regression test: dropEvent() used to call dragLeaveEvent() *after*
    _show_drop_warning() set the warning style, immediately overwriting it
    back to idle within the same call -- so the warning colour never
    actually rendered, only its text did. dragLeaveEvent() is now called
    first, so the warning style set by _show_drop_warning() is the one left
    standing."""
    zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)
    zone.dropEvent(_FakeDropEvent([_FakeUrl("/tmp/not-a-pdf.txt")]))

    assert zone.styleSheet() == DropZoneLabel._WARNING_STYLE
    assert zone.text() == "Please drop a PDF file"


def test_drop_zone_valid_pdf_emits_and_leaves_idle_style(qapp):
    """A valid drop must still emit file_dropped, and -- since nothing else
    is listening in this isolated test -- the drag-hover decoration must
    have already been cleared to idle by dragLeaveEvent() before the signal
    fired, not left in drag-hover indefinitely."""
    zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)
    received = []
    zone.file_dropped.connect(received.append)

    zone.dropEvent(_FakeDropEvent([_FakeUrl("/tmp/sample.pdf")]))

    assert received == ["/tmp/sample.pdf"]
    assert zone.styleSheet() == DropZoneLabel._IDLE_STYLE


def test_drag_leave_restores_the_accepted_display_rather_than_idle(qapp):
    """Regression test: dragLeaveEvent() used to apply _IDLE_STYLE
    unconditionally, without touching the text. A drag that entered and
    left again while a file was already loaded therefore left the accepted
    *filename* rendered in the idle style -- the same "zone display
    disagrees with the loaded file" inconsistency _reset_text() was
    introduced to fix, reached via the drag-leave path instead of the
    warning timer. dragLeaveEvent() now delegates to that same helper."""
    zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)
    zone.set_accepted("report.pdf")

    zone.dragEnterEvent(_FakeDropEvent([_FakeUrl("/tmp/other.txt")]))
    assert zone.styleSheet() == DropZoneLabel._DRAG_HOVER_STYLE

    zone.dragLeaveEvent(_FakeDropEvent([_FakeUrl("/tmp/other.txt")]))

    assert zone.text() == "report.pdf"
    assert zone.styleSheet() == DropZoneLabel._ACCEPTED_STYLE


def test_drag_leave_stays_idle_when_no_file_was_ever_accepted(qapp):
    """The other half of the branch: with nothing loaded, drag-leave must
    still land on the idle text and style, exactly as before."""
    zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)

    zone.dragEnterEvent(_FakeDropEvent([_FakeUrl("/tmp/other.txt")]))
    zone.dragLeaveEvent(_FakeDropEvent([_FakeUrl("/tmp/other.txt")]))

    assert zone.text() == DropZoneLabel._DEFAULT_TEXT
    assert zone.styleSheet() == DropZoneLabel._IDLE_STYLE


def test_open_file_applies_accepted_style(window, sample_pdf):
    window.open_file(str(sample_pdf))

    assert window.drop_zone.styleSheet() == DropZoneLabel._ACCEPTED_STYLE
    assert window.drop_zone.text() == Path(sample_pdf).name


def test_start_over_resets_drop_zone_to_idle_style(window, sample_pdf):
    window.open_file(str(sample_pdf))

    window._start_over()

    assert window.drop_zone.styleSheet() == DropZoneLabel._IDLE_STYLE
    assert window.drop_zone.text() == DropZoneLabel._DEFAULT_TEXT


def test_ocr_success_uses_ok_as_the_message_colour(window):
    window._on_ocr_success("hello world")

    assert f"color: {OK};" in window.progress_label.styleSheet()


def test_ocr_error_keeps_text_as_message_colour_and_err_as_accent_only(window):
    """ERR (#EF4444) measures 3.89:1 on SURFACE -- it clears the 3:1
    non-text floor but fails the 4.5:1 text floor (see
    tests/test_ui_theme.py). The error state must therefore keep the
    message body in TEXT and confine ERR to the left-border accent, not
    promote ERR to the text colour itself."""
    window._on_ocr_error("boom")

    style = window.progress_label.styleSheet()
    assert f"color: {TEXT};" in style
    assert f"border-left: 4px solid {ERR};" in style


def test_ignored_run_warning_keeps_text_as_message_colour(window, sample_pdf):
    window.open_file(str(sample_pdf))
    window.ocr_thread = _StubRunningThread()

    window.open_file(str(sample_pdf))

    style = window.progress_label.styleSheet()
    assert f"color: {TEXT};" in style
    assert f"border-left: 4px solid {WARN};" in style


def test_warning_timeout_restores_accepted_file_instead_of_blanking_it(window, sample_pdf):
    """Regression test for a bug the whole-branch review found: dropping an
    invalid file onto the zone *while a valid file is already loaded and
    Start OCR is armed* used to blank the zone back to "Drop PDF file here"
    once the 3s warning timer fired -- even though current_file, file_label,
    and start_ocr_btn all still referred to the original PDF. The zone told
    the user nothing was loaded while Start OCR would have silently run on
    the old file. DropZoneLabel now tracks which file (if any) it was told
    is accepted, and _reset_text() restores that display instead of always
    reverting to idle."""
    window.open_file(str(sample_pdf))

    window.drop_zone._show_drop_warning()
    assert window.drop_zone.text() == "Please drop a PDF file"

    # Fire the timer's callback directly rather than waiting out the real
    # 3s delay.
    window.drop_zone._reset_text()

    assert window.drop_zone.text() == Path(sample_pdf).name
    assert window.drop_zone.styleSheet() == DropZoneLabel._ACCEPTED_STYLE
    assert window.current_file == str(sample_pdf)
    assert window.start_ocr_btn.isEnabled()


def test_warning_timeout_reverts_to_idle_when_no_file_was_ever_accepted(qapp):
    """The other half of the fix above: when no file has ever been
    accepted, the timeout must still revert to the plain idle state, not
    get stuck trying to restore a file name that was never set."""
    zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)

    zone._show_drop_warning()
    zone._reset_text()

    assert zone.text() == DropZoneLabel._DEFAULT_TEXT
    assert zone.styleSheet() == DropZoneLabel._IDLE_STYLE


def test_buttons_have_a_pressed_style(window):
    """Regression test: the five buttons' original per-button stylesheets
    each had a QPushButton:pressed rule; the shared _button_style() this
    branch introduced dropped it entirely (0 press feedback where there
    used to be 5). FRAME_PRESSED is measured in ui/theme.py (4.89:1, dark
    ink on top of it) rather than reusing FRAME/FRAME_HOVER, so pressing a
    button now visibly darkens beyond its hover fill."""
    for button in (
        window.open_btn, window.start_ocr_btn, window.copy_btn,
        window.retry_btn, window.start_over_btn,
    ):
        assert f"background-color: {FRAME_PRESSED};" in button.styleSheet(), (
            f"{button.text()!r} button has no :pressed styling"
        )


def test_disableable_buttons_pass_dim_as_the_disabled_icon_colour(window):
    """Regression test: Qt auto-generates a disabled-mode icon pixmap via
    its style's default grey-out algorithm when none is explicitly
    registered -- measured at #6C6C6C, only 2.79:1 on SURFACE (below even
    the 3:1 non-text floor). open_btn and start_ocr_btn are the only two
    buttons _set_controls_enabled() ever disables (see that method), so
    they are the only two that need an explicit DIM-tinted Disabled-mode
    pixmap registered."""
    for button in (window.open_btn, window.start_ocr_btn):
        disabled_pixmap = button.icon().pixmap(18, 18, QIcon.Mode.Disabled)
        normal_pixmap = button.icon().pixmap(18, 18, QIcon.Mode.Normal)
        assert _first_opaque_pixel(disabled_pixmap) == DIM.lower()
        assert _first_opaque_pixel(normal_pixmap) == BG.lower()


def _first_opaque_pixel(pixmap):
    img = pixmap.toImage()
    for y in range(img.height()):
        for x in range(img.width()):
            color = img.pixelColor(x, y)
            if color.alpha() == 255:
                return color.name()
    return None
