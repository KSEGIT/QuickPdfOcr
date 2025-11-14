"""
Main Window UI for QuickPdfOcr
Features: drag-and-drop file upload, OCR processing with progress feedback, 
text display with copy functionality
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from components.ocr_worker import OCRWorker


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
        
        # Create worker thread
        self.ocr_thread = QThread()
        self.ocr_worker = OCRWorker(self.current_file)
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
    
    def _retry_ocr(self):
        """Retry OCR on the same file"""
        self.retry_btn.hide()
        self.progress_label.hide()
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
        self.text_area.hide()
        self.text_area.clear()
        self.copy_btn.hide()
        self.retry_btn.hide()
        self.start_over_btn.hide()
        
        # Re-enable controls
        self.start_ocr_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
