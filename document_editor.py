import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence, QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QToolButton, QFontComboBox, QComboBox, QColorDialog, QMessageBox,
    QFileDialog
)

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
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return True

def is_editable(path: str) -> bool:
    return True

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

        toolbar_layout = QVBoxLayout(self)
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
        save_group.addWidget(self.save_btn)

        row2.addLayout(save_group)
        row2.addStretch()

        toolbar_layout.addLayout(row2)

        default_font = QFont("Calibri", 11)
        self.text_view.setFont(default_font)
        self.font_combo.setCurrentFont(default_font)

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

    def save_current(self, current_path, is_pdf):
        if not current_path:
            return

        if is_pdf:
            txt_path = os.path.splitext(current_path)[0] + "_editado.txt"
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
            if save_text_file(current_path, content):
                QMessageBox.information(self, "Éxito", "Archivo guardado correctamente.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar el archivo.")
