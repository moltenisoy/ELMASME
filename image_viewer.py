
import os
from pathlib import Path
from typing import Dict, Tuple
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QAction, QImageReader, QPixmap, QImage, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QDialog, QMessageBox, QFileDialog, QScrollArea, QFrame
)
from image_converter import (
    IMAGE_EXTENSIONS,
    FORMAT_NAMES,
    get_image_info,
    save_image,
    resize_image,
    ImageResizeDialog,
)


class PanLabel(QLabel):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._last_pos = QPoint()
        self._offset_x = 0
        self._offset_y = 0
        self._max_offset_x = 0
        self._max_offset_y = 0
        self._image_viewer = None
        self.setCursor(Qt.OpenHandCursor)
    
    def set_pan_limits(self, max_offset_x: int, max_offset_y: int):
        self._max_offset_x = max(0, max_offset_x)
        self._max_offset_y = max(0, max_offset_y)
        self._clamp_offset()
    
    def _clamp_offset(self):
        self._offset_x = max(-self._max_offset_x, min(self._max_offset_x, self._offset_x))
        self._offset_y = max(-self._max_offset_y, min(self._max_offset_y, self._offset_y))
    
    def reset_pan(self):
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
            if self._image_viewer:
                self._image_viewer.update_pixmap_position()
        super().mouseMoveEvent(event)


class ImageViewer(QWidget):
    
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
        
        self.label = PanLabel()
        self.label._image_viewer = self
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background: transparent;")
        
        container = QFrame()
        container.setStyleSheet("background: #111827; border-radius: 14px;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.label)
        
        self.scroll_area.setWidget(container)
        
        self.zoom_in_button = QToolButton()
        self.zoom_in_button.setText("Zoom +")
        self.zoom_in_button.setFixedSize(QSize(70, 22))
        self.zoom_in_button.clicked.connect(self.zoom_in)
        
        self.zoom_out_button = QToolButton()
        self.zoom_out_button.setText("Zoom -")
        self.zoom_out_button.setFixedSize(QSize(70, 22))
        self.zoom_out_button.clicked.connect(self.zoom_out)
        
        self.reset_zoom_button = QToolButton()
        self.reset_zoom_button.setText("100%")
        self.reset_zoom_button.setFixedSize(QSize(60, 22))
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        
        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.setFixedSize(QSize(120, 22))
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        
        self.resize_button = QToolButton()
        self.resize_button.setText("Redimensionar")
        self.resize_button.setFixedSize(QSize(100, 22))
        self.resize_button.clicked.connect(self.show_resize_dialog)
        
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)
        controls.addStretch(1)
        controls.addWidget(self.zoom_out_button)
        controls.addWidget(self.reset_zoom_button)
        controls.addWidget(self.zoom_in_button)
        controls.addWidget(self.fullscreen_button)
        controls.addWidget(self.resize_button)
        controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.scroll_area, 1)
        layout.addLayout(controls)

        copy_action = QAction(self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_image)
        self.addAction(copy_action)
    
    def load_file(self, path: str):
        self.current_path = path
        ext = Path(path).suffix.lower()
        if ext in (".heif", ".heic", ".avif"):
            try:
                from PIL import Image as PILImage
                pil_img = PILImage.open(path).convert("RGBA")
                data = pil_img.tobytes("raw", "RGBA")
                self._original_image = QImage(data, pil_img.width, pil_img.height, pil_img.width * 4, QImage.Format_RGBA8888).copy()
                self._pixmap = QPixmap.fromImage(self._original_image)
                self.current_zoom_index = 3
                self.label.reset_pan()
                self._update_scaled()
                return
            except (ImportError, Exception):
                pass
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        self._original_image = reader.read()
        self._pixmap = QPixmap.fromImage(self._original_image)
        self.current_zoom_index = 3
        self.label.reset_pan()
        self._update_scaled()
    
    def keyPressEvent(self, event):
        if self._pixmap.isNull():
            return
        
        step = 50
        
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
        if self._pixmap.isNull():
            self.label.clear()
            self.label.setText("No se pudo mostrar la imagen.")
            return
        
        zoom = self.zoom_levels[self.current_zoom_index]
        
        scaled_width = int(self._pixmap.width() * zoom)
        scaled_height = int(self._pixmap.height() * zoom)
        
        scaled = self._pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        
        self.label.setPixmap(scaled)
        
        viewport_width = self.scroll_area.viewport().width()
        viewport_height = self.scroll_area.viewport().height()
        
        max_offset_x = max(0, (scaled_width - viewport_width) // 2)
        max_offset_y = max(0, (scaled_height - viewport_height) // 2)
        
        self.label.set_pan_limits(max_offset_x, max_offset_y)
        self.update_pixmap_position()
    
    def update_pixmap_position(self):
        if self.label.pixmap() is None:
            return
        
        offset_x, offset_y = self.label.get_offset()
        
        pixmap = self.label.pixmap()
        container = self.scroll_area.widget()
        
        container_width = container.width()
        container_height = container.height()
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()
        
        x = (container_width - pixmap_width) // 2 + offset_x
        y = (container_height - pixmap_height) // 2 + offset_y
        
        self.label.setGeometry(x, y, pixmap_width, pixmap_height)
    
    def zoom_in(self):
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            self._update_scaled()
    
    def zoom_out(self):
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            if self.current_zoom_index == 3:
                self.label.reset_pan()
            self._update_scaled()
    
    def reset_zoom(self):
        self.current_zoom_index = 3
        self.label.reset_pan()
        self._update_scaled()
    
    def copy_image(self):
        from PySide6.QtWidgets import QApplication
        if not self._pixmap.isNull():
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self._pixmap)
    
    def toggle_fullscreen(self):
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
        if self.fullscreen_window:
            self.fullscreen_window.close()
    
    def show_resize_dialog(self):
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
        if self._original_image is None:
            return
        
        new_image = resize_image(
            self._original_image,
            result["width"],
            result["height"],
            result.get("maintain_aspect", True),
            interpolation=result.get("interpolation", "bilinear")
        )
        
        output_format = result["format"].upper() if result["convert"] else None
        if output_format == "JPEG":
            output_format = "JPG"
        
        if result["new_file"]:
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
            
            self.load_file(self.current_path)
