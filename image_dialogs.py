import os
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QComboBox, QCheckBox, QGroupBox, QGridLayout, QSpinBox,
    QFileDialog, QTabWidget, QRadioButton, QWidget,
)
from image_converter import (
    IMAGE_EXTENSIONS, FORMAT_NAMES, INTERPOLATION_NAMES,
    save_image, resize_image,
)


class ImageResizeDialog(QDialog):

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

        size_layout.addWidget(QLabel("Interpolación:"), 3, 0)
        self.interpolation_combo = QComboBox()
        for key, name in INTERPOLATION_NAMES.items():
            self.interpolation_combo.addItem(name, key)
        self.interpolation_combo.setCurrentIndex(1)
        size_layout.addWidget(self.interpolation_combo, 3, 1)

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
            "new_file": self.new_file_radio.isChecked(),
            "interpolation": self.interpolation_combo.currentData()
        }


class ImageCropDialog(QDialog):

    ASPECT_RATIOS = {
        "Libre": None,
        "16:9": 16 / 9,
        "4:3": 4 / 3,
        "1:1": 1.0,
    }

    def __init__(self, parent=None, image: Optional[QImage] = None):
        super().__init__(parent)
        self.setWindowTitle("Recortar imagen")
        self.setMinimumSize(500, 450)

        self._image = image or QImage()
        self._aspect_ratio: Optional[float] = None
        self._updating = False

        self._build_ui()
        self._init_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumHeight(200)
        self._preview_label.setStyleSheet("background: #111827; border-radius: 8px;")
        layout.addWidget(self._preview_label, 1)

        mode_group = QGroupBox("Modo de recorte")
        mode_layout = QHBoxLayout(mode_group)
        self._mode_combo = QComboBox()
        for name in self.ASPECT_RATIOS:
            self._mode_combo.addItem(name)
        self._mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(QLabel("Relación:"))
        mode_layout.addWidget(self._mode_combo)
        layout.addWidget(mode_group)

        coord_group = QGroupBox("Coordenadas de recorte")
        coord_layout = QGridLayout(coord_group)

        self._x_spin = QSpinBox()
        self._y_spin = QSpinBox()
        self._w_spin = QSpinBox()
        self._h_spin = QSpinBox()

        for spin in (self._x_spin, self._y_spin, self._w_spin, self._h_spin):
            spin.setRange(0, 10000)

        coord_layout.addWidget(QLabel("X:"), 0, 0)
        coord_layout.addWidget(self._x_spin, 0, 1)
        coord_layout.addWidget(QLabel("Y:"), 0, 2)
        coord_layout.addWidget(self._y_spin, 0, 3)
        coord_layout.addWidget(QLabel("Ancho:"), 1, 0)
        coord_layout.addWidget(self._w_spin, 1, 1)
        coord_layout.addWidget(QLabel("Alto:"), 1, 2)
        coord_layout.addWidget(self._h_spin, 1, 3)

        self._x_spin.valueChanged.connect(self._on_coords_changed)
        self._y_spin.valueChanged.connect(self._on_coords_changed)
        self._w_spin.valueChanged.connect(self._on_width_spin_changed)
        self._h_spin.valueChanged.connect(self._on_height_spin_changed)

        layout.addWidget(coord_group)

        buttons = QHBoxLayout()
        buttons.addStretch()
        ok_btn = QPushButton("Aceptar")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _init_values(self):
        if self._image.isNull():
            return
        w = self._image.width()
        h = self._image.height()
        self._x_spin.setRange(0, max(0, w - 1))
        self._y_spin.setRange(0, max(0, h - 1))
        self._w_spin.setRange(1, w)
        self._h_spin.setRange(1, h)
        self._x_spin.setValue(0)
        self._y_spin.setValue(0)
        self._w_spin.setValue(w)
        self._h_spin.setValue(h)
        self._update_preview()

    def _on_mode_changed(self, text: str):
        self._aspect_ratio = self.ASPECT_RATIOS.get(text)
        if self._aspect_ratio is not None:
            self._updating = True
            new_h = max(1, int(self._w_spin.value() / self._aspect_ratio))
            img_h = self._image.height() if not self._image.isNull() else 10000
            if self._y_spin.value() + new_h > img_h:
                new_h = img_h - self._y_spin.value()
                new_w = max(1, int(new_h * self._aspect_ratio))
                self._w_spin.setValue(new_w)
            self._h_spin.setValue(new_h)
            self._updating = False
            self._update_preview()

    def _on_width_spin_changed(self):
        if self._updating:
            return
        if self._aspect_ratio is not None:
            self._updating = True
            new_h = max(1, int(self._w_spin.value() / self._aspect_ratio))
            self._h_spin.setValue(new_h)
            self._updating = False
        self._update_preview()

    def _on_height_spin_changed(self):
        if self._updating:
            return
        if self._aspect_ratio is not None:
            self._updating = True
            new_w = max(1, int(self._h_spin.value() * self._aspect_ratio))
            self._w_spin.setValue(new_w)
            self._updating = False
        self._update_preview()

    def _on_coords_changed(self):
        if not self._updating:
            self._update_preview()

    def _update_preview(self):
        if self._image.isNull():
            return
        x = self._x_spin.value()
        y = self._y_spin.value()
        w = self._w_spin.value()
        h = self._h_spin.value()
        cropped = self._image.copy(x, y, w, h)
        pix = QPixmap.fromImage(cropped)
        label_size = self._preview_label.size()
        scaled = pix.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._preview_label.setPixmap(scaled)

    def get_result(self) -> Dict:
        return {
            "x": self._x_spin.value(),
            "y": self._y_spin.value(),
            "width": self._w_spin.value(),
            "height": self._h_spin.value(),
        }


class BatchConvertDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversión por lotes")
        self.setMinimumWidth(450)
        self._files: list = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QDialog { background: #1e293b; color: #e2e8f0; }
            QGroupBox { color: #e2e8f0; border: 1px solid #334155; border-radius: 6px;
                         margin-top: 10px; padding-top: 14px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QLabel { color: #e2e8f0; }
            QPushButton { background: #334155; color: #e2e8f0; border: 1px solid #475569;
                          border-radius: 4px; padding: 5px 12px; }
            QPushButton:hover { background: #475569; }
            QSpinBox, QComboBox { background: #0f172a; color: #e2e8f0;
                                  border: 1px solid #334155; border-radius: 4px; padding: 3px; }
        """)

        files_group = QGroupBox("Archivos de entrada")
        files_layout = QVBoxLayout(files_group)
        self._files_label = QLabel("Ningún archivo seleccionado")
        files_layout.addWidget(self._files_label)
        select_btn = QPushButton("Seleccionar archivos…")
        select_btn.clicked.connect(self._select_files)
        files_layout.addWidget(select_btn)
        layout.addWidget(files_group)

        options_group = QGroupBox("Opciones de conversión")
        options_layout = QGridLayout(options_group)

        options_layout.addWidget(QLabel("Formato destino:"), 0, 0)
        self._format_combo = QComboBox()
        for ext in sorted(IMAGE_EXTENSIONS):
            self._format_combo.addItem(FORMAT_NAMES.get(ext, ext), ext)
        options_layout.addWidget(self._format_combo, 0, 1)

        options_layout.addWidget(QLabel("Calidad:"), 1, 0)
        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(1, 100)
        self._quality_spin.setValue(90)
        options_layout.addWidget(self._quality_spin, 1, 1)

        layout.addWidget(options_group)

        dir_group = QGroupBox("Directorio de salida")
        dir_layout = QHBoxLayout(dir_group)
        self._dir_label = QLabel("Mismo directorio que el original")
        dir_layout.addWidget(self._dir_label, 1)
        dir_btn = QPushButton("Cambiar…")
        dir_btn.clicked.connect(self._select_dir)
        dir_layout.addWidget(dir_btn)
        layout.addWidget(dir_group)

        self._progress_label = QLabel("")
        layout.addWidget(self._progress_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self._convert_btn = QPushButton("Convertir")
        self._convert_btn.clicked.connect(self._run_conversion)
        buttons.addWidget(self._convert_btn)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        self._output_dir: Optional[str] = None

    def _select_files(self):
        exts = " ".join(f"*{e}" for e in sorted(IMAGE_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "", f"Imágenes ({exts})"
        )
        if files:
            self._files = files
            self._files_label.setText(f"{len(files)} archivo(s) seleccionado(s)")

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Directorio de salida")
        if d:
            self._output_dir = d
            self._dir_label.setText(d)

    def _run_conversion(self):
        if not self._files:
            self._progress_label.setText("No hay archivos seleccionados.")
            return

        target_ext = self._format_combo.currentData()
        quality = self._quality_spin.value()
        fmt = target_ext.lstrip(".").upper()
        total = len(self._files)
        success = 0

        for i, file_path in enumerate(self._files, 1):
            self._progress_label.setText(f"Procesando {i}/{total}…")
            self._progress_label.repaint()

            img = QImage(file_path)
            if img.isNull():
                continue

            base = os.path.splitext(os.path.basename(file_path))[0]
            out_dir = self._output_dir or os.path.dirname(file_path)
            out_path = os.path.join(out_dir, f"{base}{target_ext}")

            if save_image(img, out_path, fmt, quality):
                success += 1

        self._progress_label.setText(
            f"Completado: {success}/{total} archivos convertidos."
        )


class EditConvertDialog(QDialog):

    def __init__(self, parent=None, current_width=0, current_height=0):
        super().__init__(parent)
        self.setWindowTitle("Edición y Conversión")
        self.setMinimumWidth(520)

        self.original_width = current_width
        self.original_height = current_height
        self.aspect_ratio = current_width / current_height if current_height > 0 else 1

        self._batch_files: list = []
        self._batch_output_dir: Optional[str] = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QDialog { background: #1e293b; color: #e2e8f0; }
            QGroupBox { color: #e2e8f0; border: 1px solid #334155; border-radius: 6px;
                         margin-top: 10px; padding-top: 14px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QLabel { color: #e2e8f0; }
            QPushButton { background: #334155; color: #e2e8f0; border: 1px solid #475569;
                          border-radius: 4px; padding: 5px 12px; }
            QPushButton:hover { background: #475569; }
            QSpinBox, QComboBox { background: #0f172a; color: #e2e8f0;
                                  border: 1px solid #334155; border-radius: 4px; padding: 3px; }
            QCheckBox, QRadioButton { color: #e2e8f0; }
            QTabWidget::pane { border: 1px solid #334155; border-radius: 4px; }
            QTabBar::tab { background: #334155; color: #e2e8f0; padding: 6px 16px;
                           border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #475569; }
        """)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._build_single_tab()
        self._build_batch_tab()

    def _build_single_tab(self):
        widget = QWidget()
        vl = QVBoxLayout(widget)

        size_group = QGroupBox("Redimensionar")
        size_layout = QGridLayout(size_group)

        size_layout.addWidget(QLabel("Ancho:"), 0, 0)
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(self.original_width or 1)
        self.width_input.valueChanged.connect(self._on_width_changed)
        size_layout.addWidget(self.width_input, 0, 1)

        size_layout.addWidget(QLabel("Alto:"), 1, 0)
        self.height_input = QSpinBox()
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(self.original_height or 1)
        self.height_input.valueChanged.connect(self._on_height_changed)
        size_layout.addWidget(self.height_input, 1, 1)

        self.maintain_aspect = QCheckBox("Mantener relación de aspecto")
        self.maintain_aspect.setChecked(True)
        size_layout.addWidget(self.maintain_aspect, 2, 0, 1, 2)

        size_layout.addWidget(QLabel("Interpolación:"), 3, 0)
        self.interpolation_combo = QComboBox()
        for key, name in INTERPOLATION_NAMES.items():
            self.interpolation_combo.addItem(name, key)
        self.interpolation_combo.setCurrentIndex(1)
        size_layout.addWidget(self.interpolation_combo, 3, 1)

        vl.addWidget(size_group)

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

        vl.addWidget(format_group)

        save_group = QGroupBox("Guardar como")
        save_layout = QVBoxLayout(save_group)

        self.new_file_check = QCheckBox("Crear nuevo archivo")
        self.new_file_check.setChecked(True)
        save_layout.addWidget(self.new_file_check)

        self.overwrite_check = QCheckBox("Sobrescribir archivo original")
        self.overwrite_check.toggled.connect(self._sync_save_checks_from_overwrite)
        self.new_file_check.toggled.connect(self._sync_save_checks_from_new)
        save_layout.addWidget(self.overwrite_check)

        vl.addWidget(save_group)

        btns = QHBoxLayout()
        btns.addStretch()
        apply_btn = QPushButton("Aplicar")
        apply_btn.clicked.connect(self.accept)
        if self.original_width == 0:
            apply_btn.setEnabled(False)
        btns.addWidget(apply_btn)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        vl.addLayout(btns)

        self._tabs.addTab(widget, "Imagen actual")

    def _build_batch_tab(self):
        widget = QWidget()
        vl = QVBoxLayout(widget)

        files_group = QGroupBox("Archivos de entrada")
        files_gl = QVBoxLayout(files_group)
        self._batch_files_label = QLabel("Ningún archivo seleccionado")
        files_gl.addWidget(self._batch_files_label)
        select_btn = QPushButton("Seleccionar archivos…")
        select_btn.clicked.connect(self._select_batch_files)
        files_gl.addWidget(select_btn)
        vl.addWidget(files_group)

        conv_group = QGroupBox("Conversión de formato")
        conv_layout = QGridLayout(conv_group)
        conv_layout.addWidget(QLabel("Formato destino:"), 0, 0)
        self._batch_format_combo = QComboBox()
        for ext in sorted(IMAGE_EXTENSIONS):
            self._batch_format_combo.addItem(FORMAT_NAMES.get(ext, ext), ext)
        conv_layout.addWidget(self._batch_format_combo, 0, 1)
        conv_layout.addWidget(QLabel("Calidad:"), 1, 0)
        self._batch_quality_spin = QSpinBox()
        self._batch_quality_spin.setRange(1, 100)
        self._batch_quality_spin.setValue(90)
        conv_layout.addWidget(self._batch_quality_spin, 1, 1)
        vl.addWidget(conv_group)

        resize_group = QGroupBox("Redimensionar por lotes")
        resize_vl = QVBoxLayout(resize_group)

        self._batch_resize_check = QCheckBox("Activar redimensionado")
        resize_vl.addWidget(self._batch_resize_check)

        self._batch_resize_pct_radio = QRadioButton("Por porcentaje del tamaño original")
        self._batch_resize_pct_radio.setChecked(True)
        resize_vl.addWidget(self._batch_resize_pct_radio)

        pct_hl = QHBoxLayout()
        pct_hl.addWidget(QLabel("Porcentaje:"))
        self._batch_pct_spin = QSpinBox()
        self._batch_pct_spin.setRange(1, 500)
        self._batch_pct_spin.setValue(100)
        self._batch_pct_spin.setSuffix("%")
        pct_hl.addWidget(self._batch_pct_spin)
        resize_vl.addLayout(pct_hl)

        self._batch_resize_exact_radio = QRadioButton("Medida exacta en píxeles")
        resize_vl.addWidget(self._batch_resize_exact_radio)

        exact_gl = QGridLayout()
        exact_gl.addWidget(QLabel("Ancho:"), 0, 0)
        self._batch_width_spin = QSpinBox()
        self._batch_width_spin.setRange(1, 10000)
        self._batch_width_spin.setValue(800)
        exact_gl.addWidget(self._batch_width_spin, 0, 1)
        exact_gl.addWidget(QLabel("Alto:"), 1, 0)
        self._batch_height_spin = QSpinBox()
        self._batch_height_spin.setRange(1, 10000)
        self._batch_height_spin.setValue(600)
        exact_gl.addWidget(self._batch_height_spin, 1, 1)
        self._batch_keep_aspect = QCheckBox("Mantener relación de aspecto")
        self._batch_keep_aspect.setChecked(True)
        exact_gl.addWidget(self._batch_keep_aspect, 2, 0, 1, 2)
        resize_vl.addLayout(exact_gl)

        interp_hl = QHBoxLayout()
        interp_hl.addWidget(QLabel("Interpolación:"))
        self._batch_interp_combo = QComboBox()
        for key, name in INTERPOLATION_NAMES.items():
            self._batch_interp_combo.addItem(name, key)
        self._batch_interp_combo.setCurrentIndex(1)
        interp_hl.addWidget(self._batch_interp_combo)
        resize_vl.addLayout(interp_hl)

        vl.addWidget(resize_group)

        self._batch_resize_check.toggled.connect(self._toggle_batch_resize)
        self._batch_resize_pct_radio.toggled.connect(self._on_batch_resize_mode)
        self._toggle_batch_resize(False)

        dir_group = QGroupBox("Directorio de salida")
        dir_hl = QHBoxLayout(dir_group)
        self._batch_dir_label = QLabel("Mismo directorio que el original")
        dir_hl.addWidget(self._batch_dir_label, 1)
        dir_btn = QPushButton("Cambiar…")
        dir_btn.clicked.connect(self._select_batch_dir)
        dir_hl.addWidget(dir_btn)
        vl.addWidget(dir_group)

        self._batch_progress_label = QLabel("")
        vl.addWidget(self._batch_progress_label)

        btns = QHBoxLayout()
        btns.addStretch()
        self._batch_convert_btn = QPushButton("Convertir")
        self._batch_convert_btn.clicked.connect(self._run_batch)
        btns.addWidget(self._batch_convert_btn)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.reject)
        btns.addWidget(close_btn)
        vl.addLayout(btns)

        self._tabs.addTab(widget, "Procesamiento por lotes")

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
            "new_file": self.new_file_check.isChecked(),
            "interpolation": self.interpolation_combo.currentData(),
        }

    def _sync_save_checks_from_overwrite(self):
        self.new_file_check.blockSignals(True)
        self.new_file_check.setChecked(not self.overwrite_check.isChecked())
        self.new_file_check.blockSignals(False)

    def _sync_save_checks_from_new(self):
        self.overwrite_check.blockSignals(True)
        self.overwrite_check.setChecked(not self.new_file_check.isChecked())
        self.overwrite_check.blockSignals(False)

    def _toggle_batch_resize(self, enabled):
        is_pct = self._batch_resize_pct_radio.isChecked()
        self._batch_resize_pct_radio.setEnabled(enabled)
        self._batch_resize_exact_radio.setEnabled(enabled)
        self._batch_pct_spin.setEnabled(enabled and is_pct)
        self._batch_width_spin.setEnabled(enabled and not is_pct)
        self._batch_height_spin.setEnabled(enabled and not is_pct)
        self._batch_keep_aspect.setEnabled(enabled and not is_pct)
        self._batch_interp_combo.setEnabled(enabled)

    def _on_batch_resize_mode(self):
        if not self._batch_resize_check.isChecked():
            return
        is_pct = self._batch_resize_pct_radio.isChecked()
        self._batch_pct_spin.setEnabled(is_pct)
        self._batch_width_spin.setEnabled(not is_pct)
        self._batch_height_spin.setEnabled(not is_pct)
        self._batch_keep_aspect.setEnabled(not is_pct)

    def _select_batch_files(self):
        exts = " ".join(f"*{e}" for e in sorted(IMAGE_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "", f"Imágenes ({exts})"
        )
        if files:
            self._batch_files = files
            self._batch_files_label.setText(f"{len(files)} archivo(s) seleccionado(s)")

    def _select_batch_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Directorio de salida")
        if d:
            self._batch_output_dir = d
            self._batch_dir_label.setText(d)

    def _run_batch(self):
        if not self._batch_files:
            self._batch_progress_label.setText("No hay archivos seleccionados.")
            return

        target_ext = self._batch_format_combo.currentData()
        quality = self._batch_quality_spin.value()
        fmt = target_ext.lstrip(".").upper()
        do_resize = self._batch_resize_check.isChecked()
        total = len(self._batch_files)
        success = 0

        for i, file_path in enumerate(self._batch_files, 1):
            self._batch_progress_label.setText(f"Procesando {i}/{total}…")
            self._batch_progress_label.repaint()

            img = QImage(file_path)
            if img.isNull():
                continue

            if do_resize:
                if self._batch_resize_pct_radio.isChecked():
                    pct = self._batch_pct_spin.value() / 100.0
                    new_w = max(1, int(img.width() * pct))
                    new_h = max(1, int(img.height() * pct))
                    keep_aspect = False
                else:
                    new_w = self._batch_width_spin.value()
                    new_h = self._batch_height_spin.value()
                    keep_aspect = self._batch_keep_aspect.isChecked()

                interp = self._batch_interp_combo.currentData()
                img = resize_image(img, new_w, new_h, keep_aspect, interpolation=interp)

            base = os.path.splitext(os.path.basename(file_path))[0]
            out_dir = self._batch_output_dir or os.path.dirname(file_path)
            out_path = os.path.join(out_dir, f"{base}{target_ext}")

            if save_image(img, out_path, fmt, quality):
                success += 1

        self._batch_progress_label.setText(
            f"Completado: {success}/{total} archivos procesados."
        )
