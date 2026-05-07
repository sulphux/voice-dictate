"""System tray icon with full control menu."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QActionGroup, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from voice_dictate.engine import IDLE, RECORDING, TRANSCRIBING, LOADING

MODELS = ["base", "small", "medium", "large-v3"]
LANGUAGES = [("pl", "Polski"), ("en", "English"), ("de", "Deutsch"), ("auto", "Auto-detect")]

_STATE_COLOR = {
    IDLE: "#3a3a40",
    RECORDING: "#dc3232",
    TRANSCRIBING: "#e6aa28",
    LOADING: "#5a6ec8",
}


def _make_icon(color: str = "#3a3a40") -> QIcon:
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
    toggleRequested        = Signal()
    showWidgetRequested    = Signal(bool)
    modelChangeRequested   = Signal(str)
    languageChangeRequested = Signal(str)
    autostartToggled       = Signal()
    installRequested       = Signal()
    uninstallRequested     = Signal()
    quitRequested          = Signal()
    historyPasteRequested  = Signal(str)

    def __init__(
        self,
        current_model: str,
        current_language: str,
        hotkey: str,
        widget_visible: bool,
        autostart: bool,
        is_installed: bool,
    ) -> None:
        super().__init__()
        self._model = current_model
        self._language = current_language
        self._hotkey = hotkey
        self._widget_visible = widget_visible
        self._autostart = autostart
        self._is_installed = is_installed
        self._state = IDLE
        self._history: list[str] = []   # last 10 transcriptions

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_make_icon())
        self.tray.setToolTip("Voice Dictate")
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _build_menu(self) -> None:
        m = self.menu
        m.clear()

        self.show_action = QAction("Ukryj widget" if self._widget_visible else "Pokaż widget", m)
        self.show_action.triggered.connect(lambda: self.showWidgetRequested.emit(not self._widget_visible))
        m.addAction(self.show_action)

        self.toggle_action = QAction(self._toggle_label(), m)
        self.toggle_action.triggered.connect(self.toggleRequested.emit)
        self.toggle_action.setEnabled(self._state in (IDLE, RECORDING))
        m.addAction(self.toggle_action)

        m.addSeparator()

        # Model submenu
        model_menu = m.addMenu("Model")
        mg = QActionGroup(model_menu)
        mg.setExclusive(True)
        for name in MODELS:
            a = QAction(name, model_menu)
            a.setCheckable(True)
            a.setChecked(name == self._model)
            a.triggered.connect(lambda _=False, n=name: self.modelChangeRequested.emit(n))
            mg.addAction(a)
            model_menu.addAction(a)

        # Language submenu
        lang_menu = m.addMenu("Język")
        lg = QActionGroup(lang_menu)
        lg.setExclusive(True)
        for code, label in LANGUAGES:
            a = QAction(f"{label} ({code})", lang_menu)
            a.setCheckable(True)
            a.setChecked(code == self._language)
            a.triggered.connect(lambda _=False, c=code: self.languageChangeRequested.emit(c))
            lg.addAction(a)
            lang_menu.addAction(a)

        hotkey_info = QAction(f"Hotkey: {self._hotkey}", m)
        hotkey_info.setEnabled(False)
        m.addAction(hotkey_info)

        m.addSeparator()

        # Transcription history submenu
        history_menu = m.addMenu("Historia transkrypcji")
        if self._history:
            for i, entry in enumerate(reversed(self._history), 1):
                label = entry if len(entry) <= 50 else entry[:47] + "…"
                a = QAction(f"{i}. {label}", history_menu)
                a.triggered.connect(lambda _=False, t=entry: self.historyPasteRequested.emit(t))
                history_menu.addAction(a)
        else:
            empty = QAction("(brak nagrań)", history_menu)
            empty.setEnabled(False)
            history_menu.addAction(empty)

        m.addSeparator()= QAction(
            "✓ Uruchamiaj przy starcie" if self._autostart else "Uruchamiaj przy starcie", m
        )
        autostart_action.triggered.connect(self.autostartToggled.emit)
        m.addAction(autostart_action)

        if not self._is_installed:
            install_action = QAction("Zainstaluj...", m)
            install_action.triggered.connect(self.installRequested.emit)
            m.addAction(install_action)
        else:
            uninstall_action = QAction("Odinstaluj", m)
            uninstall_action.triggered.connect(self.uninstallRequested.emit)
            m.addAction(uninstall_action)

        m.addSeparator()
        quit_action = QAction("Zakończ", m)
        quit_action.triggered.connect(self.quitRequested.emit)
        m.addAction(quit_action)

    def _toggle_label(self) -> str:
        return {IDLE: "Nagrywaj", RECORDING: "Stop", TRANSCRIBING: "Transkrypcja...", LOADING: "Ładowanie..."}.get(
            self._state, "Nagrywaj"
        )

    def add_to_history(self, text: str) -> None:
        """Add transcribed text to history (max 10 entries) and rebuild menu."""
        if text:
            self._history.append(text)
            if len(self._history) > 10:
                self._history.pop(0)
            self._build_menu()

    def set_state(self, state: str) -> None:
        self._state = state
        self.toggle_action.setText(self._toggle_label())
        self.toggle_action.setEnabled(state in (IDLE, RECORDING))
        self.tray.setIcon(_make_icon(_STATE_COLOR.get(state, "#3a3a40")))
        self.tray.setToolTip(f"Voice Dictate — {state}")

    def set_widget_visible(self, v: bool) -> None:
        self._widget_visible = v
        self.show_action.setText("Ukryj widget" if v else "Pokaż widget")

    def set_autostart(self, v: bool) -> None:
        self._autostart = v
        self._build_menu()

    def set_model(self, m: str) -> None:
        self._model = m
        self._build_menu()

    def set_language(self, l: str) -> None:
        self._language = l
        self._build_menu()

    def show_message(self, title: str, msg: str) -> None:
        self.tray.showMessage(title, msg, QSystemTrayIcon.Information, 2500)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:        # left click
            self.showWidgetRequested.emit(not self._widget_visible)
        elif reason == QSystemTrayIcon.DoubleClick:  # double click
            self.toggleRequested.emit()
