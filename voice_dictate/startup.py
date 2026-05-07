"""Autostart management via HKCU registry Run key — no admin required."""
from __future__ import annotations

import sys
import winreg
from pathlib import Path

_REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "VoiceDictate"


def _exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    # Development: installed via pip entry point or direct python -m
    return f'"{sys.executable}" -m voice_dictate'


def enable() -> bool:
    """Register app in HKCU Run. Returns True on success."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _exe_path())
        return True
    except Exception as e:
        print(f"[startup] enable failed: {e}")
        return False


def disable() -> bool:
    """Remove app from HKCU Run. Returns True on success."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass
        return True
    except Exception as e:
        print(f"[startup] disable failed: {e}")
        return False


def is_enabled() -> bool:
    """Check if app is in HKCU Run."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_READ
        ) as key:
            winreg.QueryValueEx(key, _APP_NAME)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def toggle() -> bool:
    """Toggle autostart. Returns new state (True = enabled)."""
    if is_enabled():
        disable()
        return False
    else:
        enable()
        return True
