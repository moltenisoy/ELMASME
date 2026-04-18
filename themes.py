THEME_NAMES = ["Oscuro", "Claro", "Cyberpunk 2038", "Retro Terminal"]


def get_theme(name):
    return _THEMES.get(name, _THEMES["Oscuro"])


_THEMES = {
    "Oscuro": """
        QMainWindow { background: #0a0a0a; }
        QWidget { color: #e5e7eb; font-family: 'Segoe UI'; font-size: 13px; }
        QMenu { background: #141414; color: #e5e7eb; border: 1px solid rgba(148,163,184,0.2); }
        QMenu::item:selected { background: rgba(255,255,255,0.12); }
        QPushButton, QToolButton {
            background: rgba(28,28,28,0.92);
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 8px;
            padding: 1px 6px;
        }
        QPushButton:hover, QToolButton:hover {
            background: rgba(50,50,50,0.96);
            border: 1px solid rgba(180,180,180,0.45);
        }
        QPushButton:pressed, QToolButton:pressed {
            background: rgba(70,70,70,0.55);
        }
        QLabel#FileNameLabel { font-size: 13px; font-weight: 600; color: #f8fafc; }
        QLabel#FilePathLabel { color: #94a3b8; font-size: 11px; }
        QLabel#CounterLabel {
            font-size: 12px; font-weight: 500; color: #cbd5e1;
            background: rgba(10,10,10,0.6); padding: 4px 12px; border-radius: 12px;
        }
        QFrame#Panel {
            background: rgba(10,10,10,0.92);
            border: 1px solid rgba(148,163,184,0.12);
            border-radius: 12px;
        }
        QFrame#FooterPanel {
            background: rgba(10,10,10,0.85);
            border: 1px solid rgba(148,163,184,0.1);
            border-radius: 10px;
            padding: 4px;
        }
        QTextEdit {
            background: #1a1a1a; color: #f1f5f9;
            border: 1px solid rgba(148,163,184,0.2);
            border-radius: 10px; padding: 8px;
            selection-background-color: rgba(150,150,150,0.4);
        }
        QTabWidget::pane { border: none; background: transparent; }
        QTabBar::tab {
            background: rgba(28,28,28,0.92); color: #e5e7eb;
            border: 1px solid rgba(148,163,184,0.18);
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            padding: 6px 16px; margin-right: 2px;
        }
        QTabBar::tab:selected { background: rgba(255,255,255,0.15); border-bottom-color: transparent; }
        QTabBar::tab:hover { background: rgba(50,50,50,0.96); }
        QListWidget {
            background: #141414;
            border: 1px solid rgba(148,163,184,0.15);
            border-radius: 8px;
        }
        QListWidget::item { padding: 4px; }
        QListWidget::item:selected { background: rgba(255,255,255,0.15); }
        QListWidget::item:alternate { background: rgba(28,28,28,0.5); }
        QSlider::groove:horizontal {
            background: #1a1a1a; height: 6px; border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #a0a0a0; width: 14px; height: 14px;
            margin: -4px 0; border-radius: 7px;
        }
        QSlider::sub-page:horizontal { background: #a0a0a0; border-radius: 3px; }
        QComboBox {
            background: #1a1a1a; color: #e5e7eb;
            border: 1px solid rgba(148,163,184,0.3);
            border-radius: 4px; padding: 2px 8px;
        }
        QComboBox::drop-down {
            border-left: 1px solid rgba(148,163,184,0.3);
            background: rgba(255,255,255,0.08);
        }
        QComboBox QAbstractItemView {
            background: #141414; color: #e5e7eb;
            selection-background-color: rgba(255,255,255,0.15);
        }
        QScrollBar:horizontal, QScrollBar:vertical {
            background: #1a1a1a; border-radius: 4px;
        }
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
            background: #475569; border-radius: 4px;
        }
        QToolTip {
            background: #1a1a1a; color: #f1f5f9;
            border: 1px solid rgba(148,163,184,0.3);
            padding: 4px;
        }
        QMessageBox { background: #0a0a0a; color: #e5e7eb; }
        QDialog { background: #0a0a0a; color: #e5e7eb; }
        QInputDialog { background: #0a0a0a; color: #e5e7eb; }
    """,

    "Claro": """
        QMainWindow { background: #f8fafc; }
        QWidget { color: #1e293b; font-family: 'Segoe UI'; font-size: 13px; }
        QMenu { background: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; }
        QMenu::item:selected { background: #e0f2fe; }
        QPushButton, QToolButton {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 1px 6px;
            color: #1e293b;
        }
        QPushButton:hover, QToolButton:hover {
            background: #f0f9ff;
            border: 1px solid #93c5fd;
        }
        QPushButton:pressed, QToolButton:pressed {
            background: #dbeafe;
        }
        QLabel#FileNameLabel { font-size: 13px; font-weight: 600; color: #0f172a; }
        QLabel#FilePathLabel { color: #64748b; font-size: 11px; }
        QLabel#CounterLabel {
            font-size: 12px; font-weight: 500; color: #475569;
            background: #f1f5f9; padding: 4px 12px; border-radius: 12px;
        }
        QFrame#Panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }
        QFrame#FooterPanel {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 4px;
        }
        QTextEdit {
            background: #ffffff; color: #1e293b;
            border: 1px solid #e2e8f0;
            border-radius: 10px; padding: 8px;
            selection-background-color: rgba(59,130,246,0.3);
        }
        QTabWidget::pane { border: none; background: transparent; }
        QTabBar::tab {
            background: #f1f5f9; color: #1e293b;
            border: 1px solid #e2e8f0;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            padding: 6px 16px; margin-right: 2px;
        }
        QTabBar::tab:selected { background: #dbeafe; border-bottom-color: transparent; }
        QTabBar::tab:hover { background: #e0f2fe; }
        QListWidget {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
        QListWidget::item { padding: 4px; color: #1e293b; }
        QListWidget::item:selected { background: #dbeafe; }
        QListWidget::item:alternate { background: #f8fafc; }
        QSlider::groove:horizontal {
            background: #e2e8f0; height: 6px; border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #3b82f6; width: 14px; height: 14px;
            margin: -4px 0; border-radius: 7px;
        }
        QSlider::sub-page:horizontal { background: #3b82f6; border-radius: 3px; }
        QComboBox {
            background: #ffffff; color: #1e293b;
            border: 1px solid #cbd5e1;
            border-radius: 4px; padding: 2px 8px;
        }
        QComboBox::drop-down {
            border-left: 1px solid #cbd5e1;
            background: #f0f9ff;
        }
        QComboBox QAbstractItemView {
            background: #ffffff; color: #1e293b;
            selection-background-color: #dbeafe;
        }
        QScrollBar:horizontal, QScrollBar:vertical {
            background: #f1f5f9; border-radius: 4px;
        }
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
            background: #94a3b8; border-radius: 4px;
        }
        QToolTip {
            background: #ffffff; color: #1e293b;
            border: 1px solid #cbd5e1;
            padding: 4px;
        }
        QMessageBox { background: #f8fafc; color: #1e293b; }
        QDialog { background: #f8fafc; color: #1e293b; }
        QInputDialog { background: #f8fafc; color: #1e293b; }
    """,

    "Cyberpunk 2038": """
        QMainWindow { background: #0d0d17; }
        QWidget {
            color: #00ffd5; font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
        }
        QMenu {
            background: #12121f; color: #fcdb03;
            border: 1px solid #fcdb03;
        }
        QMenu::item:selected { background: rgba(252,219,3,0.2); }
        QPushButton, QToolButton {
            background: rgba(13,13,23,0.95);
            border: 1px solid #fcdb03;
            border-radius: 0px;
            padding: 1px 6px;
            color: #fcdb03;
            font-weight: bold;
        }
        QPushButton:hover, QToolButton:hover {
            background: rgba(252,219,3,0.15);
            border: 1px solid #00ffd5;
            color: #00ffd5;
        }
        QPushButton:pressed, QToolButton:pressed {
            background: rgba(252,219,3,0.3);
            color: #ff003c;
        }
        QLabel#FileNameLabel { font-size: 13px; font-weight: 600; color: #fcdb03; }
        QLabel#FilePathLabel { color: #00ffd5; font-size: 11px; }
        QLabel#CounterLabel {
            font-size: 12px; font-weight: 500; color: #fcdb03;
            background: rgba(252,219,3,0.1); padding: 4px 12px;
            border-radius: 0px; border: 1px solid #fcdb03;
        }
        QFrame#Panel {
            background: rgba(13,13,23,0.95);
            border: 1px solid rgba(252,219,3,0.4);
            border-radius: 0px;
        }
        QFrame#FooterPanel {
            background: rgba(13,13,23,0.9);
            border: 1px solid rgba(252,219,3,0.3);
            border-radius: 0px;
            padding: 4px;
        }
        QTextEdit {
            background: #0d0d17; color: #00ffd5;
            border: 1px solid #fcdb03;
            border-radius: 0px; padding: 8px;
            selection-background-color: rgba(252,219,3,0.3);
            font-family: 'Consolas', monospace;
        }
        QTabWidget::pane { border: none; background: transparent; }
        QTabBar::tab {
            background: rgba(13,13,23,0.95); color: #fcdb03;
            border: 1px solid rgba(252,219,3,0.4);
            border-top-left-radius: 0px; border-top-right-radius: 0px;
            padding: 6px 16px; margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: rgba(252,219,3,0.2);
            border-bottom-color: transparent;
        }
        QTabBar::tab:hover { background: rgba(0,255,213,0.1); }
        QListWidget {
            background: #0d0d17;
            border: 1px solid rgba(252,219,3,0.3);
            border-radius: 0px;
        }
        QListWidget::item { padding: 4px; color: #00ffd5; }
        QListWidget::item:selected { background: rgba(252,219,3,0.2); }
        QListWidget::item:alternate { background: rgba(18,18,31,0.8); }
        QSlider::groove:horizontal {
            background: #1a1a2e; height: 6px;
            border-radius: 0px; border: 1px solid #fcdb03;
        }
        QSlider::handle:horizontal {
            background: #fcdb03; width: 14px; height: 14px;
            margin: -4px 0; border-radius: 0px;
        }
        QSlider::sub-page:horizontal { background: #ff003c; border-radius: 0px; }
        QComboBox {
            background: #12121f; color: #fcdb03;
            border: 1px solid #fcdb03;
            border-radius: 0px; padding: 2px 8px;
        }
        QComboBox::drop-down {
            border-left: 1px solid #fcdb03;
            background: rgba(252,219,3,0.1);
        }
        QComboBox QAbstractItemView {
            background: #12121f; color: #fcdb03;
            selection-background-color: rgba(252,219,3,0.2);
        }
        QScrollBar:horizontal, QScrollBar:vertical {
            background: #0d0d17; border-radius: 0px;
        }
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
            background: #fcdb03; border-radius: 0px;
        }
        QToolTip {
            background: #12121f; color: #fcdb03;
            border: 1px solid #fcdb03;
            padding: 4px;
        }
        QMessageBox { background: #0d0d17; color: #00ffd5; }
        QDialog { background: #0d0d17; color: #00ffd5; }
        QInputDialog { background: #0d0d17; color: #00ffd5; }
    """,

    "Retro Terminal": """
        QMainWindow { background: #001100; }
        QWidget {
            color: #00ff00; font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
        }
        QMenu { background: #001a00; color: #00ff00; border: 1px solid #00aa00; }
        QMenu::item:selected { background: rgba(0,255,0,0.15); }
        QPushButton, QToolButton {
            background: #001a00;
            border: 1px solid #00aa00;
            border-radius: 2px;
            padding: 1px 6px;
            color: #00ff00;
        }
        QPushButton:hover, QToolButton:hover {
            background: #003300;
            border: 1px solid #00ff00;
        }
        QPushButton:pressed, QToolButton:pressed {
            background: #004400;
        }
        QLabel#FileNameLabel { font-size: 13px; font-weight: 600; color: #00ff00; }
        QLabel#FilePathLabel { color: #00aa00; font-size: 11px; }
        QLabel#CounterLabel {
            font-size: 12px; font-weight: 500; color: #00ff00;
            background: rgba(0,170,0,0.15); padding: 4px 12px; border-radius: 2px;
        }
        QFrame#Panel {
            background: rgba(0,17,0,0.95);
            border: 1px solid rgba(0,170,0,0.4);
            border-radius: 2px;
        }
        QFrame#FooterPanel {
            background: rgba(0,17,0,0.9);
            border: 1px solid rgba(0,170,0,0.3);
            border-radius: 2px;
            padding: 4px;
        }
        QTextEdit {
            background: #001100; color: #00ff00;
            border: 1px solid #00aa00;
            border-radius: 2px; padding: 8px;
            selection-background-color: rgba(0,255,0,0.3);
            font-family: 'Consolas', monospace;
        }
        QTabWidget::pane { border: none; background: transparent; }
        QTabBar::tab {
            background: #001a00; color: #00ff00;
            border: 1px solid rgba(0,170,0,0.4);
            border-top-left-radius: 2px; border-top-right-radius: 2px;
            padding: 6px 16px; margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: rgba(0,255,0,0.15);
            border-bottom-color: transparent;
        }
        QTabBar::tab:hover { background: rgba(0,255,0,0.1); }
        QListWidget {
            background: #001100;
            border: 1px solid rgba(0,170,0,0.3);
            border-radius: 2px;
        }
        QListWidget::item { padding: 4px; color: #00ff00; }
        QListWidget::item:selected { background: rgba(0,255,0,0.15); }
        QListWidget::item:alternate { background: rgba(0,26,0,0.8); }
        QSlider::groove:horizontal {
            background: #001a00; height: 6px;
            border-radius: 2px; border: 1px solid #00aa00;
        }
        QSlider::handle:horizontal {
            background: #00ff00; width: 14px; height: 14px;
            margin: -4px 0; border-radius: 2px;
        }
        QSlider::sub-page:horizontal { background: #00aa00; border-radius: 2px; }
        QComboBox {
            background: #001a00; color: #00ff00;
            border: 1px solid #00aa00;
            border-radius: 2px; padding: 2px 8px;
        }
        QComboBox::drop-down {
            border-left: 1px solid #00aa00;
            background: rgba(0,170,0,0.1);
        }
        QComboBox QAbstractItemView {
            background: #001a00; color: #00ff00;
            selection-background-color: rgba(0,255,0,0.15);
        }
        QScrollBar:horizontal, QScrollBar:vertical {
            background: #001100; border-radius: 2px;
        }
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
            background: #00aa00; border-radius: 2px;
        }
        QToolTip {
            background: #001a00; color: #00ff00;
            border: 1px solid #00aa00;
            padding: 4px;
        }
        QMessageBox { background: #001100; color: #00ff00; }
        QDialog { background: #001100; color: #00ff00; }
        QInputDialog { background: #001100; color: #00ff00; }
    """,
}
