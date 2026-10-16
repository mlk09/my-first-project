#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED Rotary Encoder LED Flow' short, same house style as the
robot-eyes / parking shorts: knob turn + rainbow LED flow in the hook, callout tags, encoder close-up
with a live CLK/DT pulse panel, clockwise vs counter-clockwise flow with a rotation arrow drawn on the
knob, press = BREATHE mode, end card + Like / Share / Subscribe outro. Every detent clicks (like a
real KY-040), plus a pitched pluck per LED step.
Usage: python3 edit14/build_short.py [audio] [video]
"""
import importlib.util
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402
from timeline import FPS, N, SHOTS, NLED, PRESS, knob, step, direction, mode, leds, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-rotary-encoder-SHORT.mp4")
KNOB_XY = json.load(open(os.path.join(WORK, "knob_xy.json")))
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
RAINBOW = [(255, 40, 40), (255, 120, 20), (255, 210, 20), (80, 240, 60), (30, 230, 190), (40, 120, 255), (130, 60, 255), (255, 60, 170)]
OUTRO = 60
TOTAL = N + OUTRO
BTN_POP = (4, 10, 16)
BTN_PRESS = (24, 35, 46)


def t(f):
    return f / FPS


def font(p, s):
    return ImageFont.truetype(p, max(8, int(s)))


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


def beep(freq, dur, square=False):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * tt)) * 0.5 if square else np.sin(2 * np.pi * freq * tt)
    return x * np.minimum(1, tt / 0.003) * np.minimum(1, (dur - tt) / 0.01) * 0.6


def ok_beep():
    return np.concatenate([beep(2700, 0.09), np.zeros(int(0.04 * SR)), beep(3600, 0.16)])


def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    return _grade(im)


def _grade(im):
    """BGR render -> graded 1080x1920 RGB (sharpen + saturated-highlight bloom)."""
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    im = cv2.addWeighted(im, 1.25, cv2.GaussianBlur(im, (0, 0), 1.6), -0.25, 0)
    x = im.astype(np.float32) / 255
    sat = x.max(2, keepdims=True) - x.min(2, keepdims=True)
    bright = x * np.clip((x.max(2, keepdims=True) - 0.7) / 0.3, 0, 1) * np.clip(sat / 0.35, 0, 1)
    sm = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    x += cv2.resize(cv2.GaussianBlur(sm, (0, 0), 7), (W, H)) * 0.5
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def txt(d, xy, s, size, fill, f=MONT, stroke=None, anchor="mm"):
    d.text(xy, s, font=font(f, size), fill=fill, anchor=anchor,
           stroke_width=stroke if stroke is not None else max(4, int(size) // 10), stroke_fill=(0, 0, 0))


def pop_s(age, dur=8):
    if age < 0:
        return 0
    u = min(1, age / dur)
    return ease(u) * (1 + 0.25 * np.sin(np.pi * min(1, age / (dur * 0.8))))


def corner_frame(d, box, u, col=CYAN, w=8, L=110):
    x0, y0, x1, y1 = box
    ln = L * ease(u)
    if ln < 2:
        return
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((cx, cy, cx + sx * ln, cy), fill=col, width=w)
        d.line((cx, cy, cx, cy + sy * ln), fill=col, width=w)


def label(lay, d, text, sub, local, y=1530, em=None, col=WHT):
    s = pop_s(local - 2)
    if s <= 0:
        return
    txt(d, (W / 2, y), text, 86 * s, col, stroke=8)
    v = ease((local - 9) / 6)
    if v > 0 and sub:
        tw = d.textlength(sub, font=font(BOLD, 46)) + 60
        d.rounded_rectangle((W / 2 - tw / 2, y + 62, W / 2 + tw / 2, y + 132), 35, fill=(0, 0, 0, int(170 * v)))
        d.text((W / 2, y + 97), sub, font=font(BOLD, 46), fill=(235, 240, 255, int(255 * v)), anchor="mm")
    if em and s > 0.9:
        tw = d.textlength(text, font=font(MONT, 86))
        lay.alpha_composite(e5.emoji(em, 92), (int(W / 2 + tw / 2 + 14), int(y - 52)))


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🎛️", 46), (W - 388, 46))


def zoom(fr, z, cx=W / 2, cy=H / 2, dx=0.0):
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    M[0, 2] += dx
    return cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


def tag(lay, d, anchor, box_c, text, sub, u, col=CYAN):
    """Callout tag: dot on the part, leader line, rounded label that grows in."""
    if u <= 0:
        return
    ax, ay = anchor
    bx, by = box_c
    d.ellipse((ax - 12, ay - 12, ax + 12, ay + 12), fill=col, outline=WHT, width=3)
    ex = ax + (bx - ax) * min(1, u * 1.6)
    ey = ay + (by - ay) * min(1, u * 1.6)
    d.line((ax, ay, ex, ey), fill=WHT, width=5)
    v = ease((u - 0.5) * 2)
    if v <= 0:
        return
    tw = max(d.textlength(text, font=font(MONT, 48)), d.textlength(sub, font=font(BOLD, 32)) if sub else 0) + 60
    w_, h_ = tw * v, (120 if sub else 80) * v
    d.rounded_rectangle((bx - w_ / 2, by - h_ / 2, bx + w_ / 2, by + h_ / 2), 24, fill=col + (240,))
    if v > 0.9:
        d.text((bx, by - (20 if sub else 0)), text, font=font(MONT, 48), fill=INK, anchor="mm")
        if sub:
            d.text((bx, by + 30), sub, font=font(BOLD, 32), fill=INK, anchor="mm")


_OUTRO_BG = None


def outro(a):
    """Like / Share / Subscribe end card: buttons pop in, a finger presses each one in turn."""
    global _OUTRO_BG
    if _OUTRO_BG is None:
        bg = cv2.GaussianBlur(load3d(N - 1), (0, 0), 28).astype(np.float32) * 0.38
        _OUTRO_BG = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
    im = _OUTRO_BG.copy()
    d = ImageDraw.Draw(im)
    s = pop_s(a, 6)
    txt(d, (W / 2, 330), "Project pasand aaya?", 76 * s, WHT, stroke=8)
    if s > 0.9:
        im.alpha_composite(e5.emoji("😍", 110), (W // 2 - 55, 410))
    btns = [("LIKE", "👍", (255, 255, 255), (40, 120, 255)),
            ("SHARE", "↗", (255, 255, 255), (40, 200, 110)),
            ("SUBSCRIBE", "🔔", (230, 30, 40), (90, 90, 96))]
    for i, (name, ic, col, pressed_col) in enumerate(btns):
        u = pop_s(a - BTN_POP[i], 6)
        if u <= 0:
            continue
        pressed = a >= BTN_PRESS[i]
        bump = 1 + 0.08 * max(0, 1 - (a - BTN_PRESS[i]) / 5) if pressed else 1
        w_, h_ = 640 * u * bump, 150 * u * bump
        cy = 760 + i * 230
        fill = pressed_col if pressed else col
        d.rounded_rectangle((W / 2 - w_ / 2 + 6, cy - h_ / 2 + 10, W / 2 + w_ / 2 + 6, cy + h_ / 2 + 10), 75, fill=(0, 0, 0, 120))
        d.rounded_rectangle((W / 2 - w_ / 2, cy - h_ / 2, W / 2 + w_ / 2, cy + h_ / 2), 75, fill=fill)
        if u < 0.9:
            continue
        label_ = "SUBSCRIBED" if (pressed and i == 2) else ("LIKED" if (pressed and i == 0) else name)
        tcol = WHT if (pressed or i == 2) else INK
        d.text((W / 2 + 40, cy), label_, font=font(MONT, 62), fill=tcol, anchor="mm")
        tw = d.textlength(label_, font=font(MONT, 62))
        ix = int(W / 2 + 40 - tw / 2 - 110)
        if ic == "↗":
            d.text((ix + 45, cy), "↗", font=font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80),
                   fill=tcol, anchor="mm")
        else:
            ang = 18 * np.sin((a - BTN_PRESS[2]) * 1.3) * max(0, 1 - (a - BTN_PRESS[2]) / 14) if (i == 2 and pressed) else 0
            im.alpha_composite(e5.emoji(ic, 86).rotate(ang, expand=False, resample=Image.BICUBIC), (ix, int(cy - 43)))
    # finger travelling to each button and pressing
    if a >= BTN_POP[2] + 4:
        tgt = [(W / 2 + 200, 760 + i * 230 + 40) for i in range(3)]
        seg = 0 if a < BTN_PRESS[0] else 1 if a < BTN_PRESS[1] else 2
        prev = (W / 2 + 330, 1550) if seg == 0 else tgt[seg - 1]
        start = BTN_POP[2] + 4 if seg == 0 else BTN_PRESS[seg - 1] + 2
        u = ease((a - start) / max(1, BTN_PRESS[seg] - 2 - start))
        x = prev[0] + (tgt[seg][0] - prev[0]) * u
        y = prev[1] + (tgt[seg][1] - prev[1]) * u
        press = max(0, 1 - abs(a - BTN_PRESS[seg]) / 3)
        sz = int(130 * (1 - 0.15 * press))
        im.alpha_composite(e5.emoji("👆", sz), (int(x - sz * 0.35), int(y)))
    v = ease((a - BTN_PRESS[2] - 4) / 6)
    if v > 0:
        txt(d, (W / 2, 1530), "@The IOT Engineer", 64 * (0.8 + 0.2 * v), YEL, stroke=6)
        d.text((W / 2, 1620), "Aise aur ESP32 / IoT projects ke liye", font=font(BOLD, 46), fill=(235, 240, 255), anchor="mm")
    badge(im, d)
    return np.array(im.convert("RGB"))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== audio
def detent_click():
    n = int(0.025 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 91), "bandpass", [2500, 9000]) * np.exp(-tt * 260)
    return x + np.sin(2 * np.pi * 3200 * tt) * np.exp(-tt * 300) * 0.4


def pluck(freq):
    return fx.synth_note(freq, 0.35, "tri", 12, 5000) * 0.5


SCALE = [523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5]   # C major pentatonic-ish, one per LED


def music(total):
    """112 BPM bright pluck groove; drop on the first knob turn; softer pad in BREATHE mode."""
    bpm, n = 112, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[261.6, 329.6, 392.0], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7]]
    roots = [65.4, 55.0, 43.7, 49.0]
    kick = fx.kick() * 0.5
    drop = t(6)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        for s in range(2):
            fx.place(mel, fx.synth_note(ch[(pos + s) % 3] * 2, beat / 2 * 1.6, "tri", 8, 3500), t0 + s * beat / 2, 0.11)
        if t0 >= drop:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 240), t0, 0.6)
            if pos in (0, 2):
                fx.place(drums, kick, t0, 0.75)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.25)
            for s in range(2):
                fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / 2, 0.05)
        b += 1
    mix = mel + bass + drums
    i = int(drop * SR)
    mix[:i] = fx.filt(mix[:i], "lowpass", 900)
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.3), 0.0, 0.3)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for s in (SHOTS[1], SHOTS[2], SHOTS[5]):
        P(buf, fx.pop(), t(s + 4), 0.25)
    for f in range(1, N):                                     # detent clicks + LED plucks
        if step(f) != step(f - 1):
            P(buf, detent_click(), t(f), 0.55)
            if mode(f) == "FLOW":
                P(buf, pluck(SCALE[step(f) % NLED]), t(f), 0.22)
    P(buf, fx.pop(), t(PRESS), 0.5)                           # push switch
    P(buf, detent_click() * 1.4, t(PRESS), 0.6)
    P(buf, fx.riser(0.6)[::-1], t(PRESS + 1), 0.35)
    P(buf, fx.ding(), t(PRESS + 4), 0.4)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
def rot_arrow(lay, f, r=150):
    """Glowing circular arrow around the knob showing the turn direction."""
    dr = direction(f)
    x, y = KNOB_XY[min(f, N - 1)]
    if dr == 0 or not (-200 < x < W + 200 and -200 < y < H + 200):
        return
    col = CYAN if dr > 0 else ORG
    ov = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(ov)
    ph = (knob(f) * 1.0) % 360
    a0, a1 = ph - 120, ph + 120
    d.arc((x - r, y - r * 0.55, x + r, y + r * 0.55), a0, a1, fill=col + (255,), width=12)
    tip = math.radians(a1 if dr > 0 else a0)
    tx, ty = x + r * math.cos(tip), y + r * 0.55 * math.sin(tip)
    tang = tip + (math.pi / 2 if dr > 0 else -math.pi / 2)
    p1 = (tx + 34 * math.cos(tang), ty + 34 * 0.55 * math.sin(tang))
    nrm = tip
    p2 = (tx + 22 * math.cos(nrm), ty + 22 * math.sin(nrm))
    p3 = (tx - 22 * math.cos(nrm), ty - 22 * math.sin(nrm))
    d.polygon([p1, p2, p3], fill=col + (255,))
    glow = ov.filter(ImageFilter.GaussianBlur(10))
    lay.alpha_composite(glow)
    lay.alpha_composite(ov)


def pulse_panel(d, f, y0=1330):
    """KY-040 quadrature: CLK and DT square waves, 90 deg apart; which one leads = direction."""
    d.rounded_rectangle((60, y0, W - 60, y0 + 330), 30, fill=(8, 12, 18, 210), outline=(60, 220, 255, 180), width=3)
    dr = direction(f)
    lead = "CLK pehle = Clockwise" if dr >= 0 else "DT pehle = Counter-CW"
    d.text((W / 2, y0 + 40), lead, font=font(BOLD, 38), fill=WHT, anchor="mm")
    x0, x1 = 220, W - 100
    ph = knob(f) / 18.0 * 80
    for name, col, yc, off in (("CLK", YEL, y0 + 140, 0), ("DT", CYAN, y0 + 255, 20 if dr >= 0 else -20)):
        d.text((130, yc), name, font=font(MONT, 40), fill=col, anchor="mm")
        pts = []
        for x in range(x0, x1, 4):
            v = 1 if ((x - x0 + ph + off) % 80) < 40 else 0
            pts.append((x, yc + 30 - v * 60))
        d.line(pts, fill=col, width=6)


def led_row(d, f, y0=1560):
    """On-screen mirror of the 8 LEDs, rainbow, with the step counter."""
    lv = leds(f)
    w_ = 840
    d.rounded_rectangle((W / 2 - w_ / 2, y0 - 55, W / 2 + w_ / 2, y0 + 55), 55, fill=(10, 12, 18, 225), outline=(255, 255, 255, 120), width=3)
    for i in range(NLED):
        x = W / 2 - w_ / 2 + 70 + i * 70
        c = RAINBOW[i]
        v = lv[i]
        d.ellipse((x - 24, y0 - 24, x + 24, y0 + 24), fill=tuple(int(20 + (cc - 20) * max(v, 0.08)) for cc in c) + (255,))
    d.text((W / 2 + w_ / 2 - 80, y0), f"{step(f):+d}", font=font(MONO, 40), fill=WHT, anchor="mm")


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "esp": ((330, 690), (230, 470), "ESP32", "DevKit V1"),
    "oled": ((800, 690), (830, 470), "OLED", "Step + direction"),
    "knob": ((230, 1219), (230, 1500), "Rotary Encoder", "KY-040"),
    "led": ((700, 1200), (820, 1500), "8 LEDs", "Rainbow flow"),
}


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i < 6:
        g = Image.new("L", (1, H))
        g.putdata([int(140 * max(0, 1 - y_ / 560)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    if i in (0, 3, 4):
        rot_arrow(lay, f)
        d = ImageDraw.Draw(lay)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Knob ghumao...", 76 * s, WHT, stroke=8)
        s2 = pop_s(local - 14, 6)
        if s2 > 0:
            txt(d, (W / 2, 380), "LED BEHNE LAGI!", 100 * s2, YEL, stroke=10)
            if s2 > 0.9:
                lay.alpha_composite(e5.emoji("🌈", 96), (W // 2 - 48, 450))
        led_row(d, f)
        v = ease((local - 36) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 360, 1670, W / 2 + 360, 1770), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1720), "ESP32 + Rotary Encoder", font=font(MONT, 44), fill=INK, anchor="mm")
    elif i == 1:
        label(lay, d, "LED Flow Setup", None, local, y=300, em="🎛️")
        for j, key in enumerate(("esp", "oled", "knob", "led")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 7) / 10))
    elif i == 2:
        label(lay, d, "Rotary Encoder", "Har click = 1 step (20 per round)", local, y=300, em="🔄")
        pulse_panel(d, f)
    elif i == 3:
        label(lay, d, "Clockwise", "LEDs right ki taraf behti hain", local, y=300, em="➡️")
        led_row(d, f)
    elif i == 4:
        label(lay, d, "Ulta ghumao", "LEDs left ki taraf wapas", local, y=300, em="⬅️")
        led_row(d, f)
    elif i == 5:
        if f < PRESS + 2:
            label(lay, d, "Knob dabao...", None, local, y=300, em="👇")
        else:
            s = pop_s(f - PRESS - 2, 6)
            txt(d, (W / 2, 300), "BREATHE MODE!", 104 * s, (180, 140, 255), stroke=10)
            if s > 0.9:
                lay.alpha_composite(e5.emoji("✨", 90), (W // 2 - 45, 370))
        led_row(d, f)
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y_ / 700)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Circuit FREE", 78 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130)
        v = ease((local - 10) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"KNOB\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 18) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1780), "Follow @The IOT Engineer", 54, WHT, stroke=5)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2).clip(0, 1)[..., None].astype(np.float32)
    for f in range(TOTAL):
        if f >= N:
            fr = outro(f - N)
            if f - N < 4:
                k_ = 1 - (f - N) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 20 * k_), 1 + 0.06 * k_)
            fr[0:10, :] = CYAN
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z = 1.0
        if step(f) != step(f - 1):
            z += 0.008                                         # tiny tick-punch on every detent
        a = f - PRESS
        if 0 <= a < 8:
            z += 0.05 * (1 - a / 8) ** 2
        if z > 1.0:
            fr = zoom(fr, z)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        lv = leds(f)                                           # edge glow in the colour of the lead LED
        if max(lv) > 0.3:
            if mode(f) == "BREATHE":
                c = np.array(RAINBOW[(f // 6) % NLED], np.float32)
            else:
                c = np.array(RAINBOW[int(np.argmax(lv))], np.float32)
            k_ = 0.16 * max(lv)
            x = x * (1 - k_ * vig) + c * k_ * vig
        a = f - PRESS - 2
        if 0 <= a < 6:
            x += (np.array((180, 140, 255), np.float32) * 0.6 + 100 - x) * 0.28 * (1 - a / 6)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / TOTAL)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        for j in range(NLED):
            fr[0:10, j * W // NLED: min(p, (j + 1) * W // NLED)] = RAINBOW[j]
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 48 == 0:
            print(f"  frame {f}/{TOTAL}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["audio", "video"]
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
