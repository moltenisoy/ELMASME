
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Callable

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".m4v", ".flv"
}

FORMAT_NAMES = {
    ".mp4": "MP4 (MPEG-4)",
    ".mkv": "MKV (Matroska)",
    ".avi": "AVI (Audio Video Interleave)",
    ".mov": "MOV (QuickTime)",
    ".wmv": "WMV (Windows Media Video)",
    ".webm": "WEBM (Web Media)",
    ".m4v": "M4V (iTunes Video)",
    ".flv": "FLV (Flash Video)"
}

FORMAT_CODECS = {
    ".mp4": {"video": "libx264", "audio": "aac"},
    ".mkv": {"video": "libx264", "audio": "aac"},
    ".avi": {"video": "libxvid", "audio": "mp3"},
    ".mov": {"video": "libx264", "audio": "aac"},
    ".wmv": {"video": "wmv2", "audio": "wmav2"},
    ".webm": {"video": "libvpx-vp9", "audio": "libopus"},
    ".m4v": {"video": "libx264", "audio": "aac"},
    ".flv": {"video": "libx264", "audio": "aac"}
}


def get_video_info(path: str) -> Dict:
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "duration": 0,
        "bitrate": 0,
        "width": 0,
        "height": 0,
        "fps": 0,
        "video_codec": "",
        "audio_codec": ""
    }
    
    if os.path.exists(path):
        info["size"] = os.path.getsize(path)
    
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            if "format" in data:
                fmt = data["format"]
                info["duration"] = float(fmt.get("duration", 0))
                info["bitrate"] = int(fmt.get("bit_rate", 0)) // 1000
            
            if "streams" in data:
                for stream in data["streams"]:
                    if stream.get("codec_type") == "video":
                        info["width"] = stream.get("width", 0)
                        info["height"] = stream.get("height", 0)
                        info["video_codec"] = stream.get("codec_name", "")
                        avg_frame_rate = stream.get("avg_frame_rate", "0/1")
                        if "/" in avg_frame_rate:
                            num, den = avg_frame_rate.split("/")
                            if int(den) != 0:
                                info["fps"] = round(int(num) / int(den), 2)
                    elif stream.get("codec_type") == "audio":
                        info["audio_codec"] = stream.get("codec_name", "")
    
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    
    return info


def is_ffmpeg_available() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_video(
    input_path: str,
    output_path: str,
    output_format: str,
    quality: str = "high",
    progress_callback: Optional[Callable[[int], None]] = None,
    resolution: Optional[str] = None,
    framerate: Optional[int] = None
) -> bool:
    if not is_ffmpeg_available():
        raise RuntimeError("ffmpeg no está instalado o no está disponible en el PATH")
    
    codecs = FORMAT_CODECS.get(output_format.lower(), {"video": "copy", "audio": "copy"})
    
    quality_presets = {
        "low": {"crf": "28", "preset": "veryfast", "audio_bitrate": "96k"},
        "medium": {"crf": "23", "preset": "medium", "audio_bitrate": "128k"},
        "high": {"crf": "18", "preset": "slow", "audio_bitrate": "192k"},
        "original": {"crf": "copy", "preset": "medium", "audio_bitrate": "copy"}
    }
    
    preset = quality_presets.get(quality, quality_presets["high"])
    
    cmd = ["ffmpeg", "-y", "-i", input_path]
    
    if quality == "original" and not resolution and not framerate:
        cmd.extend(["-c:v", "copy"])
    else:
        if quality == "original":
            cmd.extend(["-c:v", codecs["video"]])
        else:
            cmd.extend([
                "-c:v", codecs["video"],
                "-crf", preset["crf"],
                "-preset", preset["preset"]
            ])
        
        if resolution:
            res_map = {
                "480p": "854:480",
                "720p": "1280:720",
                "1080p": "1920:1080",
                "4K": "3840:2160"
            }
            scale = res_map.get(resolution)
            if scale:
                w, h = scale.split(":")
                cmd.extend(["-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"])
        
        if framerate:
            cmd.extend(["-r", str(framerate)])
    
    if quality == "original" or preset["audio_bitrate"] == "copy":
        if not resolution and not framerate:
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", codecs["audio"], "-b:a", "192k"])
    else:
        cmd.extend([
            "-c:a", codecs["audio"],
            "-b:a", preset["audio_bitrate"]
        ])
    
    cmd.append(output_path)
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        if progress_callback:
            progress_callback(0)
            import time
            for i in range(10):
                time.sleep(0.2)
                progress_callback((i + 1) * 10)
        
        stdout, stderr = process.communicate(timeout=600)
        
        if progress_callback:
            progress_callback(100)
        
        return process.returncode == 0 and os.path.exists(output_path)
    
    except subprocess.TimeoutExpired:
        process.kill()
        return False
    except Exception:
        return False


def get_supported_output_formats(input_format: str) -> List[str]:
    return sorted([ext for ext in VIDEO_EXTENSIONS if ext != input_format.lower()])

