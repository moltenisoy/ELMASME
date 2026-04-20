from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel
)

from formats import get_content_type


class ViewerHost(QWidget):
    """Viewer container with lazy loading of viewer widgets.

    Viewer modules are imported and instantiated only on first use,
    reducing startup time by avoiding heavy imports until needed.
    """

    def __init__(self):
        super().__init__()

        self._image_viewer = None
        self._audio_viewer = None
        self._video_viewer = None
        self._document_viewer = None
        self._archive_viewer = None
        self._spreadsheet_viewer = None
        self._presentation_viewer = None
        self._ebook_viewer = None

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;padding:24px;font-size:15px;"
        )

        self.stack = QStackedWidget()
        self.stack.addWidget(self.message)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    @property
    def image_viewer(self):
        if self._image_viewer is None:
            from image_handler import ImageViewer
            self._image_viewer = ImageViewer()
            self.stack.addWidget(self._image_viewer)
        return self._image_viewer

    @property
    def audio_viewer(self):
        if self._audio_viewer is None:
            from audio_handler import AudioViewer
            self._audio_viewer = AudioViewer()
            self.stack.addWidget(self._audio_viewer)
        return self._audio_viewer

    @property
    def video_viewer(self):
        if self._video_viewer is None:
            from video_handler import VideoViewer
            self._video_viewer = VideoViewer()
            self.stack.addWidget(self._video_viewer)
        return self._video_viewer

    @property
    def document_viewer(self):
        if self._document_viewer is None:
            from document_handler import DocumentViewer
            self._document_viewer = DocumentViewer()
            self.stack.addWidget(self._document_viewer)
        return self._document_viewer

    @property
    def archive_viewer(self):
        if self._archive_viewer is None:
            from archive_viewer import ArchiveViewer
            self._archive_viewer = ArchiveViewer()
            self.stack.addWidget(self._archive_viewer)
        return self._archive_viewer

    @property
    def spreadsheet_viewer(self):
        if self._spreadsheet_viewer is None:
            from spreadsheet_viewer import SpreadsheetViewer
            self._spreadsheet_viewer = SpreadsheetViewer()
            self.stack.addWidget(self._spreadsheet_viewer)
        return self._spreadsheet_viewer

    @property
    def presentation_viewer(self):
        if self._presentation_viewer is None:
            from presentation_viewer import PresentationViewer
            self._presentation_viewer = PresentationViewer()
            self.stack.addWidget(self._presentation_viewer)
        return self._presentation_viewer

    @property
    def ebook_viewer(self):
        if self._ebook_viewer is None:
            from ebook_viewer import EbookViewer
            self._ebook_viewer = EbookViewer()
            self.stack.addWidget(self._ebook_viewer)
        return self._ebook_viewer

    def stop_media(self):
        if self._audio_viewer is not None:
            self._audio_viewer.stop()
        if self._video_viewer is not None:
            self._video_viewer.stop()
            if self._video_viewer.is_fullscreen:
                self._video_viewer.exit_fullscreen()

    def load_file(self, path: str):
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

        if kind == "archive":
            self.archive_viewer.load_file(path)
            self.stack.setCurrentWidget(self.archive_viewer)
            return

        if kind == "spreadsheet":
            self.spreadsheet_viewer.load_file(path)
            self.stack.setCurrentWidget(self.spreadsheet_viewer)
            return

        if kind == "presentation":
            self.presentation_viewer.load_file(path)
            self.stack.setCurrentWidget(self.presentation_viewer)
            return

        if kind == "ebook":
            self.ebook_viewer.load_file(path)
            self.stack.setCurrentWidget(self.ebook_viewer)
            return

        self.message.setText("Formato de archivo no compatible.")
        self.stack.setCurrentWidget(self.message)

    def show_message(self, text: str):
        self.stop_media()
        self.message.setText(text)
        self.stack.setCurrentWidget(self.message)

    def has_unsaved_changes(self):
        if self._document_viewer is None:
            return False
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
