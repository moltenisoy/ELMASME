"""
Módulo central de formatos y tipos de archivo.
Define extensiones soportadas y funciones de identificación de tipos.
"""

from pathlib import Path

# Importar extensiones desde los handlers
from audio_handler import AUDIO_EXTENSIONS
from video_handler import VIDEO_EXTENSIONS
from image_handler import IMAGE_EXTENSIONS
from document_handler import PDF_EXTENSIONS, TEXT_DOCUMENT_EXTENSIONS, DOCX_EXTENSIONS, DOCUMENT_EXTENSIONS

# Extensiones asociables en Windows
ALL_SUPPORTED_EXTENSIONS = (
    IMAGE_EXTENSIONS
    | AUDIO_EXTENSIONS
    | VIDEO_EXTENSIONS
    | DOCUMENT_EXTENSIONS
)

ASSOCIATION_EXTENSIONS = sorted(ALL_SUPPORTED_EXTENSIONS)

# Etiquetas para mostrar al usuario
TYPE_LABELS = {
    "image": "Imagen",
    "audio": "Audio",
    "video": "Video",
    "pdf": "PDF",
    "text": "Documento",
    "unsupported": "No compatible",
}


def normalize_extension(path: str) -> str:
    """Normaliza la extensión de un archivo a minúsculas."""
    return Path(path).suffix.lower()


def get_content_type(path: str) -> str:
    """
    Determina el tipo de contenido de un archivo.
    
    Returns:
        Uno de: "image", "audio", "video", "pdf", "text", "unsupported"
    """
    ext = normalize_extension(path)
    
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in TEXT_DOCUMENT_EXTENSIONS or ext in DOCX_EXTENSIONS:
        return "text"
    
    return "unsupported"


def is_supported(path: str) -> bool:
    """Verifica si un archivo tiene un formato soportado."""
    return normalize_extension(path) in ALL_SUPPORTED_EXTENSIONS


def display_type(path: str) -> str:
    """Retorna una etiqueta legible del tipo de archivo."""
    return TYPE_LABELS.get(get_content_type(path), "No compatible")


def supported_extensions():
    """Retorna la lista de extensiones soportadas ordenadas."""
    return sorted(ALL_SUPPORTED_EXTENSIONS)


def get_file_category(path: str) -> str:
    """
    Retorna la categoría general del archivo.
    
    Returns:
        Una de: "media", "document", "image", "unsupported"
    """
    content_type = get_content_type(path)
    
    if content_type in ("audio", "video"):
        return "media"
    if content_type in ("pdf", "text"):
        return "document"
    if content_type == "image":
        return "image"
    
    return "unsupported"


# Funciones de utilidad para obtener extensiones por tipo
def get_audio_extensions():
    """Retorna las extensiones de audio soportadas."""
    return sorted(AUDIO_EXTENSIONS)


def get_video_extensions():
    """Retorna las extensiones de video soportadas."""
    return sorted(VIDEO_EXTENSIONS)


def get_image_extensions():
    """Retorna las extensiones de imagen soportadas."""
    return sorted(IMAGE_EXTENSIONS)


def get_document_extensions():
    """Retorna las extensiones de documento soportadas."""
    return sorted(DOCUMENT_EXTENSIONS)
