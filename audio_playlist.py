import json
import os
import random
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog,
    QToolButton, QMenu
)

from audio_converter import AUDIO_EXTENSIONS


class AudioPlaylistWidget(QWidget):

    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths = []
        self._list_visible = True
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setSpacing(2)

        title = QLabel("Lista de reproducción")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header.addWidget(title)
        header.addStretch()

        self.add_btn = QPushButton("+ Agregar")
        self.add_btn.setFixedHeight(24)
        header.addWidget(self.add_btn)

        self.remove_btn = QPushButton("- Quitar")
        self.remove_btn.setFixedHeight(24)
        header.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setFixedHeight(24)
        header.addWidget(self.clear_btn)

        self.save_playlist_btn = QPushButton("💾")
        self.save_playlist_btn.setFixedSize(28, 24)
        self.save_playlist_btn.setToolTip("Guardar playlist")
        header.addWidget(self.save_playlist_btn)

        self.load_playlist_btn = QPushButton("📂")
        self.load_playlist_btn.setFixedSize(28, 24)
        self.load_playlist_btn.setToolTip("Cargar playlist")
        header.addWidget(self.load_playlist_btn)

        self.sort_btn = QToolButton()
        self.sort_btn.setText("Ordenar ▼")
        self.sort_btn.setFixedHeight(24)
        self.sort_btn.setPopupMode(QToolButton.InstantPopup)
        sort_menu = QMenu(self)
        sort_menu.addAction("Nombre", lambda: self._sort_by("name"))
        sort_menu.addAction("Fecha", lambda: self._sort_by("date"))
        sort_menu.addAction("Tamaño", lambda: self._sort_by("size"))
        sort_menu.addAction("Aleatorio", lambda: self._sort_by("random"))
        self.sort_btn.setMenu(sort_menu)
        header.addWidget(self.sort_btn)

        self._play_modes = ["▶ Secuencial", "🔁 Repetir", "🔀 Aleatorio"]
        self._play_mode_index = 0
        self.play_mode_btn = QToolButton()
        self.play_mode_btn.setText("▶")
        self.play_mode_btn.setFixedSize(28, 24)
        self.play_mode_btn.setToolTip("Modo: Secuencial")
        self.play_mode_btn.clicked.connect(self._cycle_play_mode)
        header.addWidget(self.play_mode_btn)

        self.toggle_btn = QPushButton("▲")
        self.toggle_btn.setFixedSize(28, 24)
        self.toggle_btn.setToolTip("Mostrar/ocultar lista")
        self.toggle_btn.clicked.connect(self._toggle_list)
        header.addWidget(self.toggle_btn)

        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(60)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.viewport().setAcceptDrops(True)
        layout.addWidget(self.list_widget, 1)

    def _toggle_list(self):
        self._list_visible = not self._list_visible
        self.list_widget.setVisible(self._list_visible)
        self.toggle_btn.setText("▲" if self._list_visible else "▼")

    def _cycle_play_mode(self):
        icons = ["▶", "🔁", "🔀"]
        labels = ["Secuencial", "Repetir", "Aleatorio"]
        self._play_mode_index = (self._play_mode_index + 1) % len(icons)
        self.play_mode_btn.setText(icons[self._play_mode_index])
        self.play_mode_btn.setToolTip(f"Modo: {labels[self._play_mode_index]}")

    def get_play_mode(self) -> str:
        modes = ["sequential", "repeat", "shuffle"]
        return modes[self._play_mode_index]

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._add_files)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_all)
        self.save_playlist_btn.clicked.connect(self._save_playlist)
        self.load_playlist_btn.clicked.connect(self._load_playlist)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def _add_files(self):
        extensions = " ".join(f"*{ext}" for ext in sorted(AUDIO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Agregar archivos de audio",
            "",
            f"Audio ({extensions});;Todos los archivos (*.*)"
        )
        for f in files:
            self._add_path(f)

    def _add_path(self, path: str):
        ext = Path(path).suffix.lower()
        if ext not in AUDIO_EXTENSIONS:
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
        self._sync_paths_from_list()
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
        self._sync_paths_from_list()
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

    def _save_playlist(self):
        if not self._paths:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar playlist", "",
            "Playlist JSON (*.json);;Todos los archivos (*.*)"
        )
        if not file_path:
            return
        self._sync_paths_from_list()
        data = {"files": list(self._paths)}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_playlist(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir playlist", "",
            "Playlist JSON (*.json);;Todos los archivos (*.*)"
        )
        if not file_path:
            return
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        files = data.get("files", [])
        if not files:
            return
        self._clear_all()
        for path in files:
            if os.path.isfile(path):
                self._add_path(path)

    def _sync_paths_from_list(self):
        self._paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(Qt.UserRole)
            if path:
                self._paths.append(path)
