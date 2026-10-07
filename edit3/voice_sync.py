#!/usr/bin/env python3
"""Fit the millis-delay.m4a voiceover onto the short.

Each of the 7 script lines (found from the long pauses in the recording) is cleaned,
has its inner pauses tightened, is sped up 8 % (pitch kept), and is placed at the
start of its shot. Every shot is then lengthened to fit its line.
Writes work/voice.wav and work/vo_timing.json (read by build_short.py).
"""
import json
import os
import subprocess

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "millis-delay.m4a")
WORK = os.path.join(HERE, "work")
SR, FPS = 48000, 30
TEMPO, MAX_GAP = 1.08, 0.28
ORDER = ["A", "B", "C", "D", "E", "F", "G"]
LINES = {"A": (0.75, 7.70), "B": (8.40, 16.85), "C": (17.95, 22.85), "D": (23.95, 37.50),
         "E": (38.30, 50.35), "F": (51.20, 57.10), "G": (57.75, 60.80)}
MIN_LEN = {"A": 3.5, "B": 5.0, "C": 4.0, "D": 5.0, "E": 6.0, "F": 5.0, "G": 3.5}  # seconds
LEAD, TAIL = {"A": 0.45}, 0.45


def load(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                        "-af", "highpass=f=80,equalizer=f=200:t=q:w=6:g=-14,afftdn=nf=-30",
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def tighten(x):
    b = signal.sosfilt(signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos"), x)
    hop = SR // 50
    r = np.sqrt(np.convolve(b ** 2, np.ones(hop) / hop, "same"))[::hop]
    db = np.convolve(20 * np.log10(r + 1e-9), np.ones(5) / 5, "same")
    lo, hi = np.percentile(db, 10), np.percentile(db, 90)
    quiet = db < lo + 0.3 * (hi - lo)
    keep, i, cur = [], 0, 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) / 50 > MAX_GAP and i > 0 and j < len(quiet):
                mid = (i + j) / 2 / 50
                keep.append((cur, int((mid - MAX_GAP / 2) * SR)))
                cur = int((mid + MAX_GAP / 2) * SR)
            i = j
        else:
            i += 1
    keep.append((cur, len(x)))
    fade = int(0.006 * SR)
    parts = []
    for a, c in keep:
        s = x[a:c].copy()
        if len(s) > 2 * fade:
            s[:fade] *= np.linspace(0, 1, fade)
            s[-fade:] *= np.linspace(1, 0, fade)
        parts.append(s)
    return np.concatenate(parts)


def tempo(x):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", f"atempo={TEMPO}", "-f", "f32le", "-"], input=x.tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def main():
    x = load(SRC)
    lines = {k: tempo(tighten(x[int(a * SR):int(b * SR)])) for k, (a, b) in LINES.items()}
    seg, voice, t = {}, [], 0
    for k in ORDER:
        lead = LEAD.get(k, 0.12)
        dur = max(MIN_LEN[k], lead + len(lines[k]) / SR + TAIL)
        n = int(round(dur * FPS))
        seg[k] = (t, t + n)
        buf = np.zeros(int(n / FPS * SR), np.float32)
        st = int(lead * SR)
        buf[st:st + len(lines[k])] = lines[k][: len(buf) - st]
        voice.append(buf)
        t += n
    y = np.concatenate(voice)
    y = y / max(1e-6, np.abs(y).max()) * 0.9
    pcm = (y * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    os.path.join(WORK, "voice.wav")], input=pcm.tobytes(), check=True)
    json.dump({"seg": seg, "n": t}, open(os.path.join(WORK, "vo_timing.json"), "w"), indent=1)
    for k in ORDER:
        print(k, f"{seg[k][0] / FPS:5.2f}-{seg[k][1] / FPS:5.2f}s  line {len(lines[k]) / SR:.2f}s")
    print(f"total {t / FPS:.2f}s")


if __name__ == "__main__":
    main()
