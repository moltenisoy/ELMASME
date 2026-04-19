import os
import subprocess
import tempfile
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QMessageBox, QComboBox, QDialog, QDialogButtonBox,
    QApplication, QMenu, QSplitter, QFileDialog
)

from audio_converter import (
    get_audio_info, AUDIO_EXTENSIONS, convert_audio, is_ffmpeg_available,
    FORMAT_NAMES as AUDIO_FORMAT_NAMES
)
from audio_converter_dialogs import AudioConverterDialog, AudioBatchConverterDialog, AudioTrimDialog
from audio_playlist import AudioPlaylistWidget
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


class AudioViewer(QWidget):

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.is_seeking = False
        self.current_path = None
        self._progress_bar = None
        self._bg_pixmap = None
        self._midi_tmp = None

        self.setMouseTracking(True)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;font-size:16px;"
        )
        self.placeholder.setText("Audio cargado")
        self.placeholder.setMinimumHeight(200)

        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(36, 28)
        self.play_button.setStyleSheet("font-size: 36px;")
        self.play_button.clicked.connect(self.player.play)

        self.pause_button = QPushButton("⏸")
        self.pause_button.setFixedSize(36, 28)
        self.pause_button.setStyleSheet("font-size: 36px;")
        self.pause_button.clicked.connect(self.player.pause)

        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(36, 28)
        self.stop_button.setStyleSheet("font-size: 36px;")
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

        self.playlist_toggle_button = QPushButton("📃")
        self.playlist_toggle_button.setFixedSize(36, 28)
        self.playlist_toggle_button.setStyleSheet("font-size: 32px;")
        self.playlist_toggle_button.setToolTip("Mostrar/ocultar lista de reproducción")
        self.playlist_toggle_button.setCheckable(True)
        self.playlist_toggle_button.setChecked(True)
        self.playlist_toggle_button.clicked.connect(self._toggle_playlist_visibility)

        self.bg_image_button = QPushButton("🖼")
        self.bg_image_button.setFixedSize(26, 22)
        self.bg_image_button.setToolTip("Seleccionar imagen de fondo")
        self.bg_image_button.clicked.connect(self._select_bg_image)

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
        controls.addWidget(self.play_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        controls.addSpacing(8)
        controls.addWidget(vol_label)
        controls.addWidget(self.volume_slider)
        controls.addStretch(1)
        controls.addWidget(self.bg_image_button)
        controls.addWidget(self.playlist_toggle_button)
        controls.addWidget(self.edition_button)

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

    def _toggle_playlist_visibility(self):
        visible = self.playlist_toggle_button.isChecked()
        self.playlist_widget.setVisible(visible)
        self.playlist_toggle_button.setToolTip(
            "Ocultar lista de reproducción" if visible else "Mostrar lista de reproducción"
        )

    def _select_bg_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de fondo",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos los archivos (*.*)"
        )
        if not file_path:
            return
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return
        self._bg_pixmap = pixmap
        self._apply_bg_image()

    def _apply_bg_image(self):
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            pw = self.placeholder.width() or 400
            ph = self.placeholder.height() or 200
            scaled = self._bg_pixmap.scaled(pw, ph, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.placeholder.setPixmap(scaled)
            self.placeholder.setScaledContents(True)
            self.placeholder.setStyleSheet(
                "background:#111827;border-radius:14px;color:#cbd5e1;font-size:16px;"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            self._apply_bg_image()

    def load_file(self, path: str):
        self.current_path = path
        self.player.stop()
        self._cleanup_midi_tmp()
        
        ext = Path(path).suffix.lower()
        play_path = path
        if ext in (".mid", ".midi"):
            try:
                fd, tmp_wav = tempfile.mkstemp(suffix=".wav", prefix="elmasme_midi_")
                os.close(fd)
                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", path, "-c:a", "pcm_s16le", tmp_wav],
                    capture_output=True, timeout=30
                )
                if result.returncode == 0 and os.path.exists(tmp_wav):
                    play_path = tmp_wav
                    self._midi_tmp = tmp_wav
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass
        
        self.player.setSource(QUrl.fromLocalFile(play_path))

        info = get_audio_info(path)
        info_text = f"Audio: {info['filename']}"

        if info['duration'] > 0:
            minutes = int(info['duration'] // 60)
            seconds = int(info['duration'] % 60)
            info_text += f"\nDuración: {minutes}:{seconds:02d}"

        if info['bitrate'] > 0:
            info_text += f" | {info['bitrate']} kbps"

        if self._bg_pixmap and not self._bg_pixmap.isNull():
            self._apply_bg_image()
        else:
            self.placeholder.setText(info_text)
        self.player.play()

    def stop(self):
        self.player.stop()
        self._cleanup_midi_tmp()

    def _cleanup_midi_tmp(self):
        if self._midi_tmp and os.path.exists(self._midi_tmp):
            try:
                os.remove(self._midi_tmp)
            except OSError:
                pass
            self._midi_tmp = None

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
