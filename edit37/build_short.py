#!/usr/bin/env python3
"""13 s LOOP 'ESP32 Smart Plant Watering' short in the B&W + colour style: the 3D render is graded to black &
white with soft window-blind light; the OLED, the LEDs and the WATER (tank, tube, stream - blue key inside its
projected region) keep their colour, and the PLANT gets its green back as the soil gets wet (green key inside
the plant region, strength = planttime.wet). 'PLANT CAM' panel on the data shots, hook from frame 0, pump ON /
OFF, '3 din baad' dry-out loop, CTA - all text inside the Shorts safe zone. Pump hum, water pour, beeps.
Usage: python3 edit37/build_short.py [audio] [video]"""
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
from planttime import FPS, N, SHOTS, PUMP_ON, PUMP_OFF, DRYING, pump, flow, wet, state, moisture  # noqa: E402
import plantgfx  # noqa: E402

fx, e5, font, txt, pop_s, ease, head, tag, zoom = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head, b.tag, b.zoom
MONT, BOLD, INK, WHT, YEL, CYAN, GRN, RED = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN, b.RED
PINK = (255, 90, 200)
W, H, SR = 1080, 1920, 48000
WORK = os.path.join(HERE, "work")
F3D = os.environ.get("F3D", os.path.join(WORK, "frames3d"))
PROJ = os.path.join(WORK, "proj")
OUT = os.path.join(HERE, "output", "esp32-smart-plant-watering-SHORT.mp4")
TOTAL = N
PX0, PY0, PW, PH = 40, 360, 1000, 500
FLOW_AT = PUMP_ON + 6


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
    for key_ in ("led_r", "led_g"):
        cx, cy = p[key_]
        cv2.ellipse(m, (int(cx), int(cy)), (int(r * 0.42), int(r * 0.75)), 0, 0, 360, 1.0, -1)
    hsv = cv2.cvtColor(fr, cv2.COLOR_RGB2HSV)
    hh, ss, vv = hsv[..., 0].astype(np.int16), hsv[..., 1], hsv[..., 2]
    def region(box):
        rm = np.zeros((H, W), np.float32)
        x0, y0, x1, y1 = [int(v) for v in box]
        rm[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1.0
        return rm
    green = ((hh >= 25) & (hh <= 85) & (ss > 60) & (vv > 30)).astype(np.float32) * region(p["plant"]) * wet(f)
    blue = ((hh >= 90) & (hh <= 130) & (ss > 40) & (vv > 50)).astype(np.float32) * np.maximum(region(p["water"]), region(p["tube"]))
    m = np.maximum(m, np.maximum(green, blue))
    m = cv2.GaussianBlur(m, (0, 0), 3)[..., None]
    out = bw * (1 - m) + x * 1.1 * m
    glow = np.zeros((H, W, 3), np.float32)
    for key_, amt, col in (("led_r", 1.0 if pump(f) else 0.0, (255, 40, 30)), ("led_g", 1.0 if state(f) == "WET" else 0.0, (40, 255, 90))):
        if amt <= 0:
            continue
        cx, cy = p[key_]
        gm = np.zeros((H, W), np.float32)
        cv2.circle(gm, (int(cx), int(cy)), int(r * 0.9), amt, -1)
        glow += cv2.GaussianBlur(gm, (0, 0), r)[..., None] * np.array(col, np.float32)
    out = out + glow * 0.9
    return np.clip(out, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ overlay
def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🌱", 46), (W - 388, 46))


def panel(lay, f):
    g = plantgfx.draw_hd(f, PW, PH).convert("RGBA")
    m = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), 34, fill=255)
    sh = Image.new("RGBA", (PW + 40, PH + 40))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, PW + 20, PH + 26), 36, fill=(0, 0, 0, 160))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (PX0 - 20, PY0 - 20))
    lay.paste(g, (PX0, PY0), m)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((PX0, PY0, PX0 + PW - 1, PY0 + PH - 1), 34, outline=(GRN if state(f) == "WET" else (CYAN if pump(f) else RED)) + (255,), width=9)
    d.rounded_rectangle((PX0 + 22, PY0 - 26, PX0 + 300, PY0 + 26), 26, fill=RED + (255,), outline=WHT, width=3)
    d.ellipse((PX0 + 40, PY0 - 9, PX0 + 58, PY0 + 9), fill=WHT if (f // 6) % 2 == 0 else (255, 160, 160))
    d.text((PX0 + 180, PY0), "PLANT CAM", font=font(MONT, 32), fill=WHT, anchor="mm")


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
    show_panel = i in (1, 4)
    if i == 0:
        pulse = 1 + 0.04 * math.sin(f * 0.6)
        head(lay, d, "Ye paudha khud paani peeta hai!", 175, 74, YEL, "😱", pulse)
        head(lay, d, "ESP32 Smart Plant Watering", 275, 60, GRN, "🌱")
    elif i == 1:
        if f < PUMP_ON:
            head(lay, d, f"Mitti sookhi: {int(round(moisture(f)))}%", 200, 84, (255, 90, 90), "🥵", pop_s(local, 5))
        else:
            head(lay, d, "30% se kam = PUMP ON", 200, 82, CYAN, "💧", pop_s(f - PUMP_ON, 5))
    elif i == 2:
        if f < PUMP_OFF:
            head(lay, d, "Paani khud aa raha hai!", 200, 82, CYAN, "💦", pop_s(local, 5))
        else:
            head(lay, d, "Pump apne aap OFF", 200, 86, WHT, "✅", pop_s(f - PUMP_OFF, 5))
    elif i == 3:
        head(lay, d, "Paudha khush!", 200, 104, GRN, "🌿", pop_s(local, 5))
    elif i == 4:
        head(lay, d, "Vacation pe bhi tension nahi", 200, 72, YEL, "😎", pop_s(local, 5))
    else:
        if f < 292:
            head(lay, d, "3 din baad... phir sookha", 195, 76, WHT, "⏳", pop_s(local, 5))
        else:
            head(lay, d, "Apne ghar me chahiye?", 195, 82, YEL, "👇", pop_s(f - 292, 5))
        v = ease((local - 6) / 6)
        if v > 0:
            bw = int(820 * v)
            cx = W / 2 - 50
            d.rounded_rectangle((cx - bw / 2, 900, cx + bw / 2, 1010), 55, fill=YEL + (255,))
            if v > 0.9:
                d.text((cx, 955), "Comment \"PLANT\" = Code FREE", font=font(MONT, 42), fill=INK, anchor="mm")
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
    mus = fx.filt(mus, "lowpass", 2600) * 0.6
    fx.write_wav(os.path.join(WORK, "music.wav"), mus)
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.45)
    for s_ in SHOTS[1:]:
        P(buf, fx.whoosh(0.25, s_) * 0.6, max(0, t(s_) - 0.12), 0.35)
    P(buf, np.concatenate([beep(1800, 0.06, 0.4), np.zeros(int(0.04 * SR)), beep(2400, 0.08, 0.4)]), t(PUMP_ON - 4), 0.5)
    P(buf, b.detent_click(), t(PUMP_ON), 0.8)                          # relay click
    P(buf, b.detent_click(), t(PUMP_OFF), 0.8)
    n = int(t(PUMP_OFF - PUMP_ON) * SR)                                # pump hum
    tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 120 * tt) * 0.5 + fx.filt(fx.noise(n, 4), "bandpass", [200, 1200]) * 0.4)
    hum *= np.minimum(1, tt / 0.1) * np.minimum(1, (tt[-1] - tt) / 0.1) * 0.35
    P(buf, hum, t(PUMP_ON), 0.6)
    m_ = int(t(PUMP_OFF - FLOW_AT) * SR)                               # water pouring
    pour = fx.filt(fx.noise(m_, 9), "bandpass", [700, 5000]) * (0.6 + 0.4 * np.sin(np.arange(m_) / SR * 37))
    pour *= np.minimum(1, np.arange(m_) / SR / 0.15) * np.minimum(1, (m_ - np.arange(m_)) / SR / 0.15) * 0.35
    P(buf, pour, t(FLOW_AT), 0.6)
    P(buf, b.fanfare8()[: int(0.9 * SR)] * 0.6, t(SHOTS[3]), 0.5)
    P(buf, b.ok_beep(), t(PUMP_OFF) + 0.05, 0.4)
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
    for h0, amp in [(PUMP_ON, 0.04), (FLOW_AT, 0.03), (PUMP_OFF, 0.03)] + [(s_, 0.05) for s_ in SHOTS[1:]]:
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
