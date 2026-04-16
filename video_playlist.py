import os
import random
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog
)

from video_converter import VIDEO_EXTENSIONS

class VideoPlaylistWidget(QWidget):
    
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
        
        header = QHBoxLayout()
        header.setSpacing(6)
        
        title = QLabel("Lista de reproducción")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header.addWidget(title)
        header.addStretch()
        
        self.add_btn = QPushButton("+ Agregar")
        self.add_btn.setFixedHeight(26)
        self.add_btn.setToolTip("Agregar archivos a la lista")
        header.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("- Quitar")
        self.remove_btn.setFixedHeight(26)
        self.remove_btn.setToolTip("Quitar archivo seleccionado")
        header.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setFixedHeight(26)
        self.clear_btn.setToolTip("Limpiar toda la lista")
        header.addWidget(self.clear_btn)
        
        layout.addLayout(header)
        
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(120)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.viewport().setAcceptDrops(True)
        layout.addWidget(self.list_widget)
        
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(4)
        
        sort_label = QLabel("Ordenar:")
        sort_label.setStyleSheet("font-size: 11px;")
        sort_layout.addWidget(sort_label)
        
        self.sort_name_btn = QPushButton("Nombre")
        self.sort_name_btn.setFixedHeight(24)
        self.sort_name_btn.setToolTip("Ordenar por nombre")
        sort_layout.addWidget(self.sort_name_btn)
        
        self.sort_date_btn = QPushButton("Fecha")
        self.sort_date_btn.setFixedHeight(24)
        self.sort_date_btn.setToolTip("Ordenar por fecha de modificación")
        sort_layout.addWidget(self.sort_date_btn)
        
        self.sort_size_btn = QPushButton("Tamaño")
        self.sort_size_btn.setFixedHeight(24)
        self.sort_size_btn.setToolTip("Ordenar por tamaño de archivo")
        sort_layout.addWidget(self.sort_size_btn)
        
        self.sort_random_btn = QPushButton("Aleatorio")
        self.sort_random_btn.setFixedHeight(24)
        self.sort_random_btn.setToolTip("Orden aleatorio")
        sort_layout.addWidget(self.sort_random_btn)
        
        sort_layout.addStretch()
        layout.addLayout(sort_layout)
    
    def _connect_signals(self):
        self.add_btn.clicked.connect(self._add_files)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_all)
        self.sort_name_btn.clicked.connect(lambda: self._sort_by("name"))
        self.sort_date_btn.clicked.connect(lambda: self._sort_by("date"))
        self.sort_size_btn.clicked.connect(lambda: self._sort_by("size"))
        self.sort_random_btn.clicked.connect(lambda: self._sort_by("random"))
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def _add_files(self):
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
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.takeItem(row)
            path = item.data(Qt.UserRole)
            if path in self._paths:
                self._paths.remove(path)
    
    def _clear_all(self):
        self.list_widget.clear()
        self._paths.clear()
    
    def _sort_by(self, key: str):
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
        self.list_widget.clear()
        for path in self._paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.list_widget.addItem(item)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            self.file_selected.emit(path)
    
    def get_playlist(self) -> List[str]:
        return list(self._paths)
    
    def get_current_file(self) -> Optional[str]:
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None
    
    def next_file(self) -> Optional[str]:
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)
            return self.list_widget.currentItem().data(Qt.UserRole)
        return None
    
    def previous_file(self) -> Optional[str]:
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)
            return self.list_widget.currentItem().data(Qt.UserRole)
        return None
    
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
