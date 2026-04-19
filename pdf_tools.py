
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QDrag
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDialogButtonBox,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QScrollArea,
    QWidget,
    QGridLayout,
    QGroupBox,
    QInputDialog,
    QApplication,
    QFrame,
)

import fitz


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


def merge_pdfs(input_paths: list[str], output_path: str) -> bool:
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


class MergePdfDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fusionar PDFs")
        self.setMinimumSize(520, 420)
        self._output_path: str = ""
        self._build_ui()


    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Archivos PDF a fusionar:"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

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

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


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


    def get_output_path(self) -> str:
        return self._output_path


class SplitPdfDialog(QDialog):

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


def get_pdf_form_fields(input_path: str) -> list[dict]:
    """Get all interactive form fields from a PDF.
    Returns list of dicts with keys: field_name, field_type, field_value, page."""
    fields = []
    try:
        with fitz.open(input_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                for widget in page.widgets():
                    fields.append({
                        "field_name": widget.field_name or "",
                        "field_type": widget.field_type,
                        "field_type_string": widget.field_type_string or "",
                        "field_value": widget.field_value or "",
                        "page": page_num,
                        "rect": widget.rect,
                    })
    except Exception:
        pass
    return fields


def fill_pdf_form_fields(input_path: str, output_path: str, field_values: dict) -> bool:
    """Fill form fields in a PDF. field_values: {field_name: new_value}."""
    try:
        doc = fitz.open(input_path)
        for page in doc:
            for widget in page.widgets():
                name = widget.field_name
                if name in field_values:
                    widget.field_value = str(field_values[name])
                    widget.update()
        doc.save(output_path)
        doc.close()
        return True
    except Exception:
        return False


class PdfFormFillerDialog(QDialog):
    """Dialog for filling PDF form fields."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rellenar formulario PDF")
        self.setMinimumSize(600, 500)
        self._input_path = input_path
        self._output_path: str = ""
        self._field_widgets: dict = {}
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Archivo: {os.path.basename(self._input_path)}"))

        fields = get_pdf_form_fields(self._input_path)
        if not fields:
            layout.addWidget(QLabel(
                "⚠️ Este PDF no contiene campos de formulario interactivos."
            ))
            close_btn = QPushButton("Cerrar")
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return

        layout.addWidget(QLabel(f"Se encontraron {len(fields)} campo(s) de formulario:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setSpacing(8)

        for i, field in enumerate(fields):
            name = field["field_name"]
            ftype = field["field_type_string"]
            value = field["field_value"]
            page = field["page"] + 1

            label_text = f"{name} (Pág.{page}, {ftype}):"
            form_layout.addWidget(QLabel(label_text), i, 0)

            edit = QLineEdit()
            edit.setText(value)
            edit.setPlaceholderText(f"Valor para '{name}'")
            form_layout.addWidget(edit, i, 1)
            self._field_widgets[name] = edit

        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF con formulario rellenado", "", "PDF (*.pdf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        field_values = {
            name: edit.text() for name, edit in self._field_widgets.items()
        }

        ok = fill_pdf_form_fields(self._input_path, save_path, field_values)
        if ok:
            self._output_path = save_path
            QMessageBox.information(
                self, "Éxito",
                f"Formulario guardado en:\n{save_path}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error",
                "No se pudo guardar el formulario."
            )


def encrypt_pdf(input_path: str, output_path: str, user_password: str,
                owner_password: str = None) -> bool:
    """Encrypt a PDF with a password."""
    try:
        doc = fitz.open(input_path)
        perm = (
            fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
        )
        encrypt_method = fitz.PDF_ENCRYPT_AES_256
        doc.save(
            output_path,
            encryption=encrypt_method,
            user_pw=user_password,
            owner_pw=owner_password or user_password,
            permissions=perm,
        )
        doc.close()
        return True
    except Exception:
        return False


def decrypt_pdf(input_path: str, output_path: str, password: str) -> bool:
    """Decrypt a password-protected PDF."""
    try:
        doc = fitz.open(input_path)
        if doc.is_encrypted:
            if not doc.authenticate(password):
                doc.close()
                return False
        doc.save(output_path)
        doc.close()
        return True
    except Exception:
        return False


class PdfPasswordDialog(QDialog):
    """Dialog for encrypting or decrypting a PDF."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Protección con contraseña")
        self.setMinimumWidth(460)
        self._input_path = input_path
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Archivo: {os.path.basename(self._input_path)}"))

        try:
            doc = fitz.open(self._input_path)
            self._is_encrypted = doc.is_encrypted
            doc.close()
        except Exception:
            self._is_encrypted = False

        if self._is_encrypted:
            layout.addWidget(QLabel("🔒 Este PDF está protegido con contraseña."))
            layout.addWidget(QLabel("Ingrese la contraseña para descifrar:"))
            self._password_edit = QLineEdit()
            self._password_edit.setEchoMode(QLineEdit.Password)
            self._password_edit.setPlaceholderText("Contraseña")
            layout.addWidget(self._password_edit)

            decrypt_btn = QPushButton("🔓 Descifrar PDF")
            decrypt_btn.clicked.connect(self._on_decrypt)
            layout.addWidget(decrypt_btn)
        else:
            layout.addWidget(QLabel("🔓 Este PDF no está protegido."))
            layout.addWidget(QLabel("Establezca una contraseña para protegerlo:"))

            self._password_edit = QLineEdit()
            self._password_edit.setEchoMode(QLineEdit.Password)
            self._password_edit.setPlaceholderText("Contraseña de usuario")
            layout.addWidget(self._password_edit)

            self._confirm_edit = QLineEdit()
            self._confirm_edit.setEchoMode(QLineEdit.Password)
            self._confirm_edit.setPlaceholderText("Confirmar contraseña")
            layout.addWidget(self._confirm_edit)

            self._owner_edit = QLineEdit()
            self._owner_edit.setEchoMode(QLineEdit.Password)
            self._owner_edit.setPlaceholderText("Contraseña de propietario (opcional)")
            layout.addWidget(self._owner_edit)

            encrypt_btn = QPushButton("🔒 Cifrar PDF")
            encrypt_btn.clicked.connect(self._on_encrypt)
            layout.addWidget(encrypt_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        layout.addStretch()

    def _on_decrypt(self):
        password = self._password_edit.text()
        if not password:
            QMessageBox.warning(self, "Atención", "Ingrese la contraseña.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF descifrado", "", "PDF (*.pdf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        ok = decrypt_pdf(self._input_path, save_path, password)
        if ok:
            QMessageBox.information(
                self, "Éxito",
                f"PDF descifrado y guardado en:\n{save_path}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error",
                "Contraseña incorrecta o no se pudo descifrar el PDF."
            )

    def _on_encrypt(self):
        password = self._password_edit.text()
        confirm = self._confirm_edit.text()
        owner = self._owner_edit.text()

        if not password:
            QMessageBox.warning(self, "Atención", "Ingrese una contraseña.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Atención", "Las contraseñas no coinciden.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF cifrado", "", "PDF (*.pdf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        ok = encrypt_pdf(
            self._input_path, save_path, password,
            owner_password=owner if owner else None
        )
        if ok:
            QMessageBox.information(
                self, "Éxito",
                f"PDF cifrado y guardado en:\n{save_path}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error",
                "No se pudo cifrar el PDF."
            )


def reorder_pdf_pages(input_path: str, output_path: str, new_order: list[int]) -> bool:
    """Reorder pages in a PDF. new_order is a list of 0-based page indices."""
    try:
        doc = fitz.open(input_path)
        doc.select(new_order)
        doc.save(output_path)
        doc.close()
        return True
    except Exception:
        return False


class PdfReorderDialog(QDialog):
    """Dialog for reordering PDF pages via drag and drop."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reorganizar páginas del PDF")
        self.setMinimumSize(520, 480)
        self._input_path = input_path
        self._page_count = 0
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        try:
            doc = fitz.open(self._input_path)
            self._page_count = len(doc)
            doc.close()
        except Exception:
            layout.addWidget(QLabel("No se pudo abrir el PDF."))
            return

        layout.addWidget(QLabel(
            f"Archivo: {os.path.basename(self._input_path)} — {self._page_count} página(s)\n"
            "Arrastre las páginas para reordenarlas:"
        ))

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #0f172a; color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 4px;
            }
            QListWidget::item { padding: 6px; }
            QListWidget::item:selected { background: rgba(59,130,246,0.3); }
        """)

        for i in range(self._page_count):
            item = QListWidgetItem(f"Página {i + 1}")
            item.setData(Qt.UserRole, i)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        up_btn = QPushButton("⬆ Subir")
        up_btn.clicked.connect(self._move_up)
        btn_row.addWidget(up_btn)

        down_btn = QPushButton("⬇ Bajar")
        down_btn.clicked.connect(self._move_down)
        btn_row.addWidget(down_btn)

        reverse_btn = QPushButton("🔄 Invertir orden")
        reverse_btn.clicked.connect(self._reverse_order)
        btn_row.addWidget(reverse_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def _reverse_order(self):
        items_data = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            items_data.append((item.text(), item.data(Qt.UserRole)))
        self.list_widget.clear()
        for text, data in reversed(items_data):
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, data)
            self.list_widget.addItem(item)

    def _on_accept(self):
        new_order = []
        for i in range(self.list_widget.count()):
            page_idx = self.list_widget.item(i).data(Qt.UserRole)
            new_order.append(page_idx)

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF reordenado", "", "PDF (*.pdf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        ok = reorder_pdf_pages(self._input_path, save_path, new_order)
        if ok:
            QMessageBox.information(
                self, "Éxito",
                f"PDF reordenado guardado en:\n{save_path}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error",
                "No se pudo reordenar el PDF."
            )


def add_watermark(input_path: str, output_path: str,
                  text: str = None, image_path: str = None,
                  opacity: float = 0.3, fontsize: int = 48,
                  rotation: int = 45) -> bool:
    """Add text or image watermark to all pages of a PDF."""
    try:
        doc = fitz.open(input_path)

        for page in doc:
            rect = page.rect

            if text:
                center_x = rect.width / 2
                center_y = rect.height / 2

                tw = fitz.TextWriter(page.rect)
                font = fitz.Font("helv")
                text_length = font.text_length(text, fontsize=fontsize)

                x = center_x - text_length / 2
                y = center_y + fontsize / 2

                tw.append((x, y), text, font=font, fontsize=fontsize)
                tw.write_text(page, opacity=opacity, color=(0.5, 0.5, 0.5),
                              morph=(fitz.Point(center_x, center_y),
                                     fitz.Matrix(rotation)))

            if image_path and os.path.isfile(image_path):
                img_rect = fitz.Rect(
                    rect.width * 0.25, rect.height * 0.25,
                    rect.width * 0.75, rect.height * 0.75
                )
                page.insert_image(img_rect, filename=image_path,
                                  overlay=True, alpha=int(opacity * 255))

        doc.save(output_path)
        doc.close()
        return True
    except Exception:
        return False


class PdfWatermarkDialog(QDialog):
    """Dialog for adding text or image watermark to a PDF."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Marca de agua en PDF")
        self.setMinimumWidth(480)
        self._input_path = input_path
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Archivo: {os.path.basename(self._input_path)}"))

        text_group = QGroupBox("Marca de agua de texto")
        text_layout = QGridLayout(text_group)
        text_group.setStyleSheet("""
            QGroupBox { color: #e5e7eb; border: 1px solid rgba(148,163,184,0.3);
                        border-radius: 6px; margin-top: 8px; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        """)

        text_layout.addWidget(QLabel("Texto:"), 0, 0)
        self._text_edit = QLineEdit()
        self._text_edit.setPlaceholderText("Ej: CONFIDENCIAL, BORRADOR, etc.")
        text_layout.addWidget(self._text_edit, 0, 1)

        text_layout.addWidget(QLabel("Tamaño de fuente:"), 1, 0)
        self._fontsize_spin = QSpinBox()
        self._fontsize_spin.setRange(12, 120)
        self._fontsize_spin.setValue(48)
        text_layout.addWidget(self._fontsize_spin, 1, 1)

        text_layout.addWidget(QLabel("Rotación (grados):"), 2, 0)
        self._rotation_spin = QSpinBox()
        self._rotation_spin.setRange(-180, 180)
        self._rotation_spin.setValue(45)
        text_layout.addWidget(self._rotation_spin, 2, 1)

        layout.addWidget(text_group)

        img_group = QGroupBox("Marca de agua de imagen")
        img_layout = QHBoxLayout(img_group)
        img_group.setStyleSheet(text_group.styleSheet())

        self._image_path_edit = QLineEdit()
        self._image_path_edit.setReadOnly(True)
        self._image_path_edit.setPlaceholderText("Sin imagen seleccionada")
        img_layout.addWidget(self._image_path_edit)

        browse_btn = QPushButton("📂 Examinar")
        browse_btn.clicked.connect(self._browse_image)
        img_layout.addWidget(browse_btn)

        layout.addWidget(img_group)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacidad (%):"))
        self._opacity_spin = QSpinBox()
        self._opacity_spin.setRange(5, 100)
        self._opacity_spin.setValue(30)
        opacity_layout.addWidget(self._opacity_spin)
        opacity_layout.addStretch()
        layout.addLayout(opacity_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        layout.addStretch()

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de marca de agua", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Todos (*.*)"
        )
        if path:
            self._image_path_edit.setText(path)

    def _on_accept(self):
        text = self._text_edit.text().strip()
        image = self._image_path_edit.text().strip()

        if not text and not image:
            QMessageBox.warning(
                self, "Atención",
                "Ingrese un texto o seleccione una imagen para la marca de agua."
            )
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF con marca de agua", "", "PDF (*.pdf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".pdf"):
            save_path += ".pdf"

        opacity = self._opacity_spin.value() / 100.0
        fontsize = self._fontsize_spin.value()
        rotation = self._rotation_spin.value()

        ok = add_watermark(
            self._input_path, save_path,
            text=text if text else None,
            image_path=image if image else None,
            opacity=opacity,
            fontsize=fontsize,
            rotation=rotation,
        )
        if ok:
            QMessageBox.information(
                self, "Éxito",
                f"PDF con marca de agua guardado en:\n{save_path}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error",
                "No se pudo aplicar la marca de agua."
            )


def export_pdf_pages_as_images(
    input_path: str,
    output_dir: str,
    page_range: tuple = None,
    image_format: str = "png",
    dpi: int = 150,
) -> list[str]:
    """Export PDF pages as images (render pages). Returns list of created file paths."""
    created: list[str] = []
    try:
        os.makedirs(output_dir, exist_ok=True)
        base = Path(input_path).stem
        doc = fitz.open(input_path)

        if page_range:
            start, end = page_range
            pages = range(max(0, start), min(len(doc), end + 1))
        else:
            pages = range(len(doc))

        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)

        for page_num in pages:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat, alpha=False)

            dest = os.path.join(output_dir, f"{base}_pagina_{page_num + 1}.{image_format}")
            pix.save(dest)
            created.append(dest)

        doc.close()
    except Exception:
        pass
    return created


class PdfExportImagesDialog(QDialog):
    """Dialog for exporting PDF pages as images (render pages to PNG/JPEG)."""

    def __init__(self, input_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar páginas como imágenes")
        self.setMinimumWidth(480)
        self._input_path = input_path
        self._page_count = 0
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(self)

        try:
            doc = fitz.open(self._input_path)
            self._page_count = len(doc)
            doc.close()
        except Exception:
            layout.addWidget(QLabel("No se pudo abrir el PDF."))
            return

        layout.addWidget(QLabel(
            f"Archivo: {os.path.basename(self._input_path)} — {self._page_count} página(s)"
        ))

        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Rango de páginas:"))

        self._all_pages_check = QCheckBox("Todas las páginas")
        self._all_pages_check.setChecked(True)
        self._all_pages_check.toggled.connect(self._on_range_toggled)
        range_layout.addWidget(self._all_pages_check)

        range_layout.addWidget(QLabel("Desde:"))
        self._start_spin = QSpinBox()
        self._start_spin.setRange(1, self._page_count)
        self._start_spin.setValue(1)
        self._start_spin.setEnabled(False)
        range_layout.addWidget(self._start_spin)

        range_layout.addWidget(QLabel("Hasta:"))
        self._end_spin = QSpinBox()
        self._end_spin.setRange(1, self._page_count)
        self._end_spin.setValue(self._page_count)
        self._end_spin.setEnabled(False)
        range_layout.addWidget(self._end_spin)

        range_layout.addStretch()
        layout.addLayout(range_layout)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Formato:"))
        self._format_combo = QComboBox()
        self._format_combo.addItem("PNG", "png")
        self._format_combo.addItem("JPEG", "jpg")
        format_layout.addWidget(self._format_combo)

        format_layout.addSpacing(16)
        format_layout.addWidget(QLabel("DPI:"))
        self._dpi_spin = QSpinBox()
        self._dpi_spin.setRange(72, 600)
        self._dpi_spin.setValue(150)
        format_layout.addWidget(self._dpi_spin)

        format_layout.addStretch()
        layout.addLayout(format_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        layout.addStretch()

    def _on_range_toggled(self, checked):
        self._start_spin.setEnabled(not checked)
        self._end_spin.setEnabled(not checked)

    def _on_accept(self):
        output_dir = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de salida"
        )
        if not output_dir:
            return

        page_range = None
        if not self._all_pages_check.isChecked():
            page_range = (self._start_spin.value() - 1, self._end_spin.value() - 1)

        image_format = self._format_combo.currentData()
        dpi = self._dpi_spin.value()

        created = export_pdf_pages_as_images(
            self._input_path, output_dir,
            page_range=page_range,
            image_format=image_format,
            dpi=dpi,
        )

        if created:
            QMessageBox.information(
                self, "Éxito",
                f"Se exportaron {len(created)} imagen(es) en:\n{output_dir}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, "Error",
                "No se pudieron exportar las páginas como imágenes."
            )
