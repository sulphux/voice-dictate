# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for voice-dictate."""

from pathlib import Path
import sys

block_cipher = None
root = Path(SPECPATH)
icon = str(root / "voice_dictate" / "resources" / "icon.ico")

a = Analysis(
    [str(root / "voice_dictate" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "voice_dictate" / "resources" / "icon.ico"), "voice_dictate/resources"),
    ],
    hiddenimports=[
        "voice_dictate",
        "voice_dictate.app",
        "voice_dictate.engine",
        "voice_dictate.widget",
        "voice_dictate.tray",
        "voice_dictate.config",
        "voice_dictate.hotkey",
        "voice_dictate.startup",
        "voice_dictate.installer",
        "faster_whisper",
        "sounddevice",
        "pyperclip",
        "keyboard",
        "numpy",
        "PySide6",
        "PySide6.QtWidgets",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "ctypes",
        "winreg",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="voice_dictate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
    version=None,
    uac_admin=False,     # no UAC prompt — RegisterHotKey works without admin
)
