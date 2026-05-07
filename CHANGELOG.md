# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] — 2025-05-07

### Added
- Floating always-on-top 🎤 widget (frameless, no title bar)
- Toggle recording via click on widget or global hotkey (`Ctrl+Alt+Space`)
- System tray icon with full control menu
- Global hotkey using WinAPI `RegisterHotKey` — **no administrator rights required**
- Autostart via HKCU registry Run key (toggle from tray menu)
- Self-install to `%LOCALAPPDATA%\Programs\VoiceDictate\`
- Start Menu shortcut created on install
- Registered in Add/Remove Programs (uninstall from tray or Settings)
- Single instance check via Windows mutex
- Config stored in `%APPDATA%\VoiceDictate\config.json`
- Draggable widget with position persistence
- Visual states: gray (idle), red pulsing (recording), yellow (transcribing), blue (loading model)
- Model selection: base / small / medium / large-v3 (from tray, no restart needed)
- Language selection: Polish / English / German / Auto-detect
- faster-whisper backend (local, offline after initial model download)
- PyInstaller single-file exe build
