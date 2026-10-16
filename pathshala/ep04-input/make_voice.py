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
  python3 pathshala/ep04-input/make_voice.py --models <dir with the two files>
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
    ("v01", "क्या आपका प्रोग्राम आपसे बात कर सकता है? हाँ!", "Kya aapka program aapse baat kar sakta hai? Haan!"),
    ("v02", "इनपुट फ़ंक्शन यूज़र से सवाल पूछता है... और जवाब का इंतज़ार करता है।",
     "input() function user se sawaal poochta hai... aur jawab ka intezaar karta hai."),
    ("v03", "कोड लिखो: नेम बराबर इनपुट, नाम क्या है?", "Code likho: name barabar input, Naam kya hai?"),
    ("v04", "रन करो... देखो, प्रोग्राम रुक गया, आपके जवाब के लिए।", "Run karo... dekho, program ruk gaya, aapke jawab ke liye."),
    ("v05", "नाम लिखो, एंटर दबाओ... और पाइथन बोलेगा: नमस्ते अमन!", "Naam likho, Enter dabao... aur Python bolega: Namaste Aman!"),
    ("v06", "पर एक ट्विस्ट है! इनपुट हमेशा स्ट्रिंग देता है। ट्वेंटी भी स्ट्रिंग बन जाता है।",
     "Par ek twist hai! input() hamesha string deta hai. 20 bhi string ban jaata hai."),
    ("v07", "अब एज लो, और उसमें प्लस वन करो...", "Ab age lo, aur usme plus one karo..."),
    ("v08", "एरर! स्ट्रिंग और नंबर को जोड़ नहीं सकते।", "Error! String aur number ko jod nahi sakte."),
    ("v09", "फ़िक्स सिंपल है: इंट लगाओ। रन करो... ट्वेंटी वन! अब ये नंबर है।",
     "Fix simple hai: int() lagao. Run karo... 21! Ab yeh number hai."),
    ("v10", "डेसिमल चाहिए? तो फ़्लोट यूज़ करो।", "Decimal chahiye? Toh float() use karo."),
    ("v11", "ये तीन लाइन्स याद रखो, स्क्रीनशॉट ले लो!", "Yeh teen lines yaad rakho, screenshot le lo!"),
    ("v12", "लाइक, शेयर, सब्सक्राइब! अगले एपिसोड में: टाइप कास्टिंग।", "Like, share, subscribe! Agle episode mein: type casting."),
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
