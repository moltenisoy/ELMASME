import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Set, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence, QTextDocument
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QStackedWidget, QFileDialog, QLineEdit
)

from document_pdf import PDF_EXTENSIONS
from document_editor import TextEditorToolbar, read_text_file, save_text_file, is_editable
from pdf_editor import PdfEditorWidget
from diff_viewer import DiffViewerWidget
from pdf_tools import MergePdfDialog, SplitPdfDialog, merge_pdfs, split_pdf, extract_pdf_text as extract_pdf_text_tool, extract_pdf_images

TEXT_DOCUMENT_EXTENSIONS = {
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

DOCX_EXTENSIONS = {".docx"}

EPUB_EXTENSIONS = {".epub"}

RTF_EXTENSIONS = {".rtf"}

ODT_EXTENSIONS = {".odt"}

ODS_EXTENSIONS = {".ods"}

DOCUMENT_EXTENSIONS = TEXT_DOCUMENT_EXTENSIONS | PDF_EXTENSIONS | DOCX_EXTENSIONS | EPUB_EXTENSIONS | RTF_EXTENSIONS | ODT_EXTENSIONS | ODS_EXTENSIONS

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
    ".docx": "Word Document",
    ".epub": "EPUB eBook",
    ".rtf": "Rich Text Format",
    ".odt": "ODT (OpenDocument Text)",
    ".ods": "ODS (OpenDocument Spreadsheet)"
}


def _extract_docx_text(path: str) -> Optional[str]:
    try:
        ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        with zipfile.ZipFile(path, "r") as z:
            if "word/document.xml" not in z.namelist():
                return None
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                paragraphs = []
                for p in root.iter(f"{{{ns}}}p"):
                    texts = []
                    for t in p.iter(f"{{{ns}}}t"):
                        if t.text:
                            texts.append(t.text)
                    paragraphs.append("".join(texts))
                return "\n".join(paragraphs)
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


def _extract_epub_text(path: str) -> Optional[str]:
    try:
        with zipfile.ZipFile(path, "r") as z:
            container_path = "META-INF/container.xml"
            if container_path not in z.namelist():
                return None
            with z.open(container_path) as cf:
                container = ET.parse(cf)
                ns_container = "urn:oasis:names:tc:opendocument:xmlns:container"
                rootfile_el = container.find(f".//{{{ns_container}}}rootfile")
                if rootfile_el is None:
                    rootfile_el = container.find(".//{http://www.idpf.org/2007/opf}rootfile")
                if rootfile_el is None:
                    for el in container.iter():
                        if el.tag.endswith("rootfile") and el.get("full-path"):
                            rootfile_el = el
                            break
                if rootfile_el is None:
                    return None
                opf_path = rootfile_el.get("full-path")
            if not opf_path or opf_path not in z.namelist():
                return None
            opf_dir = os.path.dirname(opf_path)
            with z.open(opf_path) as opf_file:
                opf_tree = ET.parse(opf_file)
                opf_root = opf_tree.getroot()
            ns_opf = "http://www.idpf.org/2007/opf"
            manifest = {}
            for item in opf_root.iter():
                if item.tag.endswith("}item") or item.tag == "item":
                    item_id = item.get("id", "")
                    href = item.get("href", "")
                    media_type = item.get("media-type", "")
                    manifest[item_id] = (href, media_type)
            spine_items = []
            for itemref in opf_root.iter():
                if itemref.tag.endswith("}itemref") or itemref.tag == "itemref":
                    idref = itemref.get("idref", "")
                    if idref in manifest:
                        spine_items.append(manifest[idref])
            if not spine_items:
                for item_id, (href, media_type) in manifest.items():
                    if "html" in media_type or "xhtml" in media_type:
                        spine_items.append((href, media_type))
            all_text = []
            tag_re = re.compile(r"<[^>]+>")
            for href, media_type in spine_items:
                full_path = os.path.join(opf_dir, href).replace("\\", "/")
                if full_path.startswith("/"):
                    full_path = full_path[1:]
                if full_path not in z.namelist():
                    continue
                with z.open(full_path) as html_file:
                    raw = html_file.read()
                    try:
                        html_content = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        html_content = raw.decode("latin-1", errors="replace")
                    text = tag_re.sub("", html_content)
                    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
                    text = text.replace("&lt;", "<").replace("&gt;", ">")
                    text = text.replace("&quot;", '"').replace("&apos;", "'")
                    lines = [line.strip() for line in text.splitlines()]
                    cleaned = "\n".join(line for line in lines if line)
                    if cleaned:
                        all_text.append(cleaned)
            return "\n\n".join(all_text) if all_text else None
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


def _extract_rtf_text(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            rtf_content = f.read()
        if not rtf_content.startswith("{\\rtf"):
            return None
        rtf_content = re.sub(r"\\[a-z]+\d*\s?", " ", rtf_content)
        rtf_content = re.sub(r"\{[^}]*\}", "", rtf_content)
        rtf_content = rtf_content.replace("{", "").replace("}", "")
        rtf_content = re.sub(r"\\[\'\\]([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), rtf_content)
        rtf_content = rtf_content.replace("\\\n", "\n").replace("\\par", "\n")
        lines = [line.strip() for line in rtf_content.splitlines()]
        return "\n".join(lines)
    except (OSError, UnicodeDecodeError):
        return None


def _extract_odt_text(path: str) -> Optional[str]:
    try:
        ns_text = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        with zipfile.ZipFile(path, "r") as z:
            if "content.xml" not in z.namelist():
                return None
            with z.open("content.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                paragraphs = []
                for elem in root.iter():
                    if elem.tag in (f"{{{ns_text}}}p", f"{{{ns_text}}}h"):
                        text_parts = []
                        if elem.text:
                            text_parts.append(elem.text)
                        for child in elem:
                            if child.text:
                                text_parts.append(child.text)
                            if child.tail:
                                text_parts.append(child.tail)
                        paragraphs.append("".join(text_parts))
                return "\n".join(paragraphs)
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


def _extract_ods_text(path: str) -> Optional[str]:
    try:
        ns_table = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
        ns_text = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
        with zipfile.ZipFile(path, "r") as z:
            if "content.xml" not in z.namelist():
                return None
            with z.open("content.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                rows = []
                for row in root.iter(f"{{{ns_table}}}table-row"):
                    cells = []
                    for cell in row.iter(f"{{{ns_table}}}table-cell"):
                        cell_texts = []
                        for p in cell.iter(f"{{{ns_text}}}p"):
                            parts = []
                            if p.text:
                                parts.append(p.text)
                            for child in p:
                                if child.text:
                                    parts.append(child.text)
                                if child.tail:
                                    parts.append(child.tail)
                            cell_texts.append("".join(parts))
                        cells.append(" ".join(cell_texts))
                    if any(c.strip() for c in cells):
                        rows.append("\t".join(cells))
                return "\n".join(rows) if rows else None
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError):
        return None


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
                if idx <= 0:
                    prev_idx = total - 1
                else:
                    prev_idx = idx - 1
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
        self._pdf_editing = False
        self._modified = False
        self._high_contrast = False

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
        self.toolbar.save_as_btn.clicked.connect(self.save_file_as)
        self.toolbar.zoom_out_btn.clicked.connect(self.zoom_out)
        self.toolbar.zoom_in_btn.clicked.connect(self.zoom_in)
        self.toolbar.search_btn.clicked.connect(self._toggle_search)
        self.toolbar.contrast_btn.clicked.connect(self._toggle_high_contrast)
        self.toolbar.compare_btn.clicked.connect(self._open_diff_viewer)

        self.text_view.textChanged.connect(self._on_content_changed)

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;padding:24px;font-size:15px;"
        )

        self.pdf_editor = PdfEditorWidget(self)
        self.pdf_editor.modified_changed.connect(self._on_pdf_editor_modified)

        self.diff_viewer = DiffViewerWidget(self)
        self.diff_viewer.close_btn.clicked.connect(self._close_diff_viewer)

        self.stack.addWidget(self.pdf_view)
        self.stack.addWidget(self.text_view)
        self.stack.addWidget(self.message)
        self.stack.addWidget(self.pdf_editor)
        self.stack.addWidget(self.diff_viewer)

        self._pdf_bar = QWidget()
        pdf_bar_layout = QHBoxLayout(self._pdf_bar)
        pdf_bar_layout.setContentsMargins(4, 2, 4, 2)
        pdf_bar_layout.setSpacing(6)

        self._edit_pdf_btn = QPushButton("✏️ Editar PDF")
        self._edit_pdf_btn.setToolTip("Abrir el editor visual de PDF")
        self._edit_pdf_btn.setFixedHeight(30)
        self._edit_pdf_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 6px;
                padding: 4px 14px;
                color: #60a5fa;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.35);
                border-color: rgba(59, 130, 246, 0.7);
            }
        """)
        self._edit_pdf_btn.clicked.connect(self._toggle_pdf_edit_mode)
        pdf_bar_layout.addWidget(self._edit_pdf_btn)

        _pdf_btn_style = """
            QPushButton {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 6px;
                padding: 4px 10px;
                color: #60a5fa;
                font-weight: 500;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.35);
                border-color: rgba(59, 130, 246, 0.7);
            }
        """

        self._merge_pdf_btn = QPushButton("📎 Fusionar")
        self._merge_pdf_btn.setToolTip("Fusionar múltiples PDFs en uno")
        self._merge_pdf_btn.setFixedHeight(30)
        self._merge_pdf_btn.setStyleSheet(_pdf_btn_style)
        self._merge_pdf_btn.clicked.connect(self._merge_pdfs)
        pdf_bar_layout.addWidget(self._merge_pdf_btn)

        self._split_pdf_btn = QPushButton("✂️ Dividir")
        self._split_pdf_btn.setToolTip("Dividir PDF en páginas individuales")
        self._split_pdf_btn.setFixedHeight(30)
        self._split_pdf_btn.setStyleSheet(_pdf_btn_style)
        self._split_pdf_btn.clicked.connect(self._split_pdf)
        pdf_bar_layout.addWidget(self._split_pdf_btn)

        self._extract_text_btn = QPushButton("📝 Extraer texto")
        self._extract_text_btn.setToolTip("Extraer texto del PDF a archivo .txt")
        self._extract_text_btn.setFixedHeight(30)
        self._extract_text_btn.setStyleSheet(_pdf_btn_style)
        self._extract_text_btn.clicked.connect(self._extract_text)
        pdf_bar_layout.addWidget(self._extract_text_btn)

        self._extract_images_btn = QPushButton("🖼️ Extraer imágenes")
        self._extract_images_btn.setToolTip("Extraer todas las imágenes del PDF")
        self._extract_images_btn.setFixedHeight(30)
        self._extract_images_btn.setStyleSheet(_pdf_btn_style)
        self._extract_images_btn.clicked.connect(self._extract_images)
        pdf_bar_layout.addWidget(self._extract_images_btn)

        self._two_page_btn = QPushButton("📖 Libro")
        self._two_page_btn.setToolTip("Vista de dos páginas (libro abierto)")
        self._two_page_btn.setFixedHeight(30)
        self._two_page_btn.setStyleSheet(_pdf_btn_style)
        self._two_page_btn.setCheckable(True)
        self._two_page_btn.clicked.connect(self._toggle_two_page_view)
        pdf_bar_layout.addWidget(self._two_page_btn)

        pdf_bar_layout.addStretch()
        self._pdf_bar.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.toolbar)
        layout.addWidget(self._pdf_bar)
        layout.addWidget(self.stack, 1)

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
        self._pdf_editing = False
        self._pdf_bar.setVisible(False)

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
                self._pdf_bar.setVisible(True)
                self._edit_pdf_btn.setText("✏️ Editar PDF")
                self._search_widget.set_pdf_mode(self.pdf_view, self.pdf_document)
                return

            self.message.setText("No fue posible renderizar el PDF.")
            self.stack.setCurrentWidget(self.message)
            self.toolbar.setVisible(False)
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
            self.toolbar.contrast_btn.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            self._apply_contrast()
            return

        if ext in DOCX_EXTENSIONS:
            content = _extract_docx_text(path)
            if content is None:
                self.message.setText("No fue posible extraer el texto del documento DOCX.")
                self.stack.setCurrentWidget(self.message)
                self.toolbar.setVisible(False)
                self._modified = False
                return
            self.text_view.setPlainText(content)
            self.current_zoom_index = 2
            self._apply_text_zoom()
            self._modified = False
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.toolbar.contrast_btn.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            self._apply_contrast()
            return

        if ext in EPUB_EXTENSIONS:
            content = _extract_epub_text(path)
            if content is None:
                self.message.setText("No fue posible extraer el texto del documento EPUB.")
                self.stack.setCurrentWidget(self.message)
                self.toolbar.setVisible(False)
                self._modified = False
                return
            self.text_view.setPlainText(content)
            self.current_zoom_index = 2
            self._apply_text_zoom()
            self._modified = False
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.toolbar.contrast_btn.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            self._apply_contrast()
            return

        if ext in RTF_EXTENSIONS:
            content = _extract_rtf_text(path)
            if content is None:
                self.message.setText("No fue posible extraer el texto del documento RTF.")
                self.stack.setCurrentWidget(self.message)
                self.toolbar.setVisible(False)
                self._modified = False
                return
            self.text_view.setPlainText(content)
            self.current_zoom_index = 2
            self._apply_text_zoom()
            self._modified = False
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.toolbar.contrast_btn.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            self._apply_contrast()
            return

        if ext in ODT_EXTENSIONS:
            content = _extract_odt_text(path)
            if content is None:
                self.message.setText("No fue posible extraer el texto del documento ODT.")
                self.stack.setCurrentWidget(self.message)
                self.toolbar.setVisible(False)
                self._modified = False
                return
            self.text_view.setPlainText(content)
            self.current_zoom_index = 2
            self._apply_text_zoom()
            self._modified = False
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.toolbar.contrast_btn.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            self._apply_contrast()
            return

        if ext in ODS_EXTENSIONS:
            content = _extract_ods_text(path)
            if content is None:
                self.message.setText("No fue posible extraer el texto del documento ODS.")
                self.stack.setCurrentWidget(self.message)
                self.toolbar.setVisible(False)
                self._modified = False
                return
            self.text_view.setPlainText(content)
            self.current_zoom_index = 2
            self._apply_text_zoom()
            self._modified = False
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.toolbar.contrast_btn.setVisible(True)
            self._search_widget.set_text_mode(self.text_view)
            self._apply_contrast()
            return

        self.message.setText("Formato de documento incompatible para visualización directa.")
        self.stack.setCurrentWidget(self.message)
        self.toolbar.setVisible(False)
        self._modified = False

    def save_file(self):
        if self._pdf_editing:
            self.pdf_editor.save()
            return
        self.toolbar.save_current(self.current_path, self.is_pdf)
        self._modified = False

    def save_file_as(self):
        if self._pdf_editing:
            self.pdf_editor.save_as()
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "Todos los archivos (*.*)")
        if file_path:
            content = self.text_view.toPlainText()
            save_text_file(file_path, content)
            self._modified = False

    def export_pdf(self):
        self.toolbar._export_pdf()

    def is_modified(self):
        if self._pdf_editing:
            return self.pdf_editor.is_modified()
        return self._modified

    def discard_changes(self):
        self._modified = False
        if self._pdf_editing:
            self.pdf_editor.close_editor()
            self._pdf_editing = False

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

    def _toggle_high_contrast(self):
        self._high_contrast = not self._high_contrast
        self._apply_contrast()

    def _apply_contrast(self):
        if self._high_contrast:
            self.text_view.setStyleSheet("""
                QTextEdit {
                    background: #000000;
                    color: #ffffff;
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
                    background: #1a1a1a;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                    background: #555555;
                    border-radius: 4px;
                }
            """)
            self.toolbar.contrast_btn.setToolTip("Contraste normal")
        else:
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
            self.toolbar.contrast_btn.setToolTip("Alto contraste")


    def _toggle_pdf_edit_mode(self):
        if self._pdf_editing:
            self._pdf_editing = False
            self._edit_pdf_btn.setText("✏️ Editar PDF")
            self.pdf_editor.close_editor()
            if self.current_path:
                self.pdf_document.load(self.current_path)
            self.stack.setCurrentWidget(self.pdf_view)
        else:
            if not self.current_path:
                return
            if self.pdf_editor.load_file(self.current_path):
                self._pdf_editing = True
                self._edit_pdf_btn.setText("👁️ Volver a vista")
                self.stack.setCurrentWidget(self.pdf_editor)

    def _on_pdf_editor_modified(self, modified: bool):
        self._modified = modified


    def _open_diff_viewer(self):
        self._prev_widget = self.stack.currentWidget()
        self._prev_toolbar_visible = self.toolbar.isVisible()
        if self.current_path:
            self.diff_viewer.load_left_file(self.current_path)
        self.toolbar.setVisible(False)
        self._pdf_bar.setVisible(False)
        self.stack.setCurrentWidget(self.diff_viewer)

    def _close_diff_viewer(self):
        if hasattr(self, "_prev_widget") and self._prev_widget:
            self.stack.setCurrentWidget(self._prev_widget)
            self.toolbar.setVisible(getattr(self, "_prev_toolbar_visible", True))
            if self.is_pdf:
                self._pdf_bar.setVisible(True)
        else:
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)


    def _merge_pdfs(self):
        dlg = MergePdfDialog(self)
        dlg.exec()

    def _split_pdf(self):
        if not self.current_path:
            return
        output_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino", os.path.dirname(self.current_path)
        )
        if not output_dir:
            return
        results = split_pdf(self.current_path, output_dir)
        from PySide6.QtWidgets import QMessageBox
        if results:
            QMessageBox.information(
                self, "Dividir PDF",
                f"Se crearon {len(results)} archivos en:\n{output_dir}"
            )
        else:
            QMessageBox.warning(self, "Error", "No se pudo dividir el PDF.")

    def _extract_text(self):
        if not self.current_path:
            return
        default_path = os.path.splitext(self.current_path)[0] + ".txt"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar texto extraído", default_path, "Texto (*.txt)"
        )
        if not output_path:
            return
        success = extract_pdf_text_tool(self.current_path, output_path)
        from PySide6.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "Extraer texto", f"Texto guardado en:\n{output_path}")
        else:
            QMessageBox.warning(self, "Error", "No se pudo extraer el texto del PDF.")

    def _extract_images(self):
        if not self.current_path:
            return
        output_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino", os.path.dirname(self.current_path)
        )
        if not output_dir:
            return
        results = extract_pdf_images(self.current_path, output_dir)
        from PySide6.QtWidgets import QMessageBox
        if results:
            QMessageBox.information(
                self, "Extraer imágenes",
                f"Se extrajeron {len(results)} imágenes en:\n{output_dir}"
            )
        else:
            QMessageBox.information(
                self, "Extraer imágenes",
                "No se encontraron imágenes en el PDF o no se pudieron extraer."
            )

    def _toggle_two_page_view(self):
        if self._two_page_btn.isChecked():
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self._two_page_btn.setText("📖 1 Página")
            self._two_page_btn.setToolTip("Volver a vista de una página")
            self.current_zoom_index = max(0, self.current_zoom_index - 1)
            self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index] * 0.6)
        else:
            self._two_page_btn.setText("📖 Libro")
            self._two_page_btn.setToolTip("Vista de dos páginas (libro abierto)")
            self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])
