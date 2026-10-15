"""Clear character voices with Kokoro (open-weight neural TTS, Apache-2.0), replacing espeak.

speak(who, text, target_s) returns 48 kHz mono audio fitted to `target_s` seconds,
so new lines drop into the existing timing (mouth flaps and captions stay in sync).
Model files: kokoro-v1.0.onnx and voices-v1.0.bin from the kokoro-onnx GitHub release.
"""
import os

import numpy as np
from scipy import signal

SR = 48000
MODEL_DIR = os.environ.get("KOKORO_DIR", "/tmp/claude-0/-home-user-my-first-project/"
                           "b7a3d4b6-5d66-5a2f-9e67-96a1ebc10e3e/scratchpad/kokoro")
# voice, pitch shift (semitones), base speed
CAST = {
    "bolt": ("am_puck", 2.0, 1.05),
    "boo": ("af_sky", 4.0, 1.0),
    "granny": ("bf_lily", -1.0, 0.88),
    "shadow": ("bf_lily", -9.0, 0.85),
    "narrator": ("af_heart", 0.0, 0.84),
}
_K = None


def _kokoro():
    global _K
    if _K is None:
        from kokoro_onnx import Kokoro
        _K = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    return _K


def _gen(voice, text, speed):
    lang = "en-gb" if voice.startswith("b") else "en-us"
    x, sr = _kokoro().create(text, voice=voice, speed=float(np.clip(speed, 0.5, 2.0)), lang=lang)
    x = np.asarray(x, np.float32)
    nz = np.where(np.abs(x) > 0.01)[0]
    x = x[max(0, nz[0] - 100): nz[-1] + 600] if len(nz) else x
    return x, sr


def speak(who, text, target_s=None):
    voice, semis, base = CAST[who]
    ratio = 2 ** (semis / 12)
    # synthesise slower/faster, then resample: pitch moves by `ratio`, length lands on target
    x, sr = _gen(voice, text, base / ratio)
    if target_s:
        natural = len(x) / sr / ratio
        want = float(np.clip(natural / target_s, 0.8, 1.45))
        x, sr = _gen(voice, text, base * want / ratio)
    g = np.gcd(SR, int(sr * ratio))
    y = signal.resample_poly(x, SR // g, int(sr * ratio) // g)
    y = _character(who, y)
    return y / (np.max(np.abs(y)) + 1e-9)


def narrate(text, max_s):
    """Warm storyteller voice; only speeds up (never slows) to fit `max_s`."""
    voice, _, base = CAST["narrator"]
    x, sr = _gen(voice, text, base)
    if len(x) / sr > max_s:
        x, sr = _gen(voice, text, min(base * len(x) / sr / max_s * 1.03, 1.35))
    y = signal.resample_poly(x, SR // sr, 1) if SR % sr == 0 else signal.resample(x, int(len(x) * SR / sr))
    y = _delay(y.astype(np.float32), 0.06, 0.08)
    return y / (np.max(np.abs(y)) + 1e-9)


def _delay(x, s, g):
    k = int(s * SR)
    return x + g * np.concatenate([np.zeros(k, np.float32), x[:-k]])


def _character(who, x):
    t = np.arange(len(x)) / SR
    if who == "bolt":  # gentle robot sheen: a short flanger, nothing that smears words
        d = (0.0025 + 0.0012 * np.sin(2 * np.pi * 0.7 * t)) * SR
        idx = np.clip(np.arange(len(x)) - d, 0, len(x) - 1)
        x = x + 0.22 * np.interp(idx, np.arange(len(x)), x)
    elif who == "boo":  # light ghost echo
        x = _delay(_delay(x, 0.07, 0.18), 0.16, 0.1)
    elif who == "granny":
        x = x * (0.92 + 0.08 * np.sin(2 * np.pi * 5.0 * t))
        x = _delay(x, 0.05, 0.12)
    elif who == "shadow":
        b, a = signal.butter(2, 3000 / (SR / 2), "low")
        x = signal.lfilter(b, a, x) * 1.3
        x = _delay(_delay(x, 0.13, 0.45), 0.29, 0.25)
    return x.astype(np.float32)
