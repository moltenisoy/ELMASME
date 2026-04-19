import os
import datetime
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QAction, QFont, QKeySequence, QColor, QTextCharFormat,
    QTextTableFormat, QTextLength, QTextFrameFormat,
    QPainter, QFontMetrics,
)
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QToolButton, QFontComboBox, QComboBox, QColorDialog, QMessageBox,
    QFileDialog, QDialog, QSpinBox, QFormLayout, QDialogButtonBox,
    QLineEdit, QGridLayout, QGroupBox,
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


class InsertTableDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insertar tabla")
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QDialog { background: #1e293b; }
            QLabel { color: #e5e7eb; font-size: 13px; }
            QSpinBox {
                background: #0f172a; color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 4px; padding: 4px; min-width: 80px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(3)
        form.addRow("Filas:", self.rows_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 26)
        self.cols_spin.setValue(3)
        form.addRow("Columnas:", self.cols_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                background: rgba(59,130,246,0.2);
                border: 1px solid rgba(59,130,246,0.4);
                border-radius: 6px; padding: 6px 16px;
                color: #60a5fa; font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(59,130,246,0.35);
            }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return self.rows_spin.value(), self.cols_spin.value()


class HeaderFooterDialog(QDialog):

    def __init__(self, header_left="", header_center="", header_right="",
                 footer_left="", footer_center="", footer_right="",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encabezado y pie de página")
        self.setFixedSize(500, 340)
        self.setStyleSheet("""
            QDialog { background: #1e293b; }
            QLabel { color: #e5e7eb; font-size: 12px; }
            QGroupBox {
                color: #60a5fa; font-weight: 600; font-size: 13px;
                border: 1px solid rgba(96,165,250,0.3);
                border-radius: 6px; margin-top: 8px; padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QLineEdit {
                background: #0f172a; color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 4px; padding: 6px 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel("Variables: {filename} = nombre del archivo, {page} = nº de página, {date} = fecha")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(hint)

        header_group = QGroupBox("Encabezado")
        hg_layout = QGridLayout(header_group)
        hg_layout.setSpacing(6)
        hg_layout.addWidget(QLabel("Izquierda:"), 0, 0)
        self.header_left = QLineEdit(header_left)
        hg_layout.addWidget(self.header_left, 0, 1)
        hg_layout.addWidget(QLabel("Centro:"), 1, 0)
        self.header_center = QLineEdit(header_center)
        hg_layout.addWidget(self.header_center, 1, 1)
        hg_layout.addWidget(QLabel("Derecha:"), 2, 0)
        self.header_right = QLineEdit(header_right)
        hg_layout.addWidget(self.header_right, 2, 1)
        layout.addWidget(header_group)

        footer_group = QGroupBox("Pie de página")
        fg_layout = QGridLayout(footer_group)
        fg_layout.setSpacing(6)
        fg_layout.addWidget(QLabel("Izquierda:"), 0, 0)
        self.footer_left = QLineEdit(footer_left)
        fg_layout.addWidget(self.footer_left, 0, 1)
        fg_layout.addWidget(QLabel("Centro:"), 1, 0)
        self.footer_center = QLineEdit(footer_center)
        fg_layout.addWidget(self.footer_center, 1, 1)
        fg_layout.addWidget(QLabel("Derecha:"), 2, 0)
        self.footer_right = QLineEdit(footer_right)
        fg_layout.addWidget(self.footer_right, 2, 1)
        layout.addWidget(footer_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                background: rgba(59,130,246,0.2);
                border: 1px solid rgba(59,130,246,0.4);
                border-radius: 6px; padding: 6px 16px;
                color: #60a5fa; font-weight: 500;
            }
            QPushButton:hover { background: rgba(59,130,246,0.35); }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return {
            "header_left": self.header_left.text(),
            "header_center": self.header_center.text(),
            "header_right": self.header_right.text(),
            "footer_left": self.footer_left.text(),
            "footer_center": self.footer_center.text(),
            "footer_right": self.footer_right.text(),
        }


class TextEditorToolbar(QFrame):

    def __init__(self, text_view: QTextEdit, parent=None):
        super().__init__(parent)
        self.text_view = text_view
        self._header_footer_config = {
            "header_left": "", "header_center": "", "header_right": "",
            "footer_left": "", "footer_center": "{page}", "footer_right": "",
        }
        self._build_ui()
        self._setup_shortcuts()

        self.text_view.cursorPositionChanged.connect(self._update_format_buttons)
        self.text_view.cursorPositionChanged.connect(self._update_cursor_position)
        self.text_view.textChanged.connect(self._on_text_changed)

    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 8px;
                padding: 0px 4px 4px 4px;
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
        toolbar_layout.setContentsMargins(6, 0, 6, 4)
        toolbar_layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        clipboard_group = QHBoxLayout()
        clipboard_group.setSpacing(4)

        self.paste_btn = QToolButton()
        self.paste_btn.setText("📋")
        self.paste_btn.setToolTip("Pegar (Ctrl+V)")
        self.paste_btn.setFixedSize(56, 52)
        self.paste_btn.clicked.connect(self._paste)
        clipboard_group.addWidget(self.paste_btn)

        self.cut_btn = QToolButton()
        self.cut_btn.setText("✂️")
        self.cut_btn.setToolTip("Cortar (Ctrl+X)")
        self.cut_btn.setFixedSize(56, 52)
        self.cut_btn.clicked.connect(self._cut)
        clipboard_group.addWidget(self.cut_btn)

        self.copy_btn = QToolButton()
        self.copy_btn.setText("📄")
        self.copy_btn.setToolTip("Copiar (Ctrl+C)")
        self.copy_btn.setFixedSize(56, 52)
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

        self.font_label = QLabel("Fuente:")
        self.font_label.setFixedHeight(30)
        self.font_label.setStyleSheet("color: #94a3b8; font-size: 11px; border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 4px; padding: 0px 6px;")
        font_group.addWidget(self.font_label)

        self.font_combo = QFontComboBox()
        self.font_combo.setFixedWidth(180)
        self.font_combo.setFixedHeight(30)
        self.font_combo.currentFontChanged.connect(self._change_font)
        font_group.addWidget(self.font_combo)

        self.font_size_combo = QComboBox()
        self.font_size_combo.setEditable(True)
        sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("11")
        self.font_size_combo.setFixedWidth(65)
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
        row1.addSpacing(8)

        separator_insert = QFrame()
        separator_insert.setFrameShape(QFrame.VLine)
        separator_insert.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator_insert.setFixedWidth(2)
        row1.addWidget(separator_insert)
        row1.addSpacing(4)

        insert_group = QHBoxLayout()
        insert_group.setSpacing(4)

        self.insert_table_btn = QToolButton()
        self.insert_table_btn.setText("📊 Tabla")
        self.insert_table_btn.setToolTip("Insertar tabla")
        self.insert_table_btn.setFixedSize(72, 26)
        self.insert_table_btn.clicked.connect(self._insert_table)
        insert_group.addWidget(self.insert_table_btn)

        self.header_footer_btn = QToolButton()
        self.header_footer_btn.setText("📃 Encab.")
        self.header_footer_btn.setToolTip("Configurar encabezado y pie de página para impresión")
        self.header_footer_btn.setFixedSize(82, 26)
        self.header_footer_btn.clicked.connect(self._configure_header_footer)
        insert_group.addWidget(self.header_footer_btn)

        self.compare_btn = QToolButton()
        self.compare_btn.setText("⇄ Comparar")
        self.compare_btn.setToolTip("Comparar dos documentos lado a lado")
        self.compare_btn.setFixedSize(95, 26)
        insert_group.addWidget(self.compare_btn)

        row1.addLayout(insert_group)
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
        self.align_left_btn.setFixedSize(72, 52)
        self.align_left_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignLeft))
        para_group.addWidget(self.align_left_btn)

        self.align_center_btn = QToolButton()
        self.align_center_btn.setText("≡↔")
        self.align_center_btn.setToolTip("Centrar")
        self.align_center_btn.setCheckable(True)
        self.align_center_btn.setFixedSize(72, 52)
        self.align_center_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignCenter))
        para_group.addWidget(self.align_center_btn)

        self.align_right_btn = QToolButton()
        self.align_right_btn.setText("≡→")
        self.align_right_btn.setToolTip("Alinear a la derecha")
        self.align_right_btn.setCheckable(True)
        self.align_right_btn.setFixedSize(72, 52)
        self.align_right_btn.clicked.connect(lambda: self._set_alignment(Qt.AlignRight))
        para_group.addWidget(self.align_right_btn)

        self.align_justify_btn = QToolButton()
        self.align_justify_btn.setText("≡≡")
        self.align_justify_btn.setToolTip("Justificar")
        self.align_justify_btn.setCheckable(True)
        self.align_justify_btn.setFixedSize(72, 52)
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
        self.undo_btn.setFixedSize(56, 52)
        self.undo_btn.clicked.connect(self._undo)
        edit_group.addWidget(self.undo_btn)

        self.redo_btn = QToolButton()
        self.redo_btn.setText("↪️")
        self.redo_btn.setToolTip("Rehacer (Ctrl+Y)")
        self.redo_btn.setFixedSize(56, 52)
        self.redo_btn.clicked.connect(self._redo)
        edit_group.addWidget(self.redo_btn)

        self.select_all_btn = QToolButton()
        self.select_all_btn.setText("Seleccionar todo")
        self.select_all_btn.setToolTip("Seleccionar todo (Ctrl+A)")
        self.select_all_btn.setFixedSize(120, 52)
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

        self.save_as_btn = QPushButton("💾 Guardar como")
        self.save_as_btn.setToolTip("Guardar como...")
        self.save_as_btn.setStyleSheet("""
            QPushButton {
                background: rgba(234, 179, 8, 0.2);
                border: 1px solid rgba(234, 179, 8, 0.4);
                border-radius: 6px;
                padding: 4px 12px;
                color: #facc15;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(234, 179, 8, 0.3);
                border-color: rgba(234, 179, 8, 0.6);
            }
            QPushButton:pressed {
                background: rgba(234, 179, 8, 0.4);
            }
        """)
        save_group.addWidget(self.save_as_btn)

        self.export_pdf_btn = QPushButton("📄 Guardar como PDF")
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
        row2.addSpacing(8)

        separator4 = QFrame()
        separator4.setFrameShape(QFrame.VLine)
        separator4.setStyleSheet("color: rgba(148, 163, 184, 0.3);")
        separator4.setFixedWidth(2)
        row2.addWidget(separator4)
        row2.addSpacing(4)

        viewer_group = QHBoxLayout()
        viewer_group.setSpacing(4)

        self.zoom_out_btn = QPushButton("Zoom -")
        self.zoom_out_btn.setToolTip("Reducir zoom")
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                background: rgba(148, 163, 184, 0.15);
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                color: #e5e7eb;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.25);
                border-color: rgba(148, 163, 184, 0.5);
            }
        """)
        viewer_group.addWidget(self.zoom_out_btn)

        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_in_btn.setToolTip("Aumentar zoom")
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                background: rgba(148, 163, 184, 0.15);
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                color: #e5e7eb;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.25);
                border-color: rgba(148, 163, 184, 0.5);
            }
        """)
        viewer_group.addWidget(self.zoom_in_btn)

        self.search_btn = QPushButton("🔍")
        self.search_btn.setToolTip("Buscar")
        self.search_btn.setFixedSize(32, 26)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: rgba(148, 163, 184, 0.15);
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                color: #e5e7eb;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.25);
                border-color: rgba(148, 163, 184, 0.5);
            }
        """)
        viewer_group.addWidget(self.search_btn)

        self.contrast_btn = QPushButton("Alto contraste")
        self.contrast_btn.setToolTip("Alternar alto contraste")
        self.contrast_btn.setFixedSize(110, 26)
        self.contrast_btn.setStyleSheet("""
            QPushButton {
                background: rgba(148, 163, 184, 0.15);
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                color: #e5e7eb;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.25);
                border-color: rgba(148, 163, 184, 0.5);
            }
        """)
        viewer_group.addWidget(self.contrast_btn)

        row2.addLayout(viewer_group)
        row2.addStretch()

        toolbar_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 2px 4px; border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 4px;")
        row3.addWidget(self.stats_label)

        self.cursor_label = QLabel()
        self.cursor_label.setStyleSheet("color: #60a5fa; font-size: 11px; padding: 2px 4px; border: 1px solid rgba(96, 165, 250, 0.4); border-radius: 4px;")
        row3.addWidget(self.cursor_label)

        row3.addStretch()
        toolbar_layout.addLayout(row3)

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
        self._update_stats()

    def _update_stats(self):
        text = self.text_view.toPlainText()
        chars = len(text)
        lines = text.count("\n") + 1 if text else 0
        words = len(text.split()) if text.strip() else 0
        self.stats_label.setText(
            f"Palabras: {words}  |  Líneas: {lines}  |  Caracteres: {chars}"
        )

    def _update_cursor_position(self):
        cursor = self.text_view.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_label.setText(f"Línea: {line}  |  Carácter: {col}")

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


    def _insert_table(self):
        dlg = InsertTableDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        rows, cols = dlg.get_values()
        cursor = self.text_view.textCursor()
        fmt = QTextTableFormat()
        fmt.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)
        fmt.setCellPadding(4)
        fmt.setCellSpacing(0)
        fmt.setBorder(1)
        fmt.setBorderBrush(QColor("#94a3b8"))
        constraints = []
        col_width = 100.0 / cols
        for _ in range(cols):
            constraints.append(QTextLength(QTextLength.PercentageLength, col_width))
        fmt.setColumnWidthConstraints(constraints)
        cursor.insertTable(rows, cols, fmt)


    def _configure_header_footer(self):
        cfg = self._header_footer_config
        dlg = HeaderFooterDialog(
            header_left=cfg["header_left"],
            header_center=cfg["header_center"],
            header_right=cfg["header_right"],
            footer_left=cfg["footer_left"],
            footer_center=cfg["footer_center"],
            footer_right=cfg["footer_right"],
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            self._header_footer_config = dlg.get_values()

    def _export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar como PDF", "", "PDF (*.pdf)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        cfg = self._header_footer_config
        has_header = any(cfg.get(k) for k in ("header_left", "header_center", "header_right"))
        has_footer = any(cfg.get(k) for k in ("footer_left", "footer_center", "footer_right"))

        if not has_header and not has_footer:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            self.text_view.document().print_(printer)
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)

        source_doc = self.text_view.document().clone()
        source_doc.setPageSize(printer.pageRect(QPrinter.Point).size())

        painter = QPainter()
        if not painter.begin(printer):
            return

        page_rect = printer.pageRect(QPrinter.DevicePixel)
        full_rect = printer.paperRect(QPrinter.DevicePixel)

        header_font = QFont("Calibri", 9)
        header_fm = QFontMetrics(header_font)
        header_height = header_fm.height() + 10
        footer_height = header_height

        margin_top = max(0, page_rect.top() - full_rect.top())
        margin_left = max(0, page_rect.left() - full_rect.left())

        h_offset = header_height if has_header else 0
        f_offset = footer_height if has_footer else 0
        content_top = margin_top + h_offset

        filename = os.path.basename(file_path) if file_path else ""
        date_str = datetime.date.today().strftime("%Y-%m-%d")

        def _resolve(text, page_num):
            return text.replace("{page}", str(page_num)).replace(
                "{filename}", filename
            ).replace("{date}", date_str)

        source_doc.setPageSize(page_rect.size())
        total_pages = source_doc.pageCount()
        if total_pages < 1:
            total_pages = 1

        for page in range(total_pages):
            if page > 0:
                printer.newPage()

            if has_header:
                painter.setFont(header_font)
                y = margin_top + header_fm.ascent()
                if cfg["header_left"]:
                    painter.drawText(int(margin_left), int(y),
                                     _resolve(cfg["header_left"], page + 1))
                if cfg["header_center"]:
                    text = _resolve(cfg["header_center"], page + 1)
                    tw = header_fm.horizontalAdvance(text)
                    painter.drawText(int(margin_left + (page_rect.width() - tw) / 2),
                                     int(y), text)
                if cfg["header_right"]:
                    text = _resolve(cfg["header_right"], page + 1)
                    tw = header_fm.horizontalAdvance(text)
                    painter.drawText(int(margin_left + page_rect.width() - tw),
                                     int(y), text)

            if has_footer:
                painter.setFont(header_font)
                y = margin_top + page_rect.height() - 4
                if cfg["footer_left"]:
                    painter.drawText(int(margin_left), int(y),
                                     _resolve(cfg["footer_left"], page + 1))
                if cfg["footer_center"]:
                    text = _resolve(cfg["footer_center"], page + 1)
                    tw = header_fm.horizontalAdvance(text)
                    painter.drawText(int(margin_left + (page_rect.width() - tw) / 2),
                                     int(y), text)
                if cfg["footer_right"]:
                    text = _resolve(cfg["footer_right"], page + 1)
                    tw = header_fm.horizontalAdvance(text)
                    painter.drawText(int(margin_left + page_rect.width() - tw),
                                     int(y), text)

            painter.save()
            painter.translate(margin_left, content_top)
            clip_rect = page_rect.adjusted(0, 0, 0, -h_offset - f_offset)
            painter.setClipRect(clip_rect.translated(-margin_left, -content_top))
            painter.translate(0, -page * page_rect.height())
            source_doc.drawContents(painter)
            painter.restore()

        painter.end()

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
