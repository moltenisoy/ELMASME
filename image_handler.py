"""
Módulo para manejo de archivos de imagen.
Re-exporta desde image_converter e image_viewer para compatibilidad.
"""
from image_converter import (  # noqa: F401
    IMAGE_EXTENSIONS,
    FORMAT_NAMES,
    TRANSPARENT_FORMATS,
    get_image_info,
    save_image,
    resize_image,
    ImageResizeDialog,
)
from image_viewer import (  # noqa: F401
    PanLabel,
    ImageViewer,
)
