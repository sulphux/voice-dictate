<div align="center">

# 🎤 Voice Dictate

**Dyktowanie głosem dla Windows z lokalnym Whisper AI**

Polski, angielski i 90+ języków — bez chmury, bez admin, bez subskrypcji.

[![GitHub release](https://img.shields.io/github/v/tag/sulphux/voice-dictate?label=version&color=blue)](https://github.com/sulphux/voice-dictate/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)](https://github.com/sulphux/voice-dictate)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![Widget states](https://raw.githubusercontent.com/sulphux/voice-dictate/master/docs/preview.png)

</div>

---

## ✨ Funkcje

- 🎙️ **Nagrywanie push-to-talk** — kliknij widget lub naciśnij `Ctrl+Alt+Space`
- 🧠 **Lokalny Whisper AI** — transkrypcja offline, dane nie opuszczają komputera
- 🇵🇱 **Polski i 90+ języków** — w przeciwieństwie do wbudowanego dyktowania Windows
- 📌 **Widget zawsze na wierzchu** — mały, przesuwalny, nie zajmuje taskbara
- 🖱️ **Nie kradnie fokusu** — kliknięcie widgetu nie przesuwa kursora z edytora
- ⚡ **Skrót klawiszowy globalny** — działa bez klikania (`Ctrl+Alt+Space`)
- 🔒 **Nie wymaga uprawnień administratora**
- 🚀 **Autostart z Windows** — opcjonalnie w menu tray

---

## 🚀 Instalacja

### Wymagania

- Windows 10 / 11 (64-bit)
- Mikrofon

### Krok 1 — Pobierz

Pobierz najnowszy `voice_dictate.exe` z [Releases](https://github.com/sulphux/voice-dictate/releases).

### Krok 2 — Zainstaluj

Uruchom pobrany plik i poczekaj chwilę — otworzy się mały widget 🎤 na ekranie.

Alternatywnie z linii poleceń:

```powershell
voice_dictate.exe --install
```

Instalator automatycznie:
- Kopiuje aplikację do `%LOCALAPPDATA%\Programs\VoiceDictate\`
- Tworzy skrót na pulpicie i w Menu Start
- Rejestruje w Dodaj/Usuń Programy

### Krok 3 — Pierwsze uruchomienie

Przy pierwszym starcie aplikacja pobiera model Whisper (~150 MB). Przez chwilę widget będzie **niebieski** — to normalne, poczekaj aż zmieni kolor na szary.

---

## 🎯 Jak używać

### Szybki przewodnik

1. Ustaw kursor tam, gdzie chcesz wpisać tekst (np. w Notatniku, przeglądarce, edytorze)
2. Naciśnij **`Ctrl+Alt+Space`** lub kliknij widget 🎤
3. Mów — widget robi się **czerwony** (nagrywanie)
4. Naciśnij ponownie **`Ctrl+Alt+Space`** lub kliknij widget żeby zatrzymać
5. Widget robi się **żółty** (transkrypcja) — po chwili tekst zostaje wklejony

### Stany widgetu

| Kolor | Stan |
|---|---|
| ⚫ Szary | Gotowy — czeka na nagranie |
| 🔴 Czerwony pulsujący | Nagrywanie w toku |
| 🟡 Żółty | Transkrypcja (Whisper przetwarza) |
| 🔵 Niebieski | Ładowanie modelu AI |

### Sterowanie

| Akcja | Sposób |
|---|---|
| Start / Stop nagrywania | `Ctrl+Alt+Space` lub klik widgetu |
| Przesuń widget | Klik + przeciągnij |
| Pokaż / Ukryj widget | Prawy klik ikony tray → *Pokaż widget* |
| Zmień model / język | Prawy klik ikony tray |
| Autostart z Windows | Prawy klik ikony tray → *Uruchamiaj przy starcie* |
| Odinstaluj | Prawy klik ikony tray → *Odinstaluj* |

### Modele Whisper

| Model | Rozmiar | Szybkość | Dokładność |
|---|---|---|---|
| `tiny` | ~40 MB | ⚡⚡⚡ | ★★☆ |
| `base` | ~75 MB | ⚡⚡ | ★★★ |
| **`small`** *(domyślny)* | ~150 MB | ⚡ | ★★★★ |
| `medium` | ~500 MB | 🐢 | ★★★★★ |

Model można zmienić z menu tray bez restartu aplikacji.

---

## ⚙️ Konfiguracja

Plik konfiguracyjny: `%APPDATA%\VoiceDictate\config.json`

```json
{
  "model": "small",
  "language": "pl",
  "hotkey": "ctrl+alt+space",
  "widget_pos": [1300, 700],
  "widget_visible": true,
  "use_gpu": false
}
```

Logi diagnostyczne: `%APPDATA%\VoiceDictate\app.log`

---

## 🛠️ Budowanie ze źródeł

```powershell
git clone https://github.com/sulphux/voice-dictate.git
cd voice-dictate

pip install -e .
pip install pyinstaller

python build.py
dist\voice_dictate.exe --install
```

### Wymagania deweloperskie

- Python 3.10+
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (zalecane)

---

## 🗑️ Odinstalowanie

Prawy klik na ikonę tray → **Odinstaluj**

lub z linii poleceń:

```powershell
"%LOCALAPPDATA%\Programs\VoiceDictate\voice_dictate.exe" --uninstall
```

---

## 📄 Licencja

MIT — szczegóły w pliku [LICENSE](LICENSE).

