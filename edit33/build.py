#!/usr/bin/env python3
"""13 s Heart Rate Monitor short from the user's 10 s landscape Gemini AI clip (lab, finger on the sensor,
ECG on the OLED): graded to cinematic black & white while every screen keeps its colour (OLED tracked by
keyframed quads + a colour key for the oscilloscope / multimeter traces and the glowing LEDs), laid out
vertically as a big card over a blurred B&W fill, captions in the safe zone, then a 3 s Like / Share /
Subscribe end page (from edit31). Heartbeat monitor beeps, chiptune bed, whooshes on the clip's cuts.
Usage: python3 edit33/build.py [preview FRAMES OUT]"""
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
OUT = os.path.join(HERE, "output", "esp32-heart-rate-cinematic-SHORT.mp4")
FPS, SR, W, H = 24, 48000, 1080, 1920
CLIP, OUTRO = 240, 72
TOTAL = CLIP + OUTRO
CUTS = [1, 75, 97, 145]
CARD_Y, CARD_H = 340, 1000
# horizontal crop centre (src px) keyframes so the subject stays in the tall card
PAN = [(1, 690), (74, 640), (75, 640), (96, 640), (97, 700), (144, 700), (145, 880), (175, 720), (240, 640)]

# OLED quads (src 1280x720 pixels): keyframes (frame, TL, TR, BR, BL), interpolated inside each shot
OLED = [
    [(97, (693, 273), (973, 307), (913, 513), (660, 467)), (120, (713, 273), (973, 307), (913, 513), (660, 473)),
     (144, (707, 260), (980, 273), (940, 487), (673, 453))],
    [(145, (927, 367), (1120, 347), (1160, 560), (907, 547)), (175, (873, 349), (1060, 363), (1027, 549), (840, 527)),
     (205, (820, 363), (973, 376), (947, 517), (800, 504)), (240, (797, 380), (920, 389), (900, 507), (780, 496))],
]


def oled_quad(f):
    for keys in OLED:
        if keys[0][0] <= f <= keys[-1][0]:
            for (a, *pa), (z, *pz) in zip(keys, keys[1:]):
                if a <= f <= z:
                    k = (f - a) / max(1, z - a)
                    return np.array([[p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k] for p, q in zip(pa, pz)], np.int32)
    return None


def grade(im, f):
    """RGB src frame -> cinematic B&W with the screens / LEDs in colour."""
    x = im.astype(np.float32)
    g = x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11
    g = np.clip((g - 120) * 1.3 + 112, 0, 255)
    bw = np.repeat(g[..., None], 3, axis=2)
    hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
    hh, ss, vv = hsv[..., 0].astype(np.int16), hsv[..., 1], hsv[..., 2]
    key = ((hh >= 42) & (hh <= 80) & (ss > 75) & (vv > 90)) | ((hh > 80) & (hh <= 95) & (ss > 115) & (vv > 110)) | ((ss > 140) & (vv > 225))   # green / cyan traces + bright LEDs
    m = key.astype(np.float32)
    q = oled_quad(f)
    if q is not None:
        cv2.fillPoly(m, [q], 1.0)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    m = cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3), np.uint8)), (0, 0), 2.5)[..., None]
    col = x * 1.15                                                        # a bit richer colour on the screens
    out = bw * (1 - m) + col * m
    glow = cv2.GaussianBlur(np.clip(col * m * (vv[..., None] > 150), 0, 255), (0, 0), 14)   # neon bloom around coloured bits
    return np.clip(out + glow * 0.6, 0, 255).astype(np.uint8)


_VIG = None


def layout(card, f):
    """Vertical frame: blurred dark B&W fill + the graded clip as a big card."""
    global _VIG
    bg = cv2.resize(card, (int(1920 * 1280 / 720), 1920), interpolation=cv2.INTER_LINEAR)
    x0 = (bg.shape[1] - W) // 2
    bg = cv2.GaussianBlur(bg[:, x0:x0 + W], (0, 0), 30).astype(np.float32) * 0.35
    s = CARD_H / 720
    cw = int(1280 * s)
    fg = cv2.resize(card, (cw, CARD_H), interpolation=cv2.INTER_LANCZOS4)
    pc = PAN[-1][1]
    for (a, xa), (z, xz) in zip(PAN, PAN[1:]):
        if a <= f <= z:
            pc = xa + (xz - xa) * ease((f - a) / max(1, z - a))
            break
    cx0 = int(min(max(pc * s - W / 2, 0), cw - W))
    fg = fg[:, cx0:cx0 + W]
    out = bg.copy()
    out[CARD_Y:CARD_Y + CARD_H] = fg
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _VIG = (1 - 0.4 * (((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2).clip(0, 1))[..., None]
    out = out * _VIG
    cv2.line(out, (0, CARD_Y), (W, CARD_Y), (255, 214, 10), 4)
    cv2.line(out, (0, CARD_Y + CARD_H), (W, CARD_Y + CARD_H), (255, 214, 10), 4)
    return np.clip(out, 0, 255).astype(np.uint8)


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("❤️", 46), (W - 388, 46))


def overlay(fr, f):
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    badge(lay, d)
    d = ImageDraw.Draw(lay)
    if f < 75:
        head(lay, d, "Ungli rakho... aur dekho!", 180, 80, YEL, "😱", 1 + 0.03 * math.sin(f * 0.6))
        head(lay, d, "ESP32 Heart Rate Monitor", 280, 62, PINK, "❤️")
    elif f < 97:
        head(lay, d, "ESP32 = Dimaag", 210, 96, CYAN, "🧠", pop_s(f - 75, 5))
    elif f < 145:
        head(lay, d, "OLED pe dil ki dhadkan!", 210, 84, (255, 80, 110), "💓", pop_s(f - 97, 5))
    elif f < 200:
        head(lay, d, "Real-time ECG on OLED", 210, 80, GRN, "⚡", pop_s(f - 145, 5))
    else:
        head(lay, d, "Tumhara BPM kitna?", 200, 88, YEL, "👇", pop_s(f - 200, 5))
        v = ease((f - 206) / 6)
        if v > 0:
            bw = int(820 * v)
            cx = W / 2 - 50
            d.rounded_rectangle((cx - bw / 2, 1180, cx + bw / 2, 1280), 50, fill=YEL + (255,))
            if v > 0.9:
                d.text((cx, 1230), "Comment \"HEART\" = Code FREE", font=font(MONT, 42), fill=INK, anchor="mm")
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
    for c in CUTS[1:]:
        P(buf, fx.whoosh(0.25, c) * 0.6, max(0, t(c) - 0.12), 0.35)
    for bf in BEATS:
        P(buf, beep(1000, 0.09, 0.45), t(bf), 0.5)
        P(buf, thump(), t(bf), 0.75)
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
