
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


def join_audio_files(
    input_paths: List[str],
    output_path: str,
    output_format: str,
    crossfade_seconds: float = 0.0,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> bool:
    """Join multiple audio files into one, with optional crossfade between tracks.

    Args:
        input_paths: List of audio file paths to concatenate.
        output_path: Output file path.
        output_format: Output format extension (e.g. '.mp3').
        crossfade_seconds: Crossfade overlap in seconds between tracks (0 = no crossfade).
        progress_callback: Optional callback for progress updates.

    Returns:
        True if successful.
    """
    if not is_ffmpeg_available():
        raise RuntimeError("ffmpeg no está instalado o no está disponible en el PATH")

    if len(input_paths) < 2:
        raise ValueError("Se necesitan al menos 2 archivos para unir.")

    codec_map = {
        ".mp3": "libmp3lame",
        ".wav": "pcm_s16le",
        ".flac": "flac",
        ".ogg": "libvorbis",
        ".m4a": "aac",
        ".aac": "aac",
        ".wma": "wmav2",
        ".opus": "libopus",
    }
    codec = codec_map.get(output_format.lower(), "copy")

    if crossfade_seconds <= 0:
        concat_list_path = output_path + ".txt"
        try:
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for p in input_paths:
                    safe_path = p.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list_path,
                "-c:a", codec,
            ]
            cmd.append(output_path)

            if progress_callback:
                progress_callback(0)

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate(timeout=600)

            if progress_callback:
                progress_callback(100)

            return process.returncode == 0 and os.path.exists(output_path)
        except subprocess.TimeoutExpired:
            process.kill()
            return False
        except Exception:
            return False
        finally:
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
    else:
        try:
            if progress_callback:
                progress_callback(0)

            n = len(input_paths)
            filter_parts = []
            inputs = []

            for i, p in enumerate(input_paths):
                inputs.extend(["-i", p])

            for i in range(n):
                filter_parts.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}];")

            if n == 2:
                cf = crossfade_seconds
                filter_parts.append(
                    f"[a0][a1]acrossfade=d={cf}:c1=tri:c2=tri[out]"
                )
            else:
                cf = crossfade_seconds
                filter_parts.append(
                    f"[a0][a1]acrossfade=d={cf}:c1=tri:c2=tri[tmp1];"
                )
                for i in range(2, n):
                    if i < n - 1:
                        filter_parts.append(
                            f"[tmp{i-1}][a{i}]acrossfade=d={cf}:c1=tri:c2=tri[tmp{i}];"
                        )
                    else:
                        filter_parts.append(
                            f"[tmp{i-1}][a{i}]acrossfade=d={cf}:c1=tri:c2=tri[out]"
                        )

            filter_complex = "".join(filter_parts)

            cmd = ["ffmpeg", "-y"]
            cmd.extend(inputs)
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-c:a", codec,
                output_path
            ])

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate(timeout=600)

            if progress_callback:
                progress_callback(100)

            return process.returncode == 0 and os.path.exists(output_path)
        except subprocess.TimeoutExpired:
            process.kill()
            return False
        except Exception:
            return False

