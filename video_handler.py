"""
Módulo para manejo de archivos de video.
Incluye reproducción, controles y conversión entre formatos.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Callable
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QToolButton, QSizePolicy, QDialog, QComboBox, QCheckBox, QGroupBox,
    QGridLayout, QMessageBox, QFileDialog, QProgressDialog, QApplication,
    QStackedWidget, QSpinBox
)

# Formatos de video soportados
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".m4v"
}

# Nombres legibles de formatos
FORMAT_NAMES = {
    ".mp4": "MP4 (MPEG-4)",
    ".mkv": "MKV (Matroska)",
    ".avi": "AVI (Audio Video Interleave)",
    ".mov": "MOV (QuickTime)",
    ".wmv": "WMV (Windows Media Video)",
    ".webm": "WEBM (Web Media)",
    ".m4v": "M4V (iTunes Video)"
}

# Codecs recomendados por formato
FORMAT_CODECS = {
    ".mp4": {"video": "libx264", "audio": "aac"},
    ".mkv": {"video": "libx264", "audio": "aac"},
    ".avi": {"video": "libxvid", "audio": "mp3"},
    ".mov": {"video": "libx264", "audio": "aac"},
    ".wmv": {"video": "wmv2", "audio": "wmav2"},
    ".webm": {"video": "libvpx-vp9", "audio": "libopus"},
    ".m4v": {"video": "libx264", "audio": "aac"}
}


def get_video_info(path: str) -> Dict:
    """Obtiene información del archivo de video."""
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "duration": 0,
        "bitrate": 0,
        "width": 0,
        "height": 0,
        "fps": 0,
        "video_codec": "",
        "audio_codec": ""
    }
    
    if os.path.exists(path):
        info["size"] = os.path.getsize(path)
    
    # Intentar obtener metadatos con ffprobe
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            if "format" in data:
                fmt = data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0)) // 1000  # kbps
            
            if "streams" in data:
                for stream in data["streams"]:
                    if stream.get("codec_type") == "video":
                        info["width"] = stream.get("width", 0)
                        info["height"] = stream.get("height", 0)
                        info["video_codec"] = stream.get("codec_name", "")
                        # Calcular FPS
                        avg_frame_rate = stream.get("avg_frame_rate", "0/1")
                        if "/" in avg_frame_rate:
                            num, den = avg_frame_rate.split("/")
                            if int(den) != 0:
                                info["fps"] = round(int(num) / int(den), 2)
                    elif stream.get("codec_type") == "audio":
                        info["audio_codec"] = stream.get("codec_name", "")
    
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    
    return info


def is_ffmpeg_available() -> bool:
    """Verifica si ffmpeg está instalado y disponible."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_video(
    input_path: str,
    output_path: str,
    output_format: str,
    quality: str = "high",
    progress_callback: Optional[Callable[[int], None]] = None
) -> bool:
    """
    Convierte un archivo de video a otro formato usando ffmpeg.
    
    Args:
        input_path: Ruta del archivo de entrada
        output_path: Ruta del archivo de salida
        output_format: Extensión de salida (ej: ".mp4", ".avi")
        quality: Calidad de salida ("low", "medium", "high", "original")
        progress_callback: Función opcional para reportar progreso (0-100)
    
    Returns:
        True si la conversión fue exitosa, False en caso contrario
    """
    if not is_ffmpeg_available():
        raise RuntimeError("ffmpeg no está instalado o no está disponible en el PATH")
    
    codecs = FORMAT_CODECS.get(output_format.lower(), {"video": "copy", "audio": "copy"})
    
    # Presets de calidad
    quality_presets = {
        "low": {"crf": "28", "preset": "veryfast", "audio_bitrate": "96k"},
        "medium": {"crf": "23", "preset": "medium", "audio_bitrate": "128k"},
        "high": {"crf": "18", "preset": "slow", "audio_bitrate": "192k"},
        "original": {"crf": "copy", "preset": "medium", "audio_bitrate": "copy"}
    }
    
    preset = quality_presets.get(quality, quality_presets["high"])
    
    cmd = ["ffmpeg", "-y", "-i", input_path]
    
    # Configuración de video
    if quality == "original":
        cmd.extend(["-c:v", "copy"])
    else:
        cmd.extend([
            "-c:v", codecs["video"],
            "-crf", preset["crf"],
            "-preset", preset["preset"]
        ])
    
    # Configuración de audio
    if quality == "original" or preset["audio_bitrate"] == "copy":
        cmd.extend(["-c:a", "copy"])
    else:
        cmd.extend([
            "-c:a", codecs["audio"],
            "-b:a", preset["audio_bitrate"]
        ])
    
    cmd.append(output_path)
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if progress_callback:
            progress_callback(0)
            import time
            for i in range(10):
                time.sleep(0.2)
                progress_callback((i + 1) * 10)
        
        stdout, stderr = process.communicate(timeout=600)
        
        if progress_callback:
            progress_callback(100)
        
        return process.returncode == 0 and os.path.exists(output_path)
    
    except subprocess.TimeoutExpired:
        process.kill()
        return False
    except Exception:
        return False


def get_supported_output_formats(input_format: str) -> List[str]:
    """Obtiene la lista de formatos a los que se puede convertir un video."""
    return sorted([ext for ext in VIDEO_EXTENSIONS if ext != input_format.lower()])


class ClickableVideoWidget(QVideoWidget):
    """Widget de video que detecta clicks."""
    
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


class VideoConverterDialog(QDialog):
    """Diálogo para convertir archivos de video."""
    
    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.input_format = Path(input_path).suffix.lower()
        self.output_path = None
        
        self.setWindowTitle("Convertir Video")
        self.setMinimumWidth(500)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Información del archivo de entrada
        info_group = QGroupBox("Archivo de entrada")
        info_layout = QGridLayout(info_group)
        
        info = get_video_info(self.input_path)
        
        info_layout.addWidget(QLabel("Nombre:"), 0, 0)
        info_layout.addWidget(QLabel(info["filename"]), 0, 1)
        
        info_layout.addWidget(QLabel("Formato:"), 1, 0)
        info_layout.addWidget(QLabel(FORMAT_NAMES.get(self.input_format, self.input_format)), 1, 1)
        
        size_mb = info["size"] / (1024 * 1024)
        info_layout.addWidget(QLabel("Tamaño:"), 2, 0)
        info_layout.addWidget(QLabel(f"{size_mb:.2f} MB"), 2, 1)
        
        if info["duration"] > 0:
            minutes = int(info["duration"] // 60)
            seconds = int(info["duration"] % 60)
            info_layout.addWidget(QLabel("Duración:"), 3, 0)
            info_layout.addWidget(QLabel(f"{minutes}:{seconds:02d}"), 3, 1)
        
        if info["width"] > 0 and info["height"] > 0:
            info_layout.addWidget(QLabel("Resolución:"), 4, 0)
            info_layout.addWidget(QLabel(f"{info['width']}x{info['height']} @ {info['fps']}fps"), 4, 1)
        
        layout.addWidget(info_group)
        
        # Opciones de conversión
        convert_group = QGroupBox("Opciones de conversión")
        convert_layout = QVBoxLayout(convert_group)
        
        # Formato de salida
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Convertir a:"))
        self.format_combo = QComboBox()
        
        output_formats = get_supported_output_formats(self.input_format)
        for fmt in output_formats:
            self.format_combo.addItem(FORMAT_NAMES.get(fmt, fmt), fmt)
        
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        convert_layout.addLayout(format_layout)
        
        # Calidad
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Calidad:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Alta (recomendado)", "high")
        self.quality_combo.addItem("Media", "medium")
        self.quality_combo.addItem("Baja (archivo pequeño)", "low")
        self.quality_combo.addItem("Original (sin recodificar)", "original")
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        convert_layout.addLayout(quality_layout)
        
        layout.addWidget(convert_group)
        
        # Opciones de guardado
        save_group = QGroupBox("Guardar como")
        save_layout = QVBoxLayout(save_group)
        
        self.new_file_radio = QCheckBox("Crear nuevo archivo")
        self.new_file_radio.setChecked(True)
        save_layout.addWidget(self.new_file_radio)
        
        self.overwrite_radio = QCheckBox("Sobrescribir archivo original")
        self.overwrite_radio.toggled.connect(
            lambda: self.new_file_radio.setChecked(not self.overwrite_radio.isChecked())
        )
        self.new_file_radio.toggled.connect(
            lambda: self.overwrite_radio.setChecked(not self.new_file_radio.isChecked())
        )
        save_layout.addWidget(self.overwrite_radio)
        
        layout.addWidget(save_group)
        
        # Botones
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        self.convert_button = QPushButton("Convertir")
        self.convert_button.clicked.connect(self._on_convert)
        buttons.addWidget(self.convert_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        
        layout.addLayout(buttons)
        layout.addStretch()
    
    def _on_convert(self):
        output_format = self.format_combo.currentData()
        quality = self.quality_combo.currentData()
        
        if self.new_file_radio.isChecked():
            original_dir = os.path.dirname(self.input_path)
            original_name = os.path.splitext(os.path.basename(self.input_path))[0]
            suggested_name = f"{original_name}_converted{output_format}"
            suggested_path = os.path.join(original_dir, suggested_name)
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar video convertido",
                suggested_path,
                f"Video (*{output_format})"
            )
            if not file_path:
                return
            self.output_path = file_path
        else:
            original_dir = os.path.dirname(self.input_path)
            original_name = os.path.splitext(os.path.basename(self.input_path))[0]
            self.output_path = os.path.join(original_dir, f"{original_name}{output_format}")
        
        # Realizar conversión
        progress = QProgressDialog("Convirtiendo video...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        
        try:
            def update_progress(value):
                progress.setValue(value)
                QApplication.processEvents()
            
            success = convert_video(
                self.input_path,
                self.output_path,
                output_format,
                quality,
                update_progress
            )
            
            progress.setValue(100)
            
            if success:
                if self.overwrite_radio.isChecked() and self.output_path != self.input_path:
                    if os.path.exists(self.input_path):
                        os.remove(self.input_path)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Video convertido correctamente.\nGuardado en:\n{self.output_path}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo convertir el archivo de video."
                )
        
        except RuntimeError as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"{str(e)}\n\nPor favor instala ffmpeg para usar esta función."
            )
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Error durante la conversión:\n{str(e)}"
            )
    
    def get_output_path(self) -> Optional[str]:
        return self.output_path


class VideoBatchConverterDialog(QDialog):
    """Diálogo para convertir video a múltiples formatos simultáneamente."""
    
    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.input_format = Path(input_path).suffix.lower()
        self.output_paths = []
        
        self.setWindowTitle("Convertir a Múltiples Formatos")
        self.setMinimumWidth(450)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Información del archivo
        info_label = QLabel(f"Archivo: {os.path.basename(self.input_path)}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Calidad
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Calidad:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Alta", "high")
        self.quality_combo.addItem("Media", "medium")
        self.quality_combo.addItem("Baja", "low")
        self.quality_combo.addItem("Original", "original")
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        layout.addLayout(quality_layout)
        
        # Selección de formatos
        format_group = QGroupBox("Seleccionar formatos de salida")
        format_layout = QVBoxLayout(format_group)
        
        self.format_checks = {}
        output_formats = get_supported_output_formats(self.input_format)
        
        for fmt in output_formats:
            check = QCheckBox(FORMAT_NAMES.get(fmt, fmt))
            check.setChecked(True)
            self.format_checks[fmt] = check
            format_layout.addWidget(check)
        
        # Botones de selección rápida
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleccionar todos")
        select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Deseleccionar todos")
        select_none_btn.clicked.connect(self._select_none)
        select_layout.addWidget(select_none_btn)
        select_layout.addStretch()
        
        format_layout.addLayout(select_layout)
        layout.addWidget(format_group)
        
        # Opciones
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.open_folder_check = QCheckBox("Abrir carpeta al finalizar")
        self.open_folder_check.setChecked(True)
        options_layout.addWidget(self.open_folder_check)
        
        layout.addWidget(options_group)
        
        # Botones
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        self.convert_button = QPushButton("Convertir a todos")
        self.convert_button.clicked.connect(self._on_convert_all)
        buttons.addWidget(self.convert_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        
        layout.addLayout(buttons)
        layout.addStretch()
    
    def _select_all(self):
        for check in self.format_checks.values():
            check.setChecked(True)
    
    def _select_none(self):
        for check in self.format_checks.values():
            check.setChecked(False)
    
    def _on_convert_all(self):
        selected_formats = [
            fmt for fmt, check in self.format_checks.items() if check.isChecked()
        ]
        
        if not selected_formats:
            QMessageBox.warning(
                self,
                "Sin selección",
                "Por favor selecciona al menos un formato de salida."
            )
            return
        
        if not is_ffmpeg_available():
            QMessageBox.critical(
                self,
                "Error",
                "ffmpeg no está instalado.\n\nPor favor instala ffmpeg para usar esta función."
            )
            return
        
        quality = self.quality_combo.currentData()
        original_dir = os.path.dirname(self.input_path)
        original_name = os.path.splitext(os.path.basename(self.input_path))[0]
        
        progress = QProgressDialog("Convirtiendo video...", "Cancelar", 0, len(selected_formats), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        
        self.output_paths = []
        errors = []
        
        for i, fmt in enumerate(selected_formats):
            progress.setValue(i)
            progress.setLabelText(f"Convirtiendo a {FORMAT_NAMES.get(fmt, fmt)}...")
            QApplication.processEvents()
            
            if progress.wasCanceled():
                break
            
            output_path = os.path.join(original_dir, f"{original_name}_converted{fmt}")
            
            try:
                success = convert_video(self.input_path, output_path, fmt, quality)
                if success:
                    self.output_paths.append(output_path)
                else:
                    errors.append(fmt)
            except Exception as e:
                errors.append(f"{fmt}: {str(e)}")
        
        progress.setValue(len(selected_formats))
        
        if errors:
            QMessageBox.warning(
                self,
                "Conversión parcial",
                f"Se convirtieron {len(self.output_paths)} archivos.\n"
                f"Errores en: {', '.join(errors)}"
            )
        else:
            QMessageBox.information(
                self,
                "Éxito",
                f"Se crearon {len(self.output_paths)} archivos convertidos."
            )
        
        if self.open_folder_check.isChecked() and self.output_paths:
            os.startfile(original_dir)
        
        self.accept()
    
    def get_output_paths(self) -> List[str]:
        return self.output_paths


class VideoViewer(QWidget):
    """Visor de video con controles de reproducción y conversión."""
    
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
        # Controles de reproducción
        self.pause_button = QPushButton("Pausar")
        self.pause_button.setFixedSize(80, 32)
        self.pause_button.clicked.connect(self.player.pause)
        
        self.resume_button = QPushButton("Reproducir")
        self.resume_button.setFixedSize(80, 32)
        self.resume_button.clicked.connect(self.player.play)
        
        # Slider de posición
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        self.position_slider.valueChanged.connect(self._on_slider_value_changed)
        
        # Controles de volumen
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
        
        # Botón de pantalla completa
        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.setFixedSize(120, 32)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        
        # Botones de conversión
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
        
        # Layout de volumen
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(8)
        volume_layout.addWidget(QLabel("Volumen:"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addStretch()
        
        self.volume_container = QWidget()
        self.volume_container.setLayout(volume_layout)
        
        # Layout de controles
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
        controls.addStretch(1)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.video_widget, 1)
        layout.addWidget(self.position_slider)
        layout.addWidget(self.volume_container)
        layout.addLayout(controls)
    
    def _connect_signals(self):
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.video_widget.set_click_callback(self._on_video_clicked)
        self.video_widget.set_double_click_callback(self._toggle_fullscreen)
    
    def load_file(self, path: str):
        """Carga un archivo de video."""
        self.current_path = path
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
    
    def stop(self):
        """Detiene la reproducción."""
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
        """Muestra el diálogo de conversión."""
        if not self.current_path:
            return
        
        dialog = VideoConverterDialog(self.current_path, self)
        dialog.exec()
    
    def _show_batch_converter(self):
        """Muestra el diálogo de conversión por lotes."""
        if not self.current_path:
            return
        
        dialog = VideoBatchConverterDialog(self.current_path, self)
        dialog.exec()
