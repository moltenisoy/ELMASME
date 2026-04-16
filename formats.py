from pathlib import Path

from audio_handler import AUDIO_EXTENSIONS
from video_handler import VIDEO_EXTENSIONS
from image_handler import IMAGE_EXTENSIONS
from document_handler import PDF_EXTENSIONS, TEXT_DOCUMENT_EXTENSIONS, DOCUMENT_EXTENSIONS

ALL_SUPPORTED_EXTENSIONS = (
    IMAGE_EXTENSIONS
    | AUDIO_EXTENSIONS
    | VIDEO_EXTENSIONS
    | DOCUMENT_EXTENSIONS
)

ASSOCIATION_EXTENSIONS = sorted(ALL_SUPPORTED_EXTENSIONS)

TYPE_LABELS = {
    "image": "Imagen",
    "audio": "Audio",
    "video": "Video",
    "pdf": "PDF",
    "text": "Documento",
    "unsupported": "No compatible",
}

def normalize_extension(path: str) -> str:
    return Path(path).suffix.lower()

def get_content_type(path: str) -> str:
    ext = normalize_extension(path)
    
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in TEXT_DOCUMENT_EXTENSIONS:
        return "text"
    
    return "unsupported"

def is_supported(path: str) -> bool:
    return normalize_extension(path) in ALL_SUPPORTED_EXTENSIONS

def display_type(path: str) -> str:
    return TYPE_LABELS.get(get_content_type(path), "No compatible")

def supported_extensions():
    return sorted(ALL_SUPPORTED_EXTENSIONS)

def get_file_category(path: str) -> str:
    content_type = get_content_type(path)
    
    if content_type in ("audio", "video"):
        return "media"
    if content_type in ("pdf", "text"):
        return "document"
    if content_type == "image":
        return "image"
    
    return "unsupported"

def get_audio_extensions():
    return sorted(AUDIO_EXTENSIONS)

def get_video_extensions():
    return sorted(VIDEO_EXTENSIONS)

def get_image_extensions():
    return sorted(IMAGE_EXTENSIONS)

def get_document_extensions():
    return sorted(DOCUMENT_EXTENSIONS)
