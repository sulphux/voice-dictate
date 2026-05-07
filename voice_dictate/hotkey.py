"""Global hotkey via WinAPI RegisterHotKey — no administrator rights required."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QThread, Signal

WM_HOTKEY = 0x0312
MOD_ALT     = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT   = 0x0004
MOD_WIN     = 0x0008
MOD_NOREPEAT = 0x4000

_VK_MAP: dict[str, int] = {
    "space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
    "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "`": 0xC0, "-": 0xBD, "=": 0xBB, "[": 0xDB, "]": 0xDD,
    ";": 0xBA, "'": 0xDE, ",": 0xBC, ".": 0xBE, "/": 0xBF, "\\": 0xDC,
}
# Add A-Z
for _c in "abcdefghijklmnopqrstuvwxyz":
    _VK_MAP[_c] = ord(_c.upper())


def _parse_hotkey(hotkey: str) -> tuple[int, int]:
    """Parse 'ctrl+alt+space' → (modifiers, vk_code). Raises ValueError on failure."""
    parts = [p.strip().lower() for p in hotkey.split("+")]
    mods = 0
    vk = 0
    for part in parts:
        if part in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif part in ("alt",):
            mods |= MOD_ALT
        elif part in ("shift",):
            mods |= MOD_SHIFT
        elif part in ("win", "windows", "super"):
            mods |= MOD_WIN
        else:
            if part not in _VK_MAP:
                raise ValueError(f"Unknown key: {part!r}")
            vk = _VK_MAP[part]
    if vk == 0:
        raise ValueError(f"No non-modifier key found in hotkey: {hotkey!r}")
    return mods | MOD_NOREPEAT, vk


class GlobalHotkey(QThread):
    """Registers a system-wide hotkey and emits `triggered` when pressed.

    Uses WinAPI RegisterHotKey — works without admin rights.
    """
    triggered = Signal()

    _ID = 0xBEEF  # arbitrary unique ID

    def __init__(self, hotkey: str) -> None:
        super().__init__()
        self._hotkey = hotkey
        self._mods = 0
        self._vk = 0
        self._ok = False
        self._hwnd: int | None = None
        try:
            self._mods, self._vk = _parse_hotkey(hotkey)
            self._ok = True
        except ValueError as e:
            print(f"[hotkey] parse error: {e}")

    @property
    def is_valid(self) -> bool:
        return self._ok

    def run(self) -> None:
        if not self._ok:
            return
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, self._ID, self._mods, self._vk):
            print(f"[hotkey] RegisterHotKey failed for {self._hotkey!r} (err={ctypes.GetLastError()})")
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == self._ID:
                self.triggered.emit()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnregisterHotKey(None, self._ID)

    def stop(self) -> None:
        # Post WM_QUIT to the thread's message queue to break GetMessageW
        ctypes.windll.user32.PostThreadMessageW(int(self.currentThreadId()), 0x0012, 0, 0)
        self.wait(3000)
