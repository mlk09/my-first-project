#!/usr/bin/env python3
"""Generates the Hinglish voice-over lines for the episode with an
offline Kokoro TTS voice (hm_omega, Hindi). Lines are written in Devanagari so
the Hindi voice pronounces the Hinglish naturally.

Each line is saved as work/vo_XX.wav (48 kHz, trimmed). build.py places
them on the beat grid and fits them to their scene.

Setup (model files ~120 MB, not committed):
  pip install kokoro-onnx soundfile scipy numpy
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Run:
  python3 pathshala/ep06-operators/make_voice.py --models <dir with the two files>
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
    ("w01", "पाइथन के सारे ऑपरेटर्स, एक ही शॉर्ट में!", "Python ke saare operators, ek hi short mein!"),
    ("w02", "ऑपरेटर मतलब एक सिंबल जो डेटा पर काम करता है।", "Operator matlab ek symbol jo data par kaam karta hai."),
    ("w03", "जैसे टेन प्लस फ़ाइव: टेन और फ़ाइव हैं ऑपरेंड्स, प्लस है ऑपरेटर, और जवाब फ़िफ़्टीन।",
     "Jaise 10 plus 5: 10 aur 5 hain operands, plus hai operator, aur jawab 15."),
    ("w04", "पाइथन में ऑपरेटर्स के पाँच टाइप्स हैं!", "Python mein operators ke 5 types hain."),
    ("w05", "पहला अरिथमेटिक: प्लस, माइनस, गुणा, भाग... जैसे सेवन फ़्लोर टू, बराबर थ्री।",
     "Pehla Arithmetic: plus, minus, guna, bhaag... jaise 7 floor 2 = 3."),
    ("w06", "दूसरा असाइनमेंट: एक्स प्लस-इक्वल फ़ाइव, मतलब एक्स बराबर एक्स प्लस फ़ाइव।",
     "Doosra Assignment: x plus-equal 5, matlab x = x + 5."),
    ("w07", "तीसरा कम्पैरिज़न: दो चीज़ें कम्पेयर करो, फ़ाइव बड़ा है थ्री से: ट्रू।",
     "Teesra Comparison: do cheezein compare karo, 5 bada hai 3 se: True."),
    ("w08", "चौथा लॉजिकल: एंड, ऑर, नॉट। ट्रू एंड फ़ॉल्स बराबर फ़ॉल्स।",
     "Chautha Logical: and, or, not. True and False = False."),
    ("w09", "और पाँचवाँ मेंबरशिप: इन। क्या ए, एप्पल में है? ट्रू! बोर्ड सेव कर लो!",
     "Aur paanchva Membership: in. Kya 'a' apple mein hai? True! Board save kar lo!"),
    ("w10", "सबसे कन्फ़्यूज़िंग: सेवन बाय टू, थ्री पॉइंट फ़ाइव। सेवन फ़्लोर टू, थ्री। और सेवन मॉड टू, वन, जो बचा हुआ है।",
     "Sabse confusing: 7 / 2 = 3.5, 7 // 2 = 3, aur 7 % 2 = 1, jo bacha hua hai."),
    ("w11a", "क्विज़! टेन मॉड थ्री क्या होगा?", "Quiz! 10 % 3 kya hoga?"),
    ("w11b", "वन! टेन में थ्री, तीन बार, और वन बचा।", "1! 10 mein 3 teen baar, aur 1 bacha."),
    ("w12", "लाइक, शेयर, सब्सक्राइब। अगला एपिसोड: एफ़-स्ट्रिंग्स!", "Like, share, subscribe. Agla episode: f-strings!"),
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
