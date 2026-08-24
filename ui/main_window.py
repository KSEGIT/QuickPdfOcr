"""
Main Window UI for QuickPdfOcr
Features: drag-and-drop file upload, OCR processing with progress feedback,
text display with copy functionality
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QSize
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPalette

from components.ocr_worker import OCRWorker
from components.ocr import describe_language, get_engine
from ui.icons import load_icon
from ui.theme import (
    ACCENT, BG, DIM, ERR, FRAME, FRAME_HOVER, FRAME_PRESSED, OK, SURFACE, TEXT, WARN,
)

# Logical pixel size icons are rendered at for buttons -- see ui/icons.py.
_ICON_SIZE = 18

# Qt's default (unstyled) scrollbar renders in the native light appearance
# regardless of the rest of the widget's QSS -- left alone, it shows up as
# a plain white/grey bar against text_area's dark panel the moment content
# overflows. Shared by text_area and the language combo's popup view, the
# two scrollable widgets in this window.
_SCROLLBAR_QSS = f"""
    QScrollBar:vertical {{
        background: {SURFACE};
        width: 12px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {FRAME};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {FRAME_HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        border: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""


def _drop_zone_style(border_color: str, text_color: str) -> str:
    """QSS for DropZoneLabel's four states: idle, drag-hover, warning, and
    accepted all share the same geometry (dashed border, big centered
    padding) and only differ in which colour carries the state, so this is
    the one place that geometry is written out."""
    return f"""
        QLabel {{
            border: 3px dashed {border_color};
            border-radius: 10px;
            padding: 40px;
            background-color: {SURFACE};
            font-size: 16px;
            color: {text_color};
        }}
    """


def _status_style(text_color: str, accent_color: str) -> str:
    """QSS for progress_label's four semantic states (active/success/
    warning/error): a --surface card whose left border carries the state's
    accent colour.

    `text_color` is `accent_color` itself for the active/success states --
    ACCENT and OK both clear the 4.5:1 text floor against --surface (see
    tests/test_ui_theme.py). The warning and error states both pass TEXT
    instead: WARN *could* be used as text here too (6.81:1 on --surface),
    but the one caller that reaches the warning state (open_file()'s
    "already running" branch) keeps the message body in TEXT for visual
    consistency with the error state, using WARN only for the left-border
    accent. ERR has no such choice -- it only clears the 3:1 non-text floor
    against --surface (3.89:1), not the 4.5:1 text floor, so TEXT is not
    optional there the same way it is for warning -- the same lesson
    docs/index.html's --bar/--bar-ink split encodes for the site.
    """
    return f"""
        QLabel {{
            color: {text_color};
            font-size: 14px;
            padding: 10px;
            background-color: {SURFACE};
            border-left: 4px solid {accent_color};
            border-radius: 5px;
        }}
    """


def _button_style(font_size: int = 14) -> str:
    """QSS shared by every QPushButton in this window.

    background=FRAME/color=BG (5.98:1) is the same "dark ink on light-indigo
    fill" formula docs/index.html's filled .btn-primary variants settled on
    -- white-on-FRAME measures 2.98:1 there and fails, which is why this
    reuses that finding instead of re-deriving it. FRAME_HOVER is that same
    page's --indigo-hover, reused verbatim for the hover fill (8.96:1).
    FRAME_PRESSED is this file's own addition (the site has no :active state
    to reuse) for a "pushed in" cue on click -- 4.89:1, see ui/theme.py.
    """
    return f"""
        QPushButton {{
            background-color: {FRAME};
            color: {BG};
            border: none;
            border-radius: 5px;
            font-size: {font_size}px;
            font-weight: bold;
            padding: 4px 12px;
        }}
        QPushButton:hover {{
            background-color: {FRAME_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {FRAME_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {SURFACE};
            color: {DIM};
        }}
    """


class DropZoneLabel(QLabel):
    """Custom label that accepts drag-and-drop file operations"""

    file_dropped = Signal(str)

    _DEFAULT_TEXT = "Drop PDF file here"

    _IDLE_STYLE = _drop_zone_style(FRAME, DIM)
    _DRAG_HOVER_STYLE = _drop_zone_style(ACCENT, ACCENT)
    _WARNING_STYLE = _drop_zone_style(WARN, WARN)
    _ACCEPTED_STYLE = _drop_zone_style(OK, OK)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Name of the currently-loaded file, or None. Tracked here (not just
        # read off MainWindow.current_file) so _reset_text() -- fired by the
        # warning timer below, entirely on its own schedule -- can tell
        # whether a file is still loaded when it fires. See its docstring
        # for the bug this exists to fix.
        self._accepted_file_name: str | None = None

        # Timer to auto-clear the drop-zone warning after a delay
        self._warning_timer = QTimer(self)
        self._warning_timer.setSingleShot(True)
        self._warning_timer.timeout.connect(self._reset_text)

        self.setStyleSheet(self._IDLE_STYLE)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag events with files"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self._DRAG_HOVER_STYLE)

    def dragLeaveEvent(self, event):
        """Reset style when drag leaves"""
        self.setStyleSheet(self._IDLE_STYLE)

    def dropEvent(self, event: QDropEvent):
        """Handle dropped files"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        event.acceptProposedAction()
        # Clear the drag-hover decoration *before* deciding the outcome
        # below, not after: the warning/accepted styles those branches set
        # must be the last stylesheet applied, or this unconditional
        # dragLeaveEvent() call -- previously last -- immediately overwrote
        # them with the idle style within the same call, so the warning
        # colour never actually appeared (only its text did).
        self.dragLeaveEvent(event)
        if not files:
            self._show_drop_warning()
        elif files[0].lower().endswith('.pdf'):
            self.file_dropped.emit(files[0])
        else:
            self._show_drop_warning()

    def _show_drop_warning(self):
        """Show a temporary warning when a non-PDF (or empty) drop occurs."""
        self.setText("Please drop a PDF file")
        self.setStyleSheet(self._WARNING_STYLE)
        self._warning_timer.start(3000)

    def _reset_text(self):
        """Restore the drop zone once the warning timer fires.

        Regression fix: this used to unconditionally reset to the empty
        idle state ("Drop PDF file here"), including while a file was
        already loaded -- e.g. drop a valid PDF, then drop a .txt on top of
        it 2 seconds later: 3 seconds after *that*, this fired and blanked
        the zone back to "Drop PDF file here" even though current_file,
        file_label, and the still-enabled Start OCR button all still
        referred to the original PDF. The zone told the user nothing was
        loaded while Start OCR would have silently run on the old file.
        Restoring the accepted display (when set_accepted() has been
        called since the last reset_to_idle()) instead of always going to
        idle fixes that without DropZoneLabel needing to know anything
        about OCR state -- only whether *it* was last told a file was
        accepted.
        """
        if self._accepted_file_name is not None:
            self.setText(self._accepted_file_name)
            self.setStyleSheet(self._ACCEPTED_STYLE)
        else:
            self.setText(self._DEFAULT_TEXT)
            self.setStyleSheet(self._IDLE_STYLE)

    def set_accepted(self, file_name: str):
        """Show `file_name` as the currently-loaded file.

        Cancels any pending warning-reset timer, so a warning from a
        rejected drop that happened *before* this file was accepted cannot
        later fire and overwrite this display -- and records the name so a
        *later* warning (e.g. a stray invalid drop after this file is
        already loaded) restores this display instead of blanking it; see
        _reset_text().
        """
        self._warning_timer.stop()
        self._accepted_file_name = file_name
        self.setText(file_name)
        self.setStyleSheet(self._ACCEPTED_STYLE)

    def reset_to_idle(self):
        """Explicitly clear back to the empty idle state (Start Over)."""
        self._warning_timer.stop()
        self._accepted_file_name = None
        self.setText(self._DEFAULT_TEXT)
        self.setStyleSheet(self._IDLE_STYLE)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.ocr_thread = None
        self.ocr_worker = None

        # Query the platform engine once; the language list depends on the OS
        # version, so it is never hardcoded.
        self.engine = get_engine()

        self.setWindowTitle("QuickPdfOcr")
        self.setMinimumSize(600, 500)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface"""
        # Central widget and main layout
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {BG};")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Drop zone label
        self.drop_zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)
        self.drop_zone.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self.drop_zone)

        # Open file button. disabled_color=DIM: this button is disabled
        # during an OCR run (_set_controls_enabled(False)); without an
        # explicit disabled-mode pixmap, Qt auto-generates one via its
        # style's default grey-out algorithm -- measured at #6C6C6C, only
        # 2.79:1 on SURFACE (below even the 3:1 non-text floor). DIM
        # matches the disabled *text* colour in _button_style() below, so
        # icon and label dim together at a colour that actually clears it.
        self.open_btn = QPushButton("Open PDF File")
        self.open_btn.setIcon(load_icon("folder-open.svg", BG, _ICON_SIZE, disabled_color=DIM))
        self.open_btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.open_btn.setMinimumHeight(40)
        self.open_btn.setStyleSheet(_button_style(14))
        self.open_btn.clicked.connect(self._open_file_dialog)
        layout.addWidget(self.open_btn)

        # Language selector, populated from whichever engine this platform uses
        language_layout = QHBoxLayout()
        language_layout.setSpacing(10)

        language_caption = QLabel("Language:")
        language_caption.setStyleSheet(f"color: {DIM};")
        language_layout.addWidget(language_caption)

        self.language_combo = QComboBox()
        self.language_combo.setMinimumHeight(30)
        self.language_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {FRAME};
                border-radius: 5px;
                padding: 4px 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {SURFACE};
                color: {TEXT};
                selection-background-color: {FRAME};
                selection-color: {BG};
            }}
            {_SCROLLBAR_QSS}
        """)
        self._populate_languages()
        language_layout.addWidget(self.language_combo, 1)

        layout.addLayout(language_layout)

        # File name label (hidden initially)
        self.file_label = QLabel("")
        self.file_label.setStyleSheet(f"color: {TEXT}; font-weight: bold;")
        self.file_label.hide()
        layout.addWidget(self.file_label)

        # Start OCR button (hidden initially). disabled_color=DIM: see the
        # matching comment on open_btn above -- this is the other button
        # _set_controls_enabled(False) disables during an OCR run.
        self.start_ocr_btn = QPushButton("Start OCR")
        self.start_ocr_btn.setIcon(load_icon("scan-text.svg", BG, _ICON_SIZE, disabled_color=DIM))
        self.start_ocr_btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.start_ocr_btn.setMinimumHeight(40)
        self.start_ocr_btn.setStyleSheet(_button_style(14))
        self.start_ocr_btn.clicked.connect(self._start_ocr)
        self.start_ocr_btn.hide()
        layout.addWidget(self.start_ocr_btn)

        # Progress/feedback label (hidden initially)
        self.progress_label = QLabel("Processing...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(_status_style(ACCENT, ACCENT))
        self.progress_label.hide()
        layout.addWidget(self.progress_label)

        # Text area for results (hidden initially)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Extracted text will appear here...")
        # Deliberately no `color:` in this QSS block -- see the QPalette
        # block below for why. background/border/padding/font are fine as
        # QSS since none of them have this problem.
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {SURFACE};
                border: 1px solid {FRAME};
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }}
            {_SCROLLBAR_QSS}
        """)
        # Both the real text colour and the placeholder colour are set via
        # QPalette, not QSS's `color:` property, and in that order (palette
        # after stylesheet). QSS has no property for placeholder-text
        # colour, so with no explicit override Qt derives it from the `color:`
        # declaration at 50% alpha composited over the background -- verified
        # by rendering off-screen and sampling the painted glyphs: that
        # composite measures ~4.1:1 against SURFACE, below the 4.5:1 text
        # floor, and the placeholder is the only text visible in this panel
        # before an OCR run. Setting PlaceholderText via QPalette *while a
        # `color:` QSS rule is still present* was tried first and verified
        # NOT to work -- Qt's stylesheet engine re-derives PlaceholderText
        # from that rule on every polish, silently discarding the palette
        # value regardless of which was set first. Omitting `color:` from
        # the QSS avoids that engine entirely, so the explicit Text and
        # PlaceholderText roles below are what actually gets painted for both
        # real content and placeholder.
        text_area_palette = self.text_area.palette()
        text_area_palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
        text_area_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DIM))
        self.text_area.setPalette(text_area_palette)
        self.text_area.hide()
        layout.addWidget(self.text_area, 1)  # Stretch factor of 1

        # Button container for copy and retry buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Copy button (hidden initially)
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setIcon(load_icon("clipboard.svg", BG, _ICON_SIZE))
        self.copy_btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.copy_btn.setMinimumHeight(35)
        self.copy_btn.setStyleSheet(_button_style(13))
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.copy_btn.hide()
        button_layout.addWidget(self.copy_btn)

        # Try again button (hidden initially)
        self.retry_btn = QPushButton("Try Again")
        self.retry_btn.setIcon(load_icon("rotate-ccw.svg", BG, _ICON_SIZE))
        self.retry_btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.retry_btn.setMinimumHeight(35)
        self.retry_btn.setStyleSheet(_button_style(13))
        self.retry_btn.clicked.connect(self._retry_ocr)
        self.retry_btn.hide()
        button_layout.addWidget(self.retry_btn)

        # Start over button (hidden initially)
        self.start_over_btn = QPushButton("Start Over")
        self.start_over_btn.setIcon(load_icon("house.svg", BG, _ICON_SIZE))
        self.start_over_btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self.start_over_btn.setMinimumHeight(35)
        self.start_over_btn.setStyleSheet(_button_style(13))
        self.start_over_btn.clicked.connect(self._start_over)
        self.start_over_btn.hide()
        button_layout.addWidget(self.start_over_btn)

        layout.addLayout(button_layout)

    def _populate_languages(self):
        """Fill the language dropdown from the active engine.

        Vision's language list grows with the macOS version and Tesseract's
        depends on installed .traineddata, so this is queried at runtime.
        """
        self.language_combo.addItem(f"Automatic ({self.engine.name})", None)

        for code in self.engine.supported_languages():
            self.language_combo.addItem(f"{describe_language(code)} ({code})", code)

    def _selected_languages(self):
        """Language codes for the current selection, or None for automatic."""
        code = self.language_combo.currentData()
        return [code] if code else None

    def _set_controls_enabled(self, enabled: bool):
        """Enable or disable the four interactive controls together.

        Keeps start_ocr_btn, open_btn, language_combo, and the drop zone's
        drop-acceptance in one consistent state, so no exit path -- success,
        error, or a failed-cleanup early return -- can strand a subset of
        them disabled while the rest of the window looks usable.
        """
        self.start_ocr_btn.setEnabled(enabled)
        self.open_btn.setEnabled(enabled)
        self.language_combo.setEnabled(enabled)
        self.drop_zone.setAcceptDrops(enabled)

    def _open_file_dialog(self):
        """Open file picker dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf)"
        )

        if file_path:
            self._on_file_dropped(file_path)

    def _is_ocr_running(self) -> bool:
        """Whether an OCR run is currently in progress.

        Guards entry points the OS can invoke at arbitrary times -- Finder
        double-click, Dock drop, "Open With" -- which, unlike the drop zone
        and file-picker button, are not disabled by
        _set_controls_enabled(False) while a run is active.
        """
        if self.ocr_thread is None:
            return False
        try:
            return self.ocr_thread.isRunning()
        except RuntimeError:
            # self.ocr_thread is a Python wrapper around a QThread whose
            # underlying C++ object has already been deleted (deleteLater()
            # fired -- see the wiring in _start_ocr()) but the attribute
            # itself was not reset in time to observe that. A deleted
            # QThread cannot possibly still be running, so treat this the
            # same as "no thread at all" rather than letting the exception
            # propagate out of a slot, where PySide only prints it to
            # stderr (invisible inside a packaged .app) and leaves the
            # caller's control flow silently broken.
            return False

    def open_file(self, file_path: str):
        """Load a PDF for OCR. Public entry point used by drag-drop, the file
        picker, and macOS 'Open With' / Dock-drop events. macOS can invoke
        this at any time -- including mid-OCR -- so a run already in progress
        is refused rather than silently swapping out current_file underneath
        it and misattributing the in-flight result to the wrong document."""
        if self._is_ocr_running():
            file_name = Path(file_path).name
            self.progress_label.setText(
                f"Ignored \"{file_name}\": an OCR run is already in "
                "progress. Please wait for it to finish."
            )
            self.progress_label.setStyleSheet(_status_style(TEXT, WARN))
            self.progress_label.show()
            return

        self.current_file = file_path
        file_name = Path(file_path).name

        # Update UI. set_accepted() also cancels any pending warning-reset
        # timer (so it cannot overwrite the filename about to be shown) and
        # records file_name so a *later* stray warning restores this
        # display instead of blanking it -- see DropZoneLabel._reset_text().
        # This is the single code path for both drag-drop and file-dialog
        # selection.
        self.drop_zone.set_accepted(file_name)
        self.file_label.setText(f"Selected: {file_name}")
        self.file_label.show()
        self.start_ocr_btn.show()

        # Hide previous results
        self.text_area.hide()
        self.text_area.clear()
        self.copy_btn.hide()
        self.retry_btn.hide()
        self.start_over_btn.hide()
        self.progress_label.hide()

    def _on_file_dropped(self, file_path: str):
        """Slot for the drop zone's file_dropped signal."""
        self.open_file(file_path)

    def _start_ocr(self):
        """Start OCR processing in background thread"""
        if not self.current_file:
            return

        # Clean up any previous thread before starting a new one. Routed
        # through _is_ocr_running() rather than calling isRunning() directly
        # here, so this guard gets the same defensiveness against a deleted
        # QThread wrapper as open_file()'s guard does.
        if self._is_ocr_running():
            # Ask the worker to stop cooperatively first
            if self.ocr_worker is not None:
                self.ocr_worker.request_stop()
            self.ocr_thread.quit()
            if not self.ocr_thread.wait(5000):
                print(
                    f"WARNING: OCR thread (id={int(self.ocr_thread.currentThreadId())}) "
                    "did not stop within 5 s — calling terminate(). "
                    "This may leak platform resources."
                )
                self.ocr_thread.terminate()
                if not self.ocr_thread.wait(5000):
                    print(
                        "ERROR: OCR thread did not terminate within 5 s after "
                        "terminate(). Aborting new OCR to avoid undefined state."
                    )
                    # The stuck worker's run() exits via InterruptedError,
                    # which emits no signal, so neither _on_ocr_success nor
                    # _on_ocr_error will ever fire to re-enable the controls
                    # the previous _start_ocr() call disabled. Re-enable them
                    # here so the window isn't left permanently unusable.
                    self._set_controls_enabled(True)
                    self.progress_label.setText(
                        "The previous OCR run could not be stopped. Please try again."
                    )
                    self.progress_label.setStyleSheet(_status_style(TEXT, ERR))
                    self.progress_label.show()
                    return

        # Disable buttons during processing
        self._set_controls_enabled(False)

        # Show progress
        self.progress_label.setText("Converting PDF to images...")
        self.progress_label.setStyleSheet(_status_style(ACCENT, ACCENT))
        self.progress_label.show()

        # Create worker thread
        self.ocr_thread = QThread()
        self.ocr_worker = OCRWorker(self.current_file, languages=self._selected_languages())
        self.ocr_worker.moveToThread(self.ocr_thread)
        thread = self.ocr_thread  # local alias for the closure below

        # Connect signals
        self.ocr_thread.started.connect(self.ocr_worker.run)
        self.ocr_worker.progress.connect(self._on_progress)
        self.ocr_worker.finished.connect(self._on_ocr_success)
        self.ocr_worker.error.connect(self._on_ocr_error)
        self.ocr_worker.finished.connect(self.ocr_thread.quit)
        self.ocr_worker.error.connect(self.ocr_thread.quit)
        self.ocr_worker.finished.connect(self.ocr_worker.deleteLater)
        self.ocr_worker.error.connect(self.ocr_worker.deleteLater)
        self.ocr_thread.finished.connect(self.ocr_thread.deleteLater)

        def _clear_ocr_thread_reference():
            """Drop self.ocr_thread once QThread's own 'finished' signal
            proves the managed thread has genuinely stopped -- see the
            long comment on this connection, below, for why this cannot be
            done from _on_ocr_success()/_on_ocr_error() instead, and why a
            closure over `thread` is used rather than a plain bound method
            relying on self.sender() (confirmed experimentally to return
            None for this connection, since it is a Python-level slot
            invoked through a queued cross-thread delivery, not a real Qt
            meta-slot that Qt's sender-tracking recognizes)."""
            # A subsequent _start_ocr() call may already have replaced
            # self.ocr_thread with a new QThread by the time this
            # (possibly delayed) signal is delivered -- only ever clear
            # our own reference to *this* thread, never a newer one.
            if self.ocr_thread is thread:
                self.ocr_thread = None

        # Clearing self.ocr_thread happens here, tied to QThread's own
        # "the managed thread has actually stopped" signal, rather than in
        # _on_ocr_success()/_on_ocr_error(). Those two are connected to the
        # same worker.finished/error signal *ahead of* self.ocr_thread.quit()
        # a few lines above -- a cross-thread queued connection delivered in
        # FIFO order -- so by the time either slot runs, quit() has not even
        # been dispatched yet, let alone taken effect. Clearing
        # self.ocr_thread there would drop the last Python reference to a
        # QThread wrapper while Qt still considers the underlying thread
        # running, which cascades into deleting a still-running QThread's
        # C++ object -- verified experimentally to abort the whole process
        # ("QThread: Destroyed while thread is still running") rather than
        # merely log a warning. QThread.finished only fires once the
        # managed thread has actually stopped, so clearing here is safe.
        self.ocr_thread.finished.connect(_clear_ocr_thread_reference)

        # Start processing
        self.ocr_thread.start()

    def _on_progress(self, message: str):
        """Update progress message"""
        self.progress_label.setText(message)

    def _on_ocr_success(self, text: str):
        """Handle successful OCR completion"""
        self.progress_label.setText("OCR completed successfully!")
        self.progress_label.setStyleSheet(_status_style(OK, OK))

        # Show results
        self.text_area.setPlainText(text)
        self.text_area.show()
        self.copy_btn.show()
        self.start_over_btn.show()

        # Re-enable controls
        self._set_controls_enabled(True)

        # Clear our reference to the worker, now that it is done -- safe
        # here because worker.deleteLater() (connected in _start_ocr(),
        # ahead of this slot on the same signal) already ran synchronously
        # as a direct, same-thread connection by the time this slot is
        # even reachable, so the worker's fate is already sealed either
        # way. self.ocr_thread is deliberately NOT cleared here -- see the
        # comment on the ocr_thread.finished connection in _start_ocr() for
        # why doing so from this slot would be unsafe.
        self.ocr_worker = None

    def _on_ocr_error(self, error_msg: str):
        """Handle OCR error"""
        self.progress_label.setText(f"Error: {error_msg}")
        self.progress_label.setStyleSheet(_status_style(TEXT, ERR))

        # Show retry buttons
        self.retry_btn.show()
        self.start_over_btn.show()

        # Re-enable controls
        self._set_controls_enabled(True)

        # See the matching comment in _on_ocr_success() for why only the
        # worker reference is cleared here.
        self.ocr_worker = None

    def _copy_to_clipboard(self):
        """Copy text to clipboard (works on macOS, Linux, Windows)"""
        from PySide6.QtGui import QGuiApplication

        text = self.text_area.toPlainText()
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

        # Show confirmation
        QMessageBox.information(
            self,
            "Copied",
            "Text copied to clipboard!",
            QMessageBox.StandardButton.Ok
        )

    def _retry_ocr(self):
        """Retry OCR on the same file"""
        self.retry_btn.hide()
        self.start_over_btn.hide()
        self.progress_label.hide()
        self._start_ocr()

    def _start_over(self):
        """Reset to initial state"""
        self.current_file = None

        # Defensive: self.ocr_worker is normally already cleared by
        # _on_ocr_success()/_on_ocr_error() by the time Start Over is
        # reachable, but reset it unconditionally here too. self.ocr_thread
        # is handled the same way, but ONLY if _is_ocr_running() reports it
        # as not running -- unconditionally nulling it here has the same
        # hazard documented on the ocr_thread.finished connection in
        # _start_ocr(): it could drop the last Python reference to a
        # QThread Qt still considers running, which aborts the process
        # rather than merely leaving a harmless stale reference for
        # _is_ocr_running() to catch defensively.
        self.ocr_worker = None
        if self.ocr_thread is not None and not self._is_ocr_running():
            self.ocr_thread = None

        # Reset drop zone
        self.drop_zone.reset_to_idle()
        self.drop_zone.setAcceptDrops(True)

        # Hide all optional elements
        self.file_label.hide()
        self.start_ocr_btn.hide()
        self.progress_label.hide()
        self.text_area.hide()
        self.text_area.clear()
        self.copy_btn.hide()
        self.retry_btn.hide()
        self.start_over_btn.hide()

        # Re-enable controls
        self._set_controls_enabled(True)
