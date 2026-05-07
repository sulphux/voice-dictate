"""Configuration loader/saver for voice-dictate."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULTS: dict[str, Any] = {
    "model": "small",
    "language": "pl",
    "hotkey": "ctrl+alt+space",
    "widget_pos": None,            # [x, y] or None -> auto bottom-right
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
            print(f"[config] failed to read {CONFIG_PATH}: {e}")
    return cfg


def save(cfg: dict[str, Any]) -> None:
    try:
        clean = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[config] failed to write {CONFIG_PATH}: {e}")


def update(**kwargs: Any) -> dict[str, Any]:
    """Load, update with kwargs, save, return new config."""
    cfg = load()
    cfg.update(kwargs)
    save(cfg)
    return cfg
