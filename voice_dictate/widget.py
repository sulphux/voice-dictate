"""Floating mic widget: frameless, always-on-top, draggable, never steals focus."""
from __future__ import annotations

import ctypes

from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget, QApplication

from voice_dictate.engine import IDLE, RECORDING, TRANSCRIBING, LOADING

DRAG_THRESHOLD = 5
SIZE = 64

# WinAPI extended style — prevents window from stealing focus on click
_WS_EX_NOACTIVATE = 0x08000000
_GWL_EXSTYLE = -20


class MicWidget(QWidget):
    clicked = Signal()
    moved = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus   # Qt-level: no focus on click
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)  # don't activate on show
        self.setFixedSize(SIZE, SIZE)

        self._state = IDLE
        self._press_pos: QPoint | None = None
        self._drag_offset: QPoint | None = None
        self._dragged = False
        self._pulse = 0.0
        self._pulse_dir = 1

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

        self.setToolTip("Klik = nagrywaj")

    def showEvent(self, ev) -> None:
        super().showEvent(ev)
        # Apply WS_EX_NOACTIVATE at WinAPI level so clicking never steals focus
        try:
            hwnd = int(self.winId())
            ex = ctypes.windll.user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, ex | _WS_EX_NOACTIVATE)
        except Exception:
            pass

    def set_state(self, state: str) -> None:
        self._state = state
        tips = {
            IDLE: "Klik = nagrywaj  |  Ctrl+Alt+Space",
            RECORDING: "Klik = stop nagrywanie",
            TRANSCRIBING: "Transkrypcja...",
            LOADING: "Ładowanie modelu...",
        }
        self.setToolTip(tips.get(state, ""))
        self.update()

    def _tick(self) -> None:
        if self._state == RECORDING:
            self._pulse += 0.08 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse, self._pulse_dir = 1.0, -1
            elif self._pulse <= 0.0:
                self._pulse, self._pulse_dir = 0.0, 1
            self.update()
        elif self._state in (TRANSCRIBING, LOADING):
            self._pulse = (self._pulse + 0.05) % 1.0
            self.update()

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.LeftButton:
            self._press_pos = ev.globalPosition().toPoint()
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragged = False

    def mouseMoveEvent(self, ev) -> None:
        if self._press_pos is None or self._drag_offset is None:
            return
        gp = ev.globalPosition().toPoint()
        if not self._dragged and (gp - self._press_pos).manhattanLength() > DRAG_THRESHOLD:
            self._dragged = True
        if self._dragged:
            self.move(gp - self._drag_offset)

    def mouseReleaseEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton:
            return
        if self._dragged:
            p = self.pos()
            self.moved.emit(p.x(), p.y())
        else:
            self.clicked.emit()
        self._press_pos = self._drag_offset = None
        self._dragged = False

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)

        if self._state == RECORDING:
            alpha = int(180 + 75 * self._pulse)
            base = QColor(220, 50, 50, min(255, alpha))
            border = QColor(255, 100, 100, 220)
        elif self._state == TRANSCRIBING:
            base = QColor(230, 170, 40, 230)
            border = QColor(255, 200, 80, 230)
        elif self._state == LOADING:
            base = QColor(90, 110, 200, 220)
            border = QColor(140, 160, 230, 230)
        else:
            base = QColor(40, 40, 45, 220)
            border = QColor(180, 180, 190, 200)

        p.setBrush(base)
        pen = QPen(border)
        pen.setWidth(2)
        p.setPen(pen)
        p.drawEllipse(rect)

        font = p.font()
        font.setPointSize(22)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(self.rect(), Qt.AlignCenter, "🎤")

    def restore_position(self, pos: list | None) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
            x = max(screen.left(), min(int(pos[0]), screen.right() - SIZE))
            y = max(screen.top(), min(int(pos[1]), screen.bottom() - SIZE))
            self.move(x, y)
        else:
            self.move(screen.right() - SIZE - 24, screen.bottom() - SIZE - 60)
