import os
import subprocess
import threading
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QEvent, QObject, QTimer, QSize, QRect
from PySide6.QtGui import QColor, QImage, QPixmap, QPainter, QTransform
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QSizePolicy, QMessageBox, QComboBox, QDialog,
    QDialogButtonBox, QApplication, QMenu, QSplitter, QFileDialog,
    QGraphicsView, QGraphicsScene,
    QGraphicsColorizeEffect, QInputDialog, QListWidget,
    QListWidgetItem, QAbstractItemView, QScrollArea
)

from video_converter import (
    VideoConverterDialog, VideoBatchConverterDialog, VideoTrimDialog,
    VIDEO_EXTENSIONS, convert_video, is_ffmpeg_available,
    FORMAT_NAMES as VIDEO_FORMAT_NAMES
)
from audio_converter import (
    AUDIO_EXTENSIONS, convert_audio,
    FORMAT_NAMES as AUDIO_FORMAT_NAMES
)
from video_playlist import VideoPlaylistWidget
from progress_bar import ConversionProgressBar

PIP_SYNC_INTERVAL_MS = 1000
PIP_SYNC_THRESHOLD_MS = 2000
MIN_OPACITY = 0.2
MAX_OPACITY = 2.0
BRIGHTNESS_SCALE = 200.0


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


class VideoViewer(QWidget):

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.video_view = RotatableVideoView()
        self.player.setVideoOutput(self.video_view.video_item)

        self.video_widget = self.video_view

        self._frame_sink = QVideoSink(self)
        self._last_frame = None
        self._frame_sink.videoFrameChanged.connect(self._on_frame_received)

        self.is_seeking = False
        self.is_fullscreen = False
        self.current_path = None
        self._progress_bar = None
        self._fs_window = None
        self._pip_window = None
        self._pip_active = False

        self._brightness = 0
        self._contrast = 0
        self._saturation = 0

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(36, 28)
        self.play_button.setStyleSheet("font-size: 18px;")
        self.play_button.clicked.connect(self.player.play)

        self.pause_button = QPushButton("⏸")
        self.pause_button.setFixedSize(36, 28)
        self.pause_button.setStyleSheet("font-size: 18px;")
        self.pause_button.clicked.connect(self.player.pause)

        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(36, 28)
        self.stop_button.setStyleSheet("font-size: 18px;")
        self.stop_button.clicked.connect(self._stop_playback)

        vol_label = QLabel("🔊")
        vol_label.setFixedWidth(20)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setStyleSheet(VOLUME_SLIDER_STYLE)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.audio_output.setVolume(0.5)

        self._speed_button = QToolButton()
        self._speed_button.setText("1x")
        self._speed_button.setToolTip("Velocidad de reproducción")
        self._speed_button.setPopupMode(QToolButton.InstantPopup)
        speed_menu = QMenu(self)
        for speed in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]:
            label = f"{speed}x"
            action = speed_menu.addAction(label)
            action.setData(speed)
            action.triggered.connect(lambda checked, s=speed, l=label: self._set_speed(s, l))
        self._speed_button.setMenu(speed_menu)

        self.playlist_toggle_button = QPushButton("📃")
        self.playlist_toggle_button.setFixedSize(36, 28)
        self.playlist_toggle_button.setStyleSheet("font-size: 16px;")
        self.playlist_toggle_button.setToolTip("Mostrar/ocultar lista de reproducción")
        self.playlist_toggle_button.setCheckable(True)
        self.playlist_toggle_button.setChecked(True)
        self.playlist_toggle_button.clicked.connect(self._toggle_playlist_visibility)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_value_changed)

        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setFixedWidth(100)
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet("font-size: 11px; color: #94a3b8;")

        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)

        self._tools_button = QToolButton()
        self._tools_button.setText("Herramientas ▼")
        self._tools_button.setPopupMode(QToolButton.InstantPopup)
        tools_menu = QMenu(self)
        tools_menu.addAction("📷 Captura de pantalla", self._take_screenshot)
        tools_menu.addAction("🎵 Extraer audio", self._extract_audio)
        tools_menu.addSeparator()
        tools_menu.addAction("📌 Agregar marcador", self._add_bookmark)
        self._bookmarks_toggle_action = tools_menu.addAction(
            "📌 Mostrar marcadores", self._toggle_bookmarks
        )
        tools_menu.addSeparator()
        self._pip_action = tools_menu.addAction("🪟 Picture-in-Picture", self._toggle_pip)
        tools_menu.addSeparator()
        self._adjust_toggle_action = tools_menu.addAction(
            "🎨 Ajustes de imagen", self._toggle_adjustments
        )
        tools_menu.addSeparator()

        rotate_submenu = tools_menu.addMenu("🔄 Rotación / Volteo")
        rotate_submenu.addAction("Rotar 90° →", self.video_view.rotate_cw)
        rotate_submenu.addAction("Rotar 90° ←", self.video_view.rotate_ccw)
        rotate_submenu.addAction("Rotar 180°", self.video_view.rotate_180)
        rotate_submenu.addSeparator()
        rotate_submenu.addAction("Espejo horizontal ↔", self.video_view.flip_horizontal)
        rotate_submenu.addAction("Espejo vertical ↕", self.video_view.flip_vertical)
        rotate_submenu.addSeparator()
        rotate_submenu.addAction("Restablecer", self.video_view.reset_transform_state)

        self._tools_button.setMenu(tools_menu)

        self.edition_button = QToolButton()
        self.edition_button.setText("Edición ▼")
        self.edition_button.setPopupMode(QToolButton.InstantPopup)
        edition_menu = QMenu(self)
        edition_menu.addAction("Convertir", self._show_converter)
        edition_menu.addAction("Convertir playlist", self._convert_playlist)
        edition_menu.addAction("Recortar", self._show_trimmer)
        self.edition_button.setMenu(edition_menu)

        seek_row = QHBoxLayout()
        seek_row.setContentsMargins(0, 0, 0, 0)
        seek_row.addWidget(self.position_slider)
        seek_row.addWidget(self._time_label)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)
        controls.addWidget(self.play_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        controls.addSpacing(8)
        controls.addWidget(vol_label)
        controls.addWidget(self.volume_slider)
        controls.addSpacing(4)
        controls.addWidget(self._speed_button)
        controls.addStretch(1)
        controls.addWidget(self.playlist_toggle_button)
        controls.addWidget(self.fullscreen_button)
        controls.addWidget(self._tools_button)
        controls.addWidget(self.edition_button)

        self._bookmarks_widget = BookmarkListWidget()
        self._bookmarks_widget.set_add_callback(self._add_bookmark)
        self._bookmarks_widget.set_jump_callback(self._jump_to_bookmark)
        self._bookmarks_widget.setVisible(False)

        self._adjust_panel = VideoAdjustPanel()
        self._adjust_panel.set_change_callback(self._on_adjust_changed)
        self._adjust_panel.setVisible(False)

        self._side_panel = QWidget()
        side_layout = QVBoxLayout(self._side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(4)
        side_layout.addWidget(self._adjust_panel)
        side_layout.addWidget(self._bookmarks_widget)
        side_layout.addStretch()
        self._side_panel.setFixedWidth(260)
        self._side_panel.setVisible(False)

        video_area = QHBoxLayout()
        video_area.setContentsMargins(0, 0, 0, 0)
        video_area.setSpacing(0)
        video_area.addWidget(self.video_view, 1)
        video_area.addWidget(self._side_panel)

        self._top_widget = QWidget()
        self._top_layout = QVBoxLayout(self._top_widget)
        self._top_layout.setContentsMargins(0, 0, 0, 0)
        self._top_layout.setSpacing(4)
        self._top_layout.addLayout(video_area, 1)
        self._top_layout.addLayout(seek_row)
        self._top_layout.addLayout(controls)

        self.playlist_widget = VideoPlaylistWidget()
        self.playlist_widget.file_selected.connect(self.load_file)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self._top_widget)
        self.splitter.addWidget(self.playlist_widget)
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([500, 80])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.splitter)

    def _connect_signals(self):
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.video_view.set_click_callback(self._on_video_clicked)
        self.video_view.set_double_click_callback(self._toggle_fullscreen)


    def _update_side_panel_visibility(self):
        visible = self._bookmarks_widget.isVisible() or self._adjust_panel.isVisible()
        self._side_panel.setVisible(visible)

    def _toggle_bookmarks(self):
        vis = not self._bookmarks_widget.isVisible()
        self._bookmarks_widget.setVisible(vis)
        self._bookmarks_toggle_action.setText(
            "📌 Ocultar marcadores" if vis else "📌 Mostrar marcadores"
        )
        self._update_side_panel_visibility()

    def _toggle_adjustments(self):
        vis = not self._adjust_panel.isVisible()
        self._adjust_panel.setVisible(vis)
        self._adjust_toggle_action.setText(
            "🎨 Ocultar ajustes" if vis else "🎨 Ajustes de imagen"
        )
        self._update_side_panel_visibility()


    def _toggle_playlist_visibility(self):
        visible = self.playlist_toggle_button.isChecked()
        self.playlist_widget.setVisible(visible)
        self.playlist_toggle_button.setToolTip(
            "Ocultar lista de reproducción" if visible else "Mostrar lista de reproducción"
        )


    def load_file(self, path: str):
        self.current_path = path
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))

        sink = self.video_view.video_sink()
        if sink:
            try:
                sink.videoFrameChanged.disconnect(self._on_frame_received)
            except RuntimeError:
                pass
            sink.videoFrameChanged.connect(self._on_frame_received)

        self.player.play()

    def stop(self):
        self.player.stop()

    def _stop_playback(self):
        self.player.stop()
        self.position_slider.setValue(0)

    def _on_video_clicked(self):
        self.video_view.setFocus()


    @staticmethod
    def _format_time(ms):
        s = max(0, ms // 1000)
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}"

    def _on_position_changed(self, position):
        if not self.is_seeking:
            self.position_slider.setValue(position)
        dur = self.player.duration()
        self._time_label.setText(
            f"{self._format_time(position)} / {self._format_time(dur)}"
        )

    def _on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def _on_slider_pressed(self):
        self.is_seeking = True

    def _on_slider_released(self):
        self.is_seeking = False
        self.player.setPosition(self.position_slider.value())

    def _on_slider_value_changed(self, value):
        if self.is_seeking:
            self.player.setPosition(value)

    def _on_volume_changed(self, value):
        volume = value / 100.0
        self.audio_output.setVolume(volume)


    def _set_speed(self, speed, label):
        self.player.setPlaybackRate(speed)
        self._speed_button.setText(label)


    def _on_frame_received(self, frame: QVideoFrame):
        self._last_frame = frame

    def _take_screenshot(self):
        if not self.current_path:
            QMessageBox.information(self, "Sin video", "No hay video cargado.")
            return

        image = None

        if self._last_frame and self._last_frame.isValid():
            image = self._last_frame.toImage()

        if image is None or image.isNull():
            pixmap = self.video_view.grab()
            if not pixmap.isNull():
                image = pixmap.toImage()

        if image is None or image.isNull():
            QMessageBox.warning(self, "Error", "No se pudo capturar el fotograma actual.")
            return

        base_name = Path(self.current_path).stem
        pos_sec = self.player.position() // 1000
        default_name = f"{base_name}_frame_{pos_sec}s.png"

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar captura de pantalla",
            os.path.join(os.path.dirname(self.current_path), default_name),
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
        )
        if save_path:
            image.save(save_path)
            QMessageBox.information(self, "Captura guardada",
                                    f"Fotograma guardado en:\n{save_path}")


    def _extract_audio(self):
        if not self.current_path:
            QMessageBox.information(self, "Sin video", "No hay video cargado.")
            return

        if not is_ffmpeg_available():
            QMessageBox.critical(self, "Error",
                                 "ffmpeg no está instalado.\n\nPor favor instala ffmpeg.")
            return

        base_name = Path(self.current_path).stem
        default_name = f"{base_name}_audio.mp3"

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar audio extraído",
            os.path.join(os.path.dirname(self.current_path), default_name),
            "MP3 (*.mp3);;WAV (*.wav);;AAC (*.aac);;OGG (*.ogg)"
        )
        if not save_path:
            return

        ext = Path(save_path).suffix.lower()
        codec_map = {
            ".mp3": ["libmp3lame", "-q:a", "2"],
            ".wav": ["pcm_s16le"],
            ".aac": ["aac", "-b:a", "192k"],
            ".ogg": ["libvorbis", "-q:a", "5"],
        }
        codec_args = codec_map.get(ext, ["copy"])

        cmd = [
            "ffmpeg", "-y", "-i", self.current_path,
            "-vn", "-c:a", codec_args[0]
        ]
        if len(codec_args) > 1:
            cmd.extend(codec_args[1:])
        cmd.append(save_path)

        self._extract_audio_cmd(cmd, save_path)

    def _extract_audio_cmd(self, cmd, save_path):
        progress = QMessageBox(self)
        progress.setWindowTitle("Extrayendo audio...")
        progress.setText("Extrayendo audio del video, por favor espere...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        QApplication.processEvents()

        def _run():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                success = result.returncode == 0 and os.path.exists(save_path)
            except (subprocess.TimeoutExpired, Exception):
                success = False
            QTimer.singleShot(0, lambda: self._on_extract_done(success, save_path, progress))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _on_extract_done(self, success, save_path, progress_dialog):
        progress_dialog.close()
        if success:
            QMessageBox.information(self, "Audio extraído",
                                    f"Audio guardado en:\n{save_path}")
        else:
            QMessageBox.warning(self, "Error",
                                "No se pudo extraer el audio del video.")


    def _add_bookmark(self):
        if not self.current_path:
            return
        position = self.player.position()
        label, ok = QInputDialog.getText(
            self, "Nuevo marcador", "Nombre del marcador (opcional):"
        )
        if ok:
            self._bookmarks_widget.add_bookmark(position, label if label else None)
            if not self._bookmarks_widget.isVisible():
                self._toggle_bookmarks()

    def _jump_to_bookmark(self, position_ms):
        self.player.setPosition(position_ms)


    def _toggle_pip(self):
        if self._pip_active:
            self._exit_pip()
        else:
            self._enter_pip()

    def _enter_pip(self):
        if not self.current_path or self._pip_active:
            return

        self._pip_window = PiPWindow(self)
        self._pip_window.set_close_callback(self._exit_pip)

        self._pip_player = QMediaPlayer(self._pip_window)
        self._pip_audio = QAudioOutput(self._pip_window)
        PIP_MUTED_VOLUME = 0
        self._pip_audio.setVolume(PIP_MUTED_VOLUME)
        self._pip_player.setAudioOutput(self._pip_audio)
        self._pip_player.setVideoOutput(self._pip_window.video_widget)
        self._pip_player.setSource(QUrl.fromLocalFile(self.current_path))

        pos = self.player.position()
        self._pip_player.setPosition(pos)
        self._pip_player.play()

        self._pip_window.show()
        self._pip_active = True
        self._pip_action.setText("🪟 Cerrar Picture-in-Picture")

        self._pip_sync_timer = QTimer(self)
        self._pip_sync_timer.setInterval(PIP_SYNC_INTERVAL_MS)
        self._pip_sync_timer.timeout.connect(self._sync_pip_position)
        self._pip_sync_timer.start()

    def _sync_pip_position(self):
        if not self._pip_active or not hasattr(self, '_pip_player'):
            return
        main_pos = self.player.position()
        pip_pos = self._pip_player.position()
        if abs(main_pos - pip_pos) > PIP_SYNC_THRESHOLD_MS:
            self._pip_player.setPosition(main_pos)

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            if self._pip_player.playbackState() != QMediaPlayer.PlayingState:
                self._pip_player.play()
        else:
            if self._pip_player.playbackState() == QMediaPlayer.PlayingState:
                self._pip_player.pause()

    def _exit_pip(self):
        if hasattr(self, '_pip_sync_timer'):
            self._pip_sync_timer.stop()
        if hasattr(self, '_pip_player'):
            self._pip_player.stop()
        if self._pip_window:
            self._pip_window.close()
            self._pip_window = None
        self._pip_active = False
        self._pip_action.setText("🪟 Picture-in-Picture")


    def _on_adjust_changed(self, brightness, contrast, saturation):
        self._brightness = brightness
        self._contrast = contrast
        self._saturation = saturation

        style = "background: black; border: none;"
        self.video_view.setStyleSheet(style)

        item = self.video_view.video_item
        if brightness != 0 or contrast != 0 or saturation != 0:
            effect = QGraphicsColorizeEffect()
            if saturation < 0:
                effect.setStrength(abs(saturation) / 100.0)
                effect.setColor(QColor(128, 128, 128))
            elif saturation > 0:
                effect.setStrength(saturation / 200.0)
                effect.setColor(QColor(255, 200, 150))
            else:
                effect.setStrength(0)

            contrast_shift = contrast / 300.0
            item.setGraphicsEffect(effect)

            opacity = max(MIN_OPACITY, min(MAX_OPACITY,
                          1.0 + brightness / BRIGHTNESS_SCALE + contrast_shift))
            item.setOpacity(opacity)
        else:
            item.setGraphicsEffect(None)
            item.setOpacity(1.0)


    def _toggle_fullscreen(self):
        if not self.is_fullscreen:
            self._enter_fullscreen()
        else:
            self._exit_fullscreen()

    def _enter_fullscreen(self):
        self._fs_window = QWidget()
        self._fs_window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self._fs_window.setAttribute(Qt.WA_DeleteOnClose, False)
        self._fs_window.setStyleSheet("background: black;")

        fs_layout = QVBoxLayout(self._fs_window)
        fs_layout.setContentsMargins(0, 0, 0, 0)
        fs_layout.setSpacing(0)

        self.video_view.setParent(self._fs_window)
        fs_layout.addWidget(self.video_view)
        self.video_view.show()

        self._fs_window.installEventFilter(self._FullscreenFilter(self))
        self._fs_window.showFullScreen()
        self.is_fullscreen = True

    def _exit_fullscreen(self):
        if not self._fs_window:
            return

        self.video_view.setParent(self._top_widget)
        video_area_layout = self._top_layout.itemAt(0).layout()
        if video_area_layout:
            video_area_layout.insertWidget(0, self.video_view, 1)
        self.video_view.show()

        self._fs_window.close()
        self._fs_window.deleteLater()
        self._fs_window = None
        self.is_fullscreen = False

    class _FullscreenFilter(QObject):
        def __init__(self, viewer):
            super().__init__(viewer)
            self._viewer = viewer

        def eventFilter(self, obj, event):
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self._viewer._exit_fullscreen()
                    return True
            return False

    def exit_fullscreen(self):
        if self.is_fullscreen:
            self._exit_fullscreen()


    def _show_converter(self):
        if not self.current_path:
            return
        dialog = VideoConverterDialog(self.current_path, self)
        dialog.exec()

    def _convert_playlist(self):
        playlist = self.playlist_widget.get_playlist()
        if not playlist:
            QMessageBox.information(self, "Playlist vacía",
                                    "No hay archivos en la lista de reproducción.")
            return

        if not is_ffmpeg_available():
            QMessageBox.critical(self, "Error",
                                 "ffmpeg no está instalado.\n\nPor favor instala ffmpeg.")
            return

        audio_files = [f for f in playlist if Path(f).suffix.lower() in AUDIO_EXTENSIONS]
        video_files = [f for f in playlist if Path(f).suffix.lower() in VIDEO_EXTENSIONS]

        video_format = None
        audio_format = None

        if video_files:
            video_format = self._ask_format("video", VIDEO_FORMAT_NAMES, VIDEO_EXTENSIONS)
            if not video_format:
                return

        if audio_files:
            audio_format = self._ask_format("audio", AUDIO_FORMAT_NAMES, AUDIO_EXTENSIONS)
            if not audio_format:
                return

        if not video_format and not audio_format:
            QMessageBox.information(self, "Sin archivos",
                                    "No se encontraron archivos compatibles en la playlist.")
            return

        if not self._progress_bar:
            self._progress_bar = ConversionProgressBar()

        total = len(video_files) + len(audio_files)
        errors = []
        idx = 0

        for file_path in video_files:
            filename = os.path.basename(file_path)
            self._progress_bar.start(filename)

            ext = Path(file_path).suffix.lower()
            if ext != video_format:
                out_dir = os.path.dirname(file_path)
                out_name = os.path.splitext(os.path.basename(file_path))[0]
                out_path = os.path.join(out_dir, f"{out_name}_converted{video_format}")
                try:
                    success = convert_video(file_path, out_path, video_format)
                    if not success:
                        errors.append(filename)
                except Exception:
                    errors.append(filename)

            idx += 1
            self._progress_bar.update_progress(int((idx / total) * 100), filename)

        for file_path in audio_files:
            filename = os.path.basename(file_path)
            self._progress_bar.start(filename)

            ext = Path(file_path).suffix.lower()
            if ext != audio_format:
                out_dir = os.path.dirname(file_path)
                out_name = os.path.splitext(os.path.basename(file_path))[0]
                out_path = os.path.join(out_dir, f"{out_name}_converted{audio_format}")
                try:
                    success = convert_audio(file_path, out_path, audio_format)
                    if not success:
                        errors.append(filename)
                except Exception:
                    errors.append(filename)

            idx += 1
            self._progress_bar.update_progress(int((idx / total) * 100), filename)

        self._progress_bar.finish()

        if errors:
            QMessageBox.warning(self, "Conversión parcial",
                                f"Errores en: {', '.join(errors)}")
        else:
            QMessageBox.information(self, "Éxito",
                                    f"Se convirtieron {total} archivos correctamente.")

    def _ask_format(self, category, format_names, extensions):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Formato de {category}")
        dialog.setMinimumWidth(320)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Seleccionar formato de {category}:"))
        combo = QComboBox()
        for ext in sorted(extensions):
            combo.addItem(format_names.get(ext, ext), ext)
        layout.addWidget(combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            return combo.currentData()
        return None

    def _show_trimmer(self):
        if not self.current_path:
            return
        dialog = VideoTrimDialog(self.current_path, self)
        dialog.exec()
