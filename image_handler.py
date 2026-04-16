"""
Módulo para manejo de archivos de imagen.
Incluye visualización, zoom, desplazamiento (pan) y conversión entre formatos.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QAction, QImageReader, QPixmap, QImage, QImageWriter, QKeySequence, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QSizePolicy, QDialog, QComboBox, QCheckBox, QGroupBox, QGridLayout,
    QMessageBox, QFileDialog, QSpinBox, QScrollArea, QFrame
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


class PanLabel(QLabel):
    """Label que soporta pan/drag con el mouse."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._last_pos = QPoint()
        self._offset_x = 0
        self._offset_y = 0
        self._max_offset_x = 0
        self._max_offset_y = 0
        self.setCursor(Qt.OpenHandCursor)
    
    def set_pan_limits(self, max_offset_x: int, max_offset_y: int):
        """Establece los límites de desplazamiento."""
        self._max_offset_x = max(0, max_offset_x)
        self._max_offset_y = max(0, max_offset_y)
        self._clamp_offset()
    
    def _clamp_offset(self):
        """Restringe el offset dentro de los límites."""
        self._offset_x = max(-self._max_offset_x, min(self._max_offset_x, self._offset_x))
        self._offset_y = max(-self._max_offset_y, min(self._max_offset_y, self._offset_y))
    
    def reset_pan(self):
        """Resetea el desplazamiento."""
        self._offset_x = 0
        self._offset_y = 0
        self._dragging = False
    
    def get_offset(self) -> Tuple[int, int]:
        return (self._offset_x, self._offset_y)
    
    def set_offset(self, x: int, y: int):
        self._offset_x = x
        self._offset_y = y
        self._clamp_offset()
    
    def pan(self, dx: int, dy: int):
        """Desplaza la imagen por el delta especificado."""
        self._offset_x += dx
        self._offset_y += dy
        self._clamp_offset()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.pos() - self._last_pos
            self.pan(delta.x(), delta.y())
            self._last_pos = event.pos()
            self.parent().update_pixmap_position()
        super().mouseMoveEvent(event)


class ImageViewer(QWidget):
    """Visor de imágenes con zoom, pan (arrastre) y conversión."""
    
    def __init__(self):
        super().__init__()
        self.zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
        self.current_zoom_index = 3
        self.fullscreen_window = None
        self.current_path = None
        self._original_image = None
        self._pixmap = QPixmap()
        
        self._build_ui()
    
    def _build_ui(self):
        # ScrollArea para contener la imagen con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: #111827;
                border-radius: 14px;
                border: none;
            }
            QScrollBar:horizontal, QScrollBar:vertical {
                background: #1e293b;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
        """)
        
        # Label para mostrar la imagen con capacidad de pan
        self.label = PanLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background: transparent;")
        
        container = QFrame()
        container.setStyleSheet("background: #111827; border-radius: 14px;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.label)
        
        self.scroll_area.setWidget(container)
        
        # Botón Zoom +
        self.zoom_in_button = QToolButton()
        self.zoom_in_button.setText("Zoom +")
        self.zoom_in_button.setToolTip("Aumentar zoom")
        self.zoom_in_button.setFixedSize(QSize(70, 32))
        self.zoom_in_button.clicked.connect(self.zoom_in)
        
        # Botón Zoom -
        self.zoom_out_button = QToolButton()
        self.zoom_out_button.setText("Zoom -")
        self.zoom_out_button.setToolTip("Reducir zoom")
        self.zoom_out_button.setFixedSize(QSize(70, 32))
        self.zoom_out_button.clicked.connect(self.zoom_out)
        
        # Botón Reset Zoom
        self.reset_zoom_button = QToolButton()
        self.reset_zoom_button.setText("100%")
        self.reset_zoom_button.setToolTip("Restablecer zoom")
        self.reset_zoom_button.setFixedSize(QSize(60, 32))
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        
        # Botón Pantalla completa
        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.setToolTip("Ver en pantalla completa")
        self.fullscreen_button.setFixedSize(QSize(120, 32))
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        
        # Botón Redimensionar
        self.resize_button = QToolButton()
        self.resize_button.setText("Redimensionar")
        self.resize_button.setToolTip("Cambiar tamaño/convertir formato")
        self.resize_button.setFixedSize(QSize(100, 32))
        self.resize_button.clicked.connect(self.show_resize_dialog)
        
        # Layout de controles
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(10)
        controls.addStretch(1)
        controls.addWidget(self.zoom_out_button)
        controls.addWidget(self.reset_zoom_button)
        controls.addWidget(self.zoom_in_button)
        controls.addWidget(self.fullscreen_button)
        controls.addWidget(self.resize_button)
        controls.addStretch(1)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.scroll_area, 1)
        layout.addLayout(controls)
        
        # Atajo de teclado para copiar
        copy_action = QAction(self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_image)
        self.addAction(copy_action)
    
    def load_file(self, path: str):
        """Carga un archivo de imagen."""
        self.current_path = path
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        self._original_image = reader.read()
        self._pixmap = QPixmap.fromImage(self._original_image)
        self.current_zoom_index = 3
        self.label.reset_pan()
        self._update_scaled()
    
    def keyPressEvent(self, event):
        """Maneja teclas de dirección para pan cuando hay zoom."""
        if self._pixmap.isNull():
            return
        
        step = 50  # Píxeles de desplazamiento por tecla
        
        if event.key() == Qt.Key_Left:
            self.label.pan(step, 0)
            self.update_pixmap_position()
        elif event.key() == Qt.Key_Right:
            self.label.pan(-step, 0)
            self.update_pixmap_position()
        elif event.key() == Qt.Key_Up:
            self.label.pan(0, step)
            self.update_pixmap_position()
        elif event.key() == Qt.Key_Down:
            self.label.pan(0, -step)
            self.update_pixmap_position()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled()
    
    def _update_scaled(self):
        """Actualiza la imagen escalada según el zoom actual."""
        if self._pixmap.isNull():
            self.label.clear()
            self.label.setText("No se pudo mostrar la imagen.")
            return
        
        zoom = self.zoom_levels[self.current_zoom_index]
        
        # Calcular tamaño escalado
        scaled_width = int(self._pixmap.width() * zoom)
        scaled_height = int(self._pixmap.height() * zoom)
        
        scaled = self._pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        
        self.label.setPixmap(scaled)
        
        # Configurar límites de pan
        viewport_width = self.scroll_area.viewport().width()
        viewport_height = self.scroll_area.viewport().height()
        
        max_offset_x = max(0, (scaled_width - viewport_width) // 2)
        max_offset_y = max(0, (scaled_height - viewport_height) // 2)
        
        self.label.set_pan_limits(max_offset_x, max_offset_y)
        self.update_pixmap_position()
    
    def update_pixmap_position(self):
        """Actualiza la posición de la imagen según el offset de pan."""
        if self.label.pixmap() is None:
            return
        
        offset_x, offset_y = self.label.get_offset()
        
        # Aplicar margen para centrar con el offset
        pixmap = self.label.pixmap()
        container = self.scroll_area.widget()
        
        container_width = container.width()
        container_height = container.height()
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()
        
        # Calcular posición centrada con offset
        x = (container_width - pixmap_width) // 2 + offset_x
        y = (container_height - pixmap_height) // 2 + offset_y
        
        self.label.setGeometry(x, y, pixmap_width, pixmap_height)
    
    def zoom_in(self):
        """Aumenta el zoom."""
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            self._update_scaled()
    
    def zoom_out(self):
        """Reduce el zoom."""
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            if self.current_zoom_index == 3:  # 1.0x
                self.label.reset_pan()
            self._update_scaled()
    
    def reset_zoom(self):
        """Restablece el zoom al 100%."""
        self.current_zoom_index = 3
        self.label.reset_pan()
        self._update_scaled()
    
    def copy_image(self):
        """Copia la imagen al portapapeles."""
        from PySide6.QtWidgets import QApplication
        if not self._pixmap.isNull():
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self._pixmap)
    
    def toggle_fullscreen(self):
        """Activa/desactiva pantalla completa."""
        if self.fullscreen_window is None:
            self.fullscreen_window = QLabel()
            self.fullscreen_window.setAlignment(Qt.AlignCenter)
            self.fullscreen_window.setStyleSheet("background:#000000;")
            self.fullscreen_window.setWindowState(Qt.WindowFullScreen)
            self.fullscreen_window.mousePressEvent = lambda e: self.exit_fullscreen()
            self.fullscreen_window.keyPressEvent = lambda e: (
                self.exit_fullscreen() if e.key() == Qt.Key_Escape else None
            )
        
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.fullscreen_window.screen().size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.fullscreen_window.setPixmap(scaled)
        
        self.fullscreen_window.show()
    
    def exit_fullscreen(self):
        """Sale del modo pantalla completa."""
        if self.fullscreen_window:
            self.fullscreen_window.close()
    
    def show_resize_dialog(self):
        """Muestra el diálogo de redimensionamiento."""
        if self._original_image is None or self.current_path is None:
            return
        
        dialog = ImageResizeDialog(
            self,
            self._original_image.width(),
            self._original_image.height()
        )
        
        if dialog.exec() == QDialog.Accepted:
            result = dialog.get_result()
            self.apply_transform(result)
    
    def apply_transform(self, result: Dict):
        """Aplica las transformaciones a la imagen."""
        if self._original_image is None:
            return
        
        # Redimensionar
        new_image = resize_image(
            self._original_image,
            result["width"],
            result["height"],
            result.get("maintain_aspect", True)
        )
        
        # Determinar formato de salida
        output_format = result["format"].upper() if result["convert"] else None
        if output_format == "JPEG":
            output_format = "JPG"
        
        if result["new_file"]:
            # Guardar como nuevo archivo
            original_dir = os.path.dirname(self.current_path)
            original_name = os.path.splitext(os.path.basename(self.current_path))[0]
            ext = output_format.lower() if output_format else os.path.splitext(self.current_path)[1][1:]
            if ext == "jpeg":
                ext = "jpg"
            
            new_path = os.path.join(original_dir, f"{original_name}_resized.{ext}")
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar imagen",
                new_path,
                f"Images (*.{ext})"
            )
            
            if file_path:
                if save_image(new_image, file_path, output_format):
                    QMessageBox.information(self, "Éxito", f"Imagen guardada en:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Error", "No se pudo guardar la imagen.")
        else:
            # Sobrescribir archivo original
            if output_format:
                temp_path = os.path.splitext(self.current_path)[0] + f"_temp.{output_format.lower()}"
                if save_image(new_image, temp_path, output_format):
                    os.remove(self.current_path)
                    final_path = os.path.splitext(self.current_path)[0] + f".{output_format.lower()}"
                    os.rename(temp_path, final_path)
                    self.current_path = final_path
                    QMessageBox.information(self, "Éxito", "Imagen actualizada correctamente.")
            else:
                if save_image(new_image, self.current_path):
                    QMessageBox.information(self, "Éxito", "Imagen actualizada correctamente.")
            
            # Recargar la imagen
            self.load_file(self.current_path)
