import os
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QMessageBox, QComboBox, QDialog, QDialogButtonBox,
    QApplication, QMenu, QSplitter
)

from audio_converter import (
    get_audio_info, AudioConverterDialog, AudioBatchConverterDialog,
    AudioTrimDialog, AUDIO_EXTENSIONS, convert_audio, is_ffmpeg_available,
    FORMAT_NAMES as AUDIO_FORMAT_NAMES
)
from audio_playlist import AudioPlaylistWidget
from progress_bar import ConversionProgressBar

OVERLAY_HEIGHT = 36
OVERLAY_TRIGGER_ZONE = 0.8

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


class AudioViewer(QWidget):

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.is_seeking = False
        self.current_path = None
        self._progress_bar = None
        self._overlay_pinned = False

        self.setMouseTracking(True)
        self._build_ui()
        self._setup_timers()
        self._connect_signals()

    def _build_ui(self):
        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;font-size:16px;"
        )
        self.placeholder.setText("Audio cargado")
        self.placeholder.setMinimumHeight(200)
        self.placeholder.setMouseTracking(True)

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
        controls.addWidget(self.edition_button)
        controls.addStretch(1)

        self.playlist_widget = AudioPlaylistWidget()
        self.playlist_widget.file_selected.connect(self.load_file)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(4)
        top_layout.addWidget(self.placeholder, 1)
        top_layout.addWidget(self.position_slider)
        top_layout.addLayout(controls)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(top_widget)
        self.splitter.addWidget(self.playlist_widget)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.splitter)

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

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pg = self.placeholder.geometry()
        pos = event.pos()
        if pg.contains(pos):
            local_y = pos.y() - pg.y()
            bottom_zone = pg.height() * OVERLAY_TRIGGER_ZONE
            if local_y >= bottom_zone:
                if not self.overlay.isVisible() and not self._show_timer.isActive():
                    self._show_timer.start()
                self._hide_timer.stop()
            else:
                self._show_timer.stop()
                if self.overlay.isVisible() and not self._overlay_pinned:
                    if not self._hide_timer.isActive():
                        self._hide_timer.start()
        else:
            self._show_timer.stop()
            if self.overlay.isVisible() and not self._overlay_pinned:
                if not self._hide_timer.isActive():
                    self._hide_timer.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
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
        pg = self.placeholder.geometry()
        overlay_h = OVERLAY_HEIGHT
        self.overlay.setGeometry(
            pg.x(), pg.y() + pg.height() - overlay_h, pg.width(), overlay_h
        )

    def _toggle_pin(self):
        self._overlay_pinned = self.pin_button.isChecked()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.overlay.isVisible():
            self._reposition_overlay()

    def load_file(self, path: str):
        self.current_path = path
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))

        info = get_audio_info(path)
        info_text = f"Audio: {info['filename']}"

        if info['duration'] > 0:
            minutes = int(info['duration'] // 60)
            seconds = int(info['duration'] % 60)
            info_text += f"\nDuración: {minutes}:{seconds:02d}"

        if info['bitrate'] > 0:
            info_text += f" | {info['bitrate']} kbps"

        self.placeholder.setText(info_text)
        self.player.play()

    def stop(self):
        self.player.stop()

    def _stop_playback(self):
        self.player.stop()
        self.position_slider.setValue(0)

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

    def _show_converter(self):
        if not self.current_path:
            return
        dialog = AudioConverterDialog(self.current_path, self)
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

        audio_format = self._ask_format("audio", AUDIO_FORMAT_NAMES, AUDIO_EXTENSIONS)
        if not audio_format:
            return

        if not self._progress_bar:
            self._progress_bar = ConversionProgressBar()

        total = len(playlist)
        errors = []

        for i, file_path in enumerate(playlist):
            filename = os.path.basename(file_path)
            self._progress_bar.start(filename)

            ext = Path(file_path).suffix.lower()
            if ext == audio_format:
                self._progress_bar.update_progress(int(((i + 1) / total) * 100), filename)
                continue

            out_dir = os.path.dirname(file_path)
            out_name = os.path.splitext(os.path.basename(file_path))[0]
            out_path = os.path.join(out_dir, f"{out_name}_converted{audio_format}")

            try:
                success = convert_audio(file_path, out_path, audio_format)
                if not success:
                    errors.append(filename)
            except Exception:
                errors.append(filename)

            self._progress_bar.update_progress(int(((i + 1) / total) * 100), filename)

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
        dialog = AudioTrimDialog(self.current_path, self)
        dialog.exec()
