from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel
)

from formats import get_content_type
from image_handler import ImageViewer
from audio_handler import AudioViewer
from video_handler import VideoViewer
from document_handler import DocumentViewer


class ViewerHost(QWidget):

    def __init__(self):
        super().__init__()

        self.image_viewer = ImageViewer()
        self.audio_viewer = AudioViewer()
        self.video_viewer = VideoViewer()
        self.document_viewer = DocumentViewer()

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;padding:24px;font-size:15px;"
        )

        self.stack = QStackedWidget()
        self.stack.addWidget(self.image_viewer)
        self.stack.addWidget(self.audio_viewer)
        self.stack.addWidget(self.video_viewer)
        self.stack.addWidget(self.document_viewer)
        self.stack.addWidget(self.message)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def stop_media(self):
        self.audio_viewer.stop()
        self.video_viewer.stop()
        if self.video_viewer.is_fullscreen:
            self.video_viewer.exit_fullscreen()

    def load_file(self, path: str):
        self.stop_media()

        kind = get_content_type(path)

        if kind == "image":
            self.image_viewer.load_file(path)
            self.stack.setCurrentWidget(self.image_viewer)
            return

        if kind == "audio":
            self.audio_viewer.load_file(path)
            self.stack.setCurrentWidget(self.audio_viewer)
            return

        if kind == "video":
            self.video_viewer.load_file(path)
            self.stack.setCurrentWidget(self.video_viewer)
            return

        if kind in ("pdf", "text"):
            self.document_viewer.load_file(path)
            self.stack.setCurrentWidget(self.document_viewer)
            return

        self.message.setText("Formato de archivo no compatible.")
        self.stack.setCurrentWidget(self.message)

    def show_message(self, text: str):
        self.stop_media()
        self.message.setText(text)
        self.stack.setCurrentWidget(self.message)

    def has_unsaved_changes(self):
        return self.document_viewer.is_modified()

    def save_document(self):
        self.document_viewer.save_file()

    def save_document_as(self):
        self.document_viewer.save_file_as()

    def discard_changes(self):
        self.document_viewer.discard_changes()

    def minimumSizeHint(self):
        return QSize(900, 620)

    @property
    def media_viewer(self):
        return self.video_viewer
