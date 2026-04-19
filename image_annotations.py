import math
from PySide6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QImage, QPixmap, QPainterPath, QPolygonF,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QColorDialog,
    QInputDialog, QFrame, QComboBox, QLabel,
)

TOOL_ARROW = "arrow"
TOOL_RECT = "rect"
TOOL_CIRCLE = "circle"
TOOL_TEXT = "text"
TOOL_FREEHAND = "freehand"

_TOOLBAR_BTN_STYLE = """
    QToolButton {
        background: rgba(30,41,59,0.85);
        border: 1px solid rgba(148,163,184,0.3);
        border-radius: 4px;
        color: #e5e7eb;
        font-size: 14px;
    }
    QToolButton:hover {
        background: rgba(59,130,246,0.3);
    }
    QToolButton:checked {
        background: rgba(59,130,246,0.5);
        border-color: #60a5fa;
    }
"""

_TOOLBAR_FRAME_STYLE = """
    QFrame {
        background: rgba(15,23,42,0.80);
        border: 1px solid rgba(148,163,184,0.25);
        border-radius: 8px;
    }
"""

_COMBO_STYLE = """
    QComboBox {
        background: rgba(30,41,59,0.85);
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.3);
        border-radius: 4px;
        padding: 2px 6px;
        min-width: 44px;
        font-size: 12px;
    }
    QComboBox::drop-down {
        border-left: 1px solid rgba(148,163,184,0.3);
        background: rgba(255,255,255,0.08);
    }
    QComboBox QAbstractItemView {
        background: #1e293b;
        color: #e5e7eb;
        selection-background-color: rgba(59,130,246,0.4);
    }
"""


def _make_tool_button(text: str, tooltip: str, checkable: bool = True) -> QToolButton:
    btn = QToolButton()
    btn.setText(text)
    btn.setToolTip(tooltip)
    btn.setCheckable(checkable)
    btn.setFixedSize(32, 32)
    btn.setStyleSheet(_TOOLBAR_BTN_STYLE)
    return btn


def _draw_arrowhead(painter: QPainter, start: QPointF, end: QPointF, size: float = 12.0):
    dx = end.x() - start.x()
    dy = end.y() - start.y()
    length = math.hypot(dx, dy)
    if length < 1e-3:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux

    p1 = QPointF(end.x() - ux * size + px * size * 0.4,
                 end.y() - uy * size + py * size * 0.4)
    p2 = QPointF(end.x() - ux * size - px * size * 0.4,
                 end.y() - uy * size - py * size * 0.4)

    head = QPolygonF([end, p1, p2])
    painter.save()
    painter.setBrush(painter.pen().color())
    painter.drawPolygon(head)
    painter.restore()


class AnnotationOverlay(QWidget):

    annotations_saved = Signal(QImage)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

        self._annotations: list[dict] = []
        self._current_tool: str = TOOL_ARROW
        self._current_color: QColor = QColor("#ef4444")
        self._current_width: int = 2
        self._drawing = False
        self._start_point: QPoint = QPoint()
        self._end_point: QPoint = QPoint()
        self._freehand_points: list[QPoint] = []

        self._base_image: QImage | None = None

        self._build_toolbar()


    def _build_toolbar(self):
        self._toolbar = QFrame(self)
        self._toolbar.setStyleSheet(_TOOLBAR_FRAME_STYLE)

        layout = QHBoxLayout(self._toolbar)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        self._btn_arrow = _make_tool_button("➤", "Flecha")
        self._btn_rect = _make_tool_button("▢", "Rectángulo")
        self._btn_circle = _make_tool_button("◯", "Círculo / Elipse")
        self._btn_text = _make_tool_button("T", "Texto")
        self._btn_freehand = _make_tool_button("✎", "Dibujo libre")

        self._tool_buttons = {
            TOOL_ARROW: self._btn_arrow,
            TOOL_RECT: self._btn_rect,
            TOOL_CIRCLE: self._btn_circle,
            TOOL_TEXT: self._btn_text,
            TOOL_FREEHAND: self._btn_freehand,
        }

        self._btn_arrow.setChecked(True)
        for tool_name, btn in self._tool_buttons.items():
            btn.clicked.connect(lambda checked, t=tool_name: self._select_tool(t))
            layout.addWidget(btn)

        sep1 = QFrame()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet("background: rgba(148,163,184,0.3);")
        layout.addWidget(sep1)

        self._btn_color = QToolButton()
        self._btn_color.setToolTip("Color")
        self._btn_color.setFixedSize(32, 32)
        self._btn_color.setStyleSheet(_TOOLBAR_BTN_STYLE)
        self._update_color_icon()
        self._btn_color.clicked.connect(self._pick_color)
        layout.addWidget(self._btn_color)

        self._width_combo = QComboBox()
        self._width_combo.setToolTip("Grosor de línea")
        self._width_combo.setStyleSheet(_COMBO_STYLE)
        self._width_combo.setFixedHeight(32)
        for w in range(1, 6):
            self._width_combo.addItem(f"{w} px", w)
        self._width_combo.setCurrentIndex(1)
        self._width_combo.currentIndexChanged.connect(self._width_changed)
        layout.addWidget(self._width_combo)

        sep2 = QFrame()
        sep2.setFixedWidth(1)
        sep2.setStyleSheet("background: rgba(148,163,184,0.3);")
        layout.addWidget(sep2)

        self._btn_clear = _make_tool_button("🗑️", "Borrar todo", checkable=False)
        self._btn_clear.clicked.connect(self.clear)
        layout.addWidget(self._btn_clear)

        self._btn_save = _make_tool_button("💾", "Guardar anotaciones en imagen", checkable=False)
        self._btn_save.clicked.connect(self._on_save)
        layout.addWidget(self._btn_save)

        self._toolbar.adjustSize()

    def _reposition_toolbar(self):
        tw = self._toolbar.sizeHint().width()
        x = max(0, (self.width() - tw) // 2)
        self._toolbar.move(x, 6)
        self._toolbar.raise_()


    def set_base_image(self, image: QImage):
        self._base_image = image

    def clear(self):
        self._annotations.clear()
        self.update()

    def burn_to_image(self, base_image: QImage) -> QImage:
        result = base_image.copy()
        if not self._annotations:
            return result

        sx = result.width() / self.width() if self.width() else 1.0
        sy = result.height() / self.height() if self.height() else 1.0

        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.scale(sx, sy)
        self._paint_annotations(painter)
        painter.end()
        return result


    def _select_tool(self, tool: str):
        self._current_tool = tool
        for name, btn in self._tool_buttons.items():
            btn.setChecked(name == tool)

    def _pick_color(self):
        color = QColorDialog.getColor(
            self._current_color, self, "Elegir color de anotación"
        )
        if color.isValid():
            self._current_color = color
            self._update_color_icon()

    def _update_color_icon(self):
        pm = QPixmap(20, 20)
        pm.fill(self._current_color)
        self._btn_color.setIcon(pm)

    def _width_changed(self, index: int):
        self._current_width = self._width_combo.currentData() or 2

    def _on_save(self):
        if self._base_image is not None:
            result = self.burn_to_image(self._base_image)
            self.annotations_saved.emit(result)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._paint_annotations(painter)
        self._paint_in_progress(painter)
        painter.end()

    def _make_pen(self, color: QColor, width: int) -> QPen:
        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen

    def _paint_annotations(self, painter: QPainter):
        for ann in self._annotations:
            pen = self._make_pen(ann["color"], ann["width"])
            painter.setPen(pen)

            atype = ann["type"]
            pts = ann["points"]

            if atype == TOOL_ARROW and len(pts) == 2:
                painter.drawLine(pts[0], pts[1])
                _draw_arrowhead(painter, QPointF(pts[0]), QPointF(pts[1]),
                                size=max(10.0, ann["width"] * 4.0))

            elif atype == TOOL_RECT and len(pts) == 2:
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(QRect(pts[0], pts[1]).normalized())

            elif atype == TOOL_CIRCLE and len(pts) == 2:
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRect(pts[0], pts[1]).normalized())

            elif atype == TOOL_TEXT:
                font = QFont("Segoe UI", max(12, ann["width"] * 5))
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(pts[0], ann.get("text", ""))

            elif atype == TOOL_FREEHAND and len(pts) >= 2:
                path = QPainterPath(QPointF(pts[0]))
                for p in pts[1:]:
                    path.lineTo(QPointF(p))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

    def _paint_in_progress(self, painter: QPainter):
        if not self._drawing:
            return

        pen = self._make_pen(self._current_color, self._current_width)
        painter.setPen(pen)

        if self._current_tool == TOOL_ARROW:
            painter.drawLine(self._start_point, self._end_point)
            _draw_arrowhead(painter, QPointF(self._start_point),
                            QPointF(self._end_point),
                            size=max(10.0, self._current_width * 4.0))

        elif self._current_tool == TOOL_RECT:
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRect(self._start_point, self._end_point).normalized())

        elif self._current_tool == TOOL_CIRCLE:
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRect(self._start_point, self._end_point).normalized())

        elif self._current_tool == TOOL_FREEHAND and len(self._freehand_points) >= 2:
            path = QPainterPath(QPointF(self._freehand_points[0]))
            for p in self._freehand_points[1:]:
                path.lineTo(QPointF(p))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)


    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        pos = event.pos()

        if self._current_tool == TOOL_TEXT:
            text, ok = QInputDialog.getText(
                self, "Anotación de texto", "Escriba el texto:"
            )
            if ok and text:
                self._annotations.append({
                    "type": TOOL_TEXT,
                    "points": [pos],
                    "color": QColor(self._current_color),
                    "width": self._current_width,
                    "text": text,
                })
                self.update()
            return

        self._drawing = True
        self._start_point = pos
        self._end_point = pos

        if self._current_tool == TOOL_FREEHAND:
            self._freehand_points = [pos]

    def mouseMoveEvent(self, event):
        if not self._drawing:
            return
        self._end_point = event.pos()
        if self._current_tool == TOOL_FREEHAND:
            self._freehand_points.append(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self._drawing:
            return
        self._drawing = False
        self._end_point = event.pos()

        if self._current_tool == TOOL_FREEHAND:
            if len(self._freehand_points) >= 2:
                self._annotations.append({
                    "type": TOOL_FREEHAND,
                    "points": list(self._freehand_points),
                    "color": QColor(self._current_color),
                    "width": self._current_width,
                    "text": "",
                })
            self._freehand_points.clear()
        else:
            self._annotations.append({
                "type": self._current_tool,
                "points": [self._start_point, self._end_point],
                "color": QColor(self._current_color),
                "width": self._current_width,
                "text": "",
            })

        self.update()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_toolbar()

    def showEvent(self, event):
        super().showEvent(event)
        self._toolbar.adjustSize()
        self._reposition_toolbar()
