#!/usr/bin/env python3
"""16 s Smart Plant IoT short: reference-style labels (white bold text + animated blue corner
frames), blur transitions, hook title, progress bar and end card; original music + synced SFX
(shadow swoosh, live-data blips, servo whirr, LED click).
Usage: python3 edit6/build_short.py [audio] [video]
"""
import importlib.util
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402
from timeline import FPS, N, SHOTS, SHADOW, SLIDE, LED_ON, servo_deg  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "smart-plant-iot-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
BLUE, WHT, YEL, INK = (40, 140, 255), (255, 255, 255), (255, 214, 10), (15, 18, 26)

# shot index -> (label, sub, frame box (x0,y0,x1,y1) or None, emoji)
LABELS = {
    1: ("LDR Sensor", "Haath hilao → graph girta hai", (300, 330, 780, 1000), None),
    2: ("Live Dashboard", "WiFi se real-time data", (180, 120, 900, 1700), "📶"),
    3: ("Arduino UNO R4 WiFi", "12×8 LED matrix", (120, 520, 960, 1300), None),
    4: ("Phone Slider", "drag karo → servo ghoomega", (180, 900, 900, 1400), None),
    5: ("Motor (SG90)", "Servo follows the phone", (240, 300, 860, 1300), "⚙️"),
    6: ("Andhera? LED ON", "LDR khud detect karta hai", None, "💡"),
}


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


ease = e5.ease
font = e5.font


# ================================================================== audio
def servo_whirr(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = fx.signal.sawtooth(2 * np.pi * (170 + 25 * np.sin(2 * np.pi * 3 * t)) * t)
    x = fx.filt(x, "bandpass", [150, 2500]) + 0.3 * fx.filt(fx.noise(n, 4), "bandpass", [2000, 6000])
    env = np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.08)
    return x * env * 0.35


def click():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return fx.filt(fx.noise(n, 9), "bandpass", [1500, 7000]) * np.exp(-t * 140) * 0.8


def sfx_track(total):
    n = int(total * SR)
    buf = np.zeros(n)
    P = fx.place
    t = lambda f: f / FPS  # noqa: E731
    P(buf, fx.boom()[: int(0.5 * SR)], 0.0, 0.45)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for i, s in enumerate(SHOTS[1:7]):
        P(buf, e5.blip(1175 + 120 * (i % 3)), t(s + 4), 0.3)               # label pop
    P(buf, fx.whoosh(0.6, 77)[::-1], t(SHADOW[0]), 0.55)                    # hand-shadow swoosh
    for f in range(SHOTS[2], SHOTS[3], 6):                                   # live data blips
        P(buf, e5.ping() * 0.6, t(f), 0.25)
    P(buf, servo_whirr(t(SLIDE[1] - SLIDE[0])), t(SLIDE[0]), 0.5)          # slider drag -> servo
    for f in range(SLIDE[0], SLIDE[1], 4):
        P(buf, click() * 0.4, t(f), 0.2)
    P(buf, servo_whirr(t(44)), t(242), 0.6)                                 # servo sweep close-up
    P(buf, click(), t(LED_ON), 0.7)                                          # LED switch
    P(buf, e5.blip(880), t(LED_ON + 2), 0.4)
    P(buf, e5.notify(), t(SHOTS[7] + 6), 0.5)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), e5.music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    fc = ("[0:a]loudnorm=I=-19:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== video
def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    im = cv2.addWeighted(im, 1.25, cv2.GaussianBlur(im, (0, 0), 1.6), -0.25, 0)
    x = im.astype(np.float32) / 255
    sat = x.max(2, keepdims=True) - x.min(2, keepdims=True)
    bright = x * np.clip((x.max(2, keepdims=True) - 0.7) / 0.3, 0, 1) * np.clip(sat / 0.35, 0, 1)
    sm = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    x += cv2.resize(cv2.GaussianBlur(sm, (0, 0), 8), (W, H)) * 0.45
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def corner_frame(d, box, u, col=BLUE, w=8, L=120):
    """Reference-style blue corner brackets that draw themselves in (u: 0..1)."""
    x0, y0, x1, y1 = box
    ln = L * ease(u)
    if ln < 2:
        return
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((cx, cy, cx + sx * ln, cy), fill=col, width=w)
        d.line((cx, cy, cx, cy + sy * ln), fill=col, width=w)


def emoji_img(ch, size):
    return e5.emoji(ch, size)


def label(lay, d, text, sub, local, y=1560, em=None):
    u = ease(local / 6)
    if u <= 0:
        return
    n = min(len(text), int(local * 1.6) + 1)                        # letters type on
    fnt = font(MONT, 84)
    shown = text[:n]
    d.text((W / 2, y + (1 - u) * 40), shown, font=fnt, fill=WHT, anchor="mm", stroke_width=7, stroke_fill=(0, 0, 0))
    v = ease((local - 8) / 6)
    if v > 0 and sub:
        d.text((W / 2, y + 85), sub, font=font(BOLD, 44), fill=(225, 235, 255), anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0))
    tw = d.textlength(text, font=fnt)
    d.line((W / 2 - tw / 2 * u, y + 52, W / 2 + tw / 2 * u, y + 52), fill=BLUE, width=8)
    if em and u > 0.9:
        e = emoji_img(em, 96)
        lay.alpha_composite(e, (int(W / 2 + tw / 2 + 16), int(y - 60)))


def hook(lay, d, local):
    u = ease(local / 6)
    sc = 0.7 + 0.3 * u
    d.text((W / 2, 230), "PLANT ko PHONE se", font=font(MONT, int(64 * sc)), fill=WHT, anchor="mm",
           stroke_width=8, stroke_fill=(0, 0, 0))
    d.text((W / 2, 340), "CONTROL karo!", font=font(MONT, int(84 * sc)), fill=YEL, anchor="mm",
           stroke_width=9, stroke_fill=(0, 0, 0))
    if u > 0.9:
        lay.alpha_composite(emoji_img("🌱", 100), (110, 410))
        lay.alpha_composite(emoji_img("📱", 100), (W - 210, 410))
    v = ease((local - 10) / 8)
    if v > 0:
        d.rounded_rectangle((W / 2 - 300, 1560, W / 2 + 300, 1660), 50, fill=(255, 255, 255, int(230 * v)))
        d.text((W / 2, 1610), "Arduino IoT Project", font=font(MONT, 46), fill=INK, anchor="mm")


def end_card(lay, d, local):
    g = Image.new("L", (1, H))
    g.putdata([int(190 * max(0, 1 - y / 640)) for y in range(H)])
    lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    u = ease(local / 6)
    d.text((W / 2, 190), "Circuit + Code", font=font(MONT, int(90 * (0.8 + 0.2 * u))), fill=WHT, anchor="mm",
           stroke_width=8, stroke_fill=(0, 0, 0))
    corner_frame(d, (110, 110, W - 110, 280), u, w=9, L=140)
    v = ease((local - 8) / 8)
    if v > 0:
        bw = int(900 * v)
        d.rounded_rectangle((W / 2 - bw / 2, 1520, W / 2 + bw / 2, 1670), 75, fill=YEL)
        if v > 0.9:
            d.text((W / 2, 1595), "Comment \"PLANT\" — code bhejta hoon", font=font(MONT, 46), fill=INK, anchor="mm")
    w_ = ease((local - 16) / 8)
    if w_ > 0:
        d.text((W / 2, 1760), "@The IOT Engineer", font=font(MONT, 62), fill=WHT, anchor="mm",
               stroke_width=5, stroke_fill=(0, 0, 0))


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i == 0:
        hook(lay, d, local)
    elif i in LABELS:
        text, sub, box, em = LABELS[i]
        if box:
            corner_frame(d, box, (local - 2) / 8)
        label(lay, d, text, sub, local, em=em)
    else:
        end_card(lay, d, local)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    for f in range(N):
        i, local = shot_of(f)
        fr = overlay(load3d(f), f)
        for s in SHOTS[1:]:                                   # reference-style blur transition
            dd = f - s
            if -3 <= dd < 4:
                k_ = 1 - abs(dd + 0.5) / 4
                fr = cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_)
                z = 1 + 0.05 * k_
                M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
                fr = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)
        fr[0:8, :] = (fr[0:8, :] * 0.4).astype(np.uint8)
        fr[0:8, : int(W * (f + 1) / N)] = BLUE
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 48 == 0:
            print(f"  frame {f}/{N}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["audio", "video"]
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
