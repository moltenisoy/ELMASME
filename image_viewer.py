
import os
from pathlib import Path
from typing import Dict, List
from PySide6.QtCore import Qt, QRect, QMarginsF
from PySide6.QtGui import (
    QAction, QImageReader, QPixmap, QImage, QKeySequence, QPageLayout, QPageSize,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QDialog, QMessageBox, QFileDialog, QScrollArea, QFrame, QMenu,
    QListWidget, QDialogButtonBox, QComboBox, QCheckBox, QSpinBox,
)
from image_converter import (
    IMAGE_EXTENSIONS,
    FORMAT_NAMES,
    get_image_info,
    save_image,
    resize_image,
    crop_image,
)
from image_dialogs import EditConvertDialog
from image_pan import PanLabel
from image_annotations import AnnotationOverlay


class ImageViewer(QWidget):
    
    def __init__(self):
        super().__init__()
        self.zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
        self.current_zoom_index = 3
        self.fullscreen_window = None
        self.current_path = None
        self._original_image = None
        self._pixmap = QPixmap()
        self._annotation_mode = False
        self._crop_mode = False
        
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
        self.zoom_in_button.setFixedSize(70, 22)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        
        self.zoom_out_button = QToolButton()
        self.zoom_out_button.setText("Zoom -")
        self.zoom_out_button.setFixedSize(70, 22)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        
        self.reset_zoom_button = QToolButton()
        self.reset_zoom_button.setText("100%")
        self.reset_zoom_button.setFixedSize(60, 22)
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        
        self.fullscreen_button = QToolButton()
        self.fullscreen_button.setText("Pantalla completa")
        self.fullscreen_button.setFixedSize(120, 22)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        
        self.edit_convert_button = QToolButton()
        self.edit_convert_button.setText("Edición y Conversión")
        self.edit_convert_button.setFixedSize(180, 22)
        self.edit_convert_button.clicked.connect(self.show_edit_convert_dialog)
        
        self.crop_button = QToolButton()
        self.crop_button.setText("Recortar")
        self.crop_button.setFixedSize(100, 22)
        self.crop_button.clicked.connect(self._toggle_crop_mode)
        
        self.annotate_button = QToolButton()
        self.annotate_button.setText("Anotar")
        self.annotate_button.setFixedSize(100, 22)
        self.annotate_button.clicked.connect(self.toggle_annotation_mode)
        
        self.export_pdf_button = QToolButton()
        self.export_pdf_button.setText("Exportar a PDF")
        self.export_pdf_button.setFixedSize(120, 22)
        self.export_pdf_button.setToolTip("Generar un PDF con imágenes seleccionadas")
        self.export_pdf_button.clicked.connect(self._export_to_pdf)
        
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)
        toolbar.addWidget(self.zoom_out_button)
        toolbar.addWidget(self.reset_zoom_button)
        toolbar.addWidget(self.zoom_in_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.fullscreen_button)
        toolbar.addWidget(self.edit_convert_button)
        toolbar.addWidget(self.crop_button)
        toolbar.addWidget(self.annotate_button)
        toolbar.addWidget(self.export_pdf_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(toolbar)
        layout.addWidget(self.scroll_area, 1)

        copy_action = QAction(self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_image)
        self.addAction(copy_action)
    
    def load_file(self, path: str):
        if self._crop_mode:
            self._toggle_crop_mode()
        if self._annotation_mode:
            self.toggle_annotation_mode()
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
    
    def show_edit_convert_dialog(self):
        w = self._original_image.width() if self._original_image else 0
        h = self._original_image.height() if self._original_image else 0
        dialog = EditConvertDialog(self, w, h)
        if dialog.exec() == QDialog.Accepted:
            if self._original_image is not None and self.current_path is not None:
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
    
    def _toggle_crop_mode(self):
        if self._original_image is None or self.current_path is None:
            return
        self._crop_mode = not self._crop_mode
        self.label._crop_mode = self._crop_mode

        if self._crop_mode:
            if self._annotation_mode:
                self.toggle_annotation_mode()
            self.label.setCursor(Qt.CrossCursor)
            self.label.clear_selection()
            self.crop_button.setStyleSheet(
                "QToolButton { background: rgba(249,115,22,0.4); border: 1px solid #fb923c; border-radius: 4px; color: #e5e7eb; }"
            )
        else:
            self.label.setCursor(Qt.OpenHandCursor)
            self.label.clear_selection()
            self.crop_button.setStyleSheet("")

    def _on_crop_selection_complete(self):
        sel = QRect(self.label._sel_start, self.label._sel_end).normalized()
        if sel.width() < 5 or sel.height() < 5:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 16px; }
            QMenu::item:selected { background: #334155; }
        """)
        crop_action = menu.addAction("Recortar imagen actual")
        save_action = menu.addAction("Guardar selección como nueva imagen")

        action = menu.exec(self.label.mapToGlobal(self.label._sel_end))

        if action == crop_action:
            self._crop_to_selection(sel)
        elif action == save_action:
            self._save_selection_as_new(sel)

        self.label.clear_selection()

    def _image_rect_from_selection(self, sel_rect):
        zoom = self.zoom_levels[self.current_zoom_index]
        x = max(0, int(sel_rect.x() / zoom))
        y = max(0, int(sel_rect.y() / zoom))
        w = max(1, int(sel_rect.width() / zoom))
        h = max(1, int(sel_rect.height() / zoom))
        img_w = self._original_image.width()
        img_h = self._original_image.height()
        x = min(x, img_w - 1)
        y = min(y, img_h - 1)
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        return x, y, w, h

    def _crop_to_selection(self, sel_rect):
        if self._original_image is None:
            return
        x, y, w, h = self._image_rect_from_selection(sel_rect)
        cropped = crop_image(self._original_image, x, y, w, h)
        if cropped.isNull():
            QMessageBox.critical(self, "Error", "No se pudo recortar la imagen.")
            return
        self._original_image = cropped
        self._pixmap = QPixmap.fromImage(cropped)
        self.label.reset_pan()
        self._update_scaled()
        if save_image(cropped, self.current_path):
            QMessageBox.information(self, "Éxito", "Imagen recortada correctamente.")
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar la imagen recortada.")
        self._toggle_crop_mode()

    def _save_selection_as_new(self, sel_rect):
        if self._original_image is None:
            return
        x, y, w, h = self._image_rect_from_selection(sel_rect)
        cropped = crop_image(self._original_image, x, y, w, h)
        if cropped.isNull():
            QMessageBox.critical(self, "Error", "No se pudo recortar la imagen.")
            return
        original_dir = os.path.dirname(self.current_path) if self.current_path else ""
        filters = ";;".join(
            f"{FORMAT_NAMES.get(ext, ext)} (*{ext})" for ext in sorted(IMAGE_EXTENSIONS)
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar selección como nueva imagen",
            os.path.join(original_dir, "seleccion"),
            filters,
        )
        if file_path:
            ext = Path(file_path).suffix.lower()
            fmt = ext.lstrip(".").upper() if ext else None
            if fmt == "JPEG":
                fmt = "JPG"
            if save_image(cropped, file_path, fmt):
                QMessageBox.information(self, "Éxito", f"Selección guardada en:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar la selección.")
        self._toggle_crop_mode()
    
    def toggle_annotation_mode(self):
        self._annotation_mode = not self._annotation_mode
        if self._annotation_mode:
            if self._crop_mode:
                self._toggle_crop_mode()
            if not hasattr(self, '_annotation_overlay') or self._annotation_overlay is None:
                self._annotation_overlay = AnnotationOverlay(self.scroll_area.viewport())
                self._annotation_overlay.annotations_saved.connect(self._on_annotations_saved)
            self._annotation_overlay.setGeometry(self.scroll_area.viewport().rect())
            self._annotation_overlay.show()
            self._annotation_overlay.raise_()
            self.annotate_button.setStyleSheet(
                "QToolButton { background: rgba(59,130,246,0.4); border: 1px solid #60a5fa; border-radius: 4px; color: #e5e7eb; }"
            )
        else:
            if hasattr(self, '_annotation_overlay') and self._annotation_overlay is not None:
                self._annotation_overlay.hide()
            self.annotate_button.setStyleSheet("")

    def _on_annotations_saved(self, annotated_image):
        if self._original_image is None or self.current_path is None:
            return
        from image_annotations import AnnotationOverlay
        if hasattr(self, '_annotation_overlay') and self._annotation_overlay is not None:
            result = self._annotation_overlay.burn_to_image(self._original_image)
            original_dir = os.path.dirname(self.current_path)
            original_name = os.path.splitext(os.path.basename(self.current_path))[0]
            ext = os.path.splitext(self.current_path)[1]
            new_path = os.path.join(original_dir, f"{original_name}_annotated{ext}")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar imagen anotada", new_path,
                f"Images (*{ext})"
            )
            if file_path:
                if save_image(result, file_path):
                    QMessageBox.information(self, "Éxito", f"Imagen anotada guardada en:\n{file_path}")
                    self._annotation_overlay.clear()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo guardar la imagen anotada.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled()
        if hasattr(self, '_annotation_overlay') and self._annotation_overlay is not None and self._annotation_overlay.isVisible():
            self._annotation_overlay.setGeometry(self.scroll_area.viewport().rect())

    def _export_to_pdf(self):
        dialog = ExportImagesToPdfDialog(
            current_image_path=self.current_path,
            parent=self
        )
        dialog.exec()


class ExportImagesToPdfDialog(QDialog):

    _DIALOG_STYLE = """
        QDialog { background: #1e293b; }
        QLabel  { color: #e5e7eb; }
        QPushButton {
            background: rgba(59,130,246,0.2);
            border: 1px solid rgba(59,130,246,0.4);
            border-radius: 6px;
            padding: 6px 16px;
            color: #60a5fa;
            font-weight: 500;
        }
        QPushButton:hover { background: rgba(59,130,246,0.35); }
        QListWidget {
            background: #0f172a;
            color: #e5e7eb;
            border: 1px solid rgba(148,163,184,0.3);
            border-radius: 4px;
        }
        QComboBox {
            background: #0f172a;
            color: #e5e7eb;
            border: 1px solid rgba(148,163,184,0.3);
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox QAbstractItemView {
            background: #0f172a; color: #e5e7eb;
            selection-background-color: rgba(59,130,246,0.3);
        }
        QCheckBox { color: #e5e7eb; }
        QSpinBox {
            background: #0f172a;
            color: #e5e7eb;
            border: 1px solid rgba(148,163,184,0.3);
            border-radius: 4px;
            padding: 2px 4px;
        }
    """

    def __init__(self, current_image_path: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar imágenes a PDF")
        self.setMinimumSize(560, 480)
        self._current_image_path = current_image_path
        self._build_ui()
        if current_image_path and os.path.isfile(current_image_path):
            self.list_widget.addItem(current_image_path)

    def _build_ui(self):
        self.setStyleSheet(self._DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Imágenes a incluir en el PDF:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.list_widget)

        list_btns = QHBoxLayout()

        add_btn = QPushButton("➕ Agregar imágenes")
        add_btn.clicked.connect(self._on_add)
        list_btns.addWidget(add_btn)

        remove_btn = QPushButton("➖ Quitar selección")
        remove_btn.clicked.connect(self._on_remove)
        list_btns.addWidget(remove_btn)

        up_btn = QPushButton("⬆ Subir")
        up_btn.clicked.connect(self._on_move_up)
        list_btns.addWidget(up_btn)

        down_btn = QPushButton("⬇ Bajar")
        down_btn.clicked.connect(self._on_move_down)
        list_btns.addWidget(down_btn)

        layout.addLayout(list_btns)

        options_layout = QHBoxLayout()

        options_layout.addWidget(QLabel("Tamaño de página:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("A4", QPageSize.A4)
        self.page_size_combo.addItem("Letter", QPageSize.Letter)
        self.page_size_combo.addItem("A3", QPageSize.A3)
        self.page_size_combo.addItem("A5", QPageSize.A5)
        options_layout.addWidget(self.page_size_combo)

        options_layout.addSpacing(16)
        options_layout.addWidget(QLabel("Margen (mm):"))
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setValue(10)
        options_layout.addWidget(self.margin_spin)

        options_layout.addStretch()
        self.fit_check = QCheckBox("Ajustar imagen a la página")
        self.fit_check.setChecked(True)
        options_layout.addWidget(self.fit_check)

        layout.addLayout(options_layout)

        one_per_page_layout = QHBoxLayout()
        self.one_per_page_check = QCheckBox("Una imagen por página")
        self.one_per_page_check.setChecked(True)
        one_per_page_layout.addWidget(self.one_per_page_check)
        one_per_page_layout.addStretch()
        layout.addLayout(one_per_page_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_add(self):
        img_filter = "Imágenes (" + " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS)) + ")"
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "", f"{img_filter};;Todos los archivos (*.*)"
        )
        for p in paths:
            self.list_widget.addItem(p)

    def _on_remove(self):
        for item in reversed(self.list_widget.selectedItems()):
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def _on_move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _on_move_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def _on_accept(self):
        count = self.list_widget.count()
        if count == 0:
            QMessageBox.warning(self, "Atención", "Debe agregar al menos una imagen.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", "", "PDF (*.pdf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        image_paths = [self.list_widget.item(i).text() for i in range(count)]
        page_size_id = self.page_size_combo.currentData()
        margin_mm = self.margin_spin.value()
        fit_to_page = self.fit_check.isChecked()
        one_per_page = self.one_per_page_check.isChecked()

        try:
            self._generate_pdf(
                image_paths, save_path, page_size_id, margin_mm,
                fit_to_page, one_per_page
            )
            QMessageBox.information(
                self, "Éxito", f"PDF generado correctamente:\n{save_path}"
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(
                self, "Error", f"No se pudo generar el PDF:\n{exc}"
            )

    @staticmethod
    def _generate_pdf(
        image_paths: List[str],
        output_path: str,
        page_size_id,
        margin_mm: int,
        fit_to_page: bool,
        one_per_page: bool,
    ):
        import fitz

        page_size_map = {
            QPageSize.A4: fitz.paper_size("a4"),
            QPageSize.Letter: fitz.paper_size("letter"),
            QPageSize.A3: fitz.paper_size("a3"),
            QPageSize.A5: fitz.paper_size("a5"),
        }
        pw, ph = page_size_map.get(page_size_id, fitz.paper_size("a4"))

        margin_pt = margin_mm * 72 / 25.4

        doc = fitz.open()

        for img_path in image_paths:
            if not os.path.isfile(img_path):
                continue

            page = doc.new_page(width=pw, height=ph)

            usable_w = pw - 2 * margin_pt
            usable_h = ph - 2 * margin_pt

            if usable_w <= 0 or usable_h <= 0:
                usable_w = pw
                usable_h = ph
                margin_pt = 0

            img_doc = fitz.open(img_path)
            if img_doc.page_count == 0:
                img_doc.close()
                continue

            img_page = img_doc[0]
            img_rect = img_page.rect
            img_w = img_rect.width
            img_h = img_rect.height

            if fit_to_page and (img_w > 0 and img_h > 0):
                scale_x = usable_w / img_w
                scale_y = usable_h / img_h
                scale = min(scale_x, scale_y)
                final_w = img_w * scale
                final_h = img_h * scale
            else:
                final_w = min(img_w, usable_w)
                final_h = min(img_h, usable_h)

            x0 = margin_pt + (usable_w - final_w) / 2
            y0 = margin_pt + (usable_h - final_h) / 2

            rect = fitz.Rect(x0, y0, x0 + final_w, y0 + final_h)
            page.insert_image(rect, filename=img_path)
            img_doc.close()

        if len(doc) == 0:
            doc.close()
            raise ValueError("No se pudo agregar ninguna imagen al PDF.")

        doc.save(output_path)
        doc.close()
