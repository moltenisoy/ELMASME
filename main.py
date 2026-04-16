"""
Universal Viewer - Visor universal de archivos multimedia y documentos.

Punto de entrada principal de la aplicación.
"""

import os
import sys
from PySide6.QtWidgets import QApplication
from app_window import UniversalViewerWindow


def resolve_start_path() -> str | None:
    """
    Resuelve la ruta inicial desde los argumentos de línea de comandos.
    
    Returns:
        Ruta absoluta del archivo/carpeta o None si no se proporcionó
    """
    if len(sys.argv) > 1:
        candidate = os.path.abspath(sys.argv[1].strip('"'))
        if os.path.exists(candidate):
            return candidate
    return None


def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    app.setApplicationName("UniversalViewer")
    app.setOrganizationName("UniversalViewer")
    
    # Resolver ruta inicial
    start_path = resolve_start_path()
    
    # Crear y mostrar ventana principal
    window = UniversalViewerWindow(start_path=start_path)
    window.show()
    
    # Ejecutar bucle de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
