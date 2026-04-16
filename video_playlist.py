"""
Módulo de gestión de lista de reproducción de video.
"""

import json
import os
import random
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog,
    QMessageBox
)

from video_converter import VIDEO_EXTENSIONS


class VideoPlaylistWidget(QWidget):
    """Widget para gestionar una lista de reproducción de video."""
    
    file_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths = []
        self._build_ui()
        self._connect_signals()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        
        # Encabezado
        header = QHBoxLayout()
        header.setSpacing(6)
        
        title = QLabel("Lista de reproducción")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header.addWidget(title)
        header.addStretch()
        
        self.add_btn = QPushButton("+ Agregar")
        self.add_btn.setFixedHeight(20)
        header.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("- Quitar")
        self.remove_btn.setFixedHeight(20)
        header.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setFixedHeight(20)
        header.addWidget(self.clear_btn)
        
        self.save_playlist_btn = QPushButton("💾 Guardar")
        self.save_playlist_btn.setFixedHeight(20)
        header.addWidget(self.save_playlist_btn)
        
        self.load_playlist_btn = QPushButton("📂 Abrir")
        self.load_playlist_btn.setFixedHeight(20)
        header.addWidget(self.load_playlist_btn)
        
        layout.addLayout(header)
        
        # Lista
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(120)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.viewport().setAcceptDrops(True)
        layout.addWidget(self.list_widget)
        
        # Botones de ordenamiento
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(4)
        
        sort_label = QLabel("Ordenar:")
        sort_label.setStyleSheet("font-size: 11px;")
        sort_layout.addWidget(sort_label)
        
        self.sort_name_btn = QPushButton("Nombre")
        self.sort_name_btn.setFixedHeight(18)
        sort_layout.addWidget(self.sort_name_btn)
        
        self.sort_date_btn = QPushButton("Fecha")
        self.sort_date_btn.setFixedHeight(18)
        sort_layout.addWidget(self.sort_date_btn)
        
        self.sort_size_btn = QPushButton("Tamaño")
        self.sort_size_btn.setFixedHeight(18)
        sort_layout.addWidget(self.sort_size_btn)
        
        self.sort_random_btn = QPushButton("Aleatorio")
        self.sort_random_btn.setFixedHeight(18)
        sort_layout.addWidget(self.sort_random_btn)
        
        sort_layout.addStretch()
        layout.addLayout(sort_layout)
    
    def _connect_signals(self):
        self.add_btn.clicked.connect(self._add_files)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_all)
        self.save_playlist_btn.clicked.connect(self._save_playlist)
        self.load_playlist_btn.clicked.connect(self._load_playlist)
        self.sort_name_btn.clicked.connect(lambda: self._sort_by("name"))
        self.sort_date_btn.clicked.connect(lambda: self._sort_by("date"))
        self.sort_size_btn.clicked.connect(lambda: self._sort_by("size"))
        self.sort_random_btn.clicked.connect(lambda: self._sort_by("random"))
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def _add_files(self):
        """Abre diálogo para agregar archivos de video."""
        extensions = " ".join(f"*{ext}" for ext in sorted(VIDEO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Agregar archivos de video",
            "",
            f"Video ({extensions});;Todos los archivos (*.*)"
        )
        for f in files:
            self._add_path(f)
    
    def _add_path(self, path: str):
        """Agrega una ruta a la lista si es un archivo de video válido."""
        ext = Path(path).suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            return
        if path in self._paths:
            return
        self._paths.append(path)
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)
        self.list_widget.addItem(item)
    
    def _remove_selected(self):
        """Quita el archivo seleccionado de la lista."""
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.takeItem(row)
            path = item.data(Qt.UserRole)
            if path in self._paths:
                self._paths.remove(path)
    
    def _clear_all(self):
        """Limpia toda la lista."""
        self.list_widget.clear()
        self._paths.clear()
    
    def _sort_by(self, key: str):
        """Ordena la lista por el criterio especificado."""
        if not self._paths:
            return
        
        if key == "name":
            self._paths.sort(key=lambda p: os.path.basename(p).lower())
        elif key == "date":
            self._paths.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
        elif key == "size":
            self._paths.sort(key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0)
        elif key == "random":
            random.shuffle(self._paths)
        
        self._rebuild_list()
    
    def _rebuild_list(self):
        """Reconstruye la lista visual desde self._paths."""
        self.list_widget.clear()
        for path in self._paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.list_widget.addItem(item)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Emite señal cuando se hace doble click en un archivo."""
        path = item.data(Qt.UserRole)
        if path:
            self.file_selected.emit(path)
    
    def get_playlist(self) -> List[str]:
        """Retorna la lista completa de rutas."""
        return list(self._paths)
    
    def get_current_file(self) -> Optional[str]:
        """Retorna la ruta del archivo seleccionado actualmente."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None
    
    def next_file(self) -> Optional[str]:
        """Avanza al siguiente archivo en la lista."""
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)
            return self.list_widget.currentItem().data(Qt.UserRole)
        return None
    
    def previous_file(self) -> Optional[str]:
        """Retrocede al archivo anterior en la lista."""
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)
            return self.list_widget.currentItem().data(Qt.UserRole)
        return None
    
    # --- Drag and Drop desde cualquier origen ---
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path and os.path.isfile(path):
                    self._add_path(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    # --- Guardar / Cargar playlist ---
    
    def _save_playlist(self):
        """Guarda la playlist actual como archivo JSON."""
        if not self._paths:
            QMessageBox.information(self, "Playlist vacía",
                                    "No hay archivos en la lista para guardar.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar playlist", "",
            "Playlist JSON (*.json);;Todos los archivos (*.*)"
        )
        if not file_path:
            return
        
        # Sincronizar _paths con el orden visual actual
        self._sync_paths_from_list()
        
        data = {"files": list(self._paths)}
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Éxito",
                                    f"Playlist guardada en:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo guardar la playlist:\n{e}")
    
    def _load_playlist(self):
        """Carga una playlist desde un archivo JSON."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir playlist", "",
            "Playlist JSON (*.json);;Todos los archivos (*.*)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            files = data.get("files", [])
            if not files:
                QMessageBox.warning(self, "Playlist vacía",
                                    "La playlist no contiene archivos.")
                return
            
            self._clear_all()
            for path in files:
                if os.path.isfile(path):
                    self._add_path(path)
            
            QMessageBox.information(self, "Éxito",
                                    f"Playlist cargada: {len(self._paths)} archivos.")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo cargar la playlist:\n{e}")
    
    def _sync_paths_from_list(self):
        """Sincroniza _paths con el orden actual de la lista visual."""
        self._paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(Qt.UserRole)
            if path:
                self._paths.append(path)
