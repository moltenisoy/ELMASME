import os
from pathlib import Path
from typing import Set, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence, QTextDocument
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QStackedWidget, QFileDialog, QLineEdit
)

from document_pdf import PDF_EXTENSIONS, extract_pdf_text
from document_editor import TextEditorToolbar, read_text_file, save_text_file, is_editable

TEXT_DOCUMENT_EXTENSIONS = {
    ".txt", ".log", ".ini", ".cfg", ".conf", ".config", ".csv", ".tsv", ".xml",
    ".html", ".htm", ".xhtml", ".css", ".js", ".json", ".yaml", ".yml", ".bat",
    ".cmd", ".ps1", ".reg", ".inf", ".nfo", ".md", ".markdown", ".rst", ".tex",
    ".bib", ".sql", ".psql", ".sqlite", ".properties", ".env", ".toml", ".lock",
    ".gitignore", ".gitattributes", ".editorconfig", ".dockerfile", ".makefile",
    ".mk", ".gradle", ".groovy", ".java", ".c", ".h", ".cpp", ".hpp", ".cs",
    ".vb", ".py", ".rb", ".php", ".go", ".rs", ".swift", ".kt", ".kts",
    ".scala", ".sh", ".bash", ".zsh", ".fish", ".asm", ".s", ".v", ".sv",
    ".verilog", ".vhdl", ".hex", ".srec", ".map", ".lst", ".doc", ".docx"
}

DOCUMENT_EXTENSIONS = TEXT_DOCUMENT_EXTENSIONS | PDF_EXTENSIONS

EDITABLE_EXTENSIONS: Set[str] = {
    ".txt", ".log", ".ini", ".cfg", ".conf", ".config", ".csv", ".tsv", ".xml",
    ".html", ".htm", ".xhtml", ".css", ".js", ".json", ".yaml", ".yml", ".bat",
    ".cmd", ".ps1", ".reg", ".inf", ".nfo", ".md", ".markdown", ".rst", ".tex",
    ".bib", ".sql", ".psql", ".sqlite", ".properties", ".env", ".toml", ".lock",
    ".gitignore", ".gitattributes", ".editorconfig", ".dockerfile", ".makefile",
    ".mk", ".gradle", ".groovy", ".java", ".c", ".h", ".cpp", ".hpp", ".cs",
    ".vb", ".py", ".rb", ".php", ".go", ".rs", ".swift", ".kt", ".kts",
    ".scala", ".sh", ".bash", ".zsh", ".fish", ".asm", ".s", ".v", ".sv",
    ".verilog", ".vhdl", ".hex", ".srec", ".map", ".lst"
}

TYPE_NAMES = {
    ".pdf": "PDF Document",
    ".txt": "Text File",
    ".md": "Markdown",
    ".py": "Python Script",
    ".js": "JavaScript",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".xml": "XML",
    ".csv": "CSV",
    ".sql": "SQL",
    ".doc": "Word Document",
    ".docx": "Word Document"
}


def get_document_info(path: str) -> Dict:
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "type": "",
        "is_editable": False
    }

    if os.path.exists(path):
        info["size"] = os.path.getsize(path)

    ext = info["extension"]
    info["type"] = TYPE_NAMES.get(ext, "Document")
    info["is_editable"] = ext in EDITABLE_EXTENSIONS

    return info


class FloatingSearchWidget(QWidget):

    def __init__(self, text_edit, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._text_edit = text_edit
        self._pdf_view = None
        self._pdf_document = None
        self._search_model = None
        self._drag_pos = None
        self.setFixedSize(330, 80)
        self._build_ui()

    def set_pdf_mode(self, pdf_view, pdf_document):
        self._pdf_view = pdf_view
        self._pdf_document = pdf_document
        self._text_edit = None
        self._search_model = QPdfSearchModel(self)
        self._search_model.setDocument(pdf_document)
        self._pdf_view.setSearchModel(self._search_model)

    def set_text_mode(self, text_edit):
        self._text_edit = text_edit
        self._pdf_view = None
        self._pdf_document = None
        self._search_model = None

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: #1e293b;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 8px;
            }
            QLineEdit {
                background: #0f172a;
                color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton {
                background: rgba(30,41,59,0.92);
                border: 1px solid rgba(148,163,184,0.18);
                border-radius: 6px;
                padding: 4px 8px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background: rgba(51,65,85,0.96);
                border: 1px solid rgba(96,165,250,0.45);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        search_row = QHBoxLayout()
        search_row.setSpacing(4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar texto...")
        self.search_input.returnPressed.connect(self._search_forward)
        search_row.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍")
        self.search_btn.setFixedSize(32, 26)
        self.search_btn.clicked.connect(self._search_forward)
        search_row.addWidget(self.search_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(26, 26)
        self.close_btn.clicked.connect(self.hide)
        search_row.addWidget(self.close_btn)

        layout.addLayout(search_row)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(4)

        self.up_btn = QPushButton("▲ Arriba")
        self.up_btn.setFixedHeight(24)
        self.up_btn.clicked.connect(self._search_backward)
        dir_row.addWidget(self.up_btn)

        self.down_btn = QPushButton("▼ Abajo")
        self.down_btn.setFixedHeight(24)
        self.down_btn.clicked.connect(self._search_forward)
        dir_row.addWidget(self.down_btn)

        dir_row.addStretch()
        layout.addLayout(dir_row)

    def _search_forward(self):
        text = self.search_input.text()
        if not text:
            return
        if self._text_edit:
            self._text_edit.find(text)
        elif self._pdf_view and self._search_model:
            self._search_model.setSearchString(text)
            idx = self._pdf_view.currentSearchResultIndex()
            total = self._search_model.rowCount()
            if total > 0:
                next_idx = (idx + 1) % total
                self._pdf_view.setCurrentSearchResultIndex(next_idx)

    def _search_backward(self):
        text = self.search_input.text()
        if not text:
            return
        if self._text_edit:
            self._text_edit.find(text, QTextDocument.FindBackward)
        elif self._pdf_view and self._search_model:
            self._search_model.setSearchString(text)
            idx = self._pdf_view.currentSearchResultIndex()
            total = self._search_model.rowCount()
            if total > 0:
                prev_idx = (idx - 1) % total
                self._pdf_view.setCurrentSearchResultIndex(prev_idx)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class DocumentViewer(QWidget):

    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self.current_zoom_index = 2
        self.current_path = None
        self.edit_mode = True
        self.is_pdf = False
        self._modified = False

        self._build_ui()

    def _build_ui(self):
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView()
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])

        self.text_view = QTextEdit()
        self.text_view.setAcceptRichText(True)
        self.text_view.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                color: #1e293b;
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 8px;
                padding: 16px;
                font-family: 'Calibri', 'Arial', sans-serif;
                font-size: 11pt;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid rgba(59, 130, 246, 0.5);
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #f1f5f9;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #94a3b8;
                border-radius: 4px;
            }
        """)

        self.text_view.setAcceptDrops(False)

        self.toolbar = TextEditorToolbar(self.text_view, self)
        self.toolbar.save_btn.clicked.connect(self.save_file)

        self.text_view.textChanged.connect(self._on_content_changed)

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;padding:24px;font-size:15px;"
        )

        self.stack.addWidget(self.pdf_view)
        self.stack.addWidget(self.text_view)
        self.stack.addWidget(self.message)

        zoom_controls = QHBoxLayout()
        zoom_controls.setContentsMargins(0, 0, 0, 0)
        zoom_controls.setSpacing(6)
        zoom_controls.addStretch(1)

        self.zoom_out_button = QPushButton("Zoom -")
        self.zoom_out_button.setFixedSize(70, 22)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        zoom_controls.addWidget(self.zoom_out_button)

        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_in_button.setFixedSize(70, 22)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        zoom_controls.addWidget(self.zoom_in_button)

        self.search_button = QPushButton("🔍")
        self.search_button.setFixedSize(32, 22)
        self.search_button.clicked.connect(self._toggle_search)
        zoom_controls.addWidget(self.search_button)

        zoom_controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.stack, 1)
        layout.addLayout(zoom_controls)

        self._search_widget = FloatingSearchWidget(self.text_view)

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        save_action = QAction(self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        self.addAction(save_action)

    def load_file(self, path: str):
        self.current_path = path
        self.is_pdf = False

        ext = Path(path).suffix.lower()

        if ext in PDF_EXTENSIONS:
            self.is_pdf = True
            self.pdf_document.load(path)

            if self.pdf_document.status() == QPdfDocument.Status.Ready:
                self.current_zoom_index = 2
                self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])
                self._modified = False
                self.stack.setCurrentWidget(self.pdf_view)
                self.toolbar.setVisible(False)
                self.zoom_out_button.setVisible(True)
                self.zoom_in_button.setVisible(True)
                self.search_button.setVisible(True)
                self._search_widget.set_pdf_mode(self.pdf_view, self.pdf_document)
                return

            self.message.setText("No fue posible renderizar el PDF.")
            self.stack.setCurrentWidget(self.message)
            self.toolbar.setVisible(False)
            self.zoom_out_button.setVisible(False)
            self.zoom_in_button.setVisible(False)
            self.search_button.setVisible(False)
            self._modified = False
            return

        if ext in TEXT_DOCUMENT_EXTENSIONS:
            content = read_text_file(path)
            self.text_view.setPlainText(content)
            self.current_zoom_index = 2
            self._apply_text_zoom()
            self._modified = False
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.zoom_out_button.setVisible(True)
            self.zoom_in_button.setVisible(True)
            self.search_button.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            return

        self.message.setText("Formato de documento incompatible para visualización directa.")
        self.stack.setCurrentWidget(self.message)
        self.toolbar.setVisible(False)
        self.zoom_out_button.setVisible(False)
        self.zoom_in_button.setVisible(False)
        self.search_button.setVisible(False)
        self._modified = False

    def save_file(self):
        self.toolbar.save_current(self.current_path, self.is_pdf)
        self._modified = False

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "Todos los archivos (*.*)")
        if file_path:
            content = self.text_view.toPlainText()
            save_text_file(file_path, content)
            self._modified = False

    def is_modified(self):
        return self._modified

    def discard_changes(self):
        self._modified = False

    def _on_content_changed(self):
        self._modified = True

    def zoom_in(self):
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            if self.is_pdf:
                self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])
            else:
                self._apply_text_zoom()

    def zoom_out(self):
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            if self.is_pdf:
                self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])
            else:
                self._apply_text_zoom()

    def _apply_text_zoom(self):
        factor = self.zoom_levels[self.current_zoom_index]
        new_size = max(6, int(11 * factor))
        font = self.text_view.font()
        font.setPointSize(new_size)
        self.text_view.setFont(font)

    def _toggle_search(self):
        if self._search_widget.isVisible():
            self._search_widget.hide()
        else:
            pos = self.mapToGlobal(self.rect().topRight())
            self._search_widget.move(pos.x() - self._search_widget.width() - 20, pos.y() + 60)
            self._search_widget.show()
            self._search_widget.raise_()
            self._search_widget.search_input.setFocus()
