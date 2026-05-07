"""Self-install / uninstall logic.

install():  copies exe to %LOCALAPPDATA%\\Programs\\VoiceDictate\\,
            creates Start Menu shortcut, registers in Add/Remove Programs.
uninstall(): reverses the above.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import winreg
from pathlib import Path

_APP_NAME = "Voice Dictate"
_APP_ID = "VoiceDictate"
_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / _APP_ID
_START_MENU = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
_DESKTOP = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
_UNINSTALL_KEY = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{_APP_ID}"


def _exe_name() -> str:
    return "voice_dictate.exe" if getattr(sys, "frozen", False) else "voice_dictate.exe"


def install(silent: bool = False) -> bool:
    """Install to user Programs directory. Returns True on success."""
    if not getattr(sys, "frozen", False):
        print("[installer] Not running as a frozen exe — install only works on the built exe.")
        return False

    src = Path(sys.executable)
    dest_dir = _INSTALL_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_exe = dest_dir / src.name

    try:
        shutil.copy2(src, dest_exe)
    except Exception as e:
        print(f"[installer] copy failed: {e}")
        return False

    desc = "Voice dictation widget for Windows"

    # Start Menu shortcut
    _create_shortcut(
        target=str(dest_exe),
        shortcut_path=str(_START_MENU / f"{_APP_NAME}.lnk"),
        description=desc,
    )

    # Desktop shortcut
    _create_shortcut(
        target=str(dest_exe),
        shortcut_path=str(_DESKTOP / f"{_APP_NAME}.lnk"),
        description=desc,
    )

    # Register in Add/Remove Programs
    _register_uninstall(dest_exe)

    if not silent:
        print(f"[installer] Installed to {dest_exe}")
        print(f"[installer] Start Menu + Desktop shortcuts created.")

    # Launch installed version
    subprocess.Popen([str(dest_exe)], creationflags=subprocess.DETACHED_PROCESS)
    return True


def uninstall(silent: bool = False) -> bool:
    """Uninstall. Returns True on success."""
    # Remove from Add/Remove Programs
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _UNINSTALL_KEY)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[installer] registry cleanup error: {e}")

    # Remove Start Menu shortcut
    lnk = _START_MENU / f"{_APP_NAME}.lnk"
    if lnk.exists():
        lnk.unlink(missing_ok=True)

    # Remove autostart if set
    from voice_dictate import startup
    startup.disable()

    # Remove install dir (schedule for after exit if running from it)
    if _INSTALL_DIR.exists():
        installed_exe = _INSTALL_DIR / _exe_name()
        if getattr(sys, "frozen", False) and Path(sys.executable).resolve() == installed_exe.resolve():
            # Can't delete ourselves; schedule via cmd /c ping delay
            bat = f'@echo off\nping -n 3 127.0.0.1 >nul\nrd /s /q "{_INSTALL_DIR}"'
            bat_path = Path(os.environ.get("TEMP", "C:\\Temp")) / "vd_uninstall.bat"
            bat_path.write_text(bat)
            subprocess.Popen(
                ["cmd", "/c", str(bat_path)],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            )
        else:
            try:
                shutil.rmtree(_INSTALL_DIR, ignore_errors=True)
            except Exception as e:
                print(f"[installer] rmdir error: {e}")

    if not silent:
        print("[installer] Uninstalled.")
    return True


def is_installed() -> bool:
    """Check if app is installed in user Programs directory."""
    return (_INSTALL_DIR / _exe_name()).exists()


def get_installed_version() -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _UNINSTALL_KEY, 0, winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, "DisplayVersion")
            return val
    except Exception:
        return None


def _create_shortcut(target: str, shortcut_path: str, description: str = "") -> None:
    ps = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "{target}"; '
        f'$s.Description = "{description}"; '
        f'$s.Save()'
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=True, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"[installer] shortcut creation failed: {e}")


def _register_uninstall(exe_path: Path) -> None:
    from voice_dictate import __version__
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _UNINSTALL_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, _APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, __version__)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "voice-dictate")
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                              f'"{exe_path}" --uninstall')
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(exe_path.parent))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f"[installer] registry write failed: {e}")
