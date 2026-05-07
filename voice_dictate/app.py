"""Main application: wires engine, widget, tray, hotkey, startup, installer."""
from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox

from voice_dictate import config, startup, installer
from voice_dictate.engine import DictationEngine, IDLE, RECORDING
from voice_dictate.hotkey import GlobalHotkey
from voice_dictate.widget import MicWidget
from voice_dictate.tray import TrayController


_MUTEX_NAME = "VoiceDictateSingleInstance"


def _acquire_single_instance() -> bool:
    """Returns False if another instance is already running."""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    err = ctypes.windll.kernel32.GetLastError()
    return err != 0xB7  # ERROR_ALREADY_EXISTS


def run() -> int:
    if not _acquire_single_instance():
        # Another instance is running — just bring tray to attention
        return 0

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Voice Dictate")
    app.setApplicationVersion("1.0.0")

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Voice Dictate", "System tray jest niedostępny.")
        return 1

    cfg = config.load()
    autostart_on = startup.is_enabled()
    installed = installer.is_installed()

    engine = DictationEngine(
        model_size=cfg["model"],
        language=cfg["language"],
        use_gpu=bool(cfg.get("use_gpu", False)),
    )

    widget = MicWidget()
    widget.restore_position(cfg.get("widget_pos"))
    if cfg.get("widget_visible", True):
        widget.show()

    tray = TrayController(
        current_model=cfg["model"],
        current_language=cfg["language"],
        hotkey=cfg["hotkey"],
        widget_visible=cfg.get("widget_visible", True),
        autostart=autostart_on,
        is_installed=installed,
    )

    hotkey_thread = GlobalHotkey(cfg["hotkey"])
    if hotkey_thread.is_valid:
        hotkey_thread.triggered.connect(engine.toggle)
        hotkey_thread.start()

    # --- signal wiring -------------------------------------------------------

    widget.clicked.connect(engine.toggle)
    tray.toggleRequested.connect(engine.toggle)

    engine.stateChanged.connect(widget.set_state)
    engine.stateChanged.connect(tray.set_state)
    engine.stateChanged.emit(engine.state)

    def on_transcribed(text: str) -> None:
        if text:
            tray.show_message("Wklejono ✓", text if len(text) <= 80 else text[:77] + "…")

    engine.transcribed.connect(on_transcribed)

    def on_error(msg: str) -> None:
        print(f"[error] {msg}")
        tray.show_message("Błąd", msg)

    engine.error.connect(on_error)

    def on_moved(x: int, y: int) -> None:
        config.update(widget_pos=[x, y])

    widget.moved.connect(on_moved)

    def on_show_widget(visible: bool) -> None:
        if visible:
            widget.show()
            widget.raise_()
        else:
            widget.hide()
        tray.set_widget_visible(visible)
        config.update(widget_visible=visible)

    tray.showWidgetRequested.connect(on_show_widget)

    def on_model_change(name: str) -> None:
        engine.set_model(name)
        tray.set_model(name)
        config.update(model=name)
        tray.show_message("Voice Dictate", f"Ładowanie modelu: {name}")

    tray.modelChangeRequested.connect(on_model_change)

    def on_lang_change(code: str) -> None:
        engine.set_language(code)
        tray.set_language(code)
        config.update(language=code)

    tray.languageChangeRequested.connect(on_lang_change)

    def on_autostart_toggle() -> None:
        new_state = startup.toggle()
        tray.set_autostart(new_state)
        label = "włączony" if new_state else "wyłączony"
        tray.show_message("Autostart", f"Autostart {label}.")

    tray.autostartToggled.connect(on_autostart_toggle)

    def on_install() -> None:
        if installer.install():
            tray.show_message("Voice Dictate", "Zainstalowano pomyślnie. Uruchamiam zainstalowaną wersję…")
            app.quit()
        else:
            tray.show_message("Voice Dictate", "Instalacja dostępna tylko dla zbudowanego pliku .exe.")

    tray.installRequested.connect(on_install)

    def on_uninstall() -> None:
        startup.disable()
        tray.show_message("Voice Dictate", "Odinstalowuję…")
        app.processEvents()
        installer.uninstall()
        app.quit()

    tray.uninstallRequested.connect(on_uninstall)

    def on_quit() -> None:
        hotkey_thread.stop()
        app.quit()

    tray.quitRequested.connect(on_quit)

    return app.exec()
