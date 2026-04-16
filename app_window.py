import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QToolButton, QFrame, QMenuBar, QMenu
)

from content_viewers import ViewerHost
from file_navigation import FileNavigator
from formats import display_type, supported_extensions
from windows_integration import (
    register_file_associations,
    unregister_file_associations,
    open_windows_default_apps_settings,
    supported_extensions_text,
)

class UniversalViewerWindow(QMainWindow):
    
    def __init__(self, start_path=None):
        super().__init__()
        
        self.navigator = FileNavigator()
        self.viewer = ViewerHost()
        self.current_path = None
        
        self.setWindowTitle("Universal Viewer")
        self.resize(1280, 800)
        
        self._build_ui()
        self._center_window()
        
        if start_path:
            self.load_path(start_path)
        else:
            self.viewer.show_message("Abre un archivo o una carpeta para comenzar.")
    
    def _build_ui(self):
        self._apply_styles()
        self._build_menu()
        
        root = QWidget()
        self.setCentralWidget(root)
        
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 4, 10, 8)
        layout.setSpacing(8)
        
        viewer_panel = QFrame()
        viewer_panel.setObjectName("Panel")
        viewer_layout = QVBoxLayout(viewer_panel)
        viewer_layout.setContentsMargins(10, 10, 10, 10)
        viewer_layout.addWidget(self.viewer)
        
        footer = self._build_footer()
        
        layout.addWidget(viewer_panel, 1)
        layout.addWidget(footer)
        
        self._setup_shortcuts()
        self._refresh_navigation()
    
    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #0f172a;
            }
            QWidget {
                color: #e5e7eb;
                font-family: Segoe UI;
                font-size: 13px;
            }
            QMenuBar {
                background: rgba(15, 23, 42, 0.95);
                color: #e5e7eb;
                border: 0;
                padding: 4px 8px;
                min-height: 26px;
            }
            QMenuBar::item {
                padding: 4px 12px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background: rgba(59, 130, 246, 0.2);
                border-radius: 6px;
            }
            QMenu {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid rgba(148, 163, 184, 0.2);
            }
            QMenu::item:selected {
                background: rgba(59, 130, 246, 0.22);
            }
            QPushButton, QToolButton {
                background: rgba(30, 41, 59, 0.92);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 8px;
                padding: 6px 12px;
                min-height: 16px;
            }
            QPushButton:hover, QToolButton:hover {
                background: rgba(51, 65, 85, 0.96);
                border: 1px solid rgba(96, 165, 250, 0.45);
            }
            QPushButton:pressed, QToolButton:pressed {
                background: rgba(30, 64, 175, 0.55);
            }
            QLabel#FileNameLabel {
                font-size: 13px;
                font-weight: 600;
                color: #f8fafc;
            }
            QLabel#FilePathLabel {
                color: #94a3b8;
                font-size: 11px;
            }
            QLabel#CounterLabel {
                font-size: 12px;
                font-weight: 500;
                color: #cbd5e1;
                background: rgba(15, 23, 42, 0.6);
                padding: 4px 12px;
                border-radius: 12px;
            }
            QFrame#Panel {
                background: rgba(15, 23, 42, 0.92);
                border: 1px solid rgba(148, 163, 184, 0.12);
                border-radius: 12px;
            }
            QFrame#FooterPanel {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 10px;
                padding: 4px;
            }
            QTextEdit {
                background: #1e293b;
                color: #f1f5f9;
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 10px;
                padding: 8px;
                selection-background-color: rgba(59, 130, 246, 0.4);
            }
        """)
    
    def _build_menu(self):
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        archivo_menu = menu_bar.addMenu("Archivo")
        
        abrir_archivo = QAction("Abrir archivo", self)
        abrir_archivo.setShortcut(QKeySequence.Open)
        abrir_archivo.triggered.connect(self.open_file_dialog)
        
        abrir_carpeta = QAction("Abrir carpeta", self)
        abrir_carpeta.triggered.connect(self.open_folder_dialog)
        
        salir = QAction("Salir", self)
        salir.triggered.connect(self.close)
        
        archivo_menu.addAction(abrir_archivo)
        archivo_menu.addAction(abrir_carpeta)
        archivo_menu.addSeparator()
        archivo_menu.addAction(salir)
        
        integrar_menu = menu_bar.addMenu("Integración")
        
        registrar = QAction("Registrar asociaciones", self)
        registrar.triggered.connect(self.register_associations)
        
        desregistrar = QAction("Desregistrar asociaciones", self)
        desregistrar.triggered.connect(self.unregister_associations)
        
        abrir_default_apps = QAction("Abrir apps predeterminadas de Windows", self)
        abrir_default_apps.triggered.connect(open_windows_default_apps_settings)
        
        integrar_menu.addAction(registrar)
        integrar_menu.addAction(desregistrar)
        integrar_menu.addAction(abrir_default_apps)
    
    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("FooterPanel")
        footer.setFixedHeight(80)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 6, 12, 6)
        footer_layout.setSpacing(12)
        
        self.prev_button = QToolButton()
        self.prev_button.setText("◀ Anterior")
        self.prev_button.setFixedSize(QSize(160, 68))
        self.prev_button.clicked.connect(self.go_previous)
        
        self.archivo_button = QPushButton("Archivo")
        self.archivo_button.setFixedSize(80, 34)
        self.archivo_button.clicked.connect(self._show_archivo_menu)
        
        self.integracion_button = QPushButton("Integración")
        self.integracion_button.setFixedSize(90, 34)
        self.integracion_button.clicked.connect(self._show_integracion_menu)
        
        buttons_container = QFrame()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(4)
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.addWidget(self.archivo_button)
        buttons_layout.addWidget(self.integracion_button)
        
        info_container = QFrame()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignCenter)
        
        self.file_name_label = QLabel("Sin archivo")
        self.file_name_label.setObjectName("FileNameLabel")
        self.file_name_label.setAlignment(Qt.AlignCenter)
        
        self.file_path_label = QLabel("")
        self.file_path_label.setObjectName("FilePathLabel")
        self.file_path_label.setAlignment(Qt.AlignCenter)
        
        info_layout.addWidget(self.file_name_label)
        info_layout.addWidget(self.file_path_label)
        
        self.nav_info_label = QLabel("0 de 0")
        self.nav_info_label.setObjectName("CounterLabel")
        self.nav_info_label.setAlignment(Qt.AlignCenter)
        
        self.next_button = QToolButton()
        self.next_button.setText("Siguiente ▶")
        self.next_button.setFixedSize(QSize(160, 68))
        self.next_button.clicked.connect(self.go_next)
        
        footer_layout.addWidget(self.prev_button)
        footer_layout.addWidget(buttons_container)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.nav_info_label)
        footer_layout.addWidget(info_container, 2)
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
    
    def _show_integracion_menu(self):
        menu = QMenu(self)
        
        registrar = QAction("Registrar asociaciones", self)
        registrar.triggered.connect(self.register_associations)
        menu.addAction(registrar)
        
        desregistrar = QAction("Desregistrar asociaciones", self)
        desregistrar.triggered.connect(self.unregister_associations)
        menu.addAction(desregistrar)
        
        abrir_default_apps = QAction("Abrir apps predeterminadas de Windows", self)
        abrir_default_apps.triggered.connect(open_windows_default_apps_settings)
        menu.addAction(abrir_default_apps)
        
        menu.exec(self.integracion_button.mapToGlobal(self.integracion_button.rect().topLeft()))
    
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
    
    def open_file_dialog(self):
        extensions = " ".join(f"*{ext}" for ext in supported_extensions())
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo",
            "",
            f"Archivos compatibles ({extensions})"
        )
        if file_path:
            self.load_path(file_path)
    
    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Abrir carpeta", "")
        if folder:
            self.load_path(folder)
    
    def load_path(self, path: str):
        if not os.path.exists(path):
            QMessageBox.warning(
                self,
                "Ruta inválida",
                "La ruta seleccionada no existe."
            )
            return
        
        self.navigator.load_from_path(path)
        current = self.navigator.current()
        
        if not current:
            self.current_path = None
            self.file_name_label.setText("Sin archivo compatible")
            self.file_path_label.setText("")
            self.viewer.show_message(
                "No se encontraron archivos compatibles en la carpeta seleccionada."
            )
            self._refresh_navigation()
            return
        
        self._load_current(current)
    
    def _load_current(self, path: str):
        self.current_path = path
        self.viewer.load_file(path)
        
        file_name = os.path.basename(path)
        directory = os.path.dirname(path)
        
        self.file_name_label.setText(file_name)
        self.file_path_label.setText(directory)
        
        self._refresh_navigation()
    
    def _refresh_navigation(self):
        total = len(self.navigator.files)
        index = self.navigator.current_index + 1 if self.navigator.current_index >= 0 else 0
        
        self.prev_button.setEnabled(self.navigator.has_previous())
        self.next_button.setEnabled(self.navigator.has_next())
        self.nav_info_label.setText(f"{index} de {total}")
    
    def go_previous(self):
        path = self.navigator.previous()
        if path:
            self._load_current(path)
    
    def go_next(self):
        path = self.navigator.next()
        if path:
            self._load_current(path)
    
    def handle_left_key(self):
        if not hasattr(self.viewer.video_viewer, 'navigation_enabled') or \
           not self.viewer.video_viewer.navigation_enabled:
            self.go_previous()
    
    def handle_right_key(self):
        if not hasattr(self.viewer.video_viewer, 'navigation_enabled') or \
           not self.viewer.video_viewer.navigation_enabled:
            self.go_next()
    
    def handle_escape_key(self):
        if self.viewer.video_viewer.is_fullscreen:
            self.viewer.video_viewer.exit_fullscreen()
    
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
