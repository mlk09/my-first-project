#!/usr/bin/env python3
"""Generates the Hinglish voice-over lines for EP01 "Python kya hai?" with an
offline Kokoro TTS voice (hm_omega, Hindi). Lines are written in Devanagari so
the Hindi voice pronounces the Hinglish naturally.

Each line is saved as work/vo_XX.wav (48 kHz, trimmed). build_short.py places
them on the beat grid and fits them to their scene.

Setup (model files ~120 MB, not committed):
  pip install kokoro-onnx soundfile scipy numpy
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Run:
  python3 pathshala/ep01-python-kya-hai/make_voice.py --models <dir with the two files>
"""
import argparse
import os

import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
SR = 48000

# key, Devanagari (spoken), Roman Hinglish (README / captions)
LINES = [
    ("hook", "कंप्यूटर सिर्फ़ ज़ीरो और वन समझता है!", "Computer sirf 0 aur 1 samajhta hai!"),
    ("ask", "तो हम उससे बात कैसे करें?", "Toh hum usse baat kaise karein?"),
    ("drop", "पाइथन से!", "Python se!"),
    ("def", "पाइथन एक प्रोग्रामिंग लैंग्वेज है, जिससे हम कंप्यूटर को काम बोलते हैं।",
     "Python ek programming language hai, jisse hum computer ko kaam bolte hain."),
    ("simple", "और ये बिल्कुल इंग्लिश जैसी सिंपल है। पढ़ते ही समझ आ गया ना?",
     "Aur yeh bilkul English jaisi simple hai. Padhte hi samajh aa gaya na?"),
    ("uses", "इससे बनते हैं वेबसाइट्स, ए आई, डेटा, और ऑटोमेशन।",
     "Isse bante hain websites, AI, data aur automation."),
    ("best", "इसीलिए बिगिनर्स की नंबर वन चॉइस है...", "Isliye beginners ki No.1 choice hai..."),
    ("python", "पाइथन!", "Python!"),
    ("end", "नेक्स्ट: प्रिंट! फ़ॉलो करो!", "Next: print()! Follow karo!"),
]


def trim(x, sr, thr=0.02, pad=0.03):
    idx = np.nonzero(np.abs(x) > thr * np.max(np.abs(x)))[0]
    a, b = max(0, idx[0] - int(pad * sr)), min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--voice", default="hm_omega")
    ap.add_argument("--speed", type=float, default=1.15)
    args = ap.parse_args()
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(args.models, "kokoro-v1.0.int8.onnx"), os.path.join(args.models, "voices-v1.0.bin"))
    os.makedirs(WORK, exist_ok=True)
    for key, text, roman in LINES:
        a, sr = k.create(text, voice=args.voice, speed=args.speed, lang="hi")
        a = signal.resample_poly(trim(np.asarray(a, np.float64), sr), SR, sr)
        sf.write(os.path.join(WORK, f"vo_{key}.wav"), a / np.max(np.abs(a)) * 0.9, SR)
        print(f"{key:7s} {len(a) / SR:5.2f}s  {roman}")


if __name__ == "__main__":
    main()
