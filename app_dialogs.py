from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QTextEdit, QGridLayout, QLineEdit, QMessageBox,
    QKeySequenceEdit,
)


class SettingsDialog(QDialog):

    def __init__(self, parent, theme_names, current_theme_index, no_multi_playback,
                 on_register, on_unregister, on_open_defaults,
                 on_no_multi_changed, on_switch_theme,
                 shortcuts=None, on_shortcuts_changed=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustes")
        self.setFixedSize(450, 420)

        dlg_layout = QVBoxLayout(self)
        dlg_layout.setSpacing(12)

        integracion_label = QLabel("Integración")
        integracion_label.setStyleSheet("font-weight:bold;font-size:14px;")
        dlg_layout.addWidget(integracion_label)

        registrar_btn = QPushButton("Registrar asociaciones")
        registrar_btn.clicked.connect(on_register)
        dlg_layout.addWidget(registrar_btn)

        desregistrar_btn = QPushButton("Desregistrar asociaciones")
        desregistrar_btn.clicked.connect(on_unregister)
        dlg_layout.addWidget(desregistrar_btn)

        abrir_default_btn = QPushButton("Abrir apps predeterminadas de Windows")
        abrir_default_btn.clicked.connect(on_open_defaults)
        dlg_layout.addWidget(abrir_default_btn)

        dlg_layout.addSpacing(10)

        reproduccion_label = QLabel("Reproducción")
        reproduccion_label.setStyleSheet("font-weight:bold;font-size:14px;")
        dlg_layout.addWidget(reproduccion_label)

        no_multi_checkbox = QCheckBox("No permitir reproducción de múltiples archivos simultáneos")
        no_multi_checkbox.setChecked(no_multi_playback)
        no_multi_checkbox.toggled.connect(on_no_multi_changed)
        dlg_layout.addWidget(no_multi_checkbox)

        dlg_layout.addSpacing(10)

        tema_label = QLabel("Tema")
        tema_label.setStyleSheet("font-weight:bold;font-size:14px;")
        dlg_layout.addWidget(tema_label)

        tema_layout = QHBoxLayout()
        for i, name in enumerate(theme_names):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, idx=i: on_switch_theme(idx))
            tema_layout.addWidget(btn)
        dlg_layout.addLayout(tema_layout)

        dlg_layout.addSpacing(10)

        atajos_label = QLabel("Atajos de teclado")
        atajos_label.setStyleSheet("font-weight:bold;font-size:14px;")
        dlg_layout.addWidget(atajos_label)

        self._shortcuts = dict(shortcuts) if shortcuts else {}
        self._on_shortcuts_changed = on_shortcuts_changed

        atajos_btn = QPushButton("⌨️ Configurar atajos de teclado")
        atajos_btn.clicked.connect(self._open_shortcuts_dialog)
        dlg_layout.addWidget(atajos_btn)

        dlg_layout.addStretch()

        cerrar_btn = QPushButton("Cerrar")
        cerrar_btn.clicked.connect(self.accept)
        dlg_layout.addWidget(cerrar_btn, alignment=Qt.AlignRight)

    def _open_shortcuts_dialog(self):
        dialog = ShortcutConfigDialog(self._shortcuts, self)
        if dialog.exec() == QDialog.Accepted:
            self._shortcuts = dialog.get_shortcuts()
            if self._on_shortcuts_changed:
                self._on_shortcuts_changed(self._shortcuts)


class OpenChoiceDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abrir archivo")
        self.setFixedSize(400, 130)
        self._choice = None

        dlg_layout = QVBoxLayout(self)
        dlg_layout.addWidget(QLabel("¿Cómo desea abrir el archivo?"))

        btn_layout = QHBoxLayout()

        new_tab_btn = QPushButton("Abrir en otra pestaña")
        close_current_btn = QPushButton("Cerrar el actual")
        cancel_btn = QPushButton("Cancelar")

        new_tab_btn.clicked.connect(lambda: self._set_choice("new_tab"))
        close_current_btn.clicked.connect(lambda: self._set_choice("close_current"))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(new_tab_btn)
        btn_layout.addWidget(close_current_btn)
        btn_layout.addWidget(cancel_btn)
        dlg_layout.addLayout(btn_layout)

    def _set_choice(self, choice):
        self._choice = choice
        self.accept()

    def get_choice(self):
        return self._choice


class UnsavedChangesDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cambios no guardados")
        self.setFixedSize(520, 130)
        self._choice = None

        dlg_layout = QVBoxLayout(self)
        dlg_layout.addWidget(QLabel("Hay cambios no guardados. ¿Qué desea hacer?"))

        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Guardar")
        save_as_btn = QPushButton("Guardar como")
        discard_btn = QPushButton("Cerrar sin guardar")
        cancel_btn = QPushButton("Cancelar")

        save_btn.clicked.connect(lambda: self._set_choice("save"))
        save_as_btn.clicked.connect(lambda: self._set_choice("save_as"))
        discard_btn.clicked.connect(lambda: self._set_choice("discard"))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(save_as_btn)
        btn_layout.addWidget(discard_btn)
        btn_layout.addWidget(cancel_btn)
        dlg_layout.addLayout(btn_layout)

    def _set_choice(self, choice):
        self._choice = choice
        self.accept()

    def get_choice(self):
        return self._choice


class WelcomeDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bienvenido a ELMASME")
        self.setFixedSize(300, 300)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        dlg_layout = QVBoxLayout(self)
        dlg_layout.setContentsMargins(16, 16, 16, 16)
        dlg_layout.setSpacing(10)

        title_label = QLabel("¡Bienvenido a ELMASME!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        dlg_layout.addWidget(title_label)

        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setPlainText(
            "ELMASME es un visor universal de archivos.\n\n"
            "Soporta imágenes, audio, video, documentos, "
            "PDF, hojas de cálculo, presentaciones, "
            "archivos comprimidos y libros electrónicos.\n\n"
            "Usa el menú Archivo para abrir archivos o "
            "arrastra y suelta archivos en la ventana.\n\n"
            "Configura las asociaciones de archivos desde "
            "el botón ⚙ de ajustes."
        )
        dlg_layout.addWidget(text_area, 1)

        self._no_show_checkbox = QCheckBox("No mostrar más al iniciar")
        dlg_layout.addWidget(self._no_show_checkbox)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        dlg_layout.addWidget(close_btn, alignment=Qt.AlignCenter)

    def no_show_checked(self):
        return self._no_show_checkbox.isChecked()


_SHORTCUT_LABELS = {
    "navigate_left": "Archivo anterior",
    "navigate_right": "Archivo siguiente",
    "escape": "Salir / Cerrar",
    "open_file": "Abrir archivo",
}


class ShortcutConfigDialog(QDialog):
    """Dialog for configuring keyboard shortcuts."""

    def __init__(self, shortcuts: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar atajos de teclado")
        self.setMinimumSize(480, 280)
        self._shortcuts = dict(shortcuts)
        self._editors = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "Haga clic en un campo y presione la combinación de teclas deseada:"
        ))

        grid = QGridLayout()
        grid.setSpacing(8)

        row = 0
        for key, current_seq in sorted(self._shortcuts.items()):
            label_text = _SHORTCUT_LABELS.get(key, key)
            grid.addWidget(QLabel(label_text), row, 0)

            editor = QKeySequenceEdit()
            editor.setKeySequence(QKeySequence(current_seq))
            grid.addWidget(editor, row, 1)
            self._editors[key] = editor

            reset_btn = QPushButton("↺")
            reset_btn.setFixedWidth(32)
            reset_btn.setToolTip("Restablecer valor predeterminado")
            from settings import _DEFAULTS
            default_val = _DEFAULTS.get("shortcuts", {}).get(key, "")
            reset_btn.clicked.connect(
                lambda checked, ed=editor, dv=default_val: ed.setKeySequence(QKeySequence(dv))
            )
            grid.addWidget(reset_btn, row, 2)

            row += 1

        layout.addLayout(grid)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        for key, editor in self._editors.items():
            seq = editor.keySequence()
            self._shortcuts[key] = seq.toString()
        self.accept()

    def get_shortcuts(self) -> dict:
        return self._shortcuts
