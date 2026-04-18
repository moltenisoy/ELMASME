
import os
import sys
from PySide6.QtWidgets import QApplication
from app_window import UniversalViewerWindow


def resolve_start_path() -> str | None:
    if len(sys.argv) > 1:
        candidate = os.path.abspath(sys.argv[1].strip('"'))
        if os.path.exists(candidate):
            return candidate
    return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("UniversalViewer")
    app.setOrganizationName("UniversalViewer")
    
    start_path = resolve_start_path()
    
    window = UniversalViewerWindow(start_path=start_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
