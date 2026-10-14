#!/usr/bin/env python3
"""Generates the Hinglish voice-over for Reel #01 with an offline Kokoro TTS voice.

Each line is synthesised separately, trimmed, sped up only if it would overrun
its scene, and placed on the video's timeline (times come from build_reel.py's
beat grid). Lines are written in Devanagari so the Hindi voice pronounces the
Hinglish naturally; English tech words are spelt the way they are spoken.

Setup (model files are ~120 MB, not committed):
  pip install kokoro-onnx soundfile scipy numpy
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Run:
  python3 reels/01-esp32-party-mode/make_voice.py --models <dir with the two files>
  python3 reels/01-esp32-party-mode/build_reel.py --voice reels/01-esp32-party-mode/work/voice.wav
"""
import argparse
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import CUTS, DUR, WORK, kb  # noqa: E402

SR = 48000

# (start, latest end, text, Roman-script version for the README)
LINES = [
    (0.05, CUTS[1] - 0.05, "एक टैप... और पार्टी मोड ऑन!", "Ek tap... aur party mode on!"),
    (CUTS[1] + 0.05, CUTS[2] - 0.05, "कैसे? सिर्फ़ तीन चीज़ें।", "Kaise? Sirf teen cheezein."),
    (CUTS[2] + 0.1, CUTS[3] - 0.1, "ई एस पी थर्टी टू, एल ई डी स्ट्रिप, और फ़ाइव वोल्ट एडैप्टर।",
     "ESP32, LED strip, aur 5 volt adapter."),
    (kb(15) - 0.1, CUTS[4] - 0.05, "डेटा जी पी आई ओ फ़ाइव पे... और ग्राउंड कॉमन!", "Data GPIO 5 pe... aur ground common!"),
    (kb(21), kb(23) - 0.05, "रेड!", "Red!"),
    (kb(23), kb(25) - 0.05, "ग्रीन!", "Green!"),
    (kb(25), CUTS[5] - 0.05, "ब्लू!", "Blue!"),
    (CUTS[5] + 0.05, CUTS[6] - 0.03, "ऐप भेजता है आर, ई एस पी पढ़ता है, एल ई डी रेड!",
     "App bhejta hai R, ESP padhta hai, LED red!"),
    (kb(35) - 0.3, CUTS[7] - 0.05, "पी भेजा — पार्टी मोड!", "P bheja — party mode!"),
    (CUTS[7] + 0.05, DUR - 0.1, "नेक्स्ट: टिल्ट या म्यूज़िक? कमेंट करो!", "Next: tilt ya music? Comment karo!"),
]


def trim(x, sr, thr=0.02, pad=0.03):
    idx = np.nonzero(np.abs(x) > thr * np.max(np.abs(x)))[0]
    a, b = max(0, idx[0] - int(pad * sr)), min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def stretch(x, rate):
    """Speed up speech by `rate` without changing pitch (ffmpeg atempo)."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, "i.wav"), os.path.join(d, "o.wav")
        sf.write(i, x, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", i, "-af", f"atempo={rate:.4f}", o], check=True)
        y, _ = sf.read(o)
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--voice", default="hm_omega")
    ap.add_argument("--speed", type=float, default=1.12)
    args = ap.parse_args()
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(args.models, "kokoro-v1.0.int8.onnx"), os.path.join(args.models, "voices-v1.0.bin"))
    os.makedirs(WORK, exist_ok=True)
    track = np.zeros(int((DUR + 0.5) * SR))
    for start, end, text, roman in LINES:
        a, sr = k.create(text, voice=args.voice, speed=args.speed, lang="hi")
        a = signal.resample_poly(trim(np.asarray(a, np.float64), sr), SR, sr)
        win = end - start
        dur = len(a) / SR
        if dur > win:
            rate = dur / win
            if rate > 1.35:
                print(f"WARNING: '{roman}' needs {rate:.2f}x to fit; shorten the line", file=sys.stderr)
            a = stretch(a, min(rate, 1.5))
        i = int(start * SR)
        track[i:i + len(a)] += a[: len(track) - i]
        print(f"{start:6.2f}s  {len(a) / SR:4.2f}s / {win:4.2f}s  {roman}")
    track /= np.max(np.abs(track)) / 0.9
    out = os.path.join(WORK, "voice.wav")
    sf.write(out, track[: int(DUR * SR)], SR)
    print("wrote", out)


if __name__ == "__main__":
    main()
