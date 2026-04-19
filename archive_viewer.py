"""Visor de archivos comprimidos (ZIP, RAR, 7z, TAR, GZ, BZ2, XZ)."""

import os
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
    QMessageBox,
    QHeaderView,
)

ARCHIVE_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".tar.gz", ".bz2", ".xz",
}

_BTN_STYLE = """
    QPushButton {
        background: rgba(59,130,246,0.2);
        border: 1px solid rgba(59,130,246,0.4);
        border-radius: 6px;
        padding: 4px 14px;
        color: #60a5fa;
        font-weight: 500;
    }
    QPushButton:hover { background: rgba(59,130,246,0.35); }
"""

_TREE_STYLE = """
    QTreeWidget {
        background: #111827;
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.2);
        border-radius: 8px;
        padding: 4px;
    }
    QTreeWidget::item:selected {
        background: rgba(59,130,246,0.3);
    }
    QHeaderView::section {
        background: #1e293b;
        color: #94a3b8;
        border: 1px solid rgba(148,163,184,0.2);
        padding: 4px;
    }
"""


def _format_size(size: int) -> str:
    """Devuelve el tamaño en formato legible."""
    if size < 0:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} TB"


def _guess_archive_type(path: str) -> str:
    """Determina el tipo de archivo según su extensión."""
    lower = path.lower()
    if lower.endswith(".tar.gz") or lower.endswith(".tgz"):
        return "tar"
    if lower.endswith((".tar.bz2", ".tar.xz")):
        return "tar"
    ext = Path(lower).suffix
    if ext == ".zip":
        return "zip"
    if ext in (".tar", ".gz", ".bz2", ".xz"):
        return "tar"
    if ext == ".rar":
        return "rar"
    if ext == ".7z":
        return "7z"
    return "unknown"


class ArchiveViewer(QWidget):
    """Visor de contenido de archivos comprimidos."""

    def __init__(self) -> None:
        super().__init__()
        self.current_path: str | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)

        self.extract_all_btn = QPushButton("📦 Extraer todo")
        self.extract_all_btn.setStyleSheet(_BTN_STYLE)
        self.extract_all_btn.clicked.connect(self._extract_all)

        self.extract_sel_btn = QPushButton("📂 Extraer selección")
        self.extract_sel_btn.setStyleSheet(_BTN_STYLE)
        self.extract_sel_btn.clicked.connect(self._extract_selected)

        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.path_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        toolbar.addWidget(self.extract_all_btn)
        toolbar.addWidget(self.extract_sel_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.path_label)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nombre", "Tamaño", "Modificado", "Tipo"])
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree.setStyleSheet(_TREE_STYLE)

        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(toolbar)
        layout.addWidget(self.tree, 1)

    # ── Carga ─────────────────────────────────────────────────────────

    def load_file(self, path: str) -> None:
        """Carga y muestra el contenido de un archivo comprimido."""
        self.current_path = path
        self.tree.clear()
        self.path_label.setText(os.path.basename(path))

        archive_type = _guess_archive_type(path)

        try:
            if archive_type == "zip":
                self._load_zip(path)
            elif archive_type == "tar":
                self._load_tar(path)
            elif archive_type in ("rar", "7z"):
                self._show_unsupported(archive_type)
            else:
                self._show_error("Formato de archivo no reconocido.")
        except Exception as exc:
            self._show_error(f"Error al leer el archivo:\n{exc}")

    # ── ZIP ───────────────────────────────────────────────────────────

    def _load_zip(self, path: str) -> None:
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for info in zf.infolist():
                    is_dir = info.is_dir()
                    name = info.filename.rstrip("/")
                    size = info.file_size if not is_dir else -1
                    try:
                        modified = datetime(*info.date_time).strftime(
                            "%Y-%m-%d %H:%M"
                        )
                    except (ValueError, TypeError):
                        modified = ""
                    self._add_entry(name, size, modified, is_dir)
        except zipfile.BadZipFile:
            self._show_error("El archivo ZIP está dañado o no es válido.")
        except Exception as exc:
            self._show_error(f"Error al leer ZIP:\n{exc}")

    # ── TAR / GZ / BZ2 / XZ ──────────────────────────────────────────

    def _load_tar(self, path: str) -> None:
        try:
            with tarfile.open(path, "r:*") as tf:
                for member in tf.getmembers():
                    is_dir = member.isdir()
                    name = member.name.rstrip("/")
                    size = member.size if not is_dir else -1
                    try:
                        modified = datetime.fromtimestamp(
                            member.mtime
                        ).strftime("%Y-%m-%d %H:%M")
                    except (OSError, ValueError, OverflowError):
                        modified = ""
                    self._add_entry(name, size, modified, is_dir)
        except tarfile.TarError:
            self._show_error(
                "El archivo TAR está dañado o no es válido."
            )
        except Exception as exc:
            self._show_error(f"Error al leer TAR:\n{exc}")

    # ── Entradas ──────────────────────────────────────────────────────

    def _add_entry(
        self, name: str, size: int, modified: str, is_dir: bool
    ) -> None:
        parts = name.split("/")
        parent: QTreeWidget | QTreeWidgetItem = self.tree

        # Crear/buscar nodos intermedios
        for i, part in enumerate(parts[:-1]):
            found = None
            container = (
                parent if isinstance(parent, QTreeWidget) else parent
            )
            count = (
                container.topLevelItemCount()
                if isinstance(container, QTreeWidget)
                else container.childCount()
            )
            for idx in range(count):
                child = (
                    container.topLevelItem(idx)
                    if isinstance(container, QTreeWidget)
                    else container.child(idx)
                )
                if child is not None and child.text(0) == part:
                    found = child
                    break
            if found is None:
                found = QTreeWidgetItem()
                found.setText(0, part)
                found.setText(1, "")
                found.setText(2, "")
                found.setText(3, "📁 Carpeta")
                if isinstance(container, QTreeWidget):
                    container.addTopLevelItem(found)
                else:
                    container.addChild(found)
            parent = found

        # Nodo hoja
        leaf_name = parts[-1] if parts else name
        if not leaf_name:
            return

        item = QTreeWidgetItem()
        item.setText(0, leaf_name)
        item.setText(1, _format_size(size) if not is_dir else "")
        item.setText(2, modified)
        item.setText(3, "📁 Carpeta" if is_dir else "📄 Archivo")
        item.setData(0, Qt.UserRole, name)

        if isinstance(parent, QTreeWidget):
            parent.addTopLevelItem(item)
        else:
            parent.addChild(item)

    # ── Extracción ────────────────────────────────────────────────────

    def _choose_output_dir(self) -> str | None:
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino"
        )
        return directory if directory else None

    def _extract_all(self) -> None:
        if not self.current_path:
            return
        dest = self._choose_output_dir()
        if not dest:
            return

        archive_type = _guess_archive_type(self.current_path)
        try:
            if archive_type == "zip":
                with zipfile.ZipFile(self.current_path, "r") as zf:
                    zf.extractall(dest)
            elif archive_type == "tar":
                with tarfile.open(self.current_path, "r:*") as tf:
                    tf.extractall(dest, filter="data")
            else:
                QMessageBox.warning(
                    self,
                    "No compatible",
                    "La extracción no está disponible para este formato.",
                )
                return
            QMessageBox.information(
                self,
                "Extracción completa",
                f"Archivos extraídos en:\n{dest}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Error", f"Error al extraer:\n{exc}"
            )

    def _extract_selected(self) -> None:
        if not self.current_path:
            return
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.information(
                self,
                "Sin selección",
                "Selecciona uno o más elementos para extraer.",
            )
            return

        names = []
        for item in items:
            entry_name = item.data(0, Qt.UserRole)
            if entry_name:
                names.append(entry_name)
        if not names:
            return

        dest = self._choose_output_dir()
        if not dest:
            return

        archive_type = _guess_archive_type(self.current_path)
        try:
            if archive_type == "zip":
                with zipfile.ZipFile(self.current_path, "r") as zf:
                    for n in names:
                        try:
                            zf.extract(n, dest)
                        except KeyError:
                            pass
            elif archive_type == "tar":
                with tarfile.open(self.current_path, "r:*") as tf:
                    for n in names:
                        try:
                            member = tf.getmember(n)
                            tf.extract(member, dest, filter="data")
                        except KeyError:
                            pass
            else:
                QMessageBox.warning(
                    self,
                    "No compatible",
                    "La extracción no está disponible para este formato.",
                )
                return
            QMessageBox.information(
                self,
                "Extracción completa",
                f"Elementos extraídos en:\n{dest}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Error", f"Error al extraer:\n{exc}"
            )

    # ── Mensajes ──────────────────────────────────────────────────────

    def _show_unsupported(self, fmt: str) -> None:
        libs = {"rar": "rarfile", "7z": "py7zr"}
        lib = libs.get(fmt, fmt)
        item = QTreeWidgetItem()
        item.setText(
            0,
            f"⚠️ El formato .{fmt} requiere la biblioteca externa «{lib}».\n"
            f"Instálala con: pip install {lib}",
        )
        item.setFirstColumnSpanned(True)
        self.tree.addTopLevelItem(item)

    def _show_error(self, msg: str) -> None:
        item = QTreeWidgetItem()
        item.setText(0, f"⚠️ {msg}")
        item.setFirstColumnSpanned(True)
        self.tree.addTopLevelItem(item)
