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
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from components.ocr_worker import OCRWorker
from components.ocr import describe_language, get_engine


class DropZoneLabel(QLabel):
    """Custom label that accepts drag-and-drop file operations"""
    
    file_dropped = Signal(str)
    
    _DEFAULT_TEXT = "📄 Drop PDF file here"

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Timer to auto-clear the drop-zone warning after a delay
        self._warning_timer = QTimer(self)
        self._warning_timer.setSingleShot(True)
        self._warning_timer.timeout.connect(self._reset_text)

        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #aaa;
                border-radius: 10px;
                padding: 40px;
                background-color: #f5f5f5;
                font-size: 16px;
                color: #666;
            }
            QLabel:hover {
                border-color: #2196F3;
                background-color: #e3f2fd;
                color: #1976D2;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept drag events with files"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 3px dashed #2196F3;
                    border-radius: 10px;
                    padding: 40px;
                    background-color: #e3f2fd;
                    font-size: 16px;
                    color: #1976D2;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """Reset style when drag leaves"""
        self.setStyleSheet("""
            QLabel {
                border: 3px dashed #aaa;
                border-radius: 10px;
                padding: 40px;
                background-color: #f5f5f5;
                font-size: 16px;
                color: #666;
            }
            QLabel:hover {
                border-color: #2196F3;
                background-color: #e3f2fd;
                color: #1976D2;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Handle dropped files"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if not files:
            self._show_drop_warning()
        elif files[0].lower().endswith('.pdf'):
            self.file_dropped.emit(files[0])
        else:
            self._show_drop_warning()
        event.acceptProposedAction()
        self.dragLeaveEvent(event)

    def _show_drop_warning(self):
        """Show a temporary warning when a non-PDF (or empty) drop occurs."""
        self.setText("⚠️ Please drop a PDF file")
        self._warning_timer.start(3000)

    def _reset_text(self):
        """Restore the default drop-zone label text."""
        self.setText(self._DEFAULT_TEXT)


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
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Drop zone label
        self.drop_zone = DropZoneLabel(DropZoneLabel._DEFAULT_TEXT)
        self.drop_zone.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self.drop_zone)
        
        # Open file button
        self.open_btn = QPushButton("📁 Open PDF File")
        self.open_btn.setMinimumHeight(40)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.open_btn.clicked.connect(self._open_file_dialog)
        layout.addWidget(self.open_btn)

        # Language selector, populated from whichever engine this platform uses
        language_layout = QHBoxLayout()
        language_layout.setSpacing(10)

        language_caption = QLabel("Language:")
        language_caption.setStyleSheet("color: #333;")
        language_layout.addWidget(language_caption)

        self.language_combo = QComboBox()
        self.language_combo.setMinimumHeight(30)
        self._populate_languages()
        language_layout.addWidget(self.language_combo, 1)

        layout.addLayout(language_layout)

        # File name label (hidden initially)
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #333; font-weight: bold;")
        self.file_label.hide()
        layout.addWidget(self.file_label)
        
        # Start OCR button (hidden initially)
        self.start_ocr_btn = QPushButton("🚀 Start OCR")
        self.start_ocr_btn.setMinimumHeight(40)
        self.start_ocr_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_ocr_btn.clicked.connect(self._start_ocr)
        self.start_ocr_btn.hide()
        layout.addWidget(self.start_ocr_btn)
        
        # Progress/feedback label (hidden initially)
        self.progress_label = QLabel("⏳ Processing...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #1976D2;
                font-size: 14px;
                padding: 10px;
                background-color: #e3f2fd;
                border-radius: 5px;
            }
        """)
        self.progress_label.hide()
        layout.addWidget(self.progress_label)
        
        # Text area for results (hidden initially)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Extracted text will appear here...")
        self.text_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.text_area.hide()
        layout.addWidget(self.text_area, 1)  # Stretch factor of 1
        
        # Button container for copy and retry buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Copy button (hidden initially)
        self.copy_btn = QPushButton("📋 Copy to Clipboard")
        self.copy_btn.setMinimumHeight(35)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.copy_btn.hide()
        button_layout.addWidget(self.copy_btn)
        
        # Try again button (hidden initially)
        self.retry_btn = QPushButton("🔄 Try Again")
        self.retry_btn.setMinimumHeight(35)
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.retry_btn.clicked.connect(self._retry_ocr)
        self.retry_btn.hide()
        button_layout.addWidget(self.retry_btn)
        
        # Start over button (hidden initially)
        self.start_over_btn = QPushButton("🏠 Start Over")
        self.start_over_btn.setMinimumHeight(35)
        self.start_over_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
            QPushButton:pressed {
                background-color: #616161;
            }
        """)
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
                f"⚠️ Ignored \"{file_name}\": an OCR run is already in "
                "progress. Please wait for it to finish."
            )
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #C62828;
                    font-size: 14px;
                    padding: 10px;
                    background-color: #FFCDD2;
                    border-radius: 5px;
                }
            """)
            self.progress_label.show()
            return

        self.current_file = file_path
        file_name = Path(file_path).name

        # Cancel any pending warning-reset timer so it cannot overwrite the
        # filename we are about to display.  This is the single code path for
        # both drag-drop and file-dialog selection.
        self.drop_zone._warning_timer.stop()

        # Update UI
        self.drop_zone.setText(f"✅ {file_name}")
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
                        "❌ The previous OCR run could not be stopped. Please try again."
                    )
                    self.progress_label.setStyleSheet("""
                        QLabel {
                            color: #C62828;
                            font-size: 14px;
                            padding: 10px;
                            background-color: #FFCDD2;
                            border-radius: 5px;
                        }
                    """)
                    self.progress_label.show()
                    return

        # Disable buttons during processing
        self._set_controls_enabled(False)

        # Show progress
        self.progress_label.setText("⏳ Converting PDF to images...")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #1976D2;
                font-size: 14px;
                padding: 10px;
                background-color: #e3f2fd;
                border-radius: 5px;
            }
        """)
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
        self.progress_label.setText(f"⏳ {message}")
    
    def _on_ocr_success(self, text: str):
        """Handle successful OCR completion"""
        self.progress_label.setText("✅ OCR completed successfully!")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #2E7D32;
                font-size: 14px;
                padding: 10px;
                background-color: #C8E6C9;
                border-radius: 5px;
            }
        """)
        
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
        self.progress_label.setText(f"❌ Error: {error_msg}")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #C62828;
                font-size: 14px;
                padding: 10px;
                background-color: #FFCDD2;
                border-radius: 5px;
            }
        """)
        
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
        self.drop_zone.setText(DropZoneLabel._DEFAULT_TEXT)
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
