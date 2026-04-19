from typing import Tuple
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QLabel


class PanLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._last_pos = QPoint()
        self._offset_x = 0
        self._offset_y = 0
        self._max_offset_x = 0
        self._max_offset_y = 0
        self._image_viewer = None
        self._crop_mode = False
        self._selecting = False
        self._has_selection = False
        self._sel_start = QPoint()
        self._sel_end = QPoint()
        self.setCursor(Qt.OpenHandCursor)

    def set_pan_limits(self, max_offset_x: int, max_offset_y: int):
        self._max_offset_x = max(0, max_offset_x)
        self._max_offset_y = max(0, max_offset_y)
        self._clamp_offset()

    def _clamp_offset(self):
        self._offset_x = max(-self._max_offset_x, min(self._max_offset_x, self._offset_x))
        self._offset_y = max(-self._max_offset_y, min(self._max_offset_y, self._offset_y))

    def reset_pan(self):
        self._offset_x = 0
        self._offset_y = 0
        self._dragging = False

    def get_offset(self) -> Tuple[int, int]:
        return (self._offset_x, self._offset_y)

    def set_offset(self, x: int, y: int):
        self._offset_x = x
        self._offset_y = y
        self._clamp_offset()

    def pan(self, dx: int, dy: int):
        self._offset_x += dx
        self._offset_y += dy
        self._clamp_offset()

    def clear_selection(self):
        self._has_selection = False
        self._selecting = False
        self._sel_start = QPoint()
        self._sel_end = QPoint()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._crop_mode:
                self._selecting = True
                self._has_selection = False
                self._sel_start = event.pos()
                self._sel_end = event.pos()
                self.update()
                return
            self._dragging = True
            self._last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._crop_mode and self._selecting:
                self._selecting = False
                self._sel_end = event.pos()
                sel = QRect(self._sel_start, self._sel_end).normalized()
                if sel.width() >= 5 and sel.height() >= 5:
                    self._has_selection = True
                    self.update()
                    if self._image_viewer:
                        self._image_viewer._on_crop_selection_complete()
                else:
                    self._has_selection = False
                    self.update()
                return
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._crop_mode and self._selecting:
            self._sel_end = event.pos()
            self.update()
            return
        if self._dragging:
            delta = event.pos() - self._last_pos
            self.pan(delta.x(), delta.y())
            self._last_pos = event.pos()
            if self._image_viewer:
                self._image_viewer.update_pixmap_position()
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._crop_mode:
            return
        if not (self._selecting or self._has_selection):
            return
        sel = QRect(self._sel_start, self._sel_end).normalized()
        if sel.width() < 2 or sel.height() < 2:
            return
        painter = QPainter(self)
        dark = QColor(0, 0, 0, 120)
        full = self.rect()
        painter.fillRect(full.x(), full.y(), full.width(), sel.y() - full.y(), dark)
        painter.fillRect(full.x(), sel.bottom() + 1, full.width(), full.bottom() - sel.bottom(), dark)
        painter.fillRect(full.x(), sel.y(), sel.x() - full.x(), sel.height() + 1, dark)
        painter.fillRect(sel.right() + 1, sel.y(), full.right() - sel.right(), sel.height() + 1, dark)
        pen = QPen(QColor(59, 130, 246), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(sel)
        painter.end()
