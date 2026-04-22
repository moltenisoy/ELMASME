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
    "show_welcome": True,
    "shortcuts": {
        "navigate_left": "Left",
        "navigate_right": "Right",
        "escape": "Escape",
        "open_file": "Ctrl+O",
    },
    "recent_files": [],
}

_MAX_RECENT_FILES = 20


def load_settings() -> dict:
    settings = dict(_DEFAULTS)
    settings["shortcuts"] = dict(_DEFAULTS["shortcuts"])
    settings["recent_files"] = list(_DEFAULTS["recent_files"])
    try:
        if os.path.isfile(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key in _DEFAULTS:
                    if key in data:
                        if key == "shortcuts" and isinstance(data[key], dict):
                            for sk, sv in data[key].items():
                                if sk in _DEFAULTS["shortcuts"]:
                                    settings["shortcuts"][sk] = sv
                        elif key == "recent_files" and isinstance(data[key], list):
                            settings["recent_files"] = [
                                p for p in data[key] if isinstance(p, str)
                            ]
                        else:
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


def add_recent_file(path: str) -> None:
    """Add *path* to the top of the recent files list and persist."""
    settings = load_settings()
    recent = [p for p in settings.get("recent_files", []) if p != path]
    recent.insert(0, path)
    settings["recent_files"] = recent[:_MAX_RECENT_FILES]
    save_settings(settings)


def get_recent_files() -> list:
    """Return the list of recent file paths (most-recent first)."""
    settings = load_settings()
    return [p for p in settings.get("recent_files", []) if os.path.isfile(p)]
