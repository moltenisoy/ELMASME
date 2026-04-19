from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QSpinBox, QDialogButtonBox,
    QLabel, QLineEdit, QGridLayout, QGroupBox,
)


class InsertTableDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insertar tabla")
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QDialog { background: #1e293b; }
            QLabel { color: #e5e7eb; font-size: 13px; }
            QSpinBox {
                background: #0f172a; color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 4px; padding: 4px; min-width: 80px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(3)
        form.addRow("Filas:", self.rows_spin)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 26)
        self.cols_spin.setValue(3)
        form.addRow("Columnas:", self.cols_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                background: rgba(59,130,246,0.2);
                border: 1px solid rgba(59,130,246,0.4);
                border-radius: 6px; padding: 6px 16px;
                color: #60a5fa; font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(59,130,246,0.35);
            }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return self.rows_spin.value(), self.cols_spin.value()


class HeaderFooterDialog(QDialog):

    def __init__(self, header_left="", header_center="", header_right="",
                 footer_left="", footer_center="", footer_right="",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encabezado y pie de página")
        self.setFixedSize(500, 340)
        self.setStyleSheet("""
            QDialog { background: #1e293b; }
            QLabel { color: #e5e7eb; font-size: 12px; }
            QGroupBox {
                color: #60a5fa; font-weight: 600; font-size: 13px;
                border: 1px solid rgba(96,165,250,0.3);
                border-radius: 6px; margin-top: 8px; padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
            }
            QLineEdit {
                background: #0f172a; color: #e5e7eb;
                border: 1px solid rgba(148,163,184,0.3);
                border-radius: 4px; padding: 6px 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel("Variables: {filename} = nombre del archivo, {page} = nº de página, {date} = fecha")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(hint)

        header_group = QGroupBox("Encabezado")
        hg_layout = QGridLayout(header_group)
        hg_layout.setSpacing(6)
        hg_layout.addWidget(QLabel("Izquierda:"), 0, 0)
        self.header_left = QLineEdit(header_left)
        hg_layout.addWidget(self.header_left, 0, 1)
        hg_layout.addWidget(QLabel("Centro:"), 1, 0)
        self.header_center = QLineEdit(header_center)
        hg_layout.addWidget(self.header_center, 1, 1)
        hg_layout.addWidget(QLabel("Derecha:"), 2, 0)
        self.header_right = QLineEdit(header_right)
        hg_layout.addWidget(self.header_right, 2, 1)
        layout.addWidget(header_group)

        footer_group = QGroupBox("Pie de página")
        fg_layout = QGridLayout(footer_group)
        fg_layout.setSpacing(6)
        fg_layout.addWidget(QLabel("Izquierda:"), 0, 0)
        self.footer_left = QLineEdit(footer_left)
        fg_layout.addWidget(self.footer_left, 0, 1)
        fg_layout.addWidget(QLabel("Centro:"), 1, 0)
        self.footer_center = QLineEdit(footer_center)
        fg_layout.addWidget(self.footer_center, 1, 1)
        fg_layout.addWidget(QLabel("Derecha:"), 2, 0)
        self.footer_right = QLineEdit(footer_right)
        fg_layout.addWidget(self.footer_right, 2, 1)
        layout.addWidget(footer_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                background: rgba(59,130,246,0.2);
                border: 1px solid rgba(59,130,246,0.4);
                border-radius: 6px; padding: 6px 16px;
                color: #60a5fa; font-weight: 500;
            }
            QPushButton:hover { background: rgba(59,130,246,0.35); }
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return {
            "header_left": self.header_left.text(),
            "header_center": self.header_center.text(),
            "header_right": self.header_right.text(),
            "footer_left": self.footer_left.text(),
            "footer_center": self.footer_center.text(),
            "footer_right": self.footer_right.text(),
        }
