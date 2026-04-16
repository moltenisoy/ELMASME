"""
Módulo para manejo de archivos de video.
Re-exporta desde video_converter, video_player y video_playlist para compatibilidad.
"""
from video_converter import (  # noqa: F401
    VIDEO_EXTENSIONS,
    FORMAT_NAMES,
    FORMAT_CODECS,
    get_video_info,
    is_ffmpeg_available,
    convert_video,
    get_supported_output_formats,
    VideoConverterDialog,
    VideoBatchConverterDialog,
)
from video_player import (  # noqa: F401
    ClickableVideoWidget,
    VideoViewer,
)
from video_playlist import VideoPlaylistWidget  # noqa: F401
