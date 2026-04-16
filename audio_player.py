import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton
)

from audio_converter import get_audio_info, AudioConverterDialog, AudioBatchConverterDialog, AudioTrimDialog
from audio_playlist import AudioPlaylistWidget

class AudioViewer(QWidget):
    
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.is_seeking = False
        self.current_path = None
        
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
        
        self.pause_button = QPushButton("Pausar")
        self.pause_button.setFixedSize(80, 32)
        self.pause_button.clicked.connect(self.player.pause)
        
        self.resume_button = QPushButton("Reproducir")
        self.resume_button.setFixedSize(80, 32)
        self.resume_button.clicked.connect(self.player.play)
        
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_value_changed)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(120)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.audio_output.setVolume(0.5)
        
        self.volume_toggle_button = QToolButton()
        self.volume_toggle_button.setText("Volumen")
        self.volume_toggle_button.setFixedSize(70, 32)
        self.volume_toggle_button.clicked.connect(self._toggle_volume)
        
        self.convert_button = QToolButton()
        self.convert_button.setText("Convertir")
        self.convert_button.setToolTip("Convertir a otro formato")
        self.convert_button.setFixedSize(80, 32)
        self.convert_button.clicked.connect(self._show_converter)
        
        self.convert_all_button = QToolButton()
        self.convert_all_button.setText("Convertir a todos")
        self.convert_all_button.setToolTip("Convertir a todos los formatos")
        self.convert_all_button.setFixedSize(110, 32)
        self.convert_all_button.clicked.connect(self._show_batch_converter)
        
        self.trim_button = QToolButton()
        self.trim_button.setText("Recortar")
        self.trim_button.setToolTip("Recortar un fragmento de tiempo del audio")
        self.trim_button.setFixedSize(80, 32)
        self.trim_button.clicked.connect(self._show_trimmer)
        
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(8)
        volume_layout.addWidget(QLabel("Volumen:"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addStretch()
        
        self.volume_container = QWidget()
        self.volume_container.setLayout(volume_layout)
        
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(10)
        controls.addStretch(1)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.resume_button)
        controls.addWidget(self.volume_toggle_button)
        controls.addWidget(self.convert_button)
        controls.addWidget(self.convert_all_button)
        controls.addWidget(self.trim_button)
        controls.addStretch(1)
        
        self.playlist_widget = AudioPlaylistWidget()
        self.playlist_widget.file_selected.connect(self.load_file)
        
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
    
    def _toggle_volume(self):
        self.volume_container.setVisible(not self.volume_container.isVisible())
    
    def _show_converter(self):
        if not self.current_path:
            return
        
        dialog = AudioConverterDialog(self.current_path, self)
        dialog.exec()
    
    def _show_batch_converter(self):
        if not self.current_path:
            return
        
        dialog = AudioBatchConverterDialog(self.current_path, self)
        dialog.exec()
    
    def _show_trimmer(self):
        if not self.current_path:
            return
        
        dialog = AudioTrimDialog(self.current_path, self)
        dialog.exec()
