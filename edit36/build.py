#!/usr/bin/env python3
"""13 s ESP32 Smart Dustbin short from the user's 10 s vertical Gemini AI clip (real-looking hand, lid opens by
itself), kept ORIGINAL (no grade, no animation on the clip): full-frame 1080x1920, captions in the safe zone
over a soft top shade, detect beep / servo whirr / paper thud / lid click, then the 3 s Like / Share / big
pulsing SUBSCRIBE end page (edit31 helper). Usage: python3 edit36/build.py [preview FRAMES OUT]"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
_spec = importlib.util.spec_from_file_location("b31", os.path.join(ROOT, "edit31", "build.py"))
b31 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b31)
b = b31.b                                             # edit30 helpers
fx, e5, font, txt, pop_s, ease, head = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head
MONT, BOLD, INK, WHT, YEL, CYAN, GRN = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN
PINK = (255, 90, 200)
SRC = os.path.join(HERE, "work", "src")
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "esp32-smart-dustbin-SHORT.mp4")
FPS, SR, W, H = 24, 48000, 1080, 1920
CLIP, OUTRO = 240, 72
TOTAL = CLIP + OUTRO
HAND, OPEN, DROP, CLOSE = 40, 78, 126, 176

def grade(im, f):
    """The clip stays original - no colour change."""
    return im


_VIG = None


def layout(card, f):
    """Vertical clip -> full 1080x1920 frame with a soft dark shade behind the captions."""
    global _VIG
    out = cv2.resize(card, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    if _VIG is None:
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        _VIG = 1 - 0.62 * np.clip(1 - yy / 560, 0, 1)
    return np.clip(out * _VIG, 0, 255).astype(np.uint8)


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🗑️", 46), (W - 388, 46))


def overlay(fr, f):
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    badge(lay, d)
    d = ImageDraw.Draw(lay)
    if f < HAND:
        head(lay, d, "Ye dustbin khud khulta hai!", 180, 78, YEL, "😱", 1 + 0.03 * math.sin(f * 0.6))
        head(lay, d, "ESP32 Smart Dustbin", 282, 66, PINK, "🗑️")
    elif f < OPEN:
        head(lay, d, "Bas haath paas lao", 210, 92, CYAN, "👋", pop_s(f - HAND, 5))
    elif f < DROP - 8:
        head(lay, d, "Lid OPEN!", 210, 110, GRN, "🔓", pop_s(f - OPEN, 5))
    elif f < 152:
        head(lay, d, "Kachra andar!", 210, 104, YEL, "🎯", pop_s(f - DROP + 8, 5))
    elif f < CLOSE:
        head(lay, d, "Touch-free = Germ-free", 210, 82, GRN, "🧼", pop_s(f - 152, 5))
    elif f < 205:
        head(lay, d, "Auto CLOSE", 210, 108, WHT, "✅", pop_s(f - CLOSE, 5))
    else:
        head(lay, d, "Apne ghar me chahiye?", 200, 82, YEL, "👇", pop_s(f - 205, 5))
        v = ease((f - 211) / 6)
        if v > 0:
            bw = int(800 * v)
            cx = W / 2 - 50
            d.rounded_rectangle((cx - bw / 2, 330, cx + bw / 2, 430), 50, fill=YEL + (255,))
            if v > 0.9:
                d.text((cx, 380), "Comment \"BIN\" = Code FREE", font=font(MONT, 44), fill=INK, anchor="mm")
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def frame(f):
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, f"{f:04d}.png")), cv2.COLOR_BGR2RGB)
    fr = overlay(layout(grade(im, f), f), f)
    b.rainbow_bar(fr, int(W * f / TOTAL))
    return fr


BEATS = list(range(8, CLIP, 19))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    t = lambda f: f / FPS  # noqa: E731
    mus = fx.filt(b.music(total + 0.05), "lowpass", 2200) * 0.6
    i0 = int(t(CLIP) * SR)
    mus[i0:] = fx.filt(mus[i0:], "lowpass", 1200) * 0.7
    fx.write_wav(os.path.join(WORK, "music.wav"), mus)
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place

    def beep(freq, dur, vol=0.5):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        return np.sin(2 * np.pi * freq * tt) * np.minimum(1, tt / 0.004) * np.minimum(1, (dur - tt) / 0.02) * vol

    def thump():
        n = int(0.35 * SR)
        tt = np.arange(n) / SR
        lub = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18)
        k = int(0.16 * SR)
        dub = np.zeros(n)
        dub[k:] = np.sin(2 * np.pi * 70 * tt[: n - k]) * np.exp(-tt[: n - k] * 22) * 0.7
        return (lub + dub) * 0.9

    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.4)
    P(buf, np.concatenate([beep(1800, 0.06, 0.4), np.zeros(int(0.04 * SR)), beep(2400, 0.08, 0.4)]), t(OPEN - 6), 0.5)  # detected
    n = int(0.6 * SR)                                                      # servo whirr (open / close)
    tt = np.arange(n) / SR
    whirr = fx.filt(np.sign(np.sin(2 * np.pi * (170 + 50 * np.sin(tt * 11)) * tt)), "bandpass", [300, 3000]) * np.sin(np.pi * tt / 0.6) * 0.45
    P(buf, whirr, t(OPEN), 0.6)
    P(buf, whirr, t(CLOSE), 0.6)
    P(buf, fx.filt(fx.noise(int(0.2 * SR), 7), "lowpass", 600) * np.exp(-np.arange(int(0.2 * SR)) / SR * 25), t(DROP + 4), 0.9)
    P(buf, fx.filt(fx.noise(int(0.12 * SR), 3), "lowpass", 900) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30), t(CLOSE + 13), 0.8)
    P(buf, b.ok_beep(), t(CLOSE + 15), 0.35)
    for c_ in (HAND, OPEN, DROP - 8, 152, CLOSE, 205):
        P(buf, fx.pop(), t(c_), 0.18)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(CLIP) - 0.2, 0.45)
    for a in b31.BTN_POP:
        P(buf, fx.pop(), t(CLIP + a), 0.35)
    for a in b31.BTN_PRESS:
        P(buf, b.ok_beep()[: int(0.09 * SR)] * 0.6, t(CLIP + a), 0.4)
    P(buf, fx.ding(), t(CLIP + b31.BTN_PRESS[2] + 1), 0.5)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf)
    fc = ("[0:a]loudnorm=I=-22:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-maxrate", "16M", "-bufsize", "32M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    last = None
    for f in range(TOTAL):
        if f < CLIP:
            fr = frame(f + 1)
            last = fr
        else:
            fr = b31.outro(f - CLIP, last, "Project pasand aaya?", badge=badge, dim=0.55, sub_big=True)
            if f - CLIP < 4:
                k = 1 - (f - CLIP) / 4
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 18 * k), 1 + 0.05 * k)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        fs = [int(v) for v in sys.argv[2].split(",")]
        ims = [Image.fromarray(frame(f)).resize((360, 640)) for f in fs]
        c = Image.new("RGB", (360 * len(ims), 640))
        for i, im in enumerate(ims):
            c.paste(im, (i * 360, 0))
        c.save(sys.argv[3])
    else:
        build_audio()
        build_video()
