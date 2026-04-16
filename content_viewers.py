"""
Módulo principal de visores de contenido.
Coordina los visores especializados para cada tipo de archivo.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel
)

from formats import get_content_type
from image_handler import ImageViewer
from audio_handler import AudioViewer
from video_handler import VideoViewer
from document_handler import DocumentViewer


class ViewerHost(QWidget):
    """
    Host principal que gestiona los diferentes visores de contenido.
    Selecciona automáticamente el visor apropiado según el tipo de archivo.
    """
    
    def __init__(self):
        super().__init__()
        
        # Crear instancias de los visores especializados
        self.image_viewer = ImageViewer()
        self.audio_viewer = AudioViewer()
        self.video_viewer = VideoViewer()
        self.document_viewer = DocumentViewer()
        
        # Widget para mensajes
        self.message = QLabel()
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(
            "background:#111827;border-radius:14px;color:#cbd5e1;padding:24px;font-size:15px;"
        )
        
        # Stack para cambiar entre visores
        self.stack = QStackedWidget()
        self.stack.addWidget(self.image_viewer)      # Índice 0
        self.stack.addWidget(self.audio_viewer)      # Índice 1
        self.stack.addWidget(self.video_viewer)      # Índice 2
        self.stack.addWidget(self.document_viewer)   # Índice 3
        self.stack.addWidget(self.message)           # Índice 4
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
    
    def stop_media(self):
        """Detiene cualquier reproducción de medios activa."""
        self.audio_viewer.stop()
        self.video_viewer.stop()
        if self.video_viewer.is_fullscreen:
            self.video_viewer.exit_fullscreen()
    
    def load_file(self, path: str):
        """
        Carga un archivo en el visor apropiado.
        
        Args:
            path: Ruta del archivo a cargar
        """
        self.stop_media()
        
        kind = get_content_type(path)
        
        if kind == "image":
            self.image_viewer.load_file(path)
            self.stack.setCurrentWidget(self.image_viewer)
            return
        
        if kind == "audio":
            self.audio_viewer.load_file(path)
            self.stack.setCurrentWidget(self.audio_viewer)
            return
        
        if kind == "video":
            self.video_viewer.load_file(path)
            self.stack.setCurrentWidget(self.video_viewer)
            return
        
        if kind in ("pdf", "text"):
            self.document_viewer.load_file(path)
            self.stack.setCurrentWidget(self.document_viewer)
            return
        
        # Formato no soportado
        self.message.setText("Formato de archivo no compatible.")
        self.stack.setCurrentWidget(self.message)
    
    def show_message(self, text: str):
        """Muestra un mensaje en el visor."""
        self.stop_media()
        self.message.setText(text)
        self.stack.setCurrentWidget(self.message)
    
    def minimumSizeHint(self):
        """Tamaño mínimo sugerido para el widget."""
        return QSize(900, 620)
    
    # Propiedades de acceso para compatibilidad con código existente
    @property
    def media_viewer(self):
        """
        Retorna el visor de video para compatibilidad.
        Nota: Ahora audio y video tienen visores separados.
        """
        return self.video_viewer
