"""Dictation engine: audio recorder + Whisper transcription + paste.

Runs transcription in a background QThread so the UI never freezes.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd
import pyperclip
import keyboard
from PySide6.QtCore import QObject, QThread, Signal, Slot

SAMPLE_RATE = 16000

IDLE         = "idle"
RECORDING    = "recording"
TRANSCRIBING = "transcribing"
LOADING      = "loading"


class _Recorder:
    def __init__(self) -> None:
        self.frames: list[np.ndarray] = []
        self.stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._active = False

    def _cb(self, indata, frames, time_info, status):
        if self._active:
            self.frames.append(indata.copy())

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self.frames = []
            self._active = True
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=self._cb
            )
            self.stream.start()

    def stop(self) -> Optional[np.ndarray]:
        with self._lock:
            if not self._active:
                return None
            self._active = False
            try:
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
            except Exception:
                pass
            self.stream = None
        if not self.frames:
            return None
        return np.concatenate(self.frames, axis=0).flatten()


class _TranscribeWorker(QThread):
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, model, audio: np.ndarray, language: str) -> None:
        super().__init__()
        self.model = model
        self.audio = audio
        self.language = language

    def run(self) -> None:
        import logging
        logging.info(f"[engine] Transcribing audio ({len(self.audio) if self.audio is not None else 0} samples)")
        try:
            if self.audio is None or len(self.audio) < SAMPLE_RATE * 0.25:
                logging.info("[engine] Audio too short, skipping")
                self.done.emit("")
                return
            segments, _info = self.model.transcribe(
                self.audio,
                language=self.language if self.language != "auto" else None,
                vad_filter=True,
                beam_size=1,
                condition_on_previous_text=False,
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            logging.info(f"[engine] Transcription OK: '{text[:80]}'")
            self.done.emit(text)
        except Exception as e:
            logging.error(f"[engine] Transcription FAILED: {e}")
            self.failed.emit(str(e))


class _ModelLoader(QThread):
    loaded = Signal(object)
    failed = Signal(str)

    def __init__(self, model_size: str, use_gpu: bool) -> None:
        super().__init__()
        self.model_size = model_size
        self.use_gpu = use_gpu

    def run(self) -> None:
        import logging
        logging.info(f"[engine] Loading model: {self.model_size}")
        try:
            from faster_whisper import WhisperModel
            device = "cuda" if self.use_gpu else "cpu"
            compute = "float16" if self.use_gpu else "int8"
            self.loaded.emit(WhisperModel(self.model_size, device=device, compute_type=compute))
            logging.info(f"[engine] Model loaded OK: {self.model_size}")
        except Exception as e:
            logging.error(f"[engine] Model load FAILED: {e}")
            self.failed.emit(str(e))


class DictationEngine(QObject):
    stateChanged = Signal(str)
    transcribed  = Signal(str)
    error        = Signal(str)
    modelReady   = Signal(str)

    def __init__(self, model_size: str = "small", language: str = "pl", use_gpu: bool = False) -> None:
        super().__init__()
        self.model_size = model_size
        self.language = language
        self.use_gpu = use_gpu
        self._model = None
        self._state = IDLE
        self._recorder = _Recorder()
        self._worker: Optional[_TranscribeWorker] = None
        self._loader: Optional[_ModelLoader] = None
        self._load_model()

    @property
    def state(self) -> str:
        return self._state

    def _set_state(self, s: str) -> None:
        if s != self._state:
            self._state = s
            self.stateChanged.emit(s)

    def _load_model(self) -> None:
        self._set_state(LOADING)
        self._loader = _ModelLoader(self.model_size, self.use_gpu)
        self._loader.loaded.connect(self._on_model_loaded)
        self._loader.failed.connect(self._on_model_failed)
        self._loader.start()

    @Slot(object)
    def _on_model_loaded(self, model) -> None:
        self._model = model
        self._set_state(IDLE)
        self.modelReady.emit(self.model_size)

    @Slot(str)
    def _on_model_failed(self, msg: str) -> None:
        self.error.emit(f"Model load failed: {msg}")
        self._set_state(IDLE)

    def set_model(self, size: str) -> None:
        if size == self.model_size and self._model is not None:
            return
        self.model_size = size
        self._model = None
        self._load_model()

    def set_language(self, lang: str) -> None:
        self.language = lang

    @Slot()
    def toggle(self) -> None:
        import logging
        logging.info(f"[engine] toggle() called, state={self._state}")
        if self._state == RECORDING:
            self.stop()
        elif self._state == IDLE:
            self.start()
        else:
            logging.warning(f"[engine] toggle() ignored — state={self._state}")

    @Slot()
    def start(self) -> None:
        import logging
        if self._state != IDLE or self._model is None:
            logging.warning(f"[engine] start() ignored — state={self._state}, model={self._model is not None}")
            return
        try:
            self._recorder.start()
            self._set_state(RECORDING)
            logging.info("[engine] Recording started")
        except Exception as e:
            logging.error(f"[engine] Recording start failed: {e}")
            self.error.emit(f"Recording failed: {e}")

    @Slot()
    def stop(self) -> None:
        import logging
        if self._state != RECORDING:
            logging.warning(f"[engine] stop() ignored — state={self._state}")
            return
        audio = self._recorder.stop()
        self._set_state(TRANSCRIBING)
        logging.info("[engine] Recording stopped, starting transcription")
        self._worker = _TranscribeWorker(self._model, audio, self.language)
        self._worker.done.connect(self._on_transcribed)
        self._worker.failed.connect(self._on_transcribe_failed)
        self._worker.start()

    @Slot(str)
    def _on_transcribed(self, text: str) -> None:
        self._set_state(IDLE)
        self.transcribed.emit(text)
        if text:
            _paste(text)

    @Slot(str)
    def _on_transcribe_failed(self, msg: str) -> None:
        self._set_state(IDLE)
        self.error.emit(f"Transcription failed: {msg}")


def _paste(text: str) -> None:
    import logging
    logging.info(f"[engine] Pasting: '{text[:60]}'")
    # Copy to clipboard FIRST — text stays there even if paste fails
    pyperclip.copy(text)
    time.sleep(0.05)
    try:
        keyboard.send("ctrl+v")
        logging.info("[engine] Paste sent OK")
    except Exception as e:
        logging.error(f"[engine] Paste failed: {e}")
    # NOTE: we intentionally do NOT restore the previous clipboard content
    # so the user can always manually paste (Ctrl+V) if auto-paste missed the target
