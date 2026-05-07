# Voice Dictate

Dyktowanie głosem dla Windows — widget 🎤 zawsze na wierzchu, lokalny Whisper, polski wspierany.

**Nie wymaga uprawnień administratora.**

## Szybki start

### Ze źródeł (dev)
```powershell
cd C:\Users\laptop\Tools\voice-dictate
pip install -e .
python -m voice_dictate
```

### Zbudowany exe (produkcja)
```powershell
python build.py
dist\voice_dictate.exe --install
```

Po zainstalowaniu: Start Menu → Voice Dictate, Ustawienia → Dodaj/Usuń programy → Voice Dictate.

## Użytkowanie

| Akcja | Sposób |
|---|---|
| Start / Stop nagrywania | Klik widgetu lub Ctrl+Alt+Space |
| Pokaż / Ukryj widget | Lewy-klik ikony tray |
| Toggle nagrywania | Dwuklik ikony tray |
| Ustawienia | Prawy-klik ikony tray |
| Przesuń widget | Lewy-klik + przeciągnij |
| Autostart | Menu tray → Uruchamiaj przy starcie |
| Odinstaluj | Menu tray → Odinstaluj |

## Stany widgetu

- Szary = idle, gotowy
- Czerwony pulsujący = nagrywanie
- Żółty = transkrypcja
- Niebieski = ładowanie modelu

## Konfiguracja — %APPDATA%\VoiceDictate\config.json

```json
{
  "model": "small",
  "language": "pl",
  "hotkey": "ctrl+alt+space",
  "widget_pos": null,
  "widget_visible": true,
  "use_gpu": false
}
```

Model i język zmienialne z menu tray (bez restartu). Hotkey — zmień w pliku i uruchom ponownie.

## Budowanie exe

```powershell
pip install pyinstaller
python build.py
dist\voice_dictate.exe --install
```

## Struktura

```
voice_dictate/  - pakiet Python
  app.py, engine.py, widget.py, tray.py
  config.py, hotkey.py, startup.py, installer.py
  resources/icon.ico
scripts/gen_icon.py
voice_dictate.spec  - PyInstaller
build.py
pyproject.toml
```
