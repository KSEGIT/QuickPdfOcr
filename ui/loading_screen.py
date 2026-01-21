"""
Loading Screen for QuickPdfOcr
Displays a splash screen with progress feedback during application initialization
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QGuiApplication


class SpinnerWidget(QWidget):
    """Animated spinner widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(60, 60)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
    
    def showEvent(self, event):
        """Start animation when widget becomes visible"""
        super().showEvent(event)
        self.timer.start(50)  # Update every 50ms for smooth animation (20 FPS)
    
    def hideEvent(self, event):
        """Stop animation when widget is hidden to save CPU resources"""
        super().hideEvent(event)
        self.timer.stop()
    
    def _rotate(self):
        """Rotate the spinner"""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw spinning arc
        pen = QPen(QColor("#2196F3"), 4, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.drawArc(rect, self.angle * 16, 120 * 16)
        
        painter.end()


class LoadingScreen(QWidget):
    """Loading screen with spinner and progress messages"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
        # Animation for fading in and out
        self.fade_out_animation = None
        
        # Make it frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Fade in animation
        self.setWindowOpacity(0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def _setup_ui(self):
        """Setup the user interface"""
        self.setFixedSize(400, 300)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Background styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
            }
        """)
        
        # App name/title
        title_label = QLabel("QuickPdfOcr")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                font-size: 32px;
                font-weight: bold;
                background: transparent;
                padding: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Starting application...")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                background: transparent;
                padding: 5px;
            }
        """)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # Spinner
        spinner_container = QWidget()
        spinner_container.setStyleSheet("background: transparent;")
        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        
        self.spinner = SpinnerWidget()
        spinner_layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(spinner_container)
        
        layout.addSpacing(20)
        
        # Progress message label
        self.progress_label = QLabel("Initializing...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 13px;
                background: transparent;
                padding: 10px;
                min-height: 20px;
            }
        """)
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
    
    def set_progress(self, message: str):
        """Update progress message"""
        self.progress_label.setText(message)
    
    def show(self):
        """Show the loading screen with fade-in animation"""
        super().show()
        self.fade_animation.start()
        
        # Center on screen
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
    
    def close_with_fade(self):
        """Close the loading screen with fade-out animation"""
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(200)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()
