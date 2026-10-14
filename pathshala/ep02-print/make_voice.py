#!/usr/bin/env python3
"""Generates the Hinglish voice-over lines for EP02 "print() — pehla code" with an
offline Kokoro TTS voice (hm_omega, Hindi). Lines are written in Devanagari so
the Hindi voice pronounces the Hinglish naturally.

Each line is saved as work/vo_XX.wav (48 kHz, trimmed). build.py places
them on the beat grid and fits them to their scene.

Setup (model files ~120 MB, not committed):
  pip install kokoro-onnx soundfile scipy numpy
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Run:
  python3 pathshala/ep02-print/make_voice.py --models <dir with the two files>
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
    ("hook1", "पाइथन को बोलना सिखाना है?", "Python ko bolna sikhaana hai?"),
    ("hook2", "चलो, अपना पहला कमांड सीखते हैं!", "Chalo, apna pehla command seekhte hain!"),
    ("code", "पाइथन में स्क्रीन पर कुछ भी दिखाने के लिए, हम यूज़ करते हैं प्रिंट।",
     "Python mein screen par kuch bhi dikhane ke liye, hum use karte hain print()."),
    ("explain", "जैसे यहाँ हमने लिखा, हेलो वर्ल्ड! पाइथन इसे स्क्रीन पर डिस्प्ले कर देगा।",
     "Jaise yahan humne likha, Hello World! Python ise screen par display kar dega."),
    ("output", "देखा! बस एक लाइन कोड, और मैसेज स्क्रीन पर!", "Dekha! Bas ek line code, aur message screen par!"),
    ("chal1", "अब तुम प्रिंट का यूज़ करके, अपना नाम डिस्प्ले करो!", "Ab tum print() ka use karke, apna naam display karo!"),
    ("chal2", "कोड समझ आया? फ़ॉलो करो पाइथन की नेक्स्ट क्लास के लिए!",
     "Code samajh aaya? Follow karo Python ki next class ke liye!"),
]


def trim(x, sr, thr=0.02, pad=0.03):
    idx = np.nonzero(np.abs(x) > thr * np.max(np.abs(x)))[0]
    a, b = max(0, idx[0] - int(pad * sr)), min(len(x), idx[-1] + int(pad * sr))
    return x[a:b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--voice", default="hm_omega")
    ap.add_argument("--speed", type=float, default=1.2)
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
