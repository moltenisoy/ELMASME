import os
from pathlib import Path
from typing import Optional, Set, Dict
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QAction, QFont, QKeySequence, QColor, QTextCharFormat,
    QFontDatabase, QTextCursor
)
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QSizePolicy, QStackedWidget, QDialog, QMessageBox, QFileDialog,
    QFontComboBox, QSpinBox, QColorDialog, QFrame, QGridLayout,
    QToolButton, QComboBox, QGroupBox,
    QPlainTextEdit, QCheckBox, QSpacerItem
)

PDF_EXTENSIONS = {".pdf"}

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
    info["is_editable"] = True  
    
    return info


def is_editable(path: str) -> bool:
    return True


def read_text_file(path: str) -> str:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1"]
    
    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    
    with open(path, "r", encoding="utf-8", errors="replace") as file:
        return file.read()


def save_text_file(path: str, content: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        return True
    except Exception:
        return False


class DocumentViewer(QWidget):
    
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.zoom_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        self.current_zoom_index = 2
        self.current_path = None
        self.edit_mode = True  
        self.is_pdf = False
        
        self._build_ui()
    
    def _build_ui(self):
        self.toolbar = QFrame()
        self.toolbar.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 8px;
                padding: 4px;
            }
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 28px;
                min-height: 24px;
                color: #e5e7eb;
            }
            QToolButton:hover {
                background: rgba(59, 130, 246, 0.2);
                border-color: rgba(96, 165, 250, 0.4);
            }
            QToolButton:pressed {
                background: rgba(59, 130, 246, 0.4);
            }
            QToolButton:checked {
                background: rgba(59, 130, 246, 0.3);
                border-color: rgba(96, 165, 250, 0.6);
            }
            QComboBox {
                background: #0f172a;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
                color: #e5e7eb;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: rgba(96, 165, 250, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QSpinBox {
                background: #0f172a;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 4px;
                padding: 4px;
                color: #e5e7eb;
                min-width: 50px;
            }
            QLabel {
                color: #94a3b8;
                font-size: 11px;
            }
        """)
        
        toolbar_layout = QVBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(8)
        
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        
        clipboard_group = QHBoxLayout()
        clipboard_group.setSpacing(4)
        
        self.paste_btn = QToolButton()
        self.paste_btn.setText("📋 Pegar")
        self.paste_btn.setToolTip("Pegar (Ctrl+V)")
        self.paste_btn.clicked.connect(self._paste)
        clipboard_group.addWidget(self.paste_btn)
        
        self.cut_btn = QToolButton()
        self.cut_btn.setText("✂️ Cortar")
        self.cut_btn.setToolTip("Cortar (Ctrl+X)")
        self.cut_btn.clicked.connect(self._cut)
        clipboard_group.addWidget(self.cut_btn)
        
        self.copy_btn = QToolButton()
        self.copy_btn.setText("📄 Copiar")
        self.copy_btn.setToolTip("Copiar (Ctrl+C)")
        self.copy_btn.clicked.connect(self._copy)
        clipboard_group.addWidget(self.copy_btn)
        
        row1.addLayout(clipboard_group)
        row1.addSpacing(20)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator1.setFixedWidth(2)
        row1.addWidget(separator1)
        row1.addSpacing(10)
        
        font_group = QHBoxLayout()
        font_group.setSpacing(6)
        
        font_group.addWidget(QLabel("Fuente:"))
        
        self.font_combo = QFontComboBox()
        self.font_combo.setMinimumWidth(140)
        self.font_combo.currentFontChanged.connect(self._change_font)
        font_group.addWidget(self.font_combo)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.setEditable(True)
        sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("11")
        self.font_size_combo.setFixedWidth(55)
        self.font_size_combo.currentTextChanged.connect(self._change_font_size)
        font_group.addWidget(self.font_size_combo)
        
        font_group.addSpacing(10)
        
        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setToolTip("Negrita (Ctrl+B)")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(28, 26)
        bold_font = self.bold_btn.font()
        bold_font.setBold(True)
        self.bold_btn.setFont(bold_font)
        self.bold_btn.clicked.connect(self._toggle_bold)
        font_group.addWidget(self.bold_btn)
        
        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setToolTip("Cursiva (Ctrl+I)")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(28, 26)
        italic_font = self.italic_btn.font()
        italic_font.setItalic(True)
        self.italic_btn.setFont(italic_font)
        self.italic_btn.clicked.connect(self._toggle_italic)
        font_group.addWidget(self.italic_btn)
        
        self.underline_btn = QToolButton()
        self.underline_btn.setText("U")
        self.underline_btn.setToolTip("Subrayado (Ctrl+U)")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setFixedSize(28, 26)
        self.underline_btn.setStyleSheet("text-decoration: underline;")
        self.underline_btn.clicked.connect(self._toggle_underline)
        font_group.addWidget(self.underline_btn)
        
        self.strike_btn = QToolButton()
        self.strike_btn.setText("S")
        self.strike_btn.setToolTip("Tachado")
        self.strike_btn.setCheckable(True)
        self.strike_btn.setFixedSize(28, 26)
        self.strike_btn.setStyleSheet("text-decoration: line-through;")
        self.strike_btn.clicked.connect(self._toggle_strikethrough)
        font_group.addWidget(self.strike_btn)
        
        font_group.addSpacing(10)
        
        self.color_btn = QToolButton()
        self.color_btn.setText("A")
        self.color_btn.setToolTip("Color de texto")
        self.color_btn.setFixedSize(32, 26)
        self.color_btn.clicked.connect(self._change_text_color)
        font_group.addWidget(self.color_btn)
        
        self.highlight_btn = QToolButton()
        self.highlight_btn.setText("🖍️")
        self.highlight_btn.setToolTip("Color de resaltado")
        self.highlight_btn.setFixedSize(32, 26)
        self.highlight_btn.clicked.connect(self._change_highlight_color)
        font_group.addWidget(self.highlight_btn)
        
        row1.addLayout(font_group)
        row1.addStretch()
        
        toolbar_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        
        para_group = QHBoxLayout()
        para_group.setSpacing(4)
        
        para_group.addWidget(QLabel("Párrafo:"))
        
        self.align_left_btn = QToolButton()
        self.align_left_btn.setText("⬅️")
        self.align_left_btn.setToolTip("Alinear a la izquierda")
        self.align_left_btn.setCheckable(True)
        self.align_left_btn.setChecked(True)
        self.align_left_btn.setFixedSize(32, 26)
        self.align_left_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignLeft))
        para_group.addWidget(self.align_left_btn)
        
        self.align_center_btn = QToolButton()
        self.align_center_btn.setText("↔️")
        self.align_center_btn.setToolTip("Centrar")
        self.align_center_btn.setCheckable(True)
        self.align_center_btn.setFixedSize(32, 26)
        self.align_center_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignCenter))
        para_group.addWidget(self.align_center_btn)
        
        self.align_right_btn = QToolButton()
        self.align_right_btn.setText("➡️")
        self.align_right_btn.setToolTip("Alinear a la derecha")
        self.align_right_btn.setCheckable(True)
        self.align_right_btn.setFixedSize(32, 26)
        self.align_right_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignRight))
        para_group.addWidget(self.align_right_btn)
        
        self.align_justify_btn = QToolButton()
        self.align_justify_btn.setText("☰")
        self.align_justify_btn.setToolTip("Justificar")
        self.align_justify_btn.setCheckable(True)
        self.align_justify_btn.setFixedSize(32, 26)
        self.align_justify_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignJustify))
        para_group.addWidget(self.align_justify_btn)
        
        row2.addLayout(para_group)
        row2.addSpacing(20)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator2.setFixedWidth(2)
        row2.addWidget(separator2)
        row2.addSpacing(10)
        
        edit_group = QHBoxLayout()
        edit_group.setSpacing(4)
        
        edit_group.addWidget(QLabel("Edición:"))
        
        self.undo_btn = QToolButton()
        self.undo_btn.setText("↩️ Deshacer")
        self.undo_btn.setToolTip("Deshacer (Ctrl+Z)")
        self.undo_btn.clicked.connect(self._undo)
        edit_group.addWidget(self.undo_btn)
        
        self.redo_btn = QToolButton()
        self.redo_btn.setText("↪️ Rehacer")
        self.redo_btn.setToolTip("Rehacer (Ctrl+Y)")
        self.redo_btn.clicked.connect(self._redo)
        edit_group.addWidget(self.redo_btn)
        
        self.select_all_btn = QToolButton()
        self.select_all_btn.setText("☑️ Seleccionar todo")
        self.select_all_btn.setToolTip("Seleccionar todo (Ctrl+A)")
        self.select_all_btn.clicked.connect(self._select_all)
        edit_group.addWidget(self.select_all_btn)
        
        row2.addLayout(edit_group)
        row2.addSpacing(20)
        
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator3.setFixedWidth(2)
        row2.addWidget(separator3)
        row2.addSpacing(10)
        
        save_group = QHBoxLayout()
        save_group.setSpacing(4)
        
        self.save_btn = QPushButton("💾 Guardar")
        self.save_btn.setToolTip("Guardar cambios (Ctrl+S)")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 197, 94, 0.2);
                border: 1px solid rgba(34, 197, 94, 0.4);
                border-radius: 6px;
                padding: 6px 16px;
                color: #4ade80;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(34, 197, 94, 0.3);
                border-color: rgba(34, 197, 94, 0.6);
            }
            QPushButton:pressed {
                background: rgba(34, 197, 94, 0.4);
            }
        """)
        self.save_btn.clicked.connect(self.save_file)
        save_group.addWidget(self.save_btn)
        
        row2.addLayout(save_group)
        row2.addStretch()
        
        toolbar_layout.addLayout(row2)
        
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
        
        default_font = QFont("Calibri", 11)
        self.text_view.setFont(default_font)
        self.font_combo.setCurrentFont(default_font)
        
        self.text_view.cursorPositionChanged.connect(self._update_format_buttons)
        self.text_view.textChanged.connect(self._on_text_changed)
        
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
        zoom_controls.setSpacing(10)
        zoom_controls.addStretch(1)
        
        self.zoom_out_button = QPushButton("Zoom -")
        self.zoom_out_button.setToolTip("Reducir zoom")
        self.zoom_out_button.setFixedSize(70, 32)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        zoom_controls.addWidget(self.zoom_out_button)
        
        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_in_button.setToolTip("Aumentar zoom")
        self.zoom_in_button.setFixedSize(70, 32)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        zoom_controls.addWidget(self.zoom_in_button)
        
        zoom_controls.addStretch(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.stack, 1)
        layout.addLayout(zoom_controls)
        
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        save_action = QAction(self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        self.addAction(save_action)
        

        bold_action = QAction(self)
        bold_action.setShortcut(QKeySequence.Bold)
        bold_action.triggered.connect(self._toggle_bold)
        self.addAction(bold_action)
        
        italic_action = QAction(self)
        italic_action.setShortcut(QKeySequence.Italic)
        italic_action.triggered.connect(self._toggle_italic)
        self.addAction(italic_action)
        
        underline_action = QAction(self)
        underline_action.setShortcut(QKeySequence.Underline)
        underline_action.triggered.connect(self._toggle_underline)
        self.addAction(underline_action)
    
    def _on_text_changed(self):
        pass 
    
    def _update_format_buttons(self):
        cursor = self.text_view.textCursor()
        char_format = cursor.charFormat()
        
        self.bold_btn.setChecked(char_format.fontWeight() >= QFont.Bold)
        self.italic_btn.setChecked(char_format.fontItalic())
        self.underline_btn.setChecked(char_format.fontUnderline())
        
        self.font_combo.blockSignals(True)
        self.font_combo.setCurrentFont(char_format.font())
        self.font_combo.blockSignals(False)
        
        self.font_size_combo.blockSignals(True)
        self.font_size_combo.setCurrentText(str(int(char_format.fontPointSize())))
        self.font_size_combo.blockSignals(False)
        
        alignment = self.text_view.alignment()
        self.align_left_btn.setChecked(alignment == Qt.AlignLeft)
        self.align_center_btn.setChecked(alignment == Qt.AlignCenter)
        self.align_right_btn.setChecked(alignment == Qt.AlignRight)
        self.align_justify_btn.setChecked(alignment == Qt.AlignJustify)
    
    def _cut(self):
        self.text_view.cut()
    
    def _copy(self):
        self.text_view.copy()
    
    def _paste(self):
        self.text_view.paste()
    
    def _select_all(self):
        self.text_view.selectAll()
    
    def _undo(self):
        self.text_view.undo()
    
    def _redo(self):
        self.text_view.redo()
    
    def _change_font(self, font):
        self.text_view.setFontFamily(font.family())
    
    def _change_font_size(self, size_text):
        try:
            size = int(size_text)
            self.text_view.setFontPointSize(size)
        except ValueError:
            pass
    
    def _toggle_bold(self):
        if self.bold_btn.isChecked():
            self.text_view.setFontWeight(QFont.Bold)
        else:
            self.text_view.setFontWeight(QFont.Normal)
    
    def _toggle_italic(self):
        self.text_view.setFontItalic(self.italic_btn.isChecked())
    
    def _toggle_underline(self):
        self.text_view.setFontUnderline(self.underline_btn.isChecked())
    
    def _toggle_strikethrough(self):
        fmt = self.text_view.currentCharFormat()
        fmt.setFontStrikeOut(self.strike_btn.isChecked())
        self.text_view.setCurrentCharFormat(fmt)
    
    def _change_text_color(self):
        color = QColorDialog.getColor(self.text_view.textColor(), self, "Color de texto")
        if color.isValid():
            self.text_view.setTextColor(color)
            self.color_btn.setStyleSheet(f"color: {color.name()};")
    
    def _change_highlight_color(self):
        color = QColorDialog.getColor(Qt.yellow, self, "Color de resaltado")
        if color.isValid():
            self.text_view.setTextBackgroundColor(color)
    
    def _set_alignment(self, alignment):
        self.text_view.setAlignment(alignment)
        self._update_format_buttons()
    
    def load_file(self, path: str):
        self.current_path = path
        self.is_pdf = False
        
        ext = Path(path).suffix.lower()
        
        if ext in PDF_EXTENSIONS:
            self.is_pdf = True
            self.pdf_document.load(path)
            
            if self.pdf_document.status() == QPdfDocument.Status.Ready:
                pdf_text = self._extract_pdf_text()
                self.text_view.setPlainText(pdf_text)
                self.stack.setCurrentWidget(self.text_view)
                self.toolbar.setVisible(True)
                self.zoom_out_button.setVisible(False)
                self.zoom_in_button.setVisible(False)
                return
            
            self.message.setText("No fue posible renderizar el PDF.")
            self.stack.setCurrentWidget(self.message)
            self.toolbar.setVisible(False)
            return
        
        if ext in TEXT_DOCUMENT_EXTENSIONS:
            content = read_text_file(path)
            self.text_view.setPlainText(content)
            self.stack.setCurrentWidget(self.text_view)
            self.toolbar.setVisible(True)
            self.zoom_out_button.setVisible(False)
            self.zoom_in_button.setVisible(False)
            return
        
        self.message.setText("Formato de documento incompatible para visualización directa.")
        self.stack.setCurrentWidget(self.message)
        self.toolbar.setVisible(False)
    
    def _extract_pdf_text(self) -> str:
        text_parts = []
        page_count = self.pdf_document.pageCount()
        
        for page_num in range(page_count):
            text_parts.append(f"[Página {page_num + 1}]")
        
        return "\n\n".join(text_parts) if text_parts else "[Contenido del PDF - edición limitada]"
    
    def save_file(self):
        if not self.current_path:
            return
        
        try:
            if self.is_pdf:
                txt_path = os.path.splitext(self.current_path)[0] + "_editado.txt"
                content = self.text_view.toPlainText()
                if save_text_file(txt_path, content):
                    QMessageBox.information(
                        self, 
                        "Éxito", 
                        f"Contenido guardado como texto plano:\n{txt_path}"
                    )
                else:
                    QMessageBox.critical(self, "Error", "No se pudo guardar el archivo.")
            else:
                content = self.text_view.toPlainText()
                if save_text_file(self.current_path, content):
                    QMessageBox.information(self, "Éxito", "Archivo guardado correctamente.")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo guardar el archivo.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar:\n{str(e)}")
    
    def zoom_in(self):
        if self.stack.currentWidget() == self.pdf_view:
            if self.current_zoom_index < len(self.zoom_levels) - 1:
                self.current_zoom_index += 1
                self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])
    
    def zoom_out(self):
        if self.stack.currentWidget() == self.pdf_view:
            if self.current_zoom_index > 0:
                self.current_zoom_index -= 1
                self.pdf_view.setZoomFactor(self.zoom_levels[self.current_zoom_index])