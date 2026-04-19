
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict, Callable

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma",
    ".mid", ".midi", ".opus"
}

QT_SUPPORTED_AUDIO = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}

FORMAT_NAMES = {
    ".mp3": "MP3 (MPEG Audio)",
    ".wav": "WAV (Waveform Audio)",
    ".flac": "FLAC (Free Lossless Audio Codec)",
    ".ogg": "OGG Vorbis",
    ".m4a": "M4A (AAC Audio)",
    ".aac": "AAC (Advanced Audio Coding)",
    ".wma": "WMA (Windows Media Audio)",
    ".mid": "MIDI (Musical Instrument Digital Interface)",
    ".midi": "MIDI (Musical Instrument Digital Interface)",
    ".opus": "OPUS (Opus Audio Codec)"
}


def get_audio_info(path: str) -> Dict:
    info = {
        "path": path,
        "filename": os.path.basename(path),
        "extension": Path(path).suffix.lower(),
        "size": 0,
        "duration": 0,
        "bitrate": 0,
        "sample_rate": 0,
        "channels": 0
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
            if "streams" in data and len(data["streams"]) > 0:
                stream = data["streams"][0]
                info["sample_rate"] = int(stream.get("sample_rate", 0))
                info["channels"] = stream.get("channels", 0)
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


def convert_audio(
    input_path: str,
    output_path: str,
    output_format: str,
    progress_callback: Optional[Callable[[int], None]] = None,
    bitrate: Optional[int] = None,
    sample_rate: Optional[int] = None
) -> bool:
    if not is_ffmpeg_available():
        raise RuntimeError("ffmpeg no está instalado o no está disponible en el PATH")
    
    codec_map = {
        ".mp3": "libmp3lame",
        ".wav": "pcm_s16le",
        ".flac": "flac",
        ".ogg": "libvorbis",
        ".m4a": "aac",
        ".aac": "aac",
        ".wma": "wmav2",
        ".opus": "libopus"
    }
    
    codec = codec_map.get(output_format.lower(), "copy")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-c:a", codec,
    ]
    
    if bitrate:
        cmd.extend(["-b:a", f"{bitrate}k"])
    else:
        cmd.extend(["-q:a", "2"])
    
    if sample_rate:
        cmd.extend(["-ar", str(sample_rate)])
    
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
            for i in range(10):
                time.sleep(0.1)
                progress_callback((i + 1) * 10)
        
        stdout, stderr = process.communicate(timeout=300)
        
        if progress_callback:
            progress_callback(100)
        
        return process.returncode == 0 and os.path.exists(output_path)
    
    except subprocess.TimeoutExpired:
        process.kill()
        return False
    except Exception:
        return False


def get_supported_output_formats(input_format: str) -> List[str]:
    return sorted([ext for ext in AUDIO_EXTENSIONS if ext != input_format.lower()])

