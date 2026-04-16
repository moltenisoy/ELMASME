"""
Módulo para conversión y manipulación de archivos de imagen.
Incluye redimensionamiento, información y guardado en distintos formatos.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader, QImage
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QComboBox, QCheckBox, QGroupBox, QGridLayout, QSpinBox
)

# Formatos de imagen soportados
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"
}

# Nombres legibles de formatos
FORMAT_NAMES = {
    ".png": "PNG (Portable Network Graphics)",
    ".jpg": "JPEG (Joint Photographic Experts Group)",
    ".jpeg": "JPEG (Joint Photographic Experts Group)",
    ".bmp": "BMP (Bitmap)",
    ".gif": "GIF (Graphics Interchange Format)",
    ".webp": "WEBP (Web Picture Format)",
    ".tif": "TIFF (Tagged Image File Format)",
    ".tiff": "TIFF (Tagged Image File Format)"
}

# Formatos que soportan transparencia
TRANSPARENT_FORMATS = {".png", ".gif", ".webp", ".tif", ".tiff"}


def get_image_info(path: str) -> Dict:
    """Obtiene información de la imagen."""
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "width": 0,
        "height": 0,
        "format": "",
        "has_alpha": False
    }
    
    if os.path.exists(path):
        info["size"] = os.path.getsize(path)
    
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    
    size = reader.size()
    if size.isValid():
        info["width"] = size.width()
        info["height"] = size.height()
    
    info["format"] = reader.format().data().decode().upper() if reader.format() else "Unknown"
    
    # Verificar si tiene canal alpha
    image = reader.read()
    if not image.isNull():
        info["has_alpha"] = image.hasAlphaChannel()
    
    return info


def save_image(
    image: QImage,
    path: str,
    format: Optional[str] = None,
    quality: int = 90
) -> bool:
    """Guarda una imagen en el formato especificado."""
    if image.isNull():
        return False
    
    if format:
        fmt = format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        return image.save(path, fmt, quality)
    else:
        return image.save(path, None, quality)


def resize_image(
    image: QImage,
    width: int,
    height: int,
    keep_aspect: bool = True,
    smooth: bool = True
) -> QImage:
    """Redimensiona una imagen."""
    if image.isNull():
        return QImage()
    
    aspect_mode = Qt.KeepAspectRatio if keep_aspect else Qt.IgnoreAspectRatio
    transform_mode = Qt.SmoothTransformation if smooth else Qt.FastTransformation
    
    return image.scaled(width, height, aspect_mode, transform_mode)


class ImageResizeDialog(QDialog):
    """Diálogo para redimensionar y convertir imágenes."""
    
    def __init__(self, parent=None, current_width=0, current_height=0):
        super().__init__(parent)
        self.setWindowTitle("Cambiar tamaño de imagen")
        self.setMinimumWidth(350)
        
        self.original_width = current_width
        self.original_height = current_height
        self.aspect_ratio = current_width / current_height if current_height > 0 else 1
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        size_group = QGroupBox("Nuevo tamaño")
        size_layout = QGridLayout(size_group)
        
        size_layout.addWidget(QLabel("Ancho:"), 0, 0)
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(self.original_width)
        self.width_input.valueChanged.connect(self._on_width_changed)
        size_layout.addWidget(self.width_input, 0, 1)
        
        size_layout.addWidget(QLabel("Alto:"), 1, 0)
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(self.original_height)
        self.height_input.valueChanged.connect(self._on_height_changed)
        size_layout.addWidget(self.height_input, 1, 1)
        
        self.maintain_aspect = QCheckBox("Mantener relación de aspecto")
        self.maintain_aspect.setChecked(True)
        size_layout.addWidget(self.maintain_aspect, 2, 0, 1, 2)
        
        layout.addWidget(size_group)
        
        format_group = QGroupBox("Convertir formato")
        format_layout = QVBoxLayout(format_group)
        
        self.convert_check = QCheckBox("Convertir a otro formato")
        format_layout.addWidget(self.convert_check)
        
        self.format_combo = QComboBox()
        for ext in sorted(IMAGE_EXTENSIONS):
            self.format_combo.addItem(FORMAT_NAMES.get(ext, ext), ext)
        self.format_combo.setEnabled(False)
        self.convert_check.toggled.connect(self.format_combo.setEnabled)
        format_layout.addWidget(self.format_combo)
        
        layout.addWidget(format_group)
        
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
        
        self.ok_button = QPushButton("Aplicar")
        self.ok_button.clicked.connect(self.accept)
        buttons.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        
        layout.addLayout(buttons)
    
    def _on_width_changed(self):
        if self.maintain_aspect.isChecked():
            new_height = int(self.width_input.value() / self.aspect_ratio)
            self.height_input.blockSignals(True)
            self.height_input.setValue(new_height)
            self.height_input.blockSignals(False)
    
    def _on_height_changed(self):
        if self.maintain_aspect.isChecked():
            new_width = int(self.height_input.value() * self.aspect_ratio)
            self.width_input.blockSignals(True)
            self.width_input.setValue(new_width)
            self.width_input.blockSignals(False)
    
    def get_result(self) -> Dict:
        return {
            "width": self.width_input.value(),
            "height": self.height_input.value(),
            "maintain_aspect": self.maintain_aspect.isChecked(),
            "convert": self.convert_check.isChecked(),
            "format": self.format_combo.currentData(),
            "new_file": self.new_file_radio.isChecked()
        }
