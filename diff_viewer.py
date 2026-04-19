
import os
import difflib
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFileDialog, QSplitter, QFrame,
)


def _read_file_lines(path: str):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except OSError:
        return []


class _DiffPanel(QFrame):

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid rgba(148,163,184,0.2);
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #60a5fa; font-weight: 600; font-size: 12px; border: none;")
        header.addWidget(self.title_label)

        self.path_label = QLabel("")
        self.path_label.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        header.addWidget(self.path_label, 1)

        self.open_btn = QPushButton("📂 Abrir")
        self.open_btn.setFixedHeight(26)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59,130,246,0.2);
                border: 1px solid rgba(59,130,246,0.4);
                border-radius: 6px; padding: 2px 10px;
                color: #60a5fa; font-weight: 500;
                font-size: 26px;
            }
            QPushButton:hover { background: rgba(59,130,246,0.35); }
        """)
        header.addWidget(self.open_btn)

        layout.addLayout(header)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setAcceptDrops(False)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: #1e293b;
                color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.15);
                border-radius: 6px;
                padding: 8px;
                selection-background-color: rgba(96,165,250,0.3);
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #0f172a; border-radius: 4px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #475569; border-radius: 4px;
            }
        """)
        layout.addWidget(self.text_edit)

        self._file_path = None
        self._lines = []

    def load_file(self, path):
        self._file_path = path
        self._lines = _read_file_lines(path)
        self.path_label.setText(os.path.basename(path))
        self.text_edit.setPlainText("".join(self._lines))

    @property
    def file_path(self):
        return self._file_path

    @property
    def lines(self):
        return self._lines

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path and os.path.isfile(path):
                    self.load_file(path)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)


class DiffViewerWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        title = QLabel("📄 Comparar documentos")
        title.setStyleSheet("color: #e5e7eb; font-weight: 600; font-size: 14px;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self.compare_btn = QPushButton("▶ Comparar")
        self.compare_btn.setFixedHeight(30)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background: rgba(34,197,94,0.2);
                border: 1px solid rgba(34,197,94,0.4);
                border-radius: 6px; padding: 4px 14px;
                color: #4ade80; font-weight: 600;
                font-size: 26px;
            }
            QPushButton:hover { background: rgba(34,197,94,0.35); }
        """)
        self.compare_btn.clicked.connect(self._run_diff)
        top_bar.addWidget(self.compare_btn)

        self.close_btn = QPushButton("✕ Cerrar")
        self.close_btn.setFixedHeight(30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239,68,68,0.2);
                border: 1px solid rgba(239,68,68,0.4);
                border-radius: 6px; padding: 4px 14px;
                color: #f87171; font-weight: 600;
                font-size: 26px;
            }
            QPushButton:hover { background: rgba(239,68,68,0.35); }
        """)
        top_bar.addWidget(self.close_btn)

        layout.addLayout(top_bar)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(
            "color: #94a3b8; font-size: 11px; padding: 2px 4px;"
        )
        layout.addWidget(self.stats_label)

        self.splitter = QSplitter(Qt.Horizontal)
        self.left_panel = _DiffPanel("Documento A")
        self.right_panel = _DiffPanel("Documento B")
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        layout.addWidget(self.splitter, 1)

        self.left_panel.open_btn.clicked.connect(self._open_left)
        self.right_panel.open_btn.clicked.connect(self._open_right)

        self.left_panel.text_edit.verticalScrollBar().valueChanged.connect(
            self._sync_scroll_right
        )
        self.right_panel.text_edit.verticalScrollBar().valueChanged.connect(
            self._sync_scroll_left
        )
        self._syncing = False

    def _sync_scroll_right(self, value):
        if self._syncing:
            return
        self._syncing = True
        self.right_panel.text_edit.verticalScrollBar().setValue(value)
        self._syncing = False

    def _sync_scroll_left(self, value):
        if self._syncing:
            return
        self._syncing = True
        self.left_panel.text_edit.verticalScrollBar().setValue(value)
        self._syncing = False

    def _open_left(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir documento A", "", "Todos (*.*)")
        if path:
            self.left_panel.load_file(path)

    def _open_right(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir documento B", "", "Todos (*.*)")
        if path:
            self.right_panel.load_file(path)

    def load_left_file(self, path):
        self.left_panel.load_file(path)

    def _run_diff(self):
        left_lines = self.left_panel.lines
        right_lines = self.right_panel.lines

        if not left_lines and not right_lines:
            self.stats_label.setText("Carga dos documentos para comparar.")
            return

        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        opcodes = matcher.get_opcodes()

        added = 0
        removed = 0
        changed = 0

        left_formatted = []
        right_formatted = []

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for line in left_lines[i1:i2]:
                    left_formatted.append(("equal", line))
                for line in right_lines[j1:j2]:
                    right_formatted.append(("equal", line))
            elif tag == "replace":
                changed += (i2 - i1) + (j2 - j1)
                for line in left_lines[i1:i2]:
                    left_formatted.append(("remove", line))
                for line in right_lines[j1:j2]:
                    right_formatted.append(("add", line))
                diff = (i2 - i1) - (j2 - j1)
                if diff > 0:
                    for _ in range(diff):
                        right_formatted.append(("pad", "\n"))
                elif diff < 0:
                    for _ in range(-diff):
                        left_formatted.append(("pad", "\n"))
            elif tag == "delete":
                removed += i2 - i1
                for line in left_lines[i1:i2]:
                    left_formatted.append(("remove", line))
                for _ in range(i2 - i1):
                    right_formatted.append(("pad", "\n"))
            elif tag == "insert":
                added += j2 - j1
                for _ in range(j2 - j1):
                    left_formatted.append(("pad", "\n"))
                for line in right_lines[j1:j2]:
                    right_formatted.append(("add", line))

        self._apply_highlighting(self.left_panel.text_edit, left_formatted)
        self._apply_highlighting(self.right_panel.text_edit, right_formatted)

        self.stats_label.setText(
            f"Diferencias: {added} líneas añadidas, {removed} líneas eliminadas, "
            f"{changed} líneas modificadas"
        )

    @staticmethod
    def _apply_highlighting(text_edit, formatted_lines):
        text_edit.clear()
        cursor = text_edit.textCursor()

        fmt_equal = QTextCharFormat()
        fmt_equal.setForeground(QColor("#e5e7eb"))
        fmt_equal.setBackground(QColor("transparent"))

        fmt_add = QTextCharFormat()
        fmt_add.setForeground(QColor("#4ade80"))
        fmt_add.setBackground(QColor(34, 197, 94, 40))

        fmt_remove = QTextCharFormat()
        fmt_remove.setForeground(QColor("#f87171"))
        fmt_remove.setBackground(QColor(239, 68, 68, 40))

        fmt_pad = QTextCharFormat()
        fmt_pad.setForeground(QColor("#475569"))
        fmt_pad.setBackground(QColor(30, 41, 59, 80))

        fmt_map = {
            "equal": fmt_equal,
            "add": fmt_add,
            "remove": fmt_remove,
            "pad": fmt_pad,
        }

        for tag, line in formatted_lines:
            fmt = fmt_map.get(tag, fmt_equal)
            cursor.insertText(line, fmt)

        text_edit.setTextCursor(cursor)
        text_edit.moveCursor(QTextCursor.MoveOperation.Start)
