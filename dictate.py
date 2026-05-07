"""
Voice dictation tool for Windows (Polish-friendly).

Hold Right-Ctrl to record, release to transcribe and paste into the active window.
Press Ctrl+Alt+Q to quit.

First run downloads the Whisper model (~500MB for 'small').
"""

import os
import sys
import time
import threading
import queue
import tempfile
import wave

import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
from faster_whisper import WhisperModel

# ---- Config ---------------------------------------------------------------
MODEL_SIZE = os.environ.get("DICTATE_MODEL", "small")  # base / small / medium / large-v3
LANGUAGE   = os.environ.get("DICTATE_LANG", "pl")
HOTKEY     = os.environ.get("DICTATE_HOTKEY", "right ctrl")  # hold-to-talk
QUIT_KEY   = "ctrl+alt+q"
SAMPLE_RATE = 16000
DEVICE = "cuda" if os.environ.get("DICTATE_GPU") == "1" else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"
# ---------------------------------------------------------------------------


def beep(freq=880, dur=0.08):
    try:
        import winsound
        winsound.Beep(freq, int(dur * 1000))
    except Exception:
        pass


class Recorder:
    def __init__(self):
        self.frames = []
        self.stream = None
        self.recording = False
        self.lock = threading.Lock()

    def _callback(self, indata, frames, time_info, status):
        if self.recording:
            self.frames.append(indata.copy())

    def start(self):
        with self.lock:
            if self.recording:
                return
            self.frames = []
            self.recording = True
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                callback=self._callback,
            )
            self.stream.start()
        beep(1000, 0.06)

    def stop(self):
        with self.lock:
            if not self.recording:
                return None
            self.recording = False
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        beep(600, 0.06)
        if not self.frames:
            return None
        audio = np.concatenate(self.frames, axis=0).flatten()
        return audio


def transcribe(model, audio):
    if audio is None or len(audio) < SAMPLE_RATE * 0.25:
        return ""
    segments, _info = model.transcribe(
        audio,
        language=LANGUAGE,
        vad_filter=True,
        beam_size=1,
        condition_on_previous_text=False,
    )
    return " ".join(s.text.strip() for s in segments).strip()


def paste_text(text):
    if not text:
        return
    prev = None
    try:
        prev = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    time.sleep(0.15)
    if prev is not None:
        try:
            pyperclip.copy(prev)
        except Exception:
            pass


def main():
    print(f"[dictate] Loading Whisper model: {MODEL_SIZE} ({DEVICE}/{COMPUTE_TYPE})...")
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print(f"[dictate] Ready. Hold [{HOTKEY}] to dictate. Quit: [{QUIT_KEY}]. Lang: {LANGUAGE}")

    rec = Recorder()
    work_q = queue.Queue()

    def worker():
        while True:
            audio = work_q.get()
            if audio is None:
                return
            try:
                text = transcribe(model, audio)
                if text:
                    print(f"[dictate] -> {text}")
                    paste_text(text)
                else:
                    print("[dictate] (no speech detected)")
            except Exception as e:
                print(f"[dictate] transcription error: {e}")

    threading.Thread(target=worker, daemon=True).start()

    state = {"down": False}

    def on_press(_e):
        if not state["down"]:
            state["down"] = True
            rec.start()

    def on_release(_e):
        if state["down"]:
            state["down"] = False
            audio = rec.stop()
            work_q.put(audio)

    keyboard.on_press_key(HOTKEY, on_press, suppress=False)
    keyboard.on_release_key(HOTKEY, on_release, suppress=False)
    keyboard.add_hotkey(QUIT_KEY, lambda: os._exit(0))

    keyboard.wait()  # block forever


if __name__ == "__main__":
    main()
