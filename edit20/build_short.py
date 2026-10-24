#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED + PIR motion alarm (chor pakdo)' short, same house style
as the rotary-encoder short: a toy chor walks into the PIR zone in the hook (CHOR PAKDA!), callout
tags, PIR close-up (body heat = IR), knob arms the system with a 3-2-1 countdown, the chor sneaks in
again -> MOTION DETECTED, siren + red LED, he runs away -> ALL CLEAR; live security HUD, rainbow
edge glow + progress bar like the LED Flow short, end card + Like / Share / Subscribe outro.
Usage: python3 edit20/build_short.py [audio] [video]
"""
import importlib.util
import math
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
from timeline import FPS, N, SHOTS, ARM_CLICK, ARM_AT, thief, in_zone, armed, alarm, detecting, countdown, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-pir-motion-alarm-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
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


def detent_click():
    n = int(0.025 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 91), "bandpass", [2500, 9000]) * np.exp(-tt * 260)
    return x + np.sin(2 * np.pi * 3200 * tt) * np.exp(-tt * 300) * 0.4


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
    lay.alpha_composite(e5.emoji("🚨", 46), (W - 388, 46))


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
SW = [f for f in range(1, N) if alarm(f) != alarm(f - 1)]      # alarm on / off frames
ON1, OFF1, ON2, OFF2 = SW[:4]
RAINBOW = [(255, 40, 40), (255, 120, 20), (255, 210, 20), (80, 240, 60), (30, 230, 190), (40, 120, 255),
           (130, 60, 255), (255, 60, 170)]             # same palette as the rotary-encoder LED Flow short
BLU = (70, 150, 255)


def siren(dur):
    """Two-tone wailing siren (square), the classic alarm sound."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    fr = 950 + 450 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 2.2 * tt)))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sign(np.sin(ph)) * 0.35 + np.sin(ph) * 0.3
    return fx.filt(x, "lowpass", 4000) * np.minimum(1, tt / 0.02) * np.minimum(1, (dur - tt) / 0.05)


def step_snd(seed, soft=False):
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, seed), "bandpass", [120, 900 if soft else 1500]) * np.exp(-tt * 60)
    return x * (0.5 if soft else 1.0)


def arm_chime():
    out = np.zeros(int(0.6 * SR))
    for i, fr in enumerate((659.3, 880.0, 1318.5)):
        fx.place(out, fx.synth_note(fr, 0.25, "tri", 9, 6000) * 0.5, i * 0.09, 1.0)
    return out


def music(total):
    """108 BPM spy / heist groove (minor, plucked bass line + tick hats); filtered until the first alarm."""
    bpm, n = 108, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    line = [110.0, 110.0, 130.8, 110.0, 146.8, 138.6, 130.8, 123.5]       # A minor spy riff
    kick = fx.kick() * 0.5
    drop = t(ON1)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        for s in range(2):
            nt = line[(b * 2 + s) % len(line)]
            fx.place(bass, fx.synth_note(nt, beat / 2 * 0.9, "saw", 6, 700), t0 + s * beat / 2, 0.45)
        if pos == 0:
            fx.place(mel, fx.synth_note(880.0 if bar % 2 else 784.0, beat * 1.5, "tri", 3, 3000), t0, 0.08)
        if t0 >= drop:
            if pos in (0, 2):
                fx.place(drums, kick, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.25)
            for s in range(4):
                fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / 4, 0.03 if s % 2 else 0.05)
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
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    P(buf, fx.pop(), t(SHOTS[1] + 4), 0.25)
    walk = 0
    for f in range(1, N):                                           # footsteps while the chor walks
        if thief(f)[2] and f % (5 if f < SHOTS[4] or f > SHOTS[5] else 7) == 0:
            P(buf, step_snd(f, soft=SHOTS[4] <= f < SHOTS[5]), t(f), 0.5)
            walk += 1
    for on, off in ((ON1, OFF1), (ON2, OFF2)):                      # MOTION -> boom + siren
        P(buf, fx.boom()[: int(0.5 * SR)], t(on), 0.45)
        P(buf, siren(min(t(off) - t(on), 3.2)), t(on), 0.32)
    P(buf, ok_beep(), t(OFF2), 0.35)
    P(buf, fx.ding(), t(OFF2 + 2), 0.35)
    P(buf, detent_click(), t(ARM_CLICK + 4), 0.7)                    # knob -> 3-2-1 -> ARMED
    for k_ in range(3):
        P(buf, beep(1000, 0.08), t(ARM_CLICK + 4 + 11 * k_), 0.3)
    P(buf, arm_chime(), t(ARM_AT), 0.45)
    for f in range(SHOTS[2], SHOTS[3], 12):                          # PIR 'scan' ticks
        P(buf, beep(2400, 0.02), t(f), 0.08)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
def glow_col(f):
    """Edge glow: red flashing while the alarm rings, else the slow rainbow drift of the LED Flow short."""
    if alarm(f):
        return np.array(RED, np.float32), (0.24 if (f // 4) % 2 == 0 else 0.12)
    u = (f / 10.0) % len(RAINBOW)
    i = int(u)
    a = np.array(RAINBOW[i], np.float32)
    b_ = np.array(RAINBOW[(i + 1) % len(RAINBOW)], np.float32)
    return a + (b_ - a) * (u - i), 0.14


def rainbow_bar(fr, p):
    fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
    n = len(RAINBOW)
    for j in range(n):
        fr[0:10, j * W // n: min(p, (j + 1) * W // n)] = RAINBOW[j]


def hud(lay, d, f, y0=1590):
    """Security HUD: system state, PIR motion indicator, alarm pill (own style)."""
    d.rounded_rectangle((60, y0 - 120, W - 60, y0 + 120), 56, fill=(10, 12, 18, 225), outline=(255, 255, 255, 140), width=3)
    on, arm = alarm(f), armed(f)
    em = "🔒" if arm else "🔓"
    lay.alpha_composite(e5.emoji(em, 76), (96, int(y0 - 92)))
    txt(d, (190, y0 - 52), "ARMED" if arm else "DISARMED", 70, GRN if arm else (190, 195, 205), stroke=7, anchor="lm")
    age = min(f - x for x in SW if x <= f) if any(x <= f for x in SW) else 99
    s = 1 + 0.25 * max(0, 1 - age / 6)
    pw, ph = 300 * s, 92 * s
    cx, cy = W - 250, y0 - 52
    d.rounded_rectangle((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), 46,
                        fill=(RED if on else (GRN if arm else (70, 74, 86))) + (255,), outline=WHT, width=4)
    d.text((cx, cy), "ALARM!" if on else ("SAFE" if arm else "OFF"), font=font(MONT, 52 * s), fill=WHT, anchor="mm",
           stroke_width=3, stroke_fill=(0, 0, 0))
    mot = detecting(f) or (in_zone(f) and not arm)
    d.ellipse((110, y0 + 32, 160, y0 + 82), fill=((255, 170, 40) if mot else (70, 74, 86)) + (255,), outline=WHT, width=3)
    d.text((180, y0 + 57), "MOTION: YES" if mot else "MOTION: NO", font=font(MONT, 40), fill=WHT, anchor="lm")
    d.text((W - 100, y0 + 57), "PIR HC-SR501", font=font(MONT, 34), fill=(170, 175, 190), anchor="rm")


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "pir": ((360, 390), (800, 360), "PIR Sensor", "HC-SR501"),
    "esp": ((320, 860), (220, 660), "ESP32", "Dimaag"),
    "oled": ((650, 860), (880, 720), "OLED", "Status"),
    "knob": ((370, 1300), (250, 1560), "Knob", "ARM / DISARM"),
    "leds": ((620, 1290), (820, 1560), "LED + Buzzer", "Siren"),
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
        txt(d, (W / 2, 210), "Chor aaya?", 84 * s, WHT, stroke=8)
        s2 = pop_s(f - ON1, 6)
        if s2 > 0:
            txt(d, (W / 2 - 50, 340), "CHOR PAKDA!", 118 * s2, RED, stroke=12)
            if s2 > 0.9:
                tw = d.textlength("CHOR PAKDA!", font=font(MONT, 118))
                lay.alpha_composite(e5.emoji("🚨", 96), (int(W / 2 - 50 + tw / 2 + 8), 290))
        hud(lay, d, f)
    elif i == 1:
        label(lay, d, "ESP32 Security Alarm", None, local, y=230, em=None)
        for j, key in enumerate(("pir", "esp", "oled", "knob", "leds")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 6) / 10))
    elif i == 2:
        label(lay, d, "PIR = Body Heat", "Insaan ki body se IR nikalti hai", local, y=280, em="🔥")
        v = ease((local - 14) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 400 * v, 1180, W / 2 + 400 * v, 1390), 40, fill=(10, 12, 18, 225), outline=(255, 140, 30, 255), width=5)
            if v > 0.9:
                d.text((W / 2, 1235), "Movement + Heat", font=font(MONT, 46), fill=ORG, anchor="mm")
                d.text((W / 2, 1320), "= OUTPUT HIGH", font=font(MONT, 56), fill=WHT, anchor="mm")
        hud(lay, d, f)
    elif i == 3:
        label(lay, d, "Knob = ARM", "Ghumao aur system ON", local, y=280, em="🎛️")
        cd = countdown(f)
        if cd:
            s = pop_s((f - ARM_CLICK - 4) % 11, 4)
            txt(d, (W / 2, 820), str(cd), 220 * s, YEL, stroke=14)
        elif f >= ARM_AT:
            s = pop_s(f - ARM_AT, 6)
            txt(d, (W / 2, 820), "ARMED!", 140 * s, GRN, stroke=12)
            if s > 0.9:
                tw = d.textlength("ARMED!", font=font(MONT, 140))
                lay.alpha_composite(e5.emoji("🔒", 110), (int(W / 2 + tw / 2 + 10), 760))
        hud(lay, d, f)
    elif i == 4:
        if not alarm(f):
            label(lay, d, "Chor dabe paon...", "Dheere dheere aa raha hai", local, y=280, em="🤫")
        else:
            s = pop_s(f - ON2, 6)
            txt(d, (W / 2, 250), "MOTION DETECTED!", 92 * s, RED, stroke=10)
            if s > 0.9:
                d.rounded_rectangle((W / 2 - 360, 330, W / 2 + 360, 420), 45, fill=(0, 0, 0, 180))
                d.text((W / 2 - 30, 375), "Siren + Red LED ON", font=font(BOLD, 50), fill=WHT, anchor="mm")
                lay.alpha_composite(e5.emoji("🔊", 70), (int(W / 2 + 270), 340))
        hud(lay, d, f)
    elif i == 5:
        if f < OFF2:
            s = pop_s(local, 6)
            txt(d, (W / 2 - 50, 250), "Chor bhaaga!", 100 * s, YEL, stroke=10)
            if s > 0.9:
                tw = d.textlength("Chor bhaaga!", font=font(MONT, 100))
                lay.alpha_composite(e5.emoji("🏃", 90), (int(W / 2 - 50 + tw / 2 + 8), 200))
            if (f - ON2) % 11 < 5:
                txt(d, (870, 1250), "WEE-WOO!", 64, RED, stroke=7)
        else:
            s = pop_s(f - OFF2, 6)
            txt(d, (W / 2 - 55, 250), "ALL CLEAR", 112 * s, GRN, stroke=11)
            if s > 0.9:
                tw = d.textlength("ALL CLEAR", font=font(MONT, 112))
                lay.alpha_composite(e5.emoji("✅", 84), (int(W / 2 - 55 + tw / 2 + 8), 208))
        hud(lay, d, f)
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y_ / 700)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        d = ImageDraw.Draw(lay)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Circuit FREE", 78 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130)
        v = ease((local - 5) / 8)
        if v > 0:
            d.rounded_rectangle((90, 380, 90 + (W - 180) * v, 560), 30, fill=(12, 16, 24, 235), outline=CYAN + (255,), width=4)
            if v > 0.9:
                d.text((130, 430), "if (armed && digitalRead(PIR))", font=font(MONO, 40), fill=(255, 190, 90), anchor="lm")
                d.text((170, 505), "siren();  // LED + buzzer", font=font(MONO, 42), fill=(150, 255, 170), anchor="lm")
        v = ease((local - 12) / 8)
        if v > 0:
            bw = int(940 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"PIR\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 20) / 8)
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
            rainbow_bar(fr, W)
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z, dx = 1.0, 0.0
        for on in (ON1, ON2):                                      # punch-in + shake on MOTION
            a = f - on
            if 0 <= a < 10:
                z += 0.05 * (1 - a / 10) ** 2
                dx = 16 * np.sin(a * 2.5) * (1 - a / 10)
        a = f - ARM_AT
        if 0 <= a < 8:
            z += 0.04 * (1 - a / 8) ** 2
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        c, k_ = glow_col(f)
        x = x * (1 - k_ * vig) + c * k_ * vig
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        rainbow_bar(fr, int(W * (f + 1) / TOTAL))
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
