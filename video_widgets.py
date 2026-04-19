from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QGraphicsView, QGraphicsScene, QListWidget, QListWidgetItem,
)


VOLUME_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1e293b, stop:1 #334155);
        height: 8px;
        border-radius: 4px;
        border: 1px solid rgba(100, 116, 139, 0.4);
    }
    QSlider::handle:horizontal {
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
            fx:0.4, fy:0.4,
            stop:0 #60a5fa, stop:0.7 #3b82f6, stop:1 #2563eb);
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
        border: 2px solid #93c5fd;
    }
    QSlider::handle:horizontal:hover {
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
            fx:0.4, fy:0.4,
            stop:0 #93c5fd, stop:0.7 #60a5fa, stop:1 #3b82f6);
        border: 2px solid #bfdbfe;
    }
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2563eb, stop:1 #3b82f6);
        height: 8px;
        border-radius: 4px;
    }
    QSlider::add-page:horizontal {
        background: #1e293b;
        height: 8px;
        border-radius: 4px;
    }
"""


class ClickableVideoWidget(QVideoWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_callback = None
        self.double_click_callback = None
        self.move_callback = None
        self.leave_callback = None
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.click_callback:
            self.click_callback()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if self.double_click_callback:
            self.double_click_callback()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.move_callback:
            self.move_callback(event.pos())

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.leave_callback:
            self.leave_callback()

    def set_click_callback(self, callback):
        self.click_callback = callback

    def set_double_click_callback(self, callback):
        self.double_click_callback = callback


class RotatableVideoView(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_callback = None
        self.double_click_callback = None
        self.setMouseTracking(True)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setStyleSheet("background: black; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._video_item = QGraphicsVideoItem()
        self._scene.addItem(self._video_item)
        self._video_item.nativeSizeChanged.connect(self._on_native_size_changed)

        self._rotation = 0
        self._flip_h = False
        self._flip_v = False

    @property
    def video_item(self):
        return self._video_item

    def video_sink(self):
        return self._video_item.videoSink()

    def rotate_cw(self):
        self._rotation = (self._rotation + 90) % 360
        self._apply_transform()

    def rotate_ccw(self):
        self._rotation = (self._rotation - 90) % 360
        self._apply_transform()

    def rotate_180(self):
        self._rotation = (self._rotation + 180) % 360
        self._apply_transform()

    def flip_horizontal(self):
        self._flip_h = not self._flip_h
        self._apply_transform()

    def flip_vertical(self):
        self._flip_v = not self._flip_v
        self._apply_transform()

    def reset_transform_state(self):
        self._rotation = 0
        self._flip_h = False
        self._flip_v = False
        self._apply_transform()

    def _apply_transform(self):
        t = QTransform()
        sx = -1 if self._flip_h else 1
        sy = -1 if self._flip_v else 1
        t.scale(sx, sy)
        t.rotate(self._rotation)
        self._video_item.setTransform(t)
        self._fit_video()

    def _on_native_size_changed(self, size):
        self._fit_video()

    def _fit_video(self):
        self._video_item.setSize(self._video_item.nativeSize())
        self.fitInView(self._video_item, Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_video()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.click_callback:
            self.click_callback()

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if self.double_click_callback:
            self.double_click_callback()

    def set_click_callback(self, callback):
        self.click_callback = callback

    def set_double_click_callback(self, callback):
        self.double_click_callback = callback


class BookmarkListWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bookmarks = []
        self._jump_callback = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(QLabel("📌 Marcadores"))
        header.addStretch()
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(24, 24)
        self._add_btn.setToolTip("Agregar marcador en la posición actual")
        header.addWidget(self._add_btn)
        self._clear_btn = QPushButton("🗑")
        self._clear_btn.setFixedSize(24, 24)
        self._clear_btn.setToolTip("Eliminar todos los marcadores")
        self._clear_btn.clicked.connect(self._clear_all)
        header.addWidget(self._clear_btn)
        layout.addLayout(header)

        self._list = QListWidget()
        self._list.setMaximumHeight(150)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)

    def set_add_callback(self, callback):
        self._add_btn.clicked.connect(callback)

    def set_jump_callback(self, callback):
        self._jump_callback = callback

    def add_bookmark(self, position_ms, label=None):
        minutes = int(position_ms // 60000)
        seconds = int((position_ms % 60000) // 1000)
        time_str = f"{minutes:02d}:{seconds:02d}"
        display = f"[{time_str}] {label}" if label else f"[{time_str}]"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, position_ms)
        self._list.addItem(item)
        self._bookmarks.append(position_ms)

    def _on_item_double_clicked(self, item):
        position = item.data(Qt.UserRole)
        if self._jump_callback and position is not None:
            self._jump_callback(position)

    def _clear_all(self):
        self._list.clear()
        self._bookmarks.clear()

    def get_bookmarks(self):
        return list(self._bookmarks)


class PiPWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle("PiP - Video")
        self.resize(360, 200)
        self.setMinimumSize(200, 120)

        self._video_widget = QVideoWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._video_widget)

        self._close_callback = None

    @property
    def video_widget(self):
        return self._video_widget

    def set_close_callback(self, callback):
        self._close_callback = callback

    def closeEvent(self, event):
        if self._close_callback:
            self._close_callback()
        super().closeEvent(event)


class VideoAdjustPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._change_callback = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(QLabel("🎨 Ajustes de video"))
        header.addStretch()
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedHeight(22)
        reset_btn.clicked.connect(self._reset)
        header.addWidget(reset_btn)
        layout.addLayout(header)

        self._brightness_slider = self._make_slider("Brillo", -100, 100, 0)
        layout.addLayout(self._brightness_slider[0])

        self._contrast_slider = self._make_slider("Contraste", -100, 100, 0)
        layout.addLayout(self._contrast_slider[0])

        self._saturation_slider = self._make_slider("Saturación", -100, 100, 0)
        layout.addLayout(self._saturation_slider[0])

    def _make_slider(self, name, min_val, max_val, default):
        row = QHBoxLayout()
        label = QLabel(name)
        label.setFixedWidth(70)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        val_label = QLabel(str(default))
        val_label.setFixedWidth(30)
        val_label.setAlignment(Qt.AlignCenter)
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        slider.valueChanged.connect(lambda: self._on_change())
        row.addWidget(label)
        row.addWidget(slider)
        row.addWidget(val_label)
        return (row, slider, val_label)

    def set_change_callback(self, callback):
        self._change_callback = callback

    def _on_change(self):
        if self._change_callback:
            self._change_callback(self.brightness(), self.contrast(), self.saturation())

    def brightness(self):
        return self._brightness_slider[1].value()

    def contrast(self):
        return self._contrast_slider[1].value()

    def saturation(self):
        return self._saturation_slider[1].value()

    def _reset(self):
        self._brightness_slider[1].setValue(0)
        self._contrast_slider[1].setValue(0)
        self._saturation_slider[1].setValue(0)
