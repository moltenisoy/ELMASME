import os
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QSizePolicy, QMessageBox, QComboBox, QDialog,
    QDialogButtonBox, QApplication, QMenu
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


class VideoViewer(QWidget):

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = ClickableVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        self.is_seeking = False
        self.is_fullscreen = False
        self.navigation_enabled = False
        self.current_path = None
        self._progress_bar = None
        self._overlay_pinned = False

        self._build_ui()
        self._setup_timers()
        self._connect_signals()

    def _build_ui(self):
        self.overlay = QWidget(self)
        self.overlay.setStyleSheet(
            "background: rgba(0,0,0,0.7); border-radius: 8px;"
        )
        self.overlay.hide()

        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(8, 4, 8, 4)
        overlay_layout.setSpacing(6)

        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(32, 22)
        self.play_button.clicked.connect(self.player.play)

        self.pause_button = QPushButton("⏸")
        self.pause_button.setFixedSize(32, 22)
        self.pause_button.clicked.connect(self.player.pause)

        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(32, 22)
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

        self.pin_button = QPushButton("📌")
        self.pin_button.setFixedSize(26, 22)
        self.pin_button.setCheckable(True)
        self.pin_button.clicked.connect(self._toggle_pin)

        overlay_layout.addWidget(self.play_button)
        overlay_layout.addWidget(self.pause_button)
        overlay_layout.addWidget(self.stop_button)
        overlay_layout.addWidget(vol_label)
        overlay_layout.addWidget(self.volume_slider)
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.pin_button)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_value_changed)

        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)

        self.edition_button = QToolButton()
        self.edition_button.setText("Edición ▼")
        self.edition_button.setPopupMode(QToolButton.InstantPopup)
        edition_menu = QMenu(self)
        edition_menu.addAction("Convertir", self._show_converter)
        edition_menu.addAction("Convertir playlist", self._convert_playlist)
        edition_menu.addAction("Recortar", self._show_trimmer)
        self.edition_button.setMenu(edition_menu)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)
        controls.addStretch(1)
        controls.addWidget(self.fullscreen_button)
        controls.addWidget(self.edition_button)
        controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.video_widget, 1)
        layout.addWidget(self.position_slider)
        layout.addLayout(controls)

        self.playlist_widget = VideoPlaylistWidget()
        self.playlist_widget.file_selected.connect(self.load_file)
        layout.addWidget(self.playlist_widget)

    def _setup_timers(self):
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.setInterval(1000)
        self._show_timer.timeout.connect(self._show_overlay)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(2000)
        self._hide_timer.timeout.connect(self._hide_overlay)

    def _connect_signals(self):
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.video_widget.set_click_callback(self._on_video_clicked)
        self.video_widget.set_double_click_callback(self._toggle_fullscreen)
        self.video_widget.move_callback = self._on_video_mouse_move
        self.video_widget.leave_callback = self._on_video_leave

    def _on_video_mouse_move(self, pos):
        video_height = self.video_widget.height()
        if video_height <= 0:
            return
        bottom_zone = video_height * 0.8
        if pos.y() >= bottom_zone:
            if not self.overlay.isVisible() and not self._show_timer.isActive():
                self._show_timer.start()
            self._hide_timer.stop()
        else:
            self._show_timer.stop()
            if self.overlay.isVisible() and not self._overlay_pinned:
                if not self._hide_timer.isActive():
                    self._hide_timer.start()

    def _on_video_leave(self):
        self._show_timer.stop()
        if not self._overlay_pinned:
            self._hide_timer.start()

    def _show_overlay(self):
        self._reposition_overlay()
        self.overlay.show()
        self.overlay.raise_()

    def _hide_overlay(self):
        if not self._overlay_pinned:
            self.overlay.hide()

    def _reposition_overlay(self):
        vg = self.video_widget.geometry()
        overlay_h = 36
        self.overlay.setGeometry(
            vg.x(), vg.y() + vg.height() - overlay_h, vg.width(), overlay_h
        )

    def _toggle_pin(self):
        self._overlay_pinned = self.pin_button.isChecked()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.overlay.isVisible():
            self._reposition_overlay()

    def enterEvent(self, event):
        super().enterEvent(event)
        self._hide_timer.stop()

    def load_file(self, path: str):
        self.current_path = path
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def stop(self):
        self.player.stop()

    def _stop_playback(self):
        self.player.stop()
        self.position_slider.setValue(0)

    def is_navigation_enabled(self) -> bool:
        return self.navigation_enabled

    def _on_video_clicked(self):
        self.navigation_enabled = True
        self.video_widget.setFocus()

    def _on_position_changed(self, position):
        if not self.is_seeking:
            self.position_slider.setValue(position)

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

    def _toggle_fullscreen(self):
        window = self.window()
        if window is None:
            return
        if not self.is_fullscreen:
            window.showFullScreen()
            self.is_fullscreen = True
        else:
            window.showNormal()
            self.is_fullscreen = False

    def exit_fullscreen(self):
        if self.is_fullscreen:
            window = self.window()
            if window:
                window.showNormal()
            self.is_fullscreen = False

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
