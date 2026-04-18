
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication


class ConversionProgressBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedSize(480, 100)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget#progressContainer {
                background: #1e1e2e;
                border: 2px solid #dc2626;
                border-radius: 14px;
            }
            QLabel#fileLabel {
                color: #f1f5f9;
                font-size: 13px;
                font-weight: 500;
            }
            QLabel#percentLabel {
                color: #fca5a5;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar {
                background: #334155;
                border: none;
                border-radius: 6px;
                min-height: 16px;
                max-height: 16px;
                text-align: center;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dc2626, stop:0.5 #ef4444, stop:1 #dc2626);
                border-radius: 6px;
            }
        """)

        container = QWidget(self)
        container.setObjectName("progressContainer")
        container.setGeometry(0, 0, 480, 100)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        self.file_label = QLabel("Preparando...")
        self.file_label.setObjectName("fileLabel")
        self.file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.file_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("percentLabel")
        self.percent_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.percent_label)

    def start(self, filename: str = ""):
        self.file_label.setText(f"Convirtiendo: {filename}" if filename else "Convirtiendo...")
        self.progress_bar.setValue(0)
        self.percent_label.setText("0%")
        self._center_on_screen()
        self.show()
        self.raise_()
        QApplication.processEvents()

    def update_progress(self, value: int, filename: str = ""):
        self.progress_bar.setValue(value)
        self.percent_label.setText(f"{value}%")
        if filename:
            self.file_label.setText(f"Convirtiendo: {filename}")
        QApplication.processEvents()

    def finish(self):
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        QApplication.processEvents()
        QTimer.singleShot(600, self.hide)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2 + geo.x()
            y = (geo.height() - self.height()) // 2 + geo.y()
            self.move(x, y)
