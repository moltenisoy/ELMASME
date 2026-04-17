import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QToolButton, QFrame, QMenu,
    QTabWidget, QDialog, QCheckBox
)

from content_viewers import ViewerHost
from file_navigation import FileNavigator
from formats import display_type, supported_extensions
from themes import THEME_NAMES, get_theme
from windows_integration import (
    register_file_associations,
    unregister_file_associations,
    open_windows_default_apps_settings,
    supported_extensions_text,
)


class UniversalViewerWindow(QMainWindow):

    def __init__(self, start_path=None):
        super().__init__()
        self.setAcceptDrops(True)
        self._tab_data = {}
        self._current_theme_index = 0
        self._no_multi_playback = False
        self.setWindowTitle("Universal Viewer")
        self.resize(1280, 800)
        self._build_ui()
        self._center_window()

        if start_path:
            self._open_in_new_tab(start_path)
        else:
            self._create_empty_tab()

    def _build_ui(self):
        self._apply_theme(THEME_NAMES[self._current_theme_index])

        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 4, 10, 8)
        layout.setSpacing(8)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        viewer_panel = QFrame()
        viewer_panel.setObjectName("Panel")
        viewer_layout = QVBoxLayout(viewer_panel)
        viewer_layout.setContentsMargins(10, 10, 10, 10)
        viewer_layout.addWidget(self.tab_widget)

        footer = self._build_footer()

        layout.addWidget(viewer_panel, 1)
        layout.addWidget(footer)

        self._setup_shortcuts()
        self._update_tab_bar_visibility()

    def _apply_theme(self, theme_name):
        self.setStyleSheet(get_theme(theme_name))

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("FooterPanel")
        footer.setFixedHeight(44)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 2, 8, 2)
        footer_layout.setSpacing(6)

        self.prev_button = QToolButton()
        self.prev_button.setText("◀ Anterior")
        self.prev_button.setFixedSize(QSize(100, 30))
        self.prev_button.clicked.connect(self.go_previous)

        self.archivo_button = QPushButton("Archivo")
        self.archivo_button.setFixedSize(70, 24)
        self.archivo_button.clicked.connect(self._show_archivo_menu)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(30, 24)
        self.settings_button.clicked.connect(self._show_settings_panel)

        self.file_name_label = QLabel("Sin archivo")
        self.file_name_label.setObjectName("FileNameLabel")
        self.file_name_label.setAlignment(Qt.AlignCenter)

        self.file_path_label = QLabel("")
        self.file_path_label.setObjectName("FilePathLabel")
        self.file_path_label.setAlignment(Qt.AlignCenter)

        info_container = QFrame()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.file_name_label)
        info_layout.addWidget(self.file_path_label)

        self.nav_info_label = QLabel("0 de 0")
        self.nav_info_label.setObjectName("CounterLabel")
        self.nav_info_label.setAlignment(Qt.AlignCenter)

        self.theme_button = QPushButton("🎨 Tema")
        self.theme_button.setFixedSize(80, 24)
        self.theme_button.clicked.connect(self._show_theme_menu)

        self.next_button = QToolButton()
        self.next_button.setText("Siguiente ▶")
        self.next_button.setFixedSize(QSize(100, 30))
        self.next_button.clicked.connect(self.go_next)

        footer_layout.addWidget(self.prev_button)
        footer_layout.addWidget(self.archivo_button)
        footer_layout.addWidget(self.settings_button)
        footer_layout.addStretch(1)
        footer_layout.addWidget(info_container)
        footer_layout.addWidget(self.nav_info_label)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.theme_button)
        footer_layout.addWidget(self.next_button)

        return footer

    def _show_archivo_menu(self):
        menu = QMenu(self)

        abrir_archivo = QAction("Abrir archivo", self)
        abrir_archivo.triggered.connect(self.open_file_dialog)
        menu.addAction(abrir_archivo)

        abrir_carpeta = QAction("Abrir carpeta", self)
        abrir_carpeta.triggered.connect(self.open_folder_dialog)
        menu.addAction(abrir_carpeta)

        menu.exec(self.archivo_button.mapToGlobal(self.archivo_button.rect().topLeft()))

    def _show_settings_panel(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajustes")
        dialog.setFixedSize(450, 280)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setSpacing(12)

        integracion_label = QLabel("Integración")
        integracion_label.setStyleSheet("font-weight:bold;font-size:14px;")
        dlg_layout.addWidget(integracion_label)

        registrar_btn = QPushButton("Registrar asociaciones")
        registrar_btn.clicked.connect(self.register_associations)
        dlg_layout.addWidget(registrar_btn)

        desregistrar_btn = QPushButton("Desregistrar asociaciones")
        desregistrar_btn.clicked.connect(self.unregister_associations)
        dlg_layout.addWidget(desregistrar_btn)

        abrir_default_btn = QPushButton("Abrir apps predeterminadas de Windows")
        abrir_default_btn.clicked.connect(open_windows_default_apps_settings)
        dlg_layout.addWidget(abrir_default_btn)

        dlg_layout.addSpacing(10)

        reproduccion_label = QLabel("Reproducción")
        reproduccion_label.setStyleSheet("font-weight:bold;font-size:14px;")
        dlg_layout.addWidget(reproduccion_label)

        self._no_multi_checkbox = QCheckBox("No permitir reproducción de múltiples archivos simultáneos")
        self._no_multi_checkbox.setChecked(self._no_multi_playback)
        self._no_multi_checkbox.toggled.connect(self._on_no_multi_playback_changed)
        dlg_layout.addWidget(self._no_multi_checkbox)

        dlg_layout.addStretch()

        cerrar_btn = QPushButton("Cerrar")
        cerrar_btn.clicked.connect(dialog.accept)
        dlg_layout.addWidget(cerrar_btn, alignment=Qt.AlignRight)

        dialog.move(
            self.x() + (self.width() - dialog.width()) // 2,
            self.y() + (self.height() - dialog.height()) // 2
        )

        dialog.exec()

    def _on_no_multi_playback_changed(self, checked):
        self._no_multi_playback = checked

    def _show_theme_menu(self):
        menu = QMenu(self)
        for i, name in enumerate(THEME_NAMES):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, idx=i: self._switch_theme(idx))
            menu.addAction(action)
        menu.exec(self.theme_button.mapToGlobal(self.theme_button.rect().topLeft()))

    def _switch_theme(self, index):
        self._current_theme_index = index
        self._apply_theme(THEME_NAMES[index])

    def _setup_shortcuts(self):
        left_action = QAction(self)
        left_action.setShortcut(QKeySequence(Qt.Key_Left))
        left_action.triggered.connect(self.handle_left_key)
        self.addAction(left_action)

        right_action = QAction(self)
        right_action.setShortcut(QKeySequence(Qt.Key_Right))
        right_action.triggered.connect(self.handle_right_key)
        self.addAction(right_action)

        esc_action = QAction(self)
        esc_action.setShortcut(QKeySequence(Qt.Key_Escape))
        esc_action.triggered.connect(self.handle_escape_key)
        self.addAction(esc_action)

        open_action = QAction(self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file_dialog)
        self.addAction(open_action)

    def _center_window(self):
        screen = self.screen()
        if screen:
            geometry = screen.availableGeometry()
            frame = self.frameGeometry()
            frame.moveCenter(geometry.center())
            self.move(frame.topLeft())

    def _update_tab_bar_visibility(self):
        self.tab_widget.tabBar().setVisible(self.tab_widget.count() > 1)

    def _create_empty_tab(self):
        viewer = ViewerHost()
        self._tab_data[id(viewer)] = {
            'navigator': FileNavigator(),
            'current_path': None,
        }
        index = self.tab_widget.addTab(viewer, "Sin archivo")
        self.tab_widget.setCurrentIndex(index)
        viewer.show_message("Abre un archivo o una carpeta para comenzar.")
        self._refresh_navigation()
        self._update_tab_bar_visibility()

    def _open_in_new_tab(self, path):
        viewer = ViewerHost()
        nav = FileNavigator()
        self._tab_data[id(viewer)] = {
            'navigator': nav,
            'current_path': None,
        }
        index = self.tab_widget.addTab(viewer, os.path.basename(path))
        self.tab_widget.setCurrentIndex(index)
        self._load_path_in_tab(path, viewer, nav)
        self._update_tab_bar_visibility()

    def _load_path_in_tab(self, path, viewer, nav):
        if not os.path.exists(path):
            return

        nav.load_from_path(path)
        current = nav.current()

        if not current:
            data = self._tab_data.get(id(viewer))
            if data:
                data['current_path'] = None
            viewer.show_message("No se encontraron archivos compatibles en la carpeta seleccionada.")
            self._refresh_navigation()
            return

        self._load_file_in_tab(current, viewer, nav)

    def _load_file_in_tab(self, path, viewer, nav):
        data = self._tab_data.get(id(viewer))
        if data:
            data['current_path'] = path
        viewer.load_file(path)
        index = self.tab_widget.indexOf(viewer)
        if index >= 0:
            self.tab_widget.setTabText(index, os.path.basename(path))
        self._refresh_navigation()

    def _close_tab(self, index):
        viewer = self.tab_widget.widget(index)
        if viewer and id(viewer) in self._tab_data:
            if self._prompt_unsaved_changes(viewer):
                return
            viewer.stop_media()
            del self._tab_data[id(viewer)]
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self._create_empty_tab()
        self._update_tab_bar_visibility()
        self._refresh_navigation()

    def _on_tab_changed(self, index):
        if index < 0:
            return
        self._refresh_navigation()

    def _current_tab_data(self):
        viewer = self.tab_widget.currentWidget()
        if viewer and id(viewer) in self._tab_data:
            return self._tab_data[id(viewer)], viewer
        return None, None

    def _refresh_navigation(self):
        data, viewer = self._current_tab_data()
        if not data:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.nav_info_label.setText("0 de 0")
            self.file_name_label.setText("Sin archivo")
            self.file_path_label.setText("")
            return

        nav = data['navigator']
        path = data['current_path']

        total = len(nav.files)
        idx = nav.current_index + 1 if nav.current_index >= 0 else 0

        self.prev_button.setEnabled(nav.has_previous())
        self.next_button.setEnabled(nav.has_next())
        self.nav_info_label.setText(f"{idx} de {total}")

        if path:
            self.file_name_label.setText(os.path.basename(path))
            self.file_path_label.setText(os.path.dirname(path))
        else:
            self.file_name_label.setText("Sin archivo")
            self.file_path_label.setText("")

    def _show_open_choice_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Abrir archivo")
        dialog.setFixedSize(400, 130)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(QLabel("¿Cómo desea abrir el archivo?"))

        btn_layout = QHBoxLayout()

        new_tab_btn = QPushButton("Abrir en otra pestaña")
        close_current_btn = QPushButton("Cerrar el actual")
        cancel_btn = QPushButton("Cancelar")

        result = {"choice": None}

        def on_new_tab():
            result["choice"] = "new_tab"
            dialog.accept()

        def on_close_current():
            result["choice"] = "close_current"
            dialog.accept()

        new_tab_btn.clicked.connect(on_new_tab)
        close_current_btn.clicked.connect(on_close_current)
        cancel_btn.clicked.connect(dialog.reject)

        btn_layout.addWidget(new_tab_btn)
        btn_layout.addWidget(close_current_btn)
        btn_layout.addWidget(cancel_btn)
        dlg_layout.addLayout(btn_layout)

        dialog.move(
            self.x() + (self.width() - dialog.width()) // 2,
            self.y() + (self.height() - dialog.height()) // 2
        )

        if dialog.exec() == QDialog.Accepted:
            return result["choice"]
        return None

    def _prompt_unsaved_changes(self, viewer):
        if not viewer.has_unsaved_changes():
            return False

        dialog = QDialog(self)
        dialog.setWindowTitle("Cambios no guardados")
        dialog.setFixedSize(450, 130)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(QLabel("Hay cambios no guardados. ¿Qué desea hacer?"))

        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Guardar")
        save_as_btn = QPushButton("Guardar como")
        cancel_btn = QPushButton("Cancelar")

        result = {"choice": None}

        def on_save():
            result["choice"] = "save"
            dialog.accept()

        def on_save_as():
            result["choice"] = "save_as"
            dialog.accept()

        save_btn.clicked.connect(on_save)
        save_as_btn.clicked.connect(on_save_as)
        cancel_btn.clicked.connect(dialog.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(save_as_btn)
        btn_layout.addWidget(cancel_btn)
        dlg_layout.addLayout(btn_layout)

        dialog.move(
            self.x() + (self.width() - dialog.width()) // 2,
            self.y() + (self.height() - dialog.height()) // 2
        )

        if dialog.exec() == QDialog.Accepted:
            if result["choice"] == "save":
                viewer.save_document()
            elif result["choice"] == "save_as":
                viewer.save_document_as()
            return False

        return True

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _stop_all_media(self):
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if w:
                w.stop_media()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path and os.path.exists(path):
                    paths.append(path)

            for path in paths:
                if self._no_multi_playback:
                    data, viewer = self._current_tab_data()
                    if data and viewer:
                        if self._prompt_unsaved_changes(viewer):
                            continue
                        self._stop_all_media()
                        self._load_path_in_tab(path, viewer, data['navigator'])
                    else:
                        self._stop_all_media()
                        self._open_in_new_tab(path)
                else:
                    data, viewer = self._current_tab_data()
                    if data and data['current_path']:
                        self._open_in_new_tab(path)
                    else:
                        if viewer and data:
                            self._load_path_in_tab(path, viewer, data['navigator'])
                        else:
                            self._open_in_new_tab(path)

            event.acceptProposedAction()

    def open_file_dialog(self):
        data, viewer = self._current_tab_data()

        if self._no_multi_playback:
            if data and viewer:
                if self._prompt_unsaved_changes(viewer):
                    return
            extensions = " ".join(f"*{ext}" for ext in supported_extensions())
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Abrir archivo", "", f"Archivos compatibles ({extensions})"
            )
            if file_path:
                self._stop_all_media()
                if viewer and data:
                    self._load_path_in_tab(file_path, viewer, data['navigator'])
                else:
                    self._open_in_new_tab(file_path)
            return

        if data and data['current_path']:
            choice = self._show_open_choice_dialog()
            if choice == "new_tab":
                extensions = " ".join(f"*{ext}" for ext in supported_extensions())
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Abrir archivo", "", f"Archivos compatibles ({extensions})"
                )
                if file_path:
                    self._open_in_new_tab(file_path)
            elif choice == "close_current":
                if self._prompt_unsaved_changes(viewer):
                    return
                extensions = " ".join(f"*{ext}" for ext in supported_extensions())
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Abrir archivo", "", f"Archivos compatibles ({extensions})"
                )
                if file_path:
                    self._load_path_in_tab(file_path, viewer, data['navigator'])
            return

        extensions = " ".join(f"*{ext}" for ext in supported_extensions())
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo", "", f"Archivos compatibles ({extensions})"
        )
        if file_path:
            if viewer and data:
                self._load_path_in_tab(file_path, viewer, data['navigator'])
            else:
                self._open_in_new_tab(file_path)

    def open_folder_dialog(self):
        data, viewer = self._current_tab_data()

        if self._no_multi_playback:
            if data and viewer:
                if self._prompt_unsaved_changes(viewer):
                    return
            folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
            if folder:
                self._stop_all_media()
                if viewer and data:
                    self._load_path_in_tab(folder, viewer, data['navigator'])
                else:
                    self._open_in_new_tab(folder)
            return

        if data and data['current_path']:
            choice = self._show_open_choice_dialog()
            if choice == "new_tab":
                folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
                if folder:
                    self._open_in_new_tab(folder)
            elif choice == "close_current":
                if self._prompt_unsaved_changes(viewer):
                    return
                folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
                if folder:
                    self._load_path_in_tab(folder, viewer, data['navigator'])
            return

        folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
        if folder:
            if viewer and data:
                self._load_path_in_tab(folder, viewer, data['navigator'])
            else:
                self._open_in_new_tab(folder)

    def load_path(self, path: str):
        if not os.path.exists(path):
            return

        data, viewer = self._current_tab_data()
        if viewer and data:
            self._load_path_in_tab(path, viewer, data['navigator'])

    def _load_current(self, path: str):
        data, viewer = self._current_tab_data()
        if viewer and data:
            self._load_file_in_tab(path, viewer, data['navigator'])

    def go_previous(self):
        data, viewer = self._current_tab_data()
        if not data:
            return
        if self._prompt_unsaved_changes(viewer):
            return
        nav = data['navigator']
        path = nav.previous()
        if path:
            self._load_file_in_tab(path, viewer, nav)

    def go_next(self):
        data, viewer = self._current_tab_data()
        if not data:
            return
        if self._prompt_unsaved_changes(viewer):
            return
        nav = data['navigator']
        path = nav.next()
        if path:
            self._load_file_in_tab(path, viewer, nav)

    def handle_left_key(self):
        data, viewer = self._current_tab_data()
        if not viewer:
            return
        if viewer.video_viewer.video_widget.hasFocus():
            return
        self.go_previous()

    def handle_right_key(self):
        data, viewer = self._current_tab_data()
        if not viewer:
            return
        if viewer.video_viewer.video_widget.hasFocus():
            return
        self.go_next()

    def handle_escape_key(self):
        data, viewer = self._current_tab_data()
        if viewer and viewer.video_viewer.is_fullscreen:
            viewer.video_viewer.exit_fullscreen()

    def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            viewer = self.tab_widget.widget(i)
            if viewer and id(viewer) in self._tab_data and viewer.has_unsaved_changes():
                self.tab_widget.setCurrentIndex(i)
                if self._prompt_unsaved_changes(viewer):
                    event.ignore()
                    return
        event.accept()

    def register_associations(self):
        register_file_associations()
        QMessageBox.information(
            self,
            "Asociaciones registradas",
            "Se registró la aplicación para extensiones compatibles.\n\n"
            f"Extensiones:\n{supported_extensions_text()}\n\n"
            "Si deseas establecerla como predeterminada, completa la selección "
            "desde la configuración de aplicaciones predeterminadas de Windows."
        )

    def unregister_associations(self):
        unregister_file_associations()
        QMessageBox.information(
            self,
            "Asociaciones eliminadas",
            "Se eliminaron las asociaciones registradas por la aplicación."
        )
