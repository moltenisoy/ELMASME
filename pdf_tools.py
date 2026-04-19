"""Utilidades PDF: fusionar, dividir, extraer texto e imágenes (backend PyMuPDF)."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
    QMessageBox,
    QDialogButtonBox,
    QLineEdit,
)

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Estilos compartidos
# ---------------------------------------------------------------------------

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
    QLineEdit {
        background: #0f172a;
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.3);
        border-radius: 4px;
        padding: 4px;
    }
"""

# ---------------------------------------------------------------------------
# Funciones utilitarias
# ---------------------------------------------------------------------------


def merge_pdfs(input_paths: list[str], output_path: str) -> bool:
    """Fusiona varios PDF en un único archivo de salida.

    Returns ``True`` si la operación fue exitosa, ``False`` en caso contrario.
    """
    try:
        result = fitz.open()
        for path in input_paths:
            with fitz.open(path) as src:
                result.insert_pdf(src)
        result.save(output_path)
        result.close()
        return True
    except Exception:
        return False


def split_pdf(input_path: str, output_dir: str) -> list[str]:
    """Divide un PDF en archivos individuales por página.

    Returns una lista con las rutas de los archivos creados, o lista vacía
    si ocurre un error.
    """
    created: list[str] = []
    try:
        os.makedirs(output_dir, exist_ok=True)
        base = Path(input_path).stem
        with fitz.open(input_path) as doc:
            for i, page in enumerate(doc, start=1):
                out = fitz.open()
                out.insert_pdf(doc, from_page=i - 1, to_page=i - 1)
                dest = os.path.join(output_dir, f"{base}_pagina_{i}.pdf")
                out.save(dest)
                out.close()
                created.append(dest)
    except Exception:
        pass
    return created


def extract_pdf_text(input_path: str, output_path: str) -> bool:
    """Extrae todo el texto de un PDF y lo guarda en un archivo .txt.

    Returns ``True`` si la operación fue exitosa, ``False`` en caso contrario.
    """
    try:
        with fitz.open(input_path) as doc:
            text_parts: list[str] = []
            for page in doc:
                text_parts.append(page.get_text())
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(text_parts))
        return True
    except Exception:
        return False


def extract_pdf_images(input_path: str, output_dir: str) -> list[str]:
    """Extrae todas las imágenes incrustadas de un PDF.

    Returns una lista con las rutas de los archivos creados, o lista vacía
    si ocurre un error.
    """
    created: list[str] = []
    try:
        os.makedirs(output_dir, exist_ok=True)
        base = Path(input_path).stem
        with fitz.open(input_path) as doc:
            img_index = 0
            for page_num, page in enumerate(doc, start=1):
                for img_info in page.get_images(full=True):
                    xref = img_info[0]
                    img_data = doc.extract_image(xref)
                    ext = img_data.get("ext", "png")
                    img_index += 1
                    dest = os.path.join(
                        output_dir,
                        f"{base}_p{page_num}_img{img_index}.{ext}",
                    )
                    with open(dest, "wb") as fh:
                        fh.write(img_data["image"])
                    created.append(dest)
    except Exception:
        pass
    return created


# ---------------------------------------------------------------------------
# Diálogos de interfaz
# ---------------------------------------------------------------------------


class MergePdfDialog(QDialog):
    """Diálogo para seleccionar varios PDF y fusionarlos en uno solo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fusionar PDFs")
        self.setMinimumSize(520, 420)
        self._output_path: str = ""
        self._build_ui()

    # -- construcción de la interfaz ----------------------------------------

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Archivos PDF a fusionar:"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Botones de gestión de la lista
        list_btns = QHBoxLayout()

        self.add_btn = QPushButton("➕ Agregar")
        self.add_btn.setToolTip("Agregar archivos PDF a la lista")
        self.add_btn.clicked.connect(self._on_add)
        list_btns.addWidget(self.add_btn)

        self.remove_btn = QPushButton("➖ Quitar")
        self.remove_btn.setToolTip("Quitar el archivo seleccionado")
        self.remove_btn.clicked.connect(self._on_remove)
        list_btns.addWidget(self.remove_btn)

        self.up_btn = QPushButton("⬆ Subir")
        self.up_btn.setToolTip("Mover el archivo seleccionado hacia arriba")
        self.up_btn.clicked.connect(self._on_move_up)
        list_btns.addWidget(self.up_btn)

        self.down_btn = QPushButton("⬇ Bajar")
        self.down_btn.setToolTip("Mover el archivo seleccionado hacia abajo")
        self.down_btn.clicked.connect(self._on_move_down)
        list_btns.addWidget(self.down_btn)

        layout.addLayout(list_btns)

        # Ruta de salida
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Archivo de salida:"))
        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        out_row.addWidget(self.output_edit)
        self.browse_btn = QPushButton("📂 Examinar")
        self.browse_btn.setToolTip("Seleccionar ruta de salida")
        self.browse_btn.clicked.connect(self._on_browse_output)
        out_row.addWidget(self.browse_btn)
        layout.addLayout(out_row)

        # OK / Cancelar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -- slots --------------------------------------------------------------

    def _on_add(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar PDFs", "", "PDF (*.pdf)"
        )
        for p in paths:
            self.list_widget.addItem(p)

    def _on_remove(self):
        row = self.list_widget.currentRow()
        if row >= 0:
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

    def _on_browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF fusionado", "", "PDF (*.pdf)"
        )
        if path:
            self._output_path = path
            self.output_edit.setText(path)

    def _on_accept(self):
        if self.list_widget.count() < 2:
            QMessageBox.warning(
                self,
                "Atención",
                "Debe agregar al menos dos archivos PDF.",
            )
            return
        if not self._output_path:
            QMessageBox.warning(
                self,
                "Atención",
                "Debe seleccionar un archivo de salida.",
            )
            return

        paths = [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]
        ok = merge_pdfs(paths, self._output_path)
        if ok:
            QMessageBox.information(
                self,
                "Éxito",
                f"PDF fusionado guardado en:\n{self._output_path}",
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error", "No se pudo fusionar los archivos PDF."
            )

    # -- acceso público ------------------------------------------------------

    def get_output_path(self) -> str:
        return self._output_path


class SplitPdfDialog(QDialog):
    """Diálogo para dividir un PDF en páginas individuales."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dividir PDF")
        self.setMinimumSize(440, 200)
        self._input_path = input_path
        self._output_dir: str = ""
        self._created_files: list[str] = []
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(f"Archivo: {os.path.basename(self._input_path)}")
        )

        # Directorio de salida
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Directorio de salida:"))
        self.dir_edit = QLineEdit()
        self.dir_edit.setReadOnly(True)
        dir_row.addWidget(self.dir_edit)
        self.browse_btn = QPushButton("📂 Examinar")
        self.browse_btn.setToolTip("Seleccionar directorio de salida")
        self.browse_btn.clicked.connect(self._on_browse)
        dir_row.addWidget(self.browse_btn)
        layout.addLayout(dir_row)

        # OK / Cancelar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse(self):
        d = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de salida"
        )
        if d:
            self._output_dir = d
            self.dir_edit.setText(d)

    def _on_accept(self):
        if not self._output_dir:
            QMessageBox.warning(
                self,
                "Atención",
                "Debe seleccionar un directorio de salida.",
            )
            return

        self._created_files = split_pdf(self._input_path, self._output_dir)
        if self._created_files:
            QMessageBox.information(
                self,
                "Éxito",
                f"Se crearon {len(self._created_files)} archivos en:\n{self._output_dir}",
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error", "No se pudo dividir el PDF."
            )

    def get_created_files(self) -> list[str]:
        return self._created_files


class ExtractTextDialog(QDialog):
    """Diálogo simple de confirmación para extraer texto de un PDF."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extraer texto de PDF")
        self.setMinimumSize(440, 160)
        self._input_path = input_path
        self._output_path: str = self._default_output()
        self._build_ui()

    def _default_output(self) -> str:
        p = Path(self._input_path)
        return str(p.with_suffix(".txt"))

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(f"Archivo: {os.path.basename(self._input_path)}")
        )
        layout.addWidget(
            QLabel(f"Se guardará como:\n{self._output_path}")
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        ok = extract_pdf_text(self._input_path, self._output_path)
        if ok:
            QMessageBox.information(
                self,
                "Éxito",
                f"Texto extraído y guardado en:\n{self._output_path}",
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error", "No se pudo extraer el texto del PDF."
            )

    def get_output_path(self) -> str:
        return self._output_path
