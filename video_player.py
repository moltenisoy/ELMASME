import os
from typing import Optional
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QSizePolicy
)

from video_converter import VideoConverterDialog, VideoBatchConverterDialog, VideoTrimDialog
from video_playlist import VideoPlaylistWidget

class ClickableVideoWidget(QVideoWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_callback = None
        self.double_click_callback = None
    
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

class VideoViewer(QWidget):
    
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.video_widget = ClickableVideoWidget()
        self.player.setVideoOutput(self.video_widget)
        
        self.is_seeking = False
        self.volume_visible = True
        self.is_fullscreen = False
        self.navigation_enabled = False
        self.current_path = None
        
        self._build_ui()
        self._connect_signals()
    
    def _build_ui(self):
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
        
        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.setFixedSize(120, 32)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        
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
        self.trim_button.setToolTip("Recortar un fragmento de tiempo del video")
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
        controls.addWidget(self.fullscreen_button)
        controls.addWidget(self.convert_button)
        controls.addWidget(self.convert_all_button)
        controls.addWidget(self.trim_button)
        controls.addStretch(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.video_widget, 1)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.volume_container)
        layout.addLayout(controls)
        
        self.playlist_widget = VideoPlaylistWidget()
        self.playlist_widget.file_selected.connect(self.load_file)
        layout.addWidget(self.playlist_widget)
    
    def _connect_signals(self):
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.video_widget.set_click_callback(self._on_video_clicked)
        self.video_widget.set_double_click_callback(self._toggle_fullscreen)
    
    def load_file(self, path: str):
        self.current_path = path
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
    
    def stop(self):
        self.player.stop()
    
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
    
    def _toggle_volume(self):
        self.volume_container.setVisible(not self.volume_container.isVisible())
    
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
    
    def _show_batch_converter(self):
        if not self.current_path:
            return
        
        dialog = VideoBatchConverterDialog(self.current_path, self)
        dialog.exec()
    
    def _show_trimmer(self):
        if not self.current_path:
            return
        
        dialog = VideoTrimDialog(self.current_path, self)
        dialog.exec()
