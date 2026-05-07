"""Voice Dictate — main entry point.

Wires together:
  - DictationEngine (audio + Whisper)
  - MicWidget (floating always-on-top button)
  - TrayController (system tray icon + menu)
  - Global hotkey via `keyboard` library
"""
from __future__ import annotations

import sys
import threading

from PySide6.QtCore import QObject, Signal, Qt, Slot
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox

import keyboard

import config
from engine import DictationEngine, IDLE, RECORDING, TRANSCRIBING, LOADING
from widget import MicWidget
from tray import TrayController


class HotkeyBridge(QObject):
    """Bridges `keyboard` library callbacks (background thread) to a Qt signal."""
    triggered = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._handle = None

    def bind(self, hotkey: str) -> None:
        if self._handle is not None:
            try:
                keyboard.remove_hotkey(self._handle)
            except Exception:
                pass
            self._handle = None
        try:
            self._handle = keyboard.add_hotkey(
                hotkey,
                lambda: self.triggered.emit(),
                suppress=False,
                trigger_on_release=False,
            )
        except Exception as e:
            print(f"[hotkey] failed to bind {hotkey}: {e}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Voice Dictate", "System tray jest niedostępny.")
        return 1

    cfg = config.load()

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
    )

    hotkey_bridge = HotkeyBridge()
    hotkey_bridge.bind(cfg["hotkey"])

    # --- wiring ------------------------------------------------------------

    # widget click / hotkey / tray double-click -> engine.toggle
    widget.clicked.connect(engine.toggle)
    hotkey_bridge.triggered.connect(engine.toggle)
    tray.toggleRequested.connect(engine.toggle)

    # engine state -> widget + tray
    engine.stateChanged.connect(widget.set_state)
    engine.stateChanged.connect(tray.set_state)

    # transcription notification
    def on_transcribed(text: str) -> None:
        if text:
            preview = text if len(text) <= 80 else text[:77] + "..."
            tray.show_message("Wklejono", preview)

    engine.transcribed.connect(on_transcribed)

    def on_error(msg: str) -> None:
        print(f"[error] {msg}")
        tray.show_message("Błąd", msg)

    engine.error.connect(on_error)

    # widget moved -> persist
    def on_moved(x: int, y: int) -> None:
        config.update(widget_pos=[x, y])

    widget.moved.connect(on_moved)

    # tray show/hide widget
    def on_show_widget(visible: bool) -> None:
        if visible:
            widget.show()
            widget.raise_()
        else:
            widget.hide()
        tray.set_widget_visible(visible)
        config.update(widget_visible=visible)

    tray.showWidgetRequested.connect(on_show_widget)

    # tray model/language change
    def on_model_change(name: str) -> None:
        engine.set_model(name)
        tray.set_model(name)
        config.update(model=name)
        tray.show_message("Voice Dictate", f"Ładowanie modelu: {name}")

    def on_lang_change(code: str) -> None:
        engine.set_language(code)
        tray.set_language(code)
        config.update(language=code)

    tray.modelChangeRequested.connect(on_model_change)
    tray.languageChangeRequested.connect(on_lang_change)

    # quit
    def on_quit() -> None:
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        app.quit()

    tray.quitRequested.connect(on_quit)

    # initial sync
    engine.stateChanged.emit(engine.state)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
