#!/usr/bin/env python3
"""Generates the Hinglish voice-over lines for EP03 "Python Data Types" with an
offline Kokoro TTS voice (hm_omega, Hindi). Lines are written in Devanagari so
the Hindi voice pronounces the Hinglish naturally.

Each line is saved as work/vo_XX.wav (48 kHz, trimmed). build.py places
them on the beat grid and fits them to their scene.

Setup (model files ~120 MB, not committed):
  pip install kokoro-onnx soundfile scipy numpy
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Run:
  python3 pathshala/ep03-data-types/make_voice.py --models <dir with the two files>
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
    ("l01", "पाइथन के डेटा टाइप्स... एक ही चीट शीट में!", "Python ke data types... ek hi cheat sheet mein!"),
    ("l02", "डेटा टाइप मतलब, डेटा की किस्म।", "Data type matlab data ki kism."),
    ("l03", "नंबर अलग डिब्बे में, टेक्स्ट अलग डिब्बे में।", "Number alag dabbe mein, text alag dabbe mein."),
    ("l04", "और टाइप लिखो, तो पाइथन खुद बता देता है: ये इंट है, ये स्ट्रिंग है।",
     "Aur type() likho, toh Python khud bata deta hai: yeh int hai, yeh str hai."),
    ("l05", "पाइथन में नौ ज़रूरी टाइप्स हैं, चार फ़ैमिली में!", "Python mein 9 zaroori types hain, 4 family mein."),
    ("l06", "पहली फ़ैमिली नंबर्स: इंट मतलब पूरा नंबर, फ़्लोट मतलब पॉइंट वाला, और कॉम्प्लेक्स में जे वाला इमेजिनरी पार्ट।",
     "Pehli family Numbers: int matlab poora number, float matlab point wala, aur complex mein j wala imaginary part."),
    ("l07", "दूसरी सीक्वेंस: स्ट्रिंग मतलब टेक्स्ट, लिस्ट जो बदल सकती है, और टपल जो फ़िक्स्ड रहता है।",
     "Doosri Sequence: str matlab text, list jo badal sakti hai, aur tuple jo fixed rehta hai."),
    ("l08", "तीसरी मैपिंग: डिक्ट, जिसमें की और वैल्यू की जोड़ी होती है।",
     "Teesri Mapping: dict, jismein key aur value ki jodi hoti hai."),
    ("l09", "और लास्ट में सेट, जिसमें डुप्लीकेट नहीं, और बूल: ट्रू या फ़ॉल्स, बस हाँ या ना।",
     "Aur last mein set, jismein duplicate nahi, aur bool: True ya False, bas haan ya na."),
    ("l10", "ये पूरी शीट स्क्रीनशॉट कर लो!", "Yeh poori sheet screenshot kar lo!"),
    ("l11a", "क्विज़ टाइम! थ्री पॉइंट ज़ीरो का टाइप क्या है?", "Quiz time! 3.0 ka type kya hai?"),
    ("l11b", "फ़्लोट! क्योंकि पॉइंट है।", "Float! Kyunki point hai."),
    ("l12", "वीडियो अच्छा लगा तो लाइक, शेयर, सब्सक्राइब। कल मिलते हैं इनपुट के साथ!",
     "Video achha laga toh like, share, subscribe. Kal milte hain input() ke saath!"),
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
