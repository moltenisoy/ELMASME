"""
line_number_area.py — QTextEdit with an integrated line-number margin.

Usage:
    editor = LineNumberTextEdit()
    editor.set_line_numbers_visible(True)   # show/hide
"""

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QTextEdit, QWidget


class _LineNumberArea(QWidget):
    """Narrow widget painted on the left side of a LineNumberTextEdit."""

    def __init__(self, editor: "LineNumberTextEdit"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor._paint_line_numbers(event)


class LineNumberTextEdit(QTextEdit):
    """QTextEdit subclass with an optional line-number margin on the left."""

    _BG_COLOR    = QColor("#1e293b")
    _FG_COLOR    = QColor("#546e7a")
    _FG_CURRENT  = QColor("#94a3b8")
    _BORDER_COLOR = QColor("#334155")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ln_area = _LineNumberArea(self)
        self._ln_visible = False

        self.document().blockCountChanged.connect(self._update_area_width)
        self.verticalScrollBar().valueChanged.connect(self._update_area)
        self.textChanged.connect(self._update_area)
        self.cursorPositionChanged.connect(self._update_area)

        self._update_area_width(0)

    # ── Public API ────────────────────────────────────────────────────────

    def set_line_numbers_visible(self, visible: bool) -> None:
        self._ln_visible = visible
        self._ln_area.setVisible(visible)
        self._update_area_width(0)

    def is_line_numbers_visible(self) -> bool:
        return self._ln_visible

    # ── Overrides ─────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        w = self._line_number_area_width() if self._ln_visible else 0
        self._ln_area.setGeometry(QRect(cr.left(), cr.top(), w, cr.height()))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _line_number_area_width(self) -> int:
        if not self._ln_visible:
            return 0
        digits = max(1, len(str(max(1, self.document().blockCount()))))
        fm = self.fontMetrics()
        return fm.horizontalAdvance("9") * (digits + 2) + 8

    def _update_area_width(self, _=None) -> None:
        w = self._line_number_area_width() if self._ln_visible else 0
        self.setViewportMargins(w, 0, 0, 0)
        self._ln_area.update()

    def _update_area(self) -> None:
        if self._ln_visible:
            self._ln_area.update()

    def _paint_line_numbers(self, event) -> None:
        painter = QPainter(self._ln_area)
        painter.fillRect(event.rect(), self._BG_COLOR)

        # draw right border
        painter.setPen(self._BORDER_COLOR)
        painter.drawLine(
            self._ln_area.width() - 1, event.rect().top(),
            self._ln_area.width() - 1, event.rect().bottom(),
        )

        # figure out which document blocks are visible
        viewport_offset = self.verticalScrollBar().value()
        page_bottom = viewport_offset + self.viewport().height()

        block = self.document().begin()
        block_number = 1
        current_block = self.textCursor().block()

        fm = self.fontMetrics()

        while block.isValid():
            rect = self.document().documentLayout().blockBoundingRect(block)
            block_top = int(rect.top()) - viewport_offset
            block_bottom = block_top + int(rect.height())

            if block_top > page_bottom:
                break

            if block_bottom >= 0:
                painter.setPen(
                    self._FG_CURRENT if block == current_block else self._FG_COLOR
                )
                painter.drawText(
                    0,
                    block_top,
                    self._ln_area.width() - 6,
                    fm.height(),
                    Qt.AlignRight | Qt.AlignTop,
                    str(block_number),
                )

            block = block.next()
            block_number += 1
