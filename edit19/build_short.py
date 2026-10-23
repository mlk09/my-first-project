#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED + TTP223 touch sensor - 3 modes' short, same house
style as the rotary-encoder short: a finger taps the pad in the hook (TOUCH!), callout tags,
capacitive close-up, then the knob picks LAMP (tap toggles the LED), BELL (ding-dong) and COUNTER
(taps count, a long press resets); a finger + ripples land on the projected pad position, live mode
HUD, end card + Like / Share / Subscribe outro. Tap blips, switch clicks, ding-dong, counting beeps.
Usage: python3 edit19/build_short.py [audio] [video]
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
from timeline import (FPS, N, SHOTS, MODES, TOUCHES, HOLD, KNOB_CLICKS, BELL_AT, mode, mode_idx,  # noqa: E402
                      touching, touch_amt, led, count, hold_prog, reset_at, ease)

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-touch-sensor-SHORT.mp4")
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
    lay.alpha_composite(e5.emoji("👆", 46), (W - 388, 46))


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
import json  # noqa: E402

PAD = json.load(open(os.path.join(WORK, "pad_xy.json")))
FIRST = TOUCHES[0][0]


def blip(freq=1300):
    return np.concatenate([beep(freq, 0.035), np.zeros(int(0.01 * SR))]) * 0.8


def switch(up=True):
    n = int(0.03 * SR)
    tt = np.arange(n) / SR
    clk = fx.filt(fx.noise(n, 3), "bandpass", [1500, 7000]) * np.exp(-tt * 300)
    sw = np.concatenate([beep(900 if up else 1400, 0.05), beep(1400 if up else 900, 0.07)])
    out = np.zeros(len(sw) + n)
    out[:n] += clk
    out[n:] += sw * 0.5
    return out


def bell_tone(freq, dur=1.2):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * h * tt) for h, a in ((1, 1.0), (2.76, 0.4), (5.4, 0.2), (8.9, 0.08)))
    return x * np.exp(-tt * 3.2) * np.minimum(1, tt / 0.003) * 0.5


def music(total):
    """112 BPM funky pluck groove (Em - C - G - D); filtered until the first touch."""
    bpm, n = 112, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[329.6, 392.0, 493.9], [261.6, 329.6, 392.0], [392.0, 493.9, 587.3], [293.7, 370.0, 440.0]]
    roots = [82.4, 65.4, 98.0, 73.4]
    kick = fx.kick() * 0.5
    drop = t(FIRST)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        for s in (0, 1, 3):
            fx.place(mel, fx.synth_note(ch[(pos + s) % 3], beat / 4 * 1.2, "square", 16, 2400), t0 + s * beat / 4, 0.07)
        if t0 >= drop:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.4, "saw", 7, 300), t0, 0.5)
            fx.place(bass, fx.synth_note(roots[bar % 4] * 2, beat * 0.2, "saw", 9, 400), t0 + beat * 0.75, 0.3)
            if pos in (0, 2):
                fx.place(drums, kick, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.28)
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
    P(buf, fx.riser(0.4), 0.0, 0.3)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    P(buf, fx.pop(), t(SHOTS[1] + 4), 0.25)
    for s, n in TOUCHES:                                            # every tap
        P(buf, blip(), t(s), 0.35)
    P(buf, fx.boom()[: int(0.5 * SR)], t(FIRST), 0.4)
    P(buf, switch(True), t(FIRST), 0.45)
    P(buf, fx.ding(), t(TOUCHES[1][0] + 2), 0.25)
    for c, _ in KNOB_CLICKS:                                        # mode picks
        P(buf, detent_click(), t(c + 4), 0.7)
        P(buf, beep(1800, 0.05), t(c + 6), 0.18)
    P(buf, switch(True), t(TOUCHES[2][0]), 0.45)                    # LAMP on / off
    P(buf, switch(False), t(TOUCHES[3][0]), 0.45)
    P(buf, bell_tone(659.3), t(BELL_AT + 1), 0.55)                  # ding ... dong
    P(buf, bell_tone(523.3), t(BELL_AT + 1) + 0.38, 0.55)
    for k_, (s, n) in enumerate(TOUCHES[5:10]):                     # counting up
        P(buf, beep(523.3 * 2 ** (k_ * 2 / 12), 0.08), t(s) + 0.02, 0.35)
    P(buf, fx.riser(t(HOLD[1] - 2)), t(HOLD[0]), 0.35)              # hold ... reset
    P(buf, fx.whoosh(0.4, 9) * 0.6, t(HOLD[0] + HOLD[1] - 2), 0.45)
    P(buf, ok_beep(), t(HOLD[0] + HOLD[1] - 1), 0.35)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
BLU = (70, 150, 255)
MODE_EM = {"LAMP": "💡", "BELL": "🔔", "COUNT": "🔢"}


def finger(lay, f):
    """Pointing finger that presses onto the projected pad centre."""
    a = touch_amt(f)
    if a <= 0.02:
        return
    x, y, r = PAD[f]
    sz = int(max(120, min(260, r * 2.2)))
    em = e5.emoji("👇", sz)
    lift = (1 - a) * sz * 0.9
    squash = 1 - 0.08 * a
    em = em.resize((sz, int(sz * squash)))
    al = em.split()[3].point(lambda v: int(v * min(1, a * 1.6)))
    em.putalpha(al)
    lay.alpha_composite(em, (int(x - sz * 0.5), int(y - sz * squash * 0.95 - lift)))


def ripples(lay, f):
    d = ImageDraw.Draw(lay)
    x, y, r = PAD[f]
    for s, n in TOUCHES:
        a = f - s
        if 0 <= a < 14:
            for k_ in range(2):
                u = (a - k_ * 4) / 10
                if 0 < u <= 1:
                    rr = r * (0.6 + 1.6 * u)
                    d.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), outline=(80, 230, 255, int(255 * (1 - u))), width=8)
    if touching(f):
        for s, n in TOUCHES:
            if n > 10 and s <= f < s + n:                               # long touches keep pulsing
                u = ((f - s) % 10) / 10
                rr = r * (0.7 + 1.2 * u)
                d.ellipse((x - rr, y - rr * 0.8, x + rr, y + rr * 0.8), outline=(80, 230, 255, int(220 * (1 - u))), width=6)


def hold_ring(lay, f):
    p = hold_prog(f)
    if p <= 0 or reset_at(f):
        return
    d = ImageDraw.Draw(lay)
    x, y, r = PAD[f]
    rr = r * 1.6
    d.arc((x - rr, y - rr, x + rr, y + rr), -90, -90 + 360 * p, fill=YEL + (255,), width=14)
    txt(d, (x, y - rr - 50), f"HOLD... {int(p * 100)}%", 52, YEL, stroke=6)


def hud(lay, d, f, y0=1590):
    """Mode chips + touch indicator + LED state (own style)."""
    d.rounded_rectangle((60, y0 - 120, W - 60, y0 + 120), 56, fill=(10, 12, 18, 225), outline=(255, 255, 255, 140), width=3)
    m = mode(f)
    for k_, name in enumerate(MODES):
        cx = 220 + k_ * 320
        act = m == name
        col = (CYAN if act else (60, 64, 76))
        d.rounded_rectangle((cx - 140, y0 - 95, cx + 140, y0 - 15), 40, fill=col + (255,), outline=WHT if act else None, width=4)
        d.text((cx + 20, y0 - 55), name, font=font(MONT, 40), fill=INK if act else (170, 175, 190), anchor="mm")
        lay.alpha_composite(e5.emoji(MODE_EM[name], 44), (int(cx - 125), int(y0 - 77)))
    tch = touching(f)
    d.ellipse((110, y0 + 30, 160, y0 + 80), fill=(GRN if tch else (70, 74, 86)) + (255,), outline=WHT, width=3)
    d.text((180, y0 + 55), "TOUCH: YES" if tch else "TOUCH: NO", font=font(MONT, 40), fill=WHT, anchor="lm")
    on = led(f)
    d.rounded_rectangle((W - 400, y0 + 22, W - 100, y0 + 88), 33, fill=(BLU if on else (60, 64, 76)) + (255,), outline=WHT, width=3)
    d.text((W - 250, y0 + 55), "LED ON" if on else "LED OFF", font=font(MONT, 40), fill=WHT, anchor="mm")


def pop_text(lay, d, f, f0, s_, y, size, col, em=None):
    s = pop_s(f - f0, 6)
    if s <= 0:
        return
    txt(d, (W / 2, y), s_, size * s, col, stroke=max(6, size // 11))
    if em and s > 0.9:
        tw = d.textlength(s_, font=font(MONT, size))
        lay.alpha_composite(e5.emoji(em, int(size * 0.85)), (int(W / 2 + tw / 2 + 10), int(y - size * 0.5)))


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "ttp": ((590, 520), (850, 470), "TTP223", "Touch sensor"),
    "esp": ((320, 860), (220, 660), "ESP32", "Dimaag"),
    "oled": ((660, 860), (880, 760), "OLED", "Mode + status"),
    "knob": ((370, 1300), (250, 1560), "Knob", "Mode select"),
    "led": ((630, 1280), (820, 1560), "LED + Buzzer", "Output"),
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
    if i in (0, 2, 3, 4, 5):
        ripples(lay, f)
        hold_ring(lay, f)
        finger(lay, f)
        d = ImageDraw.Draw(lay)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 200), "Button nahi...", 80 * s, WHT, stroke=8)
        pop_text(lay, d, f, FIRST, "TOUCH!", 320, 130, CYAN, "⚡")
        hud(lay, d, f)
    elif i == 1:
        label(lay, d, "ESP32 Touch Switch", None, local, y=230, em=None)
        for j, key in enumerate(("ttp", "esp", "oled", "knob", "led")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 6) / 10))
    elif i == 2:
        label(lay, d, "Capacitive Touch", "Ungli ka charge = signal HIGH", local, y=280, em="⚡")
        if touching(f):
            x, y, r = PAD[f]
            d.rounded_rectangle((W / 2 - 230, 1180, W / 2 + 230, 1290), 55, fill=GRN + (255,), outline=WHT, width=5)
            d.text((W / 2, 1235), "SIG = HIGH", font=font(MONT, 58), fill=INK, anchor="mm")
        hud(lay, d, f)
    elif i in (3, 4, 5):
        m = MODES[i - 3]
        sub = {"LAMP": "Tap = LED ON / OFF", "BELL": "Tap = Ding Dong!", "COUNT": "Tap gino, HOLD = reset"}[m]
        name = {"LAMP": "LAMP", "BELL": "BELL", "COUNT": "COUNTER"}[m]
        label(lay, d, f"Mode {i - 2}: {name}", sub, local, y=280, em=MODE_EM[m])
        if m == "LAMP":
            for s, _ in TOUCHES[2:4]:
                if s <= f < s + 22:
                    pop_text(lay, d, f, s, "LED ON!" if led(f) else "LED OFF", 470, 120, BLU if led(f) else WHT)
        elif m == "BELL":
            if BELL_AT <= f < BELL_AT + 40:
                pop_text(lay, d, f, BELL_AT, "DING DONG!", 470, 120, YEL, "🔔")
        else:
            c = count(f)
            if reset_at(f):
                pop_text(lay, d, f, HOLD[0] + HOLD[1] - 2, "RESET!", 470, 140, RED, "🔄")
            elif c > 0:
                last = max(s for s, _ in TOUCHES[5:10] if s <= f)
                s_ = 1 + 0.35 * max(0, 1 - (f - last) / 5)
                txt(d, (W / 2, 480), f"COUNT: {c}", 120 * s_, YEL, stroke=11)
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
                d.text((130, 430), "if (digitalRead(TOUCH))", font=font(MONO, 46), fill=(255, 190, 90), anchor="lm")
                d.text((170, 505), "ledState = !ledState;", font=font(MONO, 44), fill=(150, 255, 170), anchor="lm")
        v = ease((local - 12) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"TOUCH\" — bhej dunga", font=font(MONT, 46), fill=INK, anchor="mm")
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
    hits = [s for s, _ in TOUCHES] + [HOLD[0] + HOLD[1] - 2]
    for f in range(TOTAL):
        if f >= N:
            fr = outro(f - N)
            if f - N < 4:
                k_ = 1 - (f - N) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 20 * k_), 1 + 0.06 * k_)
            fr[0:10, :] = YEL
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z, dx = 1.0, 0.0
        for h0 in hits:                                            # small punch-in on every tap
            a = f - h0
            if 0 <= a < 7:
                z += (0.05 if h0 in (FIRST, BELL_AT, hits[-1]) else 0.025) * (1 - a / 7) ** 2
        a = f - BELL_AT
        if 0 <= a < 12:                                            # bell shake
            dx = 10 * np.sin(a * 2.2) * (1 - a / 12)
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        if led(f) and f < SHOTS[6]:                                # blue edge glow while the LED is on
            x = x * (1 - 0.12 * vig) + np.array(BLU, np.float32) * 0.12 * vig
        if reset_at(f) and f < SHOTS[6]:
            k_ = 0.2 * (1 - (f - HOLD[0] - HOLD[1] + 2) / 24)
            x = x * (1 - k_ * vig) + np.array(RED, np.float32) * k_ * vig
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / TOTAL)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p] = YEL
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
