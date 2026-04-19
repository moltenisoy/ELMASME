
import os
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader, QImage, QPixmap

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff",
    ".heif", ".heic", ".avif"
}

FORMAT_NAMES = {
    ".png": "PNG (Portable Network Graphics)",
    ".jpg": "JPEG (Joint Photographic Experts Group)",
    ".jpeg": "JPEG (Joint Photographic Experts Group)",
    ".bmp": "BMP (Bitmap)",
    ".gif": "GIF (Graphics Interchange Format)",
    ".webp": "WEBP (Web Picture Format)",
    ".tif": "TIFF (Tagged Image File Format)",
    ".tiff": "TIFF (Tagged Image File Format)",
    ".heif": "HEIF (High Efficiency Image Format)",
    ".heic": "HEIC (High Efficiency Image Coding)",
    ".avif": "AVIF (AV1 Image File Format)"
}

TRANSPARENT_FORMATS = {".png", ".gif", ".webp", ".tif", ".tiff", ".avif"}


def get_image_info(path: str) -> Dict:
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "width": 0,
        "height": 0,
        "format": "",
        "has_alpha": False
    }
    
    if os.path.exists(path):
        info["size"] = os.path.getsize(path)
    
    ext = info["extension"]
    if ext in (".heif", ".heic", ".avif"):
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.open(path)
            info["width"] = pil_img.width
            info["height"] = pil_img.height
            info["format"] = pil_img.format or ext[1:].upper()
            info["has_alpha"] = pil_img.mode in ("RGBA", "LA", "PA")
            return info
        except (ImportError, Exception):
            pass
    
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    
    size = reader.size()
    if size.isValid():
        info["width"] = size.width()
        info["height"] = size.height()
    
    info["format"] = reader.format().data().decode().upper() if reader.format() else "Unknown"
    
    image = reader.read()
    if not image.isNull():
        info["has_alpha"] = image.hasAlphaChannel()
    
    return info


def save_image(
    image: QImage,
    path: str,
    format: Optional[str] = None,
    quality: int = 90
) -> bool:
    if image.isNull():
        return False
    
    fmt_lower = (format or Path(path).suffix[1:]).lower() if format or Path(path).suffix else ""
    
    if fmt_lower in ("heif", "heic", "avif"):
        try:
            from PIL import Image as PILImage
            
            converted = image.convertToFormat(QImage.Format_RGBA8888)
            w = converted.width()
            h = converted.height()
            pil_img = PILImage.frombytes("RGBA", (w, h), bytes(converted.constBits()))
            
            save_fmt = "AVIF" if fmt_lower == "avif" else "HEIF"
            pil_img.save(path, save_fmt, quality=quality)
            return True
        except (ImportError, Exception):
            return False
    
    if format:
        fmt = format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        return image.save(path, fmt, quality)
    else:
        return image.save(path, None, quality)


INTERPOLATION_METHODS = {
    "nearest": Qt.FastTransformation,
    "bilinear": Qt.SmoothTransformation,
    "bicubic": Qt.SmoothTransformation,
    "lanczos": Qt.SmoothTransformation,
}

INTERPOLATION_NAMES = {
    "nearest": "Nearest Neighbor",
    "bilinear": "Bilinear",
    "bicubic": "Bicubic",
    "lanczos": "Lanczos",
}


def resize_image(
    image: QImage,
    width: int,
    height: int,
    keep_aspect: bool = True,
    smooth: bool = True,
    interpolation: str = "bilinear"
) -> QImage:
    if image.isNull():
        return QImage()
    
    aspect_mode = Qt.KeepAspectRatio if keep_aspect else Qt.IgnoreAspectRatio
    transform_mode = INTERPOLATION_METHODS.get(interpolation, Qt.SmoothTransformation)
    
    try:
        from PIL import Image as PILImage
        
        w = image.width()
        h = image.height()
        
        converted = image.convertToFormat(QImage.Format_RGBA8888)
        pil_img = PILImage.frombytes("RGBA", (w, h), bytes(converted.constBits()))
        
        pil_interp = {
            "nearest": PILImage.NEAREST,
            "bilinear": PILImage.BILINEAR,
            "bicubic": PILImage.BICUBIC,
            "lanczos": PILImage.LANCZOS,
        }.get(interpolation, PILImage.BILINEAR)
        
        if keep_aspect:
            ratio = min(width / w, height / h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
        else:
            new_w = width
            new_h = height
        
        resized = pil_img.resize((new_w, new_h), pil_interp)
        
        data = resized.tobytes("raw", "RGBA")
        result = QImage(data, new_w, new_h, new_w * 4, QImage.Format_RGBA8888).copy()
        return result
    except (ImportError, Exception):
        return image.scaled(width, height, aspect_mode, transform_mode)



def crop_image(image: QImage, x: int, y: int, width: int, height: int) -> QImage:
    return image.copy(x, y, width, height)

