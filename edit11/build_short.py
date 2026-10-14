#!/usr/bin/env python3
"""16 s (+2.5 s outro) 'ESP32 + OLED Ultrasonic Radar' short, same house style as the OLED / robot
shorts: intruder + ALERT in the first second (red flash, shake, buzzer), callout tags on the setup,
echo-formula panel, live OLED radar, ALARM vs AREA CLEAR states, end card + Like / Share /
Subscribe outro. Original tense music, sonar pings and buzzer beeps synced to timeline.alarm().
Usage: python3 edit11/build_short.py [audio] [video]
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
from timeline import FPS, N, SHOTS, BOOT, OBJ_ANGLE, OBJ_DIST, PRESENT, SLIDE, sweep, alarm, first_alarm, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-radar-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
ALARM1 = first_alarm(0, SHOTS[1])                 # hook alert
ALARM2 = first_alarm(SHOTS[4], SHOTS[5])          # alarm shot
CLEAR = PRESENT[1][1] + SLIDE                     # cube gone again
OUTRO = 60
TOTAL = N + OUTRO
BTN_POP = (4, 10, 16)
BTN_PRESS = (24, 35, 46)


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
    lay.alpha_composite(e5.emoji("📡", 46), (W - 388, 46))


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
def sonar_ping():
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1450 * tt) * np.exp(-tt * 9) + 0.3 * np.sin(2 * np.pi * 2900 * tt) * np.exp(-tt * 14)
    return x * np.minimum(1, tt / 0.004) * 0.45


def buzz():
    """Active-buzzer style beep (like the reference's alarm), 2.4 kHz square."""
    return fx.filt(beep(2400, 0.09, square=True), "lowpass", 6000)


def servo_hum(total):
    n = int(total * SR)
    tt = np.arange(n) / SR
    fr = np.clip(tt * FPS, 0, N - 1)
    ang = np.interp(fr, np.arange(N), [sweep(f) for f in range(N)])
    spd = np.abs(np.gradient(ang)) * SR / FPS
    spd = np.minimum(spd / 6.0, 1.0)
    x = fx.signal.sawtooth(2 * np.pi * np.cumsum(160 + 60 * spd) / SR)
    x = fx.filt(x, "bandpass", [150, 2200]) + 0.2 * fx.filt(fx.noise(n, 61), "bandpass", [2000, 6000])
    return x * (0.25 + 0.75 * spd) * (tt * FPS >= BOOT) * (tt * FPS < N) * 0.06


def music(total):
    """112 BPM tense minor pulse; full drop at the first ALERT."""
    bpm, n = 112, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7], [164.8, 207.7, 246.9]]
    roots = [55.0, 43.7, 49.0, 41.2]
    kick = fx.kick() * 0.55
    drop = t(ALARM1)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        full = t0 >= drop - 0.05
        for s in range(4):
            fx.place(mel, fx.synth_note(ch[(pos + s) % 3] * 2, beat / 4 * 1.5, "square", 12, 2600), t0 + s * beat / 4,
                     0.08 if full else 0.05)
        fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.45, "saw", 6, 300), t0, 0.6 if full else 0.35)
        fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.45, "saw", 6, 300), t0 + beat / 2, 0.45 if full else 0.25)
        if full:
            fx.place(drums, kick, t0, 0.85)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.3)
        for s in range(4 if full else 2):
            fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / (4 if full else 2), 0.06 if full else 0.03)
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
    P(buf, fx.riser(0.4), 0.0, 0.3)
    for f in range(BOOT, N, 16):                                         # sonar pings
        P(buf, sonar_ping(), t(f), 0.22)
    for a, b in PRESENT:                                                 # cube slides in / out
        P(buf, fx.filt(fx.noise(int(0.35 * SR), a), "bandpass", [200, 1500]) * np.hanning(int(0.35 * SR)), t(a), 0.3)
        P(buf, fx.filt(fx.noise(int(0.35 * SR), b), "bandpass", [200, 1500]) * np.hanning(int(0.35 * SR)), t(b), 0.3)
    for f in range(N):                                                   # buzzer while alarm
        if alarm(f) and f % 6 == 0:
            P(buf, buzz(), t(f), 0.35)
    for ev in (ALARM1, ALARM2):
        P(buf, fx.boom()[: int(0.6 * SR)], t(ev), 0.55)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for s in (SHOTS[1], SHOTS[2], SHOTS[3]):
        P(buf, fx.pop(), t(s + 4), 0.25)
    P(buf, ok_beep(), t(CLEAR + 2), 0.45)
    P(buf, fx.ding(), t(CLEAR + 4), 0.4)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf + servo_hum(total)


# ================================================================== graphics
def status_chip(d, f, y0=1560):
    al = alarm(f)
    col = RED if al else GRN
    txt_ = f"OBJECT  {OBJ_DIST:.0f} cm  @ {OBJ_ANGLE:.0f}°" if al else "AREA CLEAR"
    w_ = 700 if al else 520
    d.rounded_rectangle((W / 2 - w_ / 2, y0 - 50, W / 2 + w_ / 2, y0 + 50), 50, fill=(10, 12, 18, 225), outline=col + (255,), width=5)
    if not al or (f // 4) % 2 == 0:
        d.ellipse((W / 2 - w_ / 2 + 30, y0 - 15, W / 2 - w_ / 2 + 60, y0 + 15), fill=col)
    d.text((W / 2 + 20, y0), txt_, font=font(MONO if al else MONT, 44), fill=WHT, anchor="mm")


def echo_panel(d, f, y0=1330):
    """Ping -> echo diagram + the distance formula."""
    d.rounded_rectangle((60, y0, W - 60, y0 + 330), 30, fill=(8, 12, 18, 210), outline=(60, 220, 255, 180), width=3)
    d.text((W / 2, y0 + 45), "Ping  →  Echo  →  Distance", font=font(BOLD, 40), fill=WHT, anchor="mm")
    x0, x1, yc = 120, W - 260, y0 + 140
    d.rectangle((x1, yc - 45, x1 + 70, yc + 45), fill=ORG)                 # object
    ph = (f % 24) / 24
    for k_ in range(3):                                                   # outgoing + returning arcs
        u = (ph + k_ / 3) % 1
        if u < 0.5:
            x = x0 + (x1 - x0) * u * 2
            col = CYAN
        else:
            x = x1 - (x1 - x0) * (u - 0.5) * 2
            col = YEL
        d.arc((x - 30, yc - 40, x + 30, yc + 40), 300 if col == CYAN else 120, 60 if col == CYAN else 240, fill=col, width=6)
    d.rounded_rectangle((x0 - 70, yc - 40, x0 - 10, yc + 40), 10, fill=(40, 90, 200))
    d.text((W / 2, y0 + 265), "Distance = time × 343 m/s ÷ 2", font=font(MONO, 40), fill=YEL, anchor="mm")


# ================================================================== overlay
TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "esp": ((380, 725), (230, 540), "ESP32", "DevKit V1"),
    "oled": ((575, 735), (600, 450), "OLED", "Radar screen"),
    "radar": ((830, 740), (880, 610), "HC-SR04", "on SG90 servo"),
    "led": ((260, 985), (330, 1250), "LED + Buzzer", "Alarm"),
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
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Kuch aaya...?", 76 * s, WHT, stroke=8)
        if f >= ALARM1:
            tw0 = d.textlength("Kuch aaya...?", font=font(MONT, 76))
            lay.alpha_composite(e5.emoji("👀", 80), (int(W / 2 + tw0 / 2 + 12), 210))
            s2 = pop_s(f - ALARM1, 6)
            txt(d, (W / 2, 385), "ALERT!", 140 * s2, RED, stroke=12)
            if s2 > 0.9:
                tw = d.textlength("ALERT!", font=font(MONT, 140))
                lay.alpha_composite(e5.emoji("🚨", 110), (int(W / 2 + tw / 2 + 10), 325))
        v = ease((local - 30) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 330, 1620, W / 2 + 330, 1720), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1670), "ESP32 + OLED Radar", font=font(MONT, 46), fill=INK, anchor="mm")
    elif i == 1:
        label(lay, d, "ESP32 Radar", None, local, y=300, em="📡")
        for j, key in enumerate(("esp", "oled", "radar", "led")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 6) / 10))
    elif i == 2:
        label(lay, d, "HC-SR04 = Aankh", "Sound bhej ke distance naapta hai", local, y=300, em="👁️")
        echo_panel(d, f)
    elif i == 3:
        label(lay, d, "OLED pe live radar", "Servo 15° se 165° tak ghoomta hai", local, y=300, em="🛰️")
        status_chip(d, f)
    elif i == 4:
        if f < ALARM2:
            label(lay, d, "Intruder aa raha hai...", None, local, y=300, em="😈")
        else:
            s = pop_s(f - ALARM2, 6)
            txt(d, (W / 2, 300), "ALARM!", 150 * s, RED, stroke=12)
            if s > 0.9:
                tw = d.textlength("ALARM!", font=font(MONT, 150))
                lay.alpha_composite(e5.emoji("🚨", 110), (int(W / 2 + tw / 2 + 10), 245))
        status_chip(d, f)
    elif i == 5:
        if f >= CLEAR:
            s = pop_s(f - CLEAR, 7)
            txt(d, (W / 2, 300), "Hata do... sab normal", 74 * s, GRN, stroke=8)
            if s > 0.9:
                lay.alpha_composite(e5.emoji("✅", 90), (W // 2 - 45, 360))
        status_chip(d, f)
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
                d.text((W / 2, 1615), "Comment \"RADAR\" — bhej dunga", font=font(MONT, 46), fill=INK, anchor="mm")
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
        for ev in (ALARM1, ALARM2):
            a = f - ev
            if 0 <= a < 12:
                z += 0.05 * (1 - a / 12) ** 2
                dx = 20 * np.sin(a * 2.5) * (1 - a / 12)
        a = f - CLEAR
        if 0 <= a < 6:
            z += 0.03 * (1 - a / 6)
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        if alarm(f):                                              # pulsing red alarm edges
            k_ = 0.22 + 0.18 * (np.sin(f * 0.8) * 0.5 + 0.5)
            x = x * (1 - k_ * vig) + np.array(RED, np.float32) * k_ * vig
        a = f - CLEAR
        if 0 <= a < 6:
            x += (np.array(GRN, np.float32) * 0.6 + 100 - x) * 0.28 * (1 - a / 6)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = 1 - abs(dd + 0.5) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / TOTAL)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p] = RED if alarm(f) else GRN
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
