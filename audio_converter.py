
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Callable
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QSpinBox,
    QGridLayout, QMessageBox, QFileDialog, QProgressDialog, QApplication
)

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma",
    ".mid", ".midi", ".opus"
}

QT_SUPPORTED_AUDIO = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}

FORMAT_NAMES = {
    ".mp3": "MP3 (MPEG Audio)",
    ".wav": "WAV (Waveform Audio)",
    ".flac": "FLAC (Free Lossless Audio Codec)",
    ".ogg": "OGG Vorbis",
    ".m4a": "M4A (AAC Audio)",
    ".aac": "AAC (Advanced Audio Coding)",
    ".wma": "WMA (Windows Media Audio)",
    ".mid": "MIDI (Musical Instrument Digital Interface)",
    ".midi": "MIDI (Musical Instrument Digital Interface)",
    ".opus": "OPUS (Opus Audio Codec)"
}


def get_audio_info(path: str) -> Dict:
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "duration": 0,
        "bitrate": 0,
        "sample_rate": 0,
        "channels": 0
    }
    
    if os.path.exists(path):
        info["size"] = os.path.getsize(path)
    
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "format" in data:
                fmt = data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0)) // 1000
            if "streams" in data and len(data["streams"]) > 0:
                stream = data["streams"][0]
                info["sample_rate"] = int(stream.get("sample_rate", 0))
                info["channels"] = stream.get("channels", 0)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    
    return info


def is_ffmpeg_available() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_audio(
    input_path: str,
    output_path: str,
    output_format: str,
    progress_callback: Optional[Callable[[int], None]] = None,
    bitrate: Optional[int] = None,
    sample_rate: Optional[int] = None
) -> bool:
    if not is_ffmpeg_available():
        raise RuntimeError("ffmpeg no está instalado o no está disponible en el PATH")
    
    codec_map = {
        ".mp3": "libmp3lame",
        ".wav": "pcm_s16le",
        ".flac": "flac",
        ".ogg": "libvorbis",
        ".m4a": "aac",
        ".aac": "aac",
        ".wma": "wmav2",
        ".opus": "libopus"
    }
    
    codec = codec_map.get(output_format.lower(), "copy")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-c:a", codec,
    ]
    
    if bitrate:
        cmd.extend(["-b:a", f"{bitrate}k"])
    else:
        cmd.extend(["-q:a", "2"])
    
    if sample_rate:
        cmd.extend(["-ar", str(sample_rate)])
    
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
            for i in range(10):
                time.sleep(0.1)
                progress_callback((i + 1) * 10)
        
        stdout, stderr = process.communicate(timeout=300)
        
        if progress_callback:
            progress_callback(100)
        
        return process.returncode == 0 and os.path.exists(output_path)
    
    except subprocess.TimeoutExpired:
        process.kill()
        return False
    except Exception:
        return False


def get_supported_output_formats(input_format: str) -> List[str]:
    return sorted([ext for ext in AUDIO_EXTENSIONS if ext != input_format.lower()])


class AudioConverterDialog(QDialog):
    
    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.input_format = Path(input_path).suffix.lower()
        self.output_path = None
        
        self.setWindowTitle("Convertir Audio")
        self.setMinimumWidth(450)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        info_group = QGroupBox("Archivo de entrada")
        info_layout = QGridLayout(info_group)
        
        info = get_audio_info(self.input_path)
        
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
        
        layout.addWidget(info_group)
        
        convert_group = QGroupBox("Opciones de conversión")
        convert_layout = QVBoxLayout(convert_group)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Convertir a:"))
        self.format_combo = QComboBox()
        
        output_formats = get_supported_output_formats(self.input_format)
        for fmt in output_formats:
            self.format_combo.addItem(FORMAT_NAMES.get(fmt, fmt), fmt)
        
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        convert_layout.addLayout(format_layout)
        
        self.copy_check = QCheckBox("Copiar sin recodificar (copiar códec original)")
        self.copy_check.setToolTip("Mantiene la misma calidad pero cambia el contenedor")
        convert_layout.addWidget(self.copy_check)
        
        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(QLabel("Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItem("Automático", 0)
        for br in [64, 128, 192, 256, 320]:
            self.bitrate_combo.addItem(f"{br} kbps", br)
        self.bitrate_combo.setCurrentIndex(0)
        bitrate_layout.addWidget(self.bitrate_combo)
        bitrate_layout.addStretch()
        convert_layout.addLayout(bitrate_layout)
        
        samplerate_layout = QHBoxLayout()
        samplerate_layout.addWidget(QLabel("Sample Rate:"))
        self.samplerate_combo = QComboBox()
        self.samplerate_combo.addItem("Original", 0)
        for sr in [22050, 44100, 48000]:
            self.samplerate_combo.addItem(f"{sr} Hz", sr)
        self.samplerate_combo.setCurrentIndex(0)
        samplerate_layout.addWidget(self.samplerate_combo)
        samplerate_layout.addStretch()
        convert_layout.addLayout(samplerate_layout)
        
        layout.addWidget(convert_group)
        
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
        
        if self.new_file_radio.isChecked():
            original_dir = os.path.dirname(self.input_path)
            original_name = os.path.splitext(os.path.basename(self.input_path))[0]
            suggested_name = f"{original_name}_converted{output_format}"
            suggested_path = os.path.join(original_dir, suggested_name)
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar audio convertido",
                suggested_path,
                f"Audio (*{output_format})"
            )
            if not file_path:
                return
            self.output_path = file_path
        else:
            original_dir = os.path.dirname(self.input_path)
            original_name = os.path.splitext(os.path.basename(self.input_path))[0]
            self.output_path = os.path.join(original_dir, f"{original_name}{output_format}")
        
        progress = QProgressDialog("Convirtiendo audio...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        
        bitrate = self.bitrate_combo.currentData() or None
        sample_rate = self.samplerate_combo.currentData() or None
        
        try:
            def update_progress(value):
                progress.setValue(value)
                QApplication.processEvents()
            
            success = convert_audio(
                self.input_path,
                self.output_path,
                output_format,
                update_progress,
                bitrate=bitrate,
                sample_rate=sample_rate
            )
            
            progress.setValue(100)
            
            if success:
                if self.overwrite_radio.isChecked() and self.output_path != self.input_path:
                    os.remove(self.input_path)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Audio convertido correctamente.\nGuardado en:\n{self.output_path}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo convertir el archivo de audio."
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


class AudioBatchConverterDialog(QDialog):
    
    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.input_format = Path(input_path).suffix.lower()
        self.output_paths = []
        
        self.setWindowTitle("Convertir a Múltiples Formatos")
        self.setMinimumWidth(400)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        info_label = QLabel(f"Archivo: {os.path.basename(self.input_path)}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        format_group = QGroupBox("Seleccionar formatos de salida")
        format_layout = QVBoxLayout(format_group)
        
        self.format_checks = {}
        output_formats = get_supported_output_formats(self.input_format)
        
        for fmt in output_formats:
            check = QCheckBox(FORMAT_NAMES.get(fmt, fmt))
            check.setChecked(True)
            self.format_checks[fmt] = check
            format_layout.addWidget(check)
        
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
        
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.open_folder_check = QCheckBox("Abrir carpeta al finalizar")
        self.open_folder_check.setChecked(True)
        options_layout.addWidget(self.open_folder_check)
        
        layout.addWidget(options_group)
        
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
        
        original_dir = os.path.dirname(self.input_path)
        original_name = os.path.splitext(os.path.basename(self.input_path))[0]
        
        progress = QProgressDialog("Convirtiendo audio...", "Cancelar", 0, len(selected_formats), self)
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
                success = convert_audio(self.input_path, output_path, fmt)
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
            try:
                if sys.platform == "win32":
                    os.startfile(original_dir)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", original_dir])
                else:
                    subprocess.Popen(["xdg-open", original_dir])
            except OSError:
                pass
        
        self.accept()
    
    def get_output_paths(self) -> List[str]:
        return self.output_paths


def trim_audio(
    input_path: str,
    output_path: str,
    start_seconds: float,
    end_seconds: float,
    progress_callback: Optional[Callable[[int], None]] = None
) -> bool:
    if not is_ffmpeg_available():
        raise RuntimeError("ffmpeg no está instalado o no está disponible en el PATH")

    duration = end_seconds - start_seconds
    if duration <= 0:
        return False

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_seconds),
        "-i", input_path,
        "-t", str(duration),
        "-c", "copy",
        output_path
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        if progress_callback:
            progress_callback(0)
            for i in range(10):
                time.sleep(0.1)
                progress_callback((i + 1) * 10)

        stdout, stderr = process.communicate(timeout=300)

        if progress_callback:
            progress_callback(100)

        return process.returncode == 0 and os.path.exists(output_path)

    except subprocess.TimeoutExpired:
        process.kill()
        return False
    except Exception:
        return False


class AudioTrimDialog(QDialog):

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.input_format = Path(input_path).suffix.lower()
        self.output_path = None

        self.setWindowTitle("Recortar Audio")
        self.setMinimumWidth(450)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_group = QGroupBox("Archivo de entrada")
        info_layout = QGridLayout(info_group)

        info = get_audio_info(self.input_path)
        self.total_duration = info["duration"]

        info_layout.addWidget(QLabel("Nombre:"), 0, 0)
        info_layout.addWidget(QLabel(info["filename"]), 0, 1)

        info_layout.addWidget(QLabel("Formato:"), 1, 0)
        info_layout.addWidget(QLabel(FORMAT_NAMES.get(self.input_format, self.input_format)), 1, 1)

        if self.total_duration > 0:
            minutes = int(self.total_duration // 60)
            seconds = int(self.total_duration % 60)
            info_layout.addWidget(QLabel("Duración total:"), 2, 0)
            info_layout.addWidget(QLabel(f"{minutes}:{seconds:02d}"), 2, 1)

        layout.addWidget(info_group)

        trim_group = QGroupBox("Rango de recorte")
        trim_layout = QGridLayout(trim_group)

        trim_layout.addWidget(QLabel("Inicio (mm:ss):"), 0, 0)
        start_h = QHBoxLayout()
        self.start_min = QSpinBox()
        self.start_min.setRange(0, 9999)
        self.start_min.setValue(0)
        self.start_min.setSuffix(" min")
        self.start_sec = QSpinBox()
        self.start_sec.setRange(0, 59)
        self.start_sec.setValue(0)
        self.start_sec.setSuffix(" seg")
        start_h.addWidget(self.start_min)
        start_h.addWidget(self.start_sec)
        start_h.addStretch()
        trim_layout.addLayout(start_h, 0, 1)

        trim_layout.addWidget(QLabel("Fin (mm:ss):"), 1, 0)
        end_h = QHBoxLayout()
        self.end_min = QSpinBox()
        self.end_min.setRange(0, 9999)
        self.end_sec = QSpinBox()
        self.end_sec.setRange(0, 59)
        self.end_min.setSuffix(" min")
        self.end_sec.setSuffix(" seg")

        if self.total_duration > 0:
            self.end_min.setValue(int(self.total_duration // 60))
            self.end_sec.setValue(int(self.total_duration % 60))
        else:
            self.end_min.setValue(0)
            self.end_sec.setValue(0)

        end_h.addWidget(self.end_min)
        end_h.addWidget(self.end_sec)
        end_h.addStretch()
        trim_layout.addLayout(end_h, 1, 1)

        layout.addWidget(trim_group)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.trim_button = QPushButton("Recortar")
        self.trim_button.clicked.connect(self._on_trim)
        buttons.addWidget(self.trim_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)
        layout.addStretch()

    def _on_trim(self):
        start_seconds = self.start_min.value() * 60 + self.start_sec.value()
        end_seconds = self.end_min.value() * 60 + self.end_sec.value()

        if end_seconds <= start_seconds:
            QMessageBox.warning(
                self,
                "Rango inválido",
                "El tiempo de fin debe ser mayor al tiempo de inicio."
            )
            return

        original_dir = os.path.dirname(self.input_path)
        original_name = os.path.splitext(os.path.basename(self.input_path))[0]
        suggested_name = f"{original_name}_recortado{self.input_format}"
        suggested_path = os.path.join(original_dir, suggested_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar audio recortado",
            suggested_path,
            f"Audio (*{self.input_format})"
        )
        if not file_path:
            return
        self.output_path = file_path

        progress = QProgressDialog("Recortando audio...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        try:
            def update_progress(value):
                progress.setValue(value)
                QApplication.processEvents()

            success = trim_audio(
                self.input_path,
                self.output_path,
                start_seconds,
                end_seconds,
                update_progress
            )

            progress.setValue(100)

            if success:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Audio recortado correctamente.\nGuardado en:\n{self.output_path}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo recortar el archivo de audio."
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
                f"Error durante el recorte:\n{str(e)}"
            )

    def get_output_path(self) -> Optional[str]:
        return self.output_path
