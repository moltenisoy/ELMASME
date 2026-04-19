import json
import os
from pathlib import Path


def _get_settings_dir() -> str:
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    settings_dir = os.path.join(base, "ELMASME")
    os.makedirs(settings_dir, exist_ok=True)
    return settings_dir


_SETTINGS_FILE = os.path.join(_get_settings_dir(), "settings.json")

_DEFAULTS = {
    "theme_index": 0,
    "no_multi_playback": False,
}


def load_settings() -> dict:
    settings = dict(_DEFAULTS)
    try:
        if os.path.isfile(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key in _DEFAULTS:
                    if key in data:
                        settings[key] = data[key]
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    return settings


def save_settings(settings: dict) -> None:
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except OSError:
        pass
