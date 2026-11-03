#!/usr/bin/env python3
"""13 s LOOP 'ESP32 Heart Rate Monitor' short (MAX30102 + OLED) in the moody B&W + colour-screen style:
the 3D render is graded to black & white with soft window-blind light, and only the OLED screen, the two
LEDs and the red sensor light under the finger keep their colour (projected positions from scene3d ->
work/proj). Colour 'HEART CAM' monitor panel, hook from frame 0, notification twist ('Crush ka message
aaya'), HIGH alarm, calm-down, loop question + CTA, all text inside the Shorts safe zone. Monitor beeps on
every beat, alarm while HIGH, phone ping, whooshes on cuts. Usage: python3 edit32/build_short.py [audio] [video]"""
import importlib.util
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
_spec = importlib.util.spec_from_file_location("b30", os.path.join(ROOT, "edit30", "build_short.py"))
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)
sys.path.insert(0, HERE)
from hrtime import FPS, N, SHOTS, NOTIF, BEATS, since_beat, shown_bpm, high, sensor_glow  # noqa: E402
import hrgfx  # noqa: E402

fx, e5, font, txt, pop_s, ease, head, tag, zoom = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head, b.tag, b.zoom
MONT, BOLD, INK, WHT, YEL, CYAN, GRN, RED = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN, b.RED
PINK = (255, 90, 200)
W, H, SR = 1080, 1920, 48000
WORK = os.path.join(HERE, "work")
F3D = os.environ.get("F3D", os.path.join(WORK, "frames3d"))
PROJ = os.path.join(WORK, "proj")
OUT = os.path.join(HERE, "output", "esp32-heart-rate-monitor-SHORT.mp4")
TOTAL = N
PX0, PY0, PW, PH = 40, 360, 1000, 500
HIGH_AT = next(f for f in range(N) if high(f))
CALM_AT = max(f for f in range(N) if high(f)) + 1


def t(f):
    return f / FPS


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


# ------------------------------------------------------------------ B&W + colour grade
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H * 0.5) / (H * 0.62)) ** 2).clip(0, 1)


def blinds(f):
    """Soft diagonal window-blind light falling across the scene, drifting slowly (loops)."""
    ph = 2 * math.pi * f / N
    u = (xx * 0.55 + yy * 0.83) / 120.0 + 0.6 * math.sin(ph)
    s = 0.5 + 0.5 * np.sin(u * 2 * math.pi)
    return 0.72 + 0.38 * np.clip((s - 0.35) * 2.2, 0, 1)


_BL = {}


def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    return b._grade(im)


def proj(f):
    p = os.path.join(PROJ, f"{f:04d}.json")
    with open(p) as fh:
        return json.load(fh)


def grade(fr, f):
    x = fr.astype(np.float32)
    g = (x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11)
    g = np.clip((g - 128) * 1.25 + 118, 0, 255)                     # punchy B&W
    key = f % 48
    if key not in _BL:
        _BL[key] = blinds(key * N / 48)
    g = g * _BL[key] * (1 - 0.55 * VIG)
    bw = np.repeat(g[..., None], 3, axis=2)
    p = proj(f)
    m = np.zeros((H, W), np.float32)
    s = p["screen"]
    cv2.fillPoly(m, [np.array([s[0], s[1], s[3], s[2]], np.int32)], 1.0)
    r = max(8.0, p["cm_px"])
    for key_, sx, sy in (("led_r", 0.42, 0.75), ("led_g", 0.42, 0.75), ("sensor", 0.75, 0.6)):
        cx, cy = p[key_]
        cv2.ellipse(m, (int(cx), int(cy)), (int(r * sx), int(r * sy)), 0, 0, 360, 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 4)[..., None]
    out = bw * (1 - m) + x * 1.08 * m
    # coloured glows: red beat LED, green normal LED, red sensor light through the finger
    glow = np.zeros((H, W, 3), np.float32)
    sb = since_beat(f)
    hi = high(f)
    lr = 1.0 if (sb < 4 or (hi and (f // 3) % 2 == 0)) else 0.0
    lg = 0.0 if hi else 0.7
    sg = (sensor_glow(f) - 0.5) * 1.6
    for key_, amt, col, rad in (("led_r", lr, (255, 40, 30), 1.6), ("led_g", lg, (40, 255, 90), 1.4), ("sensor", sg, (255, 30, 40), 2.2)):
        if amt <= 0:
            continue
        cx, cy = p[key_]
        gm = np.zeros((H, W), np.float32)
        cv2.circle(gm, (int(cx), int(cy)), int(r * rad * 0.6), amt, -1)
        glow += cv2.GaussianBlur(gm, (0, 0), r * rad * 0.7)[..., None] * np.array(col, np.float32)
    out = out + glow * 0.9
    if hi:                                                         # red alarm pulse at the frame edges
        a = 0.22 * (0.5 + 0.5 * math.cos(2 * math.pi * (f % 12) / 12))
        out = out * (1 - a * VIG[..., None]) + np.array((255, 20, 40), np.float32) * a * VIG[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ overlay
def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("❤️", 46), (W - 388, 46))


def panel(lay, f):
    g = hrgfx.draw_hd(f, PW, PH).convert("RGBA")
    m = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), 34, fill=255)
    sh = Image.new("RGBA", (PW + 40, PH + 40))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, PW + 20, PH + 26), 36, fill=(0, 0, 0, 160))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (PX0 - 20, PY0 - 20))
    lay.paste(g, (PX0, PY0), m)
    d = ImageDraw.Draw(lay)
    hi = high(f)
    d.rounded_rectangle((PX0, PY0, PX0 + PW - 1, PY0 + PH - 1), 34, outline=(RED if hi else YEL) + (255,), width=9)
    d.rounded_rectangle((PX0 + 22, PY0 - 26, PX0 + 300, PY0 + 26), 26, fill=RED + (255,), outline=WHT, width=3)
    d.ellipse((PX0 + 40, PY0 - 9, PX0 + 58, PY0 + 9), fill=WHT if (f // 6) % 2 == 0 else (255, 160, 160))
    d.text((PX0 + 180, PY0), "HEART CAM", font=font(MONT, 32), fill=WHT, anchor="mm")


def notification(lay, f):
    a = f - NOTIF
    if a < 0 or f >= SHOTS[3]:
        return
    u = ease(a / 6)
    y0 = 900 - (1 - u) * 260
    cx = W / 2 - 40
    d = ImageDraw.Draw(lay)
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).rounded_rectangle((cx - 400, y0 + 12, cx + 400, y0 + 182), 40, fill=(0, 0, 0, int(150 * u)))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d.rounded_rectangle((cx - 400, y0, cx + 400, y0 + 170), 40, fill=(248, 248, 252, int(250 * u)))
    if u > 0.8:
        d.rounded_rectangle((cx - 370, y0 + 30, cx - 270, y0 + 130), 24, fill=(52, 199, 89, 255))
        lay.alpha_composite(e5.emoji("💬", 64), (int(cx - 352), int(y0 + 48)))
        d.text((cx - 245, y0 + 52), "Crush", font=font(MONT, 40), fill=INK, anchor="lm")
        tw = d.textlength("Crush", font=font(MONT, 40))
        lay.alpha_composite(e5.emoji("❤️", 38), (int(cx - 245 + tw + 10), int(y0 + 33)))
        d.text((cx + 375, y0 + 52), "abhi", font=font(BOLD, 30), fill=(130, 130, 140), anchor="rm")
        d.text((cx - 245, y0 + 108), "Hi, free ho?", font=font(BOLD, 40), fill=(40, 40, 50), anchor="lm")
        tw = d.textlength("Hi, free ho?", font=font(BOLD, 40))
        lay.alpha_composite(e5.emoji("👋", 40), (int(cx - 245 + tw + 10), int(y0 + 88)))


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    g = Image.new("L", (1, H))
    g.putdata([int(170 * max(0, 1 - y_ / 520)) for y_ in range(H)])
    lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    d = ImageDraw.Draw(lay)
    show_panel = True
    if i == 0:
        pulse = 1 + 0.04 * math.sin(f * 0.6)
        head(lay, d, "Doctor ki machine ghar pe?", 175, 80, YEL, "😱", pulse)
        head(lay, d, "ESP32 Heart Rate Monitor", 275, 64, PINK, "❤️")
    elif i == 1:
        show_panel = False
        head(lay, d, "Bas ungli rakho!", 190, 92, CYAN, "☝️", pop_s(local, 5))
        p = proj(f)
        tag(lay, d, p["sensor"], (p["sensor"][0] + 230, p["sensor"][1] - 330), "MAX30102", "Heart sensor", ease((local - 4) / 10))
    elif i == 2:
        if f < NOTIF:
            head(lay, d, f"Normal: {shown_bpm(f)} BPM", 200, 84, GRN, "😌", pop_s(local, 5))
        else:
            head(lay, d, "Crush ka message aaya...", 200, 76, PINK, "😳", pop_s(f - NOTIF, 5))
            notification(lay, f)
    elif i == 3:
        if f < HIGH_AT:
            head(lay, d, "Dhak... dhak... dhak...", 200, 80, WHT, "💓", pop_s(local, 5))
        else:
            head(lay, d, "HEART RATE HIGH!", 200, 96, (255, 70, 90), "🚨", pop_s(f - HIGH_AT, 5))
    elif i == 4:
        head(lay, d, "Shant ho jao bhai", 200, 92, WHT, "😅", pop_s(local, 5))
    else:
        head(lay, d, "Tumhara BPM kitna?", 195, 84, YEL, "👇", pop_s(local, 5))
        v = ease((local - 6) / 6)
        if v > 0:
            bw = int(820 * v)
            cx = W / 2 - 50
            d.rounded_rectangle((cx - bw / 2, 900, cx + bw / 2, 1010), 55, fill=YEL + (255,))
            if v > 0.9:
                d.text((cx, 955), "Comment \"HEART\" = Code FREE", font=font(MONT, 42), fill=INK, anchor="mm")
    if show_panel:
        panel(lay, f)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


# ------------------------------------------------------------------ audio
def beep(freq, dur, vol=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * tt) * np.minimum(1, tt / 0.004) * np.minimum(1, (dur - tt) / 0.02) * vol


def thump():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    lub = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18)
    dub = np.zeros(n)
    k = int(0.16 * SR)
    dub[k:] = np.sin(2 * np.pi * 70 * tt[: n - k]) * np.exp(-tt[: n - k] * 22) * 0.7
    return (lub + dub) * 0.9


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    mus = b.music(total + 0.05)
    mus = fx.filt(mus, "lowpass", 2200) * 0.55
    fx.write_wav(os.path.join(WORK, "music.wav"), mus)
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.45)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.25, s) * 0.6, max(0, t(s) - 0.12), 0.35)
    for bf in BEATS:
        hi = high(bf)
        P(buf, beep(1350 if hi else 1000, 0.09, 0.45), t(bf), 0.55)
        P(buf, thump(), t(bf), 0.75)
    f = HIGH_AT
    while f < CALM_AT:                                           # monitor alarm while HIGH
        P(buf, beep(880, 0.12, 0.35), t(f) + 0.18, 0.35)
        P(buf, beep(880, 0.12, 0.35), t(f) + 0.36, 0.35)
        f += 24
    P(buf, np.concatenate([beep(1568, 0.08, 0.4), beep(2093, 0.16, 0.4)]), t(NOTIF), 0.6)   # phone ping
    P(buf, fx.riser(0.6), t(HIGH_AT) - 0.5, 0.3)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf)
    fc = ("[0:a]loudnorm=I=-22:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


def render_frame(f):
    fr = grade(load3d(f), f)
    z = 1.0
    for h0, amp in [(bf, 0.012) for bf in BEATS] + [(NOTIF, 0.04), (HIGH_AT, 0.05)] + [(s_, 0.05) for s_ in SHOTS[1:]]:
        a = f - h0
        if 0 <= a < 6:
            z += amp * (1 - a / 6) ** 2
    if z > 1.0:
        fr = zoom(fr, z)
    fr = overlay(fr, f)
    b.rainbow_bar(fr, int(W * (f + 1) / TOTAL))
    return fr


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-maxrate", "18M", "-bufsize", "36M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    for f in range(TOTAL):
        enc.stdin.write(np.ascontiguousarray(render_frame(f)).tobytes())
        if f % 48 == 0:
            print(f"  frame {f}/{TOTAL}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["audio", "video"]
    if steps[0] == "preview":
        fs = [int(v) for v in steps[1].split(",")]
        ims = [Image.fromarray(render_frame(f)).resize((540, 960)) for f in fs]
        c = Image.new("RGB", (540 * len(ims), 960))
        for i, im in enumerate(ims):
            c.paste(im, (i * 540, 0))
        c.save(steps[2])
        sys.exit()
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
