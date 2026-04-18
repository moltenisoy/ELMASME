import os
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence, QColor, QTextCharFormat
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QToolButton, QFontComboBox, QComboBox, QColorDialog, QMessageBox,
    QFileDialog
)


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as file:
        return file.read()


def save_text_file(path: str, content: str) -> bool:
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return True


_EDITABLE_EXTENSIONS = {
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


def is_editable(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in _EDITABLE_EXTENSIONS


class TextEditorToolbar(QFrame):

    def __init__(self, text_view: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_view = text_view
        self._build_ui()
        self._setup_shortcuts()

        self.text_view.cursorPositionChanged.connect(self._update_format_buttons)
        self.text_view.textChanged.connect(self._on_text_changed)

    def _build_ui(self):
        self.setStyleSheet("""
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
                padding: 4px 24px 4px 8px;
                color: #e5e7eb;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: rgba(96, 165, 250, 0.5);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid rgba(148, 163, 184, 0.3);
                background: rgba(59, 130, 246, 0.15);
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #94a3b8;
                margin: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #60a5fa;
            }
            QFontComboBox {
                background: #0f172a;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 4px;
                padding: 4px 24px 4px 8px;
                color: #e5e7eb;
                min-width: 140px;
            }
            QFontComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid rgba(148, 163, 184, 0.3);
                background: rgba(59, 130, 246, 0.15);
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QFontComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #94a3b8;
                margin: 0px;
            }
            QFontComboBox::down-arrow:hover {
                border-top-color: #60a5fa;
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

        toolbar_layout = QVBoxLayout(self)
        toolbar_layout.setContentsMargins(6, 4, 6, 4)
        toolbar_layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        clipboard_group = QHBoxLayout()
        clipboard_group.setSpacing(4)

        self.paste_btn = QToolButton()
        self.paste_btn.setText("📋")
        self.paste_btn.setToolTip("Pegar (Ctrl+V)")
        self.paste_btn.setFixedSize(28, 26)
        self.paste_btn.clicked.connect(self._paste)
        clipboard_group.addWidget(self.paste_btn)

        self.cut_btn = QToolButton()
        self.cut_btn.setText("✂️")
        self.cut_btn.setToolTip("Cortar (Ctrl+X)")
        self.cut_btn.setFixedSize(28, 26)
        self.cut_btn.clicked.connect(self._cut)
        clipboard_group.addWidget(self.cut_btn)

        self.copy_btn = QToolButton()
        self.copy_btn.setText("📄")
        self.copy_btn.setToolTip("Copiar (Ctrl+C)")
        self.copy_btn.setFixedSize(28, 26)
        self.copy_btn.clicked.connect(self._copy)
        clipboard_group.addWidget(self.copy_btn)

        row1.addLayout(clipboard_group)
        row1.addSpacing(8)

        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator1.setFixedWidth(2)
        row1.addWidget(separator1)
        row1.addSpacing(4)

        font_group = QHBoxLayout()
        font_group.setSpacing(4)

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
        self.font_size_combo.setFixedWidth(48)
        self.font_size_combo.currentTextChanged.connect(self._change_font_size)
        font_group.addWidget(self.font_size_combo)

        font_group.addSpacing(4)

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

        font_group.addSpacing(4)

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
        row2.setSpacing(6)

        para_group = QHBoxLayout()
        para_group.setSpacing(4)

        self.align_left_btn = QToolButton()
        self.align_left_btn.setText("≡←")
        self.align_left_btn.setToolTip("Alinear a la izquierda")
        self.align_left_btn.setCheckable(True)
        self.align_left_btn.setChecked(True)
        self.align_left_btn.setFixedSize(36, 26)
        self.align_left_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignLeft))
        para_group.addWidget(self.align_left_btn)

        self.align_center_btn = QToolButton()
        self.align_center_btn.setText("≡↔")
        self.align_center_btn.setToolTip("Centrar")
        self.align_center_btn.setCheckable(True)
        self.align_center_btn.setFixedSize(36, 26)
        self.align_center_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignCenter))
        para_group.addWidget(self.align_center_btn)

        self.align_right_btn = QToolButton()
        self.align_right_btn.setText("≡→")
        self.align_right_btn.setToolTip("Alinear a la derecha")
        self.align_right_btn.setCheckable(True)
        self.align_right_btn.setFixedSize(36, 26)
        self.align_right_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignRight))
        para_group.addWidget(self.align_right_btn)

        self.align_justify_btn = QToolButton()
        self.align_justify_btn.setText("≡≡")
        self.align_justify_btn.setToolTip("Justificar")
        self.align_justify_btn.setCheckable(True)
        self.align_justify_btn.setFixedSize(36, 26)
        self.align_justify_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignJustify))
        para_group.addWidget(self.align_justify_btn)

        row2.addLayout(para_group)
        row2.addSpacing(8)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator2.setFixedWidth(2)
        row2.addWidget(separator2)
        row2.addSpacing(4)

        edit_group = QHBoxLayout()
        edit_group.setSpacing(4)

        self.undo_btn = QToolButton()
        self.undo_btn.setText("↩️")
        self.undo_btn.setToolTip("Deshacer (Ctrl+Z)")
        self.undo_btn.setFixedSize(28, 26)
        self.undo_btn.clicked.connect(self._undo)
        edit_group.addWidget(self.undo_btn)

        self.redo_btn = QToolButton()
        self.redo_btn.setText("↪️")
        self.redo_btn.setToolTip("Rehacer (Ctrl+Y)")
        self.redo_btn.setFixedSize(28, 26)
        self.redo_btn.clicked.connect(self._redo)
        edit_group.addWidget(self.redo_btn)

        self.select_all_btn = QToolButton()
        self.select_all_btn.setText("☑️")
        self.select_all_btn.setToolTip("Seleccionar todo (Ctrl+A)")
        self.select_all_btn.setFixedSize(28, 26)
        self.select_all_btn.clicked.connect(self._select_all)
        edit_group.addWidget(self.select_all_btn)

        row2.addLayout(edit_group)
        row2.addSpacing(8)

        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator3.setFixedWidth(2)
        row2.addWidget(separator3)
        row2.addSpacing(4)

        save_group = QHBoxLayout()
        save_group.setSpacing(4)

        self.save_btn = QPushButton("💾 Guardar")
        self.save_btn.setToolTip("Guardar cambios (Ctrl+S)")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34, 197, 94, 0.2);
                border: 1px solid rgba(34, 197, 94, 0.4);
                border-radius: 6px;
                padding: 4px 12px;
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
        save_group.addWidget(self.save_btn)

        self.export_pdf_btn = QPushButton("📄 PDF")
        self.export_pdf_btn.setToolTip("Exportar como PDF")
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.2);
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 6px;
                padding: 4px 12px;
                color: #60a5fa;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(59, 130, 246, 0.3);
                border-color: rgba(59, 130, 246, 0.6);
            }
            QPushButton:pressed {
                background: rgba(59, 130, 246, 0.4);
            }
        """)
        self.export_pdf_btn.clicked.connect(self._export_pdf)
        save_group.addWidget(self.export_pdf_btn)

        row2.addLayout(save_group)
        row2.addStretch()

        toolbar_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 2px 4px;")
        row3.addWidget(self.stats_label)
        row3.addStretch()
        toolbar_layout.addLayout(row3)

        default_font = QFont("Calibri", 11)
        self.text_view.setFont(default_font)
        self.font_combo.setCurrentFont(default_font)

    def add_zoom_controls(self, zoom_out_btn, zoom_in_btn, search_btn):
        row = self.layout().itemAt(1).layout()
        stretch_idx = row.count() - 1
        row.insertWidget(stretch_idx, zoom_out_btn)
        row.insertWidget(stretch_idx + 1, zoom_in_btn)
        row.insertWidget(stretch_idx + 2, search_btn)

    def _setup_shortcuts(self):
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
        self._update_stats()

    def _update_stats(self):
        text = self.text_view.toPlainText()
        chars = len(text)
        lines = text.count("\n") + 1 if text else 0
        words = len(text.split()) if text.strip() else 0
        self.stats_label.setText(
            f"Palabras: {words}  |  Líneas: {lines}  |  Caracteres: {chars}"
        )

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
        size = char_format.fontPointSize()
        if size <= 0:
            size = self.text_view.font().pointSize()
            if size <= 0:
                size = 11
        self.font_size_combo.setCurrentText(str(int(size)))
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
        if size_text.isdigit():
            size = int(size_text)
            self.text_view.setFontPointSize(size)

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

    def _export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar como PDF", "", "PDF (*.pdf)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        self.text_view.document().print_(printer)

    def save_current(self, current_path, is_pdf):
        if not current_path:
            return
        if is_pdf:
            txt_path = os.path.splitext(current_path)[0] + "_editado.txt"
            content = self.text_view.toPlainText()
            save_text_file(txt_path, content)
        else:
            content = self.text_view.toPlainText()
            save_text_file(current_path, content)
