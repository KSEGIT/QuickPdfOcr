"""
Main Window UI for QuickPdfOcr
Features: drag-and-drop file upload, OCR processing with progress feedback, 
text display with copy functionality
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from components.ocr_worker import OCRWorker
from components.settings import Settings


class DropZoneLabel(QLabel):
    """Custom label that accepts drag-and-drop file operations"""
    
    file_dropped = Signal(str)
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        if files and files[0].lower().endswith('.pdf'):
            self.file_dropped.emit(files[0])
        event.acceptProposedAction()
        self.dragLeaveEvent(event)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.ocr_thread = None
        self.ocr_worker = None
        self.settings = Settings()
        self._download_thread = None
        self._ocr_cancelled = False

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
        self.drop_zone = DropZoneLabel("📄 Drop PDF file here")
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

        # Language selector row
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("font-weight: bold; color: #333;")
        lang_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumHeight(30)
        self.lang_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 13px;
            }
        """)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo, 1)

        self.download_lang_btn = QPushButton("Download...")
        self.download_lang_btn.setMinimumHeight(30)
        self.download_lang_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.download_lang_btn.clicked.connect(self._show_download_dialog)
        lang_layout.addWidget(self.download_lang_btn)

        layout.addLayout(lang_layout)

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

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc; border-radius: 5px; text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3; border-radius: 5px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Cancel button (hidden initially)
        self.cancel_btn = QPushButton("Cancel OCR")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; border: none;
                border-radius: 5px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        self.cancel_btn.clicked.connect(self._cancel_ocr)
        self.cancel_btn.hide()
        layout.addWidget(self.cancel_btn)

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

        # Save to file button (hidden initially)
        self.save_btn = QPushButton("Save to File")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none;
                border-radius: 5px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #2E7D32; }
        """)
        self.save_btn.clicked.connect(self._save_to_file)
        self.save_btn.hide()
        button_layout.addWidget(self.save_btn)

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

        self._populate_languages()

    def _show_download_dialog(self):
        """Show a dialog to select and download language packs."""
        if self._download_thread is not None and self._download_thread.isRunning():
            QMessageBox.information(self, "Download", "A download is already in progress.")
            return

        from components.language_manager import LanguageManager, AVAILABLE_LANGUAGES

        mgr = LanguageManager()
        installed = set(mgr.get_installed_languages())
        downloadable = {k: v for k, v in AVAILABLE_LANGUAGES.items() if k not in installed}

        if not downloadable:
            QMessageBox.information(self, "Languages", "All available languages are already installed.")
            return

        items = [f"{name} ({code})" for code, name in sorted(downloadable.items(), key=lambda x: x[1])]
        from PySide6.QtWidgets import QInputDialog
        item, ok = QInputDialog.getItem(self, "Download Language", "Select language to download:", items, 0, False)
        if not ok or not item:
            return

        lang_code = item.split("(")[-1].rstrip(")")

        self.download_lang_btn.setEnabled(False)

        self.progress_label.setText(f"Downloading {item}...")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #1976D2; font-size: 14px; padding: 10px;
                background-color: #e3f2fd; border-radius: 5px;
            }
        """)
        self.progress_label.show()

        mgr.download_progress.connect(lambda code, pct: self.progress_label.setText(f"Downloading {item}... {pct}%"))
        mgr.download_finished.connect(lambda code: self._on_language_downloaded(code))
        mgr.download_error.connect(lambda code, err: self._on_language_download_error(err))
        self._lang_manager = mgr

        self._download_thread = QThread()
        mgr.moveToThread(self._download_thread)
        self._download_thread.started.connect(lambda: mgr.download_language(lang_code))
        mgr.download_finished.connect(self._download_thread.quit)
        mgr.download_error.connect(self._download_thread.quit)
        self._download_thread.start()

    def _on_language_downloaded(self, lang_code: str):
        """Handle successful language download."""
        self.download_lang_btn.setEnabled(True)
        self.progress_label.setText("Language downloaded successfully!")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #2E7D32; font-size: 14px; padding: 10px;
                background-color: #C8E6C9; border-radius: 5px;
            }
        """)
        self._populate_languages()

    def _on_language_download_error(self, error_msg: str):
        """Handle language download failure."""
        self.download_lang_btn.setEnabled(True)
        self.progress_label.setText(f"Download failed: {error_msg}")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #C62828; font-size: 14px; padding: 10px;
                background-color: #FFCDD2; border-radius: 5px;
            }
        """)

    def _populate_languages(self):
        """Detect installed Tesseract languages and populate the combo box."""
        import pytesseract
        try:
            langs = pytesseract.get_languages(config="")
            langs = [l for l in langs if l != "osd"]
        except Exception:
            langs = ["eng"]

        self.lang_combo.blockSignals(True)  # Don't trigger save while populating
        self.lang_combo.clear()
        LANG_NAMES = {
            "eng": "English", "fra": "French", "deu": "German",
            "spa": "Spanish", "ita": "Italian", "por": "Portuguese",
            "nld": "Dutch", "pol": "Polish", "rus": "Russian",
            "chi_sim": "Chinese (Simplified)", "chi_tra": "Chinese (Traditional)",
            "jpn": "Japanese", "kor": "Korean", "ara": "Arabic",
            "hin": "Hindi", "tur": "Turkish", "vie": "Vietnamese",
            "ukr": "Ukrainian", "ces": "Czech", "swe": "Swedish",
        }
        for lang_code in sorted(langs):
            display = LANG_NAMES.get(lang_code, lang_code)
            self.lang_combo.addItem(f"{display} ({lang_code})", lang_code)

        saved_lang = self.settings.language
        idx = self.lang_combo.findData(saved_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.blockSignals(False)

    def _on_language_changed(self):
        """Save selected language to settings."""
        lang = self.lang_combo.currentData()
        if lang:
            self.settings.language = lang

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
    
    def _on_file_dropped(self, file_path: str):
        """Handle file selection (drag-drop or file picker)"""
        self.current_file = file_path
        file_name = Path(file_path).name
        
        # Update UI
        self.drop_zone.setText(f"✅ {file_name}")
        self.file_label.setText(f"Selected: {file_name}")
        self.file_label.show()
        self.start_ocr_btn.show()
        
        # Hide previous results
        self.text_area.hide()
        self.text_area.clear()
        self.copy_btn.hide()
        self.save_btn.hide()
        self.retry_btn.hide()
        self.start_over_btn.hide()
        self.progress_label.hide()
    
    def _start_ocr(self):
        """Start OCR processing in background thread"""
        if not self.current_file:
            return
        
        # Disable buttons during processing
        self.start_ocr_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.drop_zone.setAcceptDrops(False)
        
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
        self._ocr_cancelled = False
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.cancel_btn.show()
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel OCR")

        # Create worker thread
        self.ocr_thread = QThread()
        selected_lang = self.lang_combo.currentData() or "eng"
        self.ocr_worker = OCRWorker(self.current_file, lang=selected_lang)
        self.ocr_worker.moveToThread(self.ocr_thread)
        
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
        self.ocr_worker.page_progress.connect(self._on_page_progress)
        self.ocr_thread.finished.connect(self._on_ocr_thread_finished)

        # Start processing
        self.ocr_thread.start()
    
    def _cancel_ocr(self):
        """Cancel in-progress OCR."""
        self._ocr_cancelled = True
        if self.ocr_worker is not None:
            self.ocr_worker.request_stop()
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling...")

    def _on_page_progress(self, current: int, total: int):
        """Update progress bar with page-level progress."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Page {current}/{total}")

    def _on_ocr_thread_finished(self):
        """Called when OCR thread finishes. If cancelled, neither success nor error was emitted."""
        if self._ocr_cancelled:
            self.progress_label.setText("OCR cancelled.")
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #F57C00; font-size: 14px; padding: 10px;
                    background-color: #FFF3E0; border-radius: 5px;
                }
            """)
            self.progress_bar.hide()
            self.cancel_btn.hide()
            self.start_over_btn.show()
            self.start_ocr_btn.setEnabled(True)
            self.open_btn.setEnabled(True)
            self.drop_zone.setAcceptDrops(True)

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
        self.progress_bar.hide()
        self.cancel_btn.hide()

        # Show results
        self.text_area.setPlainText(text)
        self.text_area.show()
        self.copy_btn.show()
        self.save_btn.show()
        self.start_over_btn.show()
        
        # Re-enable controls
        self.start_ocr_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.drop_zone.setAcceptDrops(True)
    
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
        self.progress_bar.hide()
        self.cancel_btn.hide()

        # Show retry buttons
        self.retry_btn.show()
        self.start_over_btn.show()
        
        # Re-enable controls
        self.start_ocr_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.drop_zone.setAcceptDrops(True)
    
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
    
    def _save_to_file(self):
        """Save extracted text to a file."""
        default_dir = self.settings.output_directory or ""
        default_name = ""
        if self.current_file:
            default_name = Path(self.current_file).stem + "_ocr.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Extracted Text",
            str(Path(default_dir) / default_name) if default_dir else default_name,
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
        )
        if not file_path:
            return

        try:
            text = self.text_area.toPlainText()
            Path(file_path).write_text(text, encoding="utf-8")
            self.settings.output_directory = str(Path(file_path).parent)
            QMessageBox.information(self, "Saved", f"Text saved to:\n{file_path}")
        except OSError as e:
            QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{e}")

    def _retry_ocr(self):
        """Retry OCR on the same file"""
        self.retry_btn.hide()
        self.progress_label.hide()
        self.cancel_btn.hide()
        self.progress_bar.hide()
        self._start_ocr()
    
    def _start_over(self):
        """Reset to initial state"""
        self.current_file = None
        
        # Reset drop zone
        self.drop_zone.setText("📄 Drop PDF file here")
        self.drop_zone.setAcceptDrops(True)
        
        # Hide all optional elements
        self.file_label.hide()
        self.start_ocr_btn.hide()
        self.progress_label.hide()
        self.progress_bar.hide()
        self.cancel_btn.hide()
        self.text_area.hide()
        self.text_area.clear()
        self.copy_btn.hide()
        self.save_btn.hide()
        self.retry_btn.hide()
        self.start_over_btn.hide()

        # Re-enable controls
        self.start_ocr_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
