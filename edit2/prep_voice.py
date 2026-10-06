#!/usr/bin/env python3
"""Clean + tighten the voiceover and derive the shot timing from its phrases.

- removes the 220 Hz hum (+ harmonics), light FFT denoise
- shortens every pause longer than MAX_GAP to MAX_GAP (reference has no dead air)
- maps the 9 visual beats onto phrase boundaries -> work/timing.json
"""
import json
import os
import subprocess

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "06-10-2026 13.49.m4a")
WORK = os.path.join(HERE, "work")
SR, FPS = 48000, 30
MAX_GAP, LEAD, TAIL = 0.30, 0.12, 0.7

# beat boundaries, as the pause (in the RAW recording) where each new beat starts:
# devices, bits, no-clock-wire, mismatch, red X, fix/Hello World, same number, CTA
BEAT_PAUSES = [(3.96, 4.58), (12.08, 12.32), (17.74, 18.16), (22.88, 23.86),
               (27.38, 28.30), (32.10, 33.16), (41.58, 42.30), (46.24, 47.44)]


def main():
    os.makedirs(WORK, exist_ok=True)
    clean = os.path.join(WORK, "voice_clean.wav")
    hum = ",".join(f"equalizer=f={f}:t=q:w=8:g=-24" for f in (220, 440, 660, 880))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-ac", "1", "-ar", str(SR),
                    "-af", f"highpass=f=80,{hum},afftdn=nf=-28:tn=1", clean], check=True)
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", clean, "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32).copy()
    # voice activity from the 300-3400 Hz band
    b = signal.sosfilt(signal.butter(4, [300, 3400], "bandpass", fs=SR, output="sos"), x)
    hop = SR // 50
    r = np.sqrt(np.convolve(b ** 2, np.ones(hop) / hop, "same"))[::hop]
    db = np.convolve(20 * np.log10(r + 1e-9), np.ones(5) / 5, "same")
    lo, hi = np.percentile(db, 10), np.percentile(db, 90)
    quiet = db < lo + 0.3 * (hi - lo)
    pauses, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if j - i >= 12:
                pauses.append((i / 50, j / 50))
            i = j
        else:
            i += 1
    total = len(x) / SR
    # build keep-segments
    keep, cur = [], 0.0
    for a, c in pauses:
        if a <= 0.05:                      # leading silence
            cur = max(0.0, c - LEAD)
            continue
        if c >= total - 0.05:              # trailing silence
            keep.append((cur, min(total, a + TAIL)))
            cur = None
            break
        if c - a > MAX_GAP:
            mid = (a + c) / 2
            keep.append((cur, mid - MAX_GAP / 2))
            cur = mid + MAX_GAP / 2
    if cur is not None:
        keep.append((cur, total))

    def out_t(t):
        acc = 0.0
        for a, c in keep:
            if t < a:
                return acc
            if t <= c:
                return acc + t - a
            acc += c - a
        return acc

    fade = int(0.008 * SR)
    parts = []
    for a, c in keep:
        seg = x[int(a * SR):int(c * SR)].copy()
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        parts.append(seg)
    y = np.concatenate(parts)
    dur = len(y) / SR
    n_frames = int(round(dur * FPS))
    y = np.pad(y, (0, max(0, int(n_frames / FPS * SR) - len(y))))[: int(n_frames / FPS * SR)]
    pcm = (np.clip(y / max(1e-6, np.abs(y).max()) * 0.9, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "pipe:",
                    os.path.join(WORK, "voice.wav")], input=pcm.tobytes(), check=True)
    # each new beat starts ~3 frames before the speech after its pause resumes
    shots = [0] + [int(round(out_t(c) * FPS)) - 3 for _, c in BEAT_PAUSES]
    timing = {"shots": shots, "end": n_frames, "duration": n_frames / FPS,
              "keep": keep, "pauses": pauses}
    json.dump(timing, open(os.path.join(WORK, "timing.json"), "w"), indent=1)
    print(f"voice {total:.2f}s -> {n_frames / FPS:.2f}s ({n_frames} frames)")
    print("shot starts (frames):", shots)
    print("shot starts (s):", [round(s / FPS, 2) for s in shots])


if __name__ == "__main__":
    main()
