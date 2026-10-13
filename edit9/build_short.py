#!/usr/bin/env python3
"""16 s (+2.5 s outro) 'ESP32 Self-Balancing Robot' short, in the Tap-to-Light / door-lock style:
PID OFF fall in the first second (thud + shake), PID ON status chip, live tilt gauge + graph driven
by timeline.theta(), ball-push 'PHIR BHI KHADA' payoff, P/I/D bars, drive shot, blur-zoom cuts,
progress bar, end card and the Like / Share / Subscribe outro. Original music (filtered until PID
turns on, then the drop) + motor whine that follows wheel speed.
Usage: python3 edit9/build_short.py [audio] [video]
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
from timeline import FPS, N, SHOTS, FALL, PID_ON, PUSH, DRIVE, theta, y, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-self-balancing-robot-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
OUTRO = 60                        # Like / Share / Subscribe card after the story (2.5 s)
TOTAL = N + OUTRO
BTN_POP = (4, 10, 16)             # outro-local frames: buttons pop in
BTN_PRESS = (24, 35, 46)          # finger presses LIKE, SHARE, SUBSCRIBE


def font(p, s):
    return ImageFont.truetype(p, max(8, int(s)))


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


def t(f):
    return f / FPS


def beep(freq, dur, square=False):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * tt)) * 0.5 if square else np.sin(2 * np.pi * freq * tt)
    return x * np.minimum(1, tt / 0.003) * np.minimum(1, (dur - tt) / 0.01) * 0.6


def ok_beep():
    return np.concatenate([beep(2700, 0.09), np.zeros(int(0.04 * SR)), beep(3600, 0.16)])


def clack():
    n = int(0.18 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 21), "bandpass", [800, 6000]) * np.exp(-tt * 60)
    x += sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) * a for f, a, d in ((1850, 0.5, 30), (3100, 0.3, 40), (520, 0.6, 25)))
    return np.tanh(1.4 * x)


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
    lay.alpha_composite(e5.emoji("🤖", 46), (W - 388, 46))


def zoom(fr, z, cx=W / 2, cy=H / 2, dx=0.0):
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    M[0, 2] += dx
    return cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


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


# ================================================================== audio
def wheel_speed(f):
    """cm per frame (abs), for the motor whine."""
    return abs(y(min(f + 1, N - 1)) - y(max(f - 1, 0))) / 2


def motor_whine(total):
    n = int(total * SR)
    tt = np.arange(n) / SR
    fr = np.clip(tt * FPS, 0, N - 1)
    sp = np.interp(fr, np.arange(N), [wheel_speed(f) if f >= PID_ON else 0.0 for f in range(N)])
    sp = np.minimum(sp / 0.9, 1.0)
    freq = 140 + 900 * sp
    x = fx.signal.sawtooth(2 * np.pi * np.cumsum(freq) / SR) * 0.5 + np.sin(2 * np.pi * np.cumsum(freq * 2.01) / SR) * 0.3
    x = fx.filt(x, "bandpass", [120, 3500]) + 0.25 * fx.filt(fx.noise(n, 31), "bandpass", [2500, 7000])
    return x * (0.08 + sp) * (tt * FPS >= PID_ON) * 0.35


def thud():
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(70 + 80 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 9)
    x += fx.filt(fx.noise(n, 41), "lowpass", 2500) * np.exp(-tt * 30) * 0.8
    x += sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) * a for f, a, d in ((420, 0.3, 30), (1300, 0.15, 45)))
    return np.tanh(1.6 * x)


def boot_chime():
    return np.concatenate([beep(1320, 0.08), beep(1760, 0.08), beep(2640, 0.2)])


def music(total):
    """118 BPM pluck groove; the drums arrive (the drop) when PID turns on."""
    bpm, n = 118, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6],
              [196.0, 246.9, 293.7, 392.0], [164.8, 207.7, 246.9, 329.6]]
    roots = [55.0, 43.7, 49.0, 41.2]
    kick = fx.kick() * 0.55
    drop = t(PID_ON)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        full = t0 >= drop - 0.05
        for s in range(2):
            fx.place(mel, fx.synth_note(ch[(pos * 2 + s) % 4] * 2, beat / 2 * 1.6, "tri", 8, 3500), t0 + s * beat / 2, 0.16)
        if full:
            fx.place(mel, fx.synth_note(ch[0] * 2, beat * 0.4, "saw", 9, 2600), t0 + beat / 2, 0.12)
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 240), t0, 0.7)
            fx.place(drums, kick, t0, 0.85)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.32)
        for s in range(4 if full else 2):
            fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / (4 if full else 2), 0.06 if full else 0.03)
        b += 1
    mix = mel + bass + drums
    i = int(drop * SR)
    mix[:i] = fx.filt(mix[:i], "lowpass", 900)                   # muffled until PID turns on
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.4), 0.0, 0.35)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for s in (SHOTS[2], SHOTS[4], SHOTS[5]):
        P(buf, fx.pop(), t(s + 4), 0.25)
    P(buf, thud(), t(FALL[1]), 0.9)                                   # PID OFF: it falls
    P(buf, clack() * 0.5, t(FALL[1] + 3), 0.4)
    P(buf, boot_chime(), t(PID_ON), 0.5)                              # PID ON
    P(buf, fx.boom()[: int(0.5 * SR)], t(PID_ON), 0.45)
    P(buf, fx.filt(fx.noise(int(0.5 * SR), 51), "lowpass", 600) * np.linspace(0, 1, int(0.5 * SR)), t(PUSH) - 0.5, 0.25)
    P(buf, thud() * 0.6, t(PUSH), 0.55)                               # ball hit
    P(buf, fx.ding(), t(PUSH + 12), 0.4)
    P(buf, fx.whoosh(0.8, 63), t(DRIVE[0]), 0.35)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)                # outro
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf + motor_whine(total)


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


# ================================================================== HUD
def status_chip(d, f, y0=200):
    on = f >= PID_ON
    s = pop_s(f - PID_ON, 6) if on else 1
    col = GRN if on else RED
    txt_ = "PID: ON" if on else "PID: OFF"
    w_ = (360 + 40 * (1 - min(s, 1))) * max(s, 0.3)
    d.rounded_rectangle((W / 2 - w_ / 2, y0 - 42, W / 2 + w_ / 2, y0 + 42), 42, fill=(10, 12, 18, 220), outline=col + (255,), width=5)
    blink = (f // 6) % 2 == 0 or on
    d.ellipse((W / 2 - w_ / 2 + 28, y0 - 14, W / 2 - w_ / 2 + 56, y0 + 14), fill=col if blink else (60, 60, 60))
    d.text((W / 2 + 22, y0), txt_, font=font(MONT, 46), fill=WHT, anchor="mm")


def tilt_hud(d, f, y0=1330):
    """Arc gauge (needle = body tilt) + live graph of the last 2 s."""
    th = theta(f)
    d.rounded_rectangle((60, y0, W - 60, y0 + 330), 30, fill=(8, 12, 18, 205), outline=(60, 220, 255, 180), width=3)
    cx, cy, r = 250, y0 + 265, 130
    d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(60, 70, 90), width=16)
    d.arc((cx - r, cy - r, cx + r, cy + r), 262, 278, fill=GRN, width=16)
    a = np.radians(270 + max(-70, min(70, th)) * 1.0)
    d.line((cx, cy, cx + r * 0.9 * np.cos(a), cy + r * 0.9 * np.sin(a)), fill=YEL, width=8)
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=YEL)
    col = GRN if abs(th) < 5 else ORG if abs(th) < 20 else RED
    d.text((cx, y0 + 40), "TILT", font=font(BOLD, 34), fill=(180, 190, 210), anchor="mm")
    d.text((cx, y0 + 88), f"{th:+.1f}°", font=font(MONO, 44), fill=col, anchor="mm")
    gx0, gx1, gy0, gy1 = 450, W - 90, y0 + 40, y0 + 300
    d.text((gx0, y0 + 22), "MPU6050 angle (live)", font=font(BOLD, 28), fill=(180, 190, 210), anchor="lm")
    mid = (gy0 + gy1) / 2 + 10
    d.line((gx0, mid, gx1, mid), fill=(70, 80, 100), width=2)
    pts = []
    for i in range(48):
        ff = f - 47 + i
        if ff < 0:
            continue
        v = max(-30, min(30, theta(ff)))
        pts.append((gx0 + (gx1 - gx0) * i / 47, mid - v / 30 * (gy1 - gy0) / 2))
    if len(pts) > 1:
        d.line(pts, fill=CYAN, width=5, joint="curve")


def pid_bars(d, f, y0=1330):
    th = theta(f)
    dth = theta(min(f + 1, N - 1)) - theta(max(f - 1, 0))
    integ = sum(theta(max(f - i, 0)) for i in range(24)) / 24
    vals = [("P", th * 4.0, (255, 120, 60)), ("I", integ * 10, (60, 220, 255)), ("D", dth * 12, (200, 120, 255))]
    d.rounded_rectangle((60, y0, W - 60, y0 + 330), 30, fill=(8, 12, 18, 205), outline=(60, 220, 255, 180), width=3)
    d.text((W / 2, y0 + 40), "PID = P + I + D", font=font(MONT, 46), fill=WHT, anchor="mm")
    for i, (name, v, col) in enumerate(vals):
        yy = y0 + 110 + i * 72
        d.text((110, yy), name, font=font(MONT, 50), fill=col, anchor="mm")
        d.rounded_rectangle((170, yy - 18, W - 110, yy + 18), 18, fill=(40, 46, 60))
        c = (170 + W - 110) / 2
        L = max(-1, min(1, v / 40)) * (W - 280) / 2
        d.rounded_rectangle((min(c, c + L), yy - 18, max(c, c + L) + 1, yy + 18), 18, fill=col)
        d.line((c, yy - 26, c, yy + 26), fill=WHT, width=3)


# ================================================================== overlay
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
    if i == 0:
        status_chip(d, f)
        s = pop_s(local, 6)
        txt(d, (W / 2, 330), "Bina PID...", 76 * s, WHT, stroke=8)
        s2 = pop_s(f - FALL[1], 6)
        if s2 > 0:
            txt(d, (W / 2, 450), "DHADAM!", 120 * s2, RED, stroke=11)
            if s2 > 0.9:
                tw = d.textlength("DHADAM!", font=font(MONT, 120))
                lay.alpha_composite(e5.emoji("💥", 110), (int(W / 2 + tw / 2 + 10), 390))
        v = ease((local - 30) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 360, 1620, W / 2 + 360, 1720), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1670), "ESP32 Self-Balancing Robot", font=font(MONT, 44), fill=INK, anchor="mm")
    elif i == 1:
        status_chip(d, f)
        s = pop_s(f - PID_ON - 4, 7)
        if s > 0:
            txt(d, (W / 2, 330), "Ab dekho...", 84 * s, YEL, stroke=8)
            if s > 0.9:
                lay.alpha_composite(e5.emoji("😎", 96), (W // 2 + 240, 280))
        tilt_hud(d, f)
    elif i == 2:
        corner_frame(d, (110, 420, 970, 1360), (local - 2) / 8)
        label(lay, d, "ESP32-S3 + MPU6050", "Tilt sensor + dimaag", local)
    elif i == 3:
        if f < PUSH + 3:
            label(lay, d, "Dhakka test", None, local, y=300, em="🏀")
        else:
            s = pop_s(f - PUSH - 3, 7)
            txt(d, (W / 2, 300), "PHIR BHI KHADA!", 100 * s, YEL, stroke=10)
            if s > 0.9:
                lay.alpha_composite(e5.emoji("💪", 100), (W // 2 - 50, 370))
        tilt_hud(d, f)
    elif i == 4:
        label(lay, d, "PID Control", "Tilt → PID → Motor speed", local, y=300, em="⚖️")
        pid_bars(d, f)
    elif i == 5:
        label(lay, d, "Chalta bhi hai!", "Balance karte hue aage-peeche", local, y=300, em="🚀")
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
                d.text((W / 2, 1615), "Comment \"ROBOT\" — bhej dunga", font=font(MONT, 46), fill=INK, anchor="mm")
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
            fr[0:10, :] = GRN
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z, dx = 1.0, 0.0
        a = f - FALL[1]
        if 0 <= a < 12:                                           # fall impact: shake + punch
            z += 0.05 * (1 - a / 12) ** 2
            dx = 22 * np.sin(a * 2.4) * (1 - a / 12)
        a = f - PUSH
        if 0 <= a < 8:
            z += 0.045 * (1 - a / 8) ** 2
            dx = 12 * np.sin(a * 2.6) * (1 - a / 8)
        a = f - PID_ON
        if 0 <= a < 6:
            z += 0.03 * (1 - a / 6)
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        a = f - FALL[1]
        if 0 <= a < 16:                                           # red impact tint
            k_ = 0.4 * (1 - a / 16)
            x = x * (1 - k_ * vig) + np.array(RED, np.float32) * k_ * vig
        a = f - PID_ON
        if 0 <= a < 6:                                            # green PID-on flash
            x += (np.array(GRN, np.float32) * 0.6 + 100 - x) * 0.28 * (1 - a / 6)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = 1 - abs(dd + 0.5) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / TOTAL)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p] = GRN if f >= PID_ON else RED
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
