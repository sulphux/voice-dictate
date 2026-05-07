"""System tray icon with control menu."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QActionGroup, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from engine import IDLE, RECORDING, TRANSCRIBING, LOADING

MODELS = ["base", "small", "medium", "large-v3"]
LANGUAGES = [("pl", "Polski"), ("en", "English"), ("de", "Deutsch"), ("auto", "Auto-detect")]


def _make_icon(color: str = "#dddddd") -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(4, 4, 56, 56)
    p.setPen(QColor("white"))
    f = QFont()
    f.setPointSize(28)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "🎤")
    p.end()
    return QIcon(pm)


class TrayController(QObject):
    toggleRequested = Signal()
    showWidgetRequested = Signal(bool)   # bool: visible
    modelChangeRequested = Signal(str)
    languageChangeRequested = Signal(str)
    quitRequested = Signal()

    def __init__(self, current_model: str, current_language: str, hotkey: str, widget_visible: bool) -> None:
        super().__init__()
        self._current_model = current_model
        self._current_language = current_language
        self._hotkey = hotkey
        self._widget_visible = widget_visible
        self._state = IDLE

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_make_icon("#3a3a40"))
        self.tray.setToolTip("Voice Dictate")
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _build_menu(self) -> None:
        self.menu.clear()

        self.show_action = QAction("Ukryj widget" if self._widget_visible else "Pokaż widget", self.menu)
        self.show_action.triggered.connect(self._on_toggle_widget)
        self.menu.addAction(self.show_action)

        self.toggle_action = QAction(self._toggle_label(), self.menu)
        self.toggle_action.triggered.connect(self.toggleRequested.emit)
        self.menu.addAction(self.toggle_action)

        self.menu.addSeparator()

        # Model submenu
        model_menu = self.menu.addMenu("Model")
        model_group = QActionGroup(model_menu)
        model_group.setExclusive(True)
        for m in MODELS:
            a = QAction(m, model_menu)
            a.setCheckable(True)
            a.setChecked(m == self._current_model)
            a.triggered.connect(lambda _checked=False, name=m: self.modelChangeRequested.emit(name))
            model_group.addAction(a)
            model_menu.addAction(a)

        # Language submenu
        lang_menu = self.menu.addMenu("Język")
        lang_group = QActionGroup(lang_menu)
        lang_group.setExclusive(True)
        for code, label in LANGUAGES:
            a = QAction(f"{label} ({code})", lang_menu)
            a.setCheckable(True)
            a.setChecked(code == self._current_language)
            a.triggered.connect(lambda _checked=False, c=code: self.languageChangeRequested.emit(c))
            lang_group.addAction(a)
            lang_menu.addAction(a)

        info = QAction(f"Hotkey: {self._hotkey}", self.menu)
        info.setEnabled(False)
        self.menu.addAction(info)

        self.menu.addSeparator()
        quit_action = QAction("Zakończ", self.menu)
        quit_action.triggered.connect(self.quitRequested.emit)
        self.menu.addAction(quit_action)

    def _toggle_label(self) -> str:
        return {
            IDLE: "Nagrywaj",
            RECORDING: "Stop",
            TRANSCRIBING: "Transkrypcja...",
            LOADING: "Ładowanie modelu...",
        }.get(self._state, "Nagrywaj")

    def set_state(self, state: str) -> None:
        self._state = state
        self.toggle_action.setText(self._toggle_label())
        self.toggle_action.setEnabled(state in (IDLE, RECORDING))
        color = {
            IDLE: "#3a3a40",
            RECORDING: "#dc3232",
            TRANSCRIBING: "#e6aa28",
            LOADING: "#5a6ec8",
        }.get(state, "#3a3a40")
        self.tray.setIcon(_make_icon(color))
        self.tray.setToolTip(f"Voice Dictate — {state}")

    def set_widget_visible(self, visible: bool) -> None:
        self._widget_visible = visible
        self.show_action.setText("Ukryj widget" if visible else "Pokaż widget")

    def set_model(self, model: str) -> None:
        self._current_model = model
        self._build_menu()

    def set_language(self, lang: str) -> None:
        self._current_language = lang
        self._build_menu()

    def show_message(self, title: str, msg: str) -> None:
        self.tray.showMessage(title, msg, QSystemTrayIcon.Information, 2500)

    def _on_toggle_widget(self) -> None:
        new_state = not self._widget_visible
        self.showWidgetRequested.emit(new_state)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:  # left click
            self._on_toggle_widget()
        elif reason == QSystemTrayIcon.DoubleClick:
            self.toggleRequested.emit()
