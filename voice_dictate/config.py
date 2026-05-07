"""Configuration — stored in %APPDATA%\\VoiceDictate\\config.json."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Use %APPDATA% in installed builds, project dir in dev mode
def _config_dir() -> Path:
    # Dev mode: running from source — store next to package root
    if getattr(sys, "frozen", False):
        # PyInstaller exe: always use AppData
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    d = base / "VoiceDictate"
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_DIR = _config_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"
LOG_PATH = CONFIG_DIR / "voice_dictate.log"

DEFAULTS: dict[str, Any] = {
    "model": "small",
    "language": "pl",
    "hotkey": "ctrl+alt+space",
    "widget_pos": None,
    "widget_visible": True,
    "use_gpu": False,
}


def load() -> dict[str, Any]:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user = json.load(f)
            if isinstance(user, dict):
                cfg.update({k: v for k, v in user.items() if k in DEFAULTS})
        except Exception as e:
            print(f"[config] read error: {e}")
    return cfg


def save(cfg: dict[str, Any]) -> None:
    try:
        clean = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[config] write error: {e}")


def update(**kwargs: Any) -> dict[str, Any]:
    cfg = load()
    cfg.update(kwargs)
    save(cfg)
    return cfg
