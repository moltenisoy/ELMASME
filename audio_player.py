"""
Módulo de reproducción de archivos de audio.
Incluye el visor de audio con controles de reproducción y conversión.
"""

import os
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QMessageBox, QComboBox, QDialog, QDialogButtonBox,
    QApplication
)

from audio_converter import (
    get_audio_info, AudioConverterDialog, AudioBatchConverterDialog,
    AudioTrimDialog, AUDIO_EXTENSIONS, convert_audio, is_ffmpeg_available,
    FORMAT_NAMES as AUDIO_FORMAT_NAMES
)
from audio_playlist import AudioPlaylistWidget
from progress_bar import ConversionProgressBar

# Estilo estético para el slider de volumen
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
    """Visor de audio con controles de reproducción y conversión."""
    
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.is_seeking = False
        self.current_path = None
        self._progress_bar = None
        
        self._build_ui()
        self._connect_signals()
    
    def _build_ui(self):
        # Placeholder para audio (sin video)
        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;font-size:16px;"
        )
        self.placeholder.setText("Audio cargado")
        self.placeholder.setMinimumHeight(200)
        
        # Controles de reproducción con iconos
        self.play_button = QPushButton("▶")
        self.play_button.setToolTip("Reproducir")
        self.play_button.setFixedSize(42, 34)
        self.play_button.clicked.connect(self.player.play)
        
        self.pause_button = QPushButton("⏸")
        self.pause_button.setToolTip("Pausar")
        self.pause_button.setFixedSize(42, 34)
        self.pause_button.clicked.connect(self.player.pause)
        
        self.stop_button = QPushButton("⏹")
        self.stop_button.setToolTip("Detener")
        self.stop_button.setFixedSize(42, 34)
        self.stop_button.clicked.connect(self._stop_playback)
        
        # Slider de posición
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_value_changed)
        
        # Controles de volumen con estilo estético
        vol_label = QLabel("🔊")
        vol_label.setFixedWidth(22)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(130)
        self.volume_slider.setStyleSheet(VOLUME_SLIDER_STYLE)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.audio_output.setVolume(0.5)
        
        # Botones de conversión (más anchos)
        self.convert_button = QToolButton()
        self.convert_button.setText("Convertir")
        self.convert_button.setToolTip("Convertir a otro formato")
        self.convert_button.setFixedSize(110, 32)
        self.convert_button.clicked.connect(self._show_converter)
        
        self.convert_playlist_button = QToolButton()
        self.convert_playlist_button.setText("Convertir playlist")
        self.convert_playlist_button.setToolTip("Convertir toda la playlist actual")
        self.convert_playlist_button.setFixedSize(140, 32)
        self.convert_playlist_button.clicked.connect(self._convert_playlist)
        
        # Botón de recorte
        self.trim_button = QToolButton()
        self.trim_button.setText("Recortar")
        self.trim_button.setToolTip("Recortar un fragmento de tiempo del audio")
        self.trim_button.setFixedSize(90, 32)
        self.trim_button.clicked.connect(self._show_trimmer)
        
        # Layout de volumen (siempre visible)
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(8)
        volume_layout.addWidget(vol_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addStretch()
        
        self.volume_container = QWidget()
        self.volume_container.setLayout(volume_layout)
        
        # Layout de controles
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(10)
        controls.addStretch(1)
        controls.addWidget(self.play_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.convert_button)
        controls.addWidget(self.convert_playlist_button)
        controls.addWidget(self.trim_button)
        controls.addStretch(1)
        
        # Lista de reproducción
        self.playlist_widget = AudioPlaylistWidget()
        self.playlist_widget.file_selected.connect(self.load_file)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.placeholder, 1)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.volume_container)
        layout.addLayout(controls)
        layout.addWidget(self.playlist_widget)
    
    def _connect_signals(self):
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
    
    def load_file(self, path: str):
        """Carga un archivo de audio."""
        self.current_path = path
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))
        
        # Mostrar información del audio
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
        """Detiene la reproducción."""
        self.player.stop()
    
    def _stop_playback(self):
        """Detiene la reproducción y reinicia posición."""
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
        """Muestra el diálogo de conversión."""
        if not self.current_path:
            return
        
        dialog = AudioConverterDialog(self.current_path, self)
        dialog.exec()
    
    def _convert_playlist(self):
        """Convierte toda la playlist actual al formato elegido."""
        playlist = self.playlist_widget.get_playlist()
        if not playlist:
            QMessageBox.information(self, "Playlist vacía",
                                    "No hay archivos en la lista de reproducción.")
            return
        
        if not is_ffmpeg_available():
            QMessageBox.critical(self, "Error",
                                 "ffmpeg no está instalado.\n\nPor favor instala ffmpeg.")
            return
        
        # Preguntar formato de audio
        audio_format = self._ask_format("audio", AUDIO_FORMAT_NAMES, AUDIO_EXTENSIONS)
        if not audio_format:
            return
        
        # Convertir con barra de progreso
        if not self._progress_bar:
            self._progress_bar = ConversionProgressBar()
        
        total = len(playlist)
        errors = []
        
        for i, file_path in enumerate(playlist):
            filename = os.path.basename(file_path)
            pct = int((i / total) * 100)
            self._progress_bar.start(filename)
            self._progress_bar.update_progress(pct, filename)
            
            ext = Path(file_path).suffix.lower()
            if ext == audio_format:
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
        """Muestra un diálogo para elegir formato de conversión."""
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
        """Muestra el diálogo de recorte de audio."""
        if not self.current_path:
            return
        
        dialog = AudioTrimDialog(self.current_path, self)
        dialog.exec()
