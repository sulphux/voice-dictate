"""Floating mic widget: frameless, always-on-top, draggable."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget, QApplication

from engine import IDLE, RECORDING, TRANSCRIBING, LOADING

DRAG_THRESHOLD = 5  # px


class MicWidget(QWidget):
    clicked = Signal()
    moved = Signal(int, int)

    SIZE = 64

    def __init__(self) -> None:
        super().__init__()
        # Frameless, always on top, no taskbar entry (Tool flag), translucent
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setToolTip("Klik = nagrywaj / stop")

        self._state = IDLE
        self._press_pos: QPoint | None = None
        self._drag_offset: QPoint | None = None
        self._dragged = False

        self._pulse = 0.0
        self._pulse_dir = 1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_state(self, state: str) -> None:
        self._state = state
        tooltips = {
            IDLE: "Klik = nagrywaj",
            RECORDING: "Klik = stop",
            TRANSCRIBING: "Transkrypcja...",
            LOADING: "Ładowanie modelu...",
        }
        self.setToolTip(tooltips.get(state, ""))
        self.update()

    def _tick(self) -> None:
        if self._state == RECORDING:
            self._pulse += 0.08 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse = 1.0
                self._pulse_dir = -1
            elif self._pulse <= 0.0:
                self._pulse = 0.0
                self._pulse_dir = 1
            self.update()
        elif self._state in (TRANSCRIBING, LOADING):
            self._pulse += 0.05
            if self._pulse > 1.0:
                self._pulse -= 1.0
            self.update()

    # --- drag logic ---------------------------------------------------------

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.LeftButton:
            self._press_pos = ev.globalPosition().toPoint()
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragged = False
            ev.accept()

    def mouseMoveEvent(self, ev) -> None:
        if self._press_pos is None or self._drag_offset is None:
            return
        gp = ev.globalPosition().toPoint()
        if not self._dragged:
            if (gp - self._press_pos).manhattanLength() > DRAG_THRESHOLD:
                self._dragged = True
        if self._dragged:
            self.move(gp - self._drag_offset)
            ev.accept()

    def mouseReleaseEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton:
            return
        if self._dragged:
            p = self.pos()
            self.moved.emit(p.x(), p.y())
        else:
            self.clicked.emit()
        self._press_pos = None
        self._drag_offset = None
        self._dragged = False
        ev.accept()

    def contextMenuEvent(self, ev) -> None:
        # right-click: do nothing here, tray handles config
        ev.accept()

    # --- painting -----------------------------------------------------------

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)

        # color per state
        if self._state == RECORDING:
            base = QColor(220, 50, 50)
            alpha = int(180 + 75 * self._pulse)
            base.setAlpha(min(255, alpha))
            border = QColor(255, 100, 100, 220)
        elif self._state == TRANSCRIBING:
            base = QColor(230, 170, 40, 230)
            border = QColor(255, 200, 80, 230)
        elif self._state == LOADING:
            base = QColor(90, 110, 200, 220)
            border = QColor(140, 160, 230, 230)
        else:  # IDLE
            base = QColor(40, 40, 45, 220)
            border = QColor(180, 180, 190, 200)

        # circle
        p.setBrush(base)
        pen = QPen(border)
        pen.setWidth(2)
        p.setPen(pen)
        p.drawEllipse(rect)

        # mic emoji
        font: QFont = p.font()
        font.setPointSize(22)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(self.rect(), Qt.AlignCenter, "🎤")

    # --- positioning --------------------------------------------------------

    def restore_position(self, pos: list | None) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
            x, y = int(pos[0]), int(pos[1])
            # clamp to screen
            x = max(screen.left(), min(x, screen.right() - self.SIZE))
            y = max(screen.top(), min(y, screen.bottom() - self.SIZE))
            self.move(x, y)
        else:
            # bottom-right with margin
            self.move(screen.right() - self.SIZE - 24, screen.bottom() - self.SIZE - 60)
