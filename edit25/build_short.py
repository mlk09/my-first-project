#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED + MQ-2 gas-leak alarm' short in native 1080x1920 HD, same
house style: the LPG valve hisses open in the hook (GAS LEAK!), callout tags, MQ-2 close-up (heater
glows), knob sets the alarm limit, the gas creeps up past the limit -> siren + red LED + exhaust fan,
the fan clears the air -> SAFE; live ppm gauge HUD, rainbow edge glow + progress bar, end card +
Like / Share / Subscribe outro. Gas hiss, siren, fan whoosh, knob clicks, tense pulse music.
Usage: python3 edit25/build_short.py [audio] [video]
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
from timeline import FPS, N, SHOTS, LIMIT0, ppm, limit, alarm, fan, gas, leak, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-mq2-gas-leak-alarm-SHORT.mp4")
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
    lay.alpha_composite(e5.emoji("🔥", 46), (W - 388, 46))


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
GASC = (150, 230, 120)


def siren(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    fr = 900 + 500 * (0.5 + 0.5 * np.sin(2 * np.pi * 1.6 * tt))           # rising / falling wail
    ph = 2 * np.pi * np.cumsum(fr) / SR
    x = np.sign(np.sin(ph)) * 0.3 + np.sin(ph) * 0.35
    return fx.filt(x, "lowpass", 4500) * np.minimum(1, tt / 0.02) * np.minimum(1, (dur - tt) / 0.06)


def hiss(dur, seed=0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, seed), "bandpass", [2500, 9000])
    return x * np.minimum(1, tt / 0.08) * np.minimum(1, (dur - tt) / 0.15) * 0.7


def fan_snd(dur, seed=3):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, seed), "lowpass", 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * tt))
    return x * np.minimum(1, tt / 0.4) * np.minimum(1, (dur - tt) / 0.3)


def music(total):
    """104 BPM tense pulse (minor, ticking 8ths, sub hits); filtered until the first alarm, brighter when safe."""
    bpm, n = 104, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    roots = [55.0, 55.0, 49.0, 52.0]
    kick = fx.kick() * 0.5
    drop = t(ON1)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        for s in range(2):
            fx.place(mel, fx.synth_note(roots[bar % 4] * 8 * (1.5 if s else 1), beat / 2 * 0.6, "square", 18, 2600), t0 + s * beat / 2, 0.05)
        fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.95, "saw", 3, 220), t0, 0.5)
        if t0 >= drop:
            fx.place(drums, kick, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.25)
            for s in range(4):
                fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / 4, 0.035 if s % 2 else 0.05)
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
    for a, b_ in ((2, 44), (SHOTS[4] + 6, SHOTS[5] - 6)):              # valve opens -> gas hiss
        P(buf, fx.click() if hasattr(fx, "click") else beep(400, 0.03), t(a), 0.4)
        P(buf, hiss(t(b_ - a), a), t(a), 0.45)
    for on, off in ((ON1, OFF1), (ON2, OFF2)):                         # alarm: boom + siren + fan
        P(buf, fx.boom()[: int(0.5 * SR)], t(on), 0.45)
        P(buf, siren(min(t(off) - t(on), 3.5)), t(on), 0.3)
        P(buf, fan_snd(t(off) - t(on) + 0.8), t(on), 0.35)
    for off in (OFF1, OFF2):
        P(buf, ok_beep(), t(off), 0.35)
    P(buf, fx.ding(), t(OFF2 + 2), 0.35)
    for f in range(1, N):
        if limit(f) != limit(f - 1):
            P(buf, detent_click(), t(f), 0.7)
            P(buf, beep(1400, 0.05), t(f) + 0.03, 0.18)
    for f in range(SHOTS[2], SHOTS[3], 12):                            # sensor 'read' ticks
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
    """Red flashing while the alarm rings, else the slow rainbow drift of the LED Flow short."""
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


def gauge(lay, d, cx, cy, r, f):
    """Speedometer-style 0-1000 ppm gauge: green / yellow / red arc, limit tick, needle."""
    p, lim = ppm(f), limit(f)
    d.ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), fill=(10, 12, 18, 230), outline=(255, 255, 255, 140), width=3)
    for a0, a1, col in ((150, 222, GRN), (222, 294, YEL), (294, 390, RED)):
        d.arc((cx - r, cy - r, cx + r, cy + r), a0, a1, fill=col + (255,), width=int(r * 0.16))
    la = math.radians(150 + 240 * lim / 1000)
    d.line((cx + r * 0.68 * math.cos(la), cy + r * 0.68 * math.sin(la), cx + r * 1.08 * math.cos(la), cy + r * 1.08 * math.sin(la)),
           fill=WHT, width=8)
    na = math.radians(150 + 240 * min(p, 1000) / 1000)
    d.line((cx, cy, cx + r * 0.82 * math.cos(na), cy + r * 0.82 * math.sin(na)), fill=WHT, width=10)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=WHT)
    txt(d, (cx, cy + r * 0.45), f"{p:.0f}", int(r * 0.42), RED if alarm(f) else WHT, stroke=6)
    d.text((cx, cy + r * 0.78), "ppm", font=font(MONT, int(r * 0.17)), fill=(200, 205, 215), anchor="mm")


def hud(lay, d, f, y0=1590):
    """Gas HUD: ppm, limit marker on a 0-1000 bar, ALARM / SAFE pill + fan state (own style)."""
    p, lim, on = ppm(f), limit(f), alarm(f)
    d.rounded_rectangle((60, y0 - 120, W - 60, y0 + 120), 56, fill=(10, 12, 18, 225), outline=(255, 255, 255, 140), width=3)
    lay.alpha_composite(e5.emoji("💨", 76), (96, int(y0 - 92)))
    txt(d, (190, y0 - 52), f"{p:.0f} ppm", 76, RED if on else WHT, stroke=7, anchor="lm")
    age = min(f - x for x in SW if x <= f) if any(x <= f for x in SW) else 99
    s = 1 + 0.25 * max(0, 1 - age / 6)
    pw, ph = 300 * s, 92 * s
    cx, cy = W - 250, y0 - 52
    d.rounded_rectangle((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), 46,
                        fill=(RED if on else GRN) + (255,), outline=WHT, width=4)
    d.text((cx, cy), "ALARM!" if on else "SAFE", font=font(MONT, 52 * s), fill=WHT, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    x0, x1, by = 110, W - 330, y0 + 58

    def bx(v):
        return x0 + min(max(v, 0), 1000) / 1000 * (x1 - x0)
    d.rounded_rectangle((x0, by - 14, x1, by + 14), 14, fill=(255, 255, 255, 50))
    d.rounded_rectangle((bx(lim), by - 14, x1, by + 14), 14, fill=(255, 60, 60, 90))
    d.rounded_rectangle((x0, by - 14, max(x0 + 28, bx(p)), by + 14), 14, fill=(RED if on else GASC) + (255,))
    lx = bx(lim)
    d.line((lx, by - 34, lx, by + 30), fill=YEL, width=6)
    d.text((lx, by - 50), f"LIMIT {lim:.0f}", font=font(MONT, 28), fill=YEL, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((W - 100, by), "FAN ON" if fan(f) > 0.05 else "FAN OFF", font=font(MONT, 34),
           fill=CYAN if fan(f) > 0.05 else (150, 155, 170), anchor="rm")


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "mq": ((560, 470), (840, 380), "MQ-2", "Gas sensor"),
    "esp": ((320, 860), (220, 660), "ESP32", "Dimaag"),
    "oled": ((650, 860), (880, 760), "OLED", "ppm reading"),
    "knob": ((370, 1300), (250, 1560), "Knob", "Limit set"),
    "fan": ((200, 420), (220, 270), "Exhaust Fan", "Gas bahar"),
    "leds": ((640, 1280), (820, 1560), "LED + Buzzer", "Alarm"),
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
    on = alarm(f)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 200), "Gas leak ho gayi?", 84 * s, WHT, stroke=8)
        s2 = pop_s(f - ON1, 6)
        if s2 > 0:
            txt(d, (W / 2 - 45, 330), "ALARM BAJA!", 120 * s2, RED, stroke=12)
            if s2 > 0.9:
                tw = d.textlength("ALARM BAJA!", font=font(MONT, 120))
                lay.alpha_composite(e5.emoji("🚨", 96), (int(W / 2 - 45 + tw / 2 + 8), 275))
        hud(lay, d, f)
    elif i == 1:
        label(lay, d, "ESP32 Gas Leak Alarm", None, local, y=200, em=None)
        for j, key in enumerate(("mq", "esp", "oled", "fan", "knob", "leds")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 5) / 10))
    elif i == 2:
        label(lay, d, "MQ-2 = Gas ki naak", "LPG, dhuan, methane sab pakdega", local, y=280, em="👃")
        v = ease((local - 12) / 8)
        if v > 0:
            gauge(lay, d, W / 2, 1220, 200 * v, f)
        hud(lay, d, f)
    elif i == 3:
        label(lay, d, "Knob = LIMIT", "Ghumao aur gas limit set karo", local, y=280, em="🎛️")
        lim = limit(f)
        ch = [x for x in range(SHOTS[3], f + 1) if limit(x) != limit(x - 1)]
        s = 1 + 0.3 * max(0, 1 - (f - ch[-1]) / 6) if ch else 1
        v = ease((local - 8) / 6)
        if v > 0:
            d.rounded_rectangle((W / 2 - 280 * v, 730, W / 2 + 280 * v, 930), 50, fill=(10, 12, 18, 225), outline=YEL + (255,), width=6)
            if v > 0.9:
                d.text((W / 2, 772), "GAS LIMIT", font=font(MONT, 40), fill=YEL, anchor="mm")
                txt(d, (W / 2, 860), f"{lim:.0f} ppm", 92 * s, WHT, stroke=8)
        hud(lay, d, f)
    elif i == 4:
        if not on:
            label(lay, d, "Valve khula...", "Gas dheere dheere badh rahi hai", local, y=280, em="💨")
        else:
            s = pop_s(f - ON2, 6)
            txt(d, (W / 2, 250), "GAS LEAK!", 140 * s, RED, stroke=12)
            if s > 0.9:
                d.rounded_rectangle((W / 2 - 380, 340, W / 2 + 380, 430), 45, fill=(0, 0, 0, 180))
                d.text((W / 2 - 30, 385), "Siren + LED + FAN ON", font=font(BOLD, 50), fill=WHT, anchor="mm")
                lay.alpha_composite(e5.emoji("🌀", 70), (int(W / 2 + 300), 350))
            if (f - ON2) % 11 < 5:
                txt(d, (870, 1250), "WEE-WOO!", 64, RED, stroke=7)
        hud(lay, d, f)
    elif i == 5:
        if f < OFF2:
            label(lay, d, "Fan gas nikaal raha hai", "Hawa saaf ho rahi hai...", local, y=280, em="🌀")
        else:
            s = pop_s(f - OFF2, 6)
            txt(d, (W / 2 - 55, 250), "AIR SAFE", 124 * s, GRN, stroke=11)
            if s > 0.9:
                tw = d.textlength("AIR SAFE", font=font(MONT, 124))
                lay.alpha_composite(e5.emoji("✅", 90), (int(W / 2 - 55 + tw / 2 + 8), 200))
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
                d.text((130, 430), "if (analogRead(MQ2) > limit)", font=font(MONO, 40), fill=(255, 190, 90), anchor="lm")
                d.text((170, 505), "alarm(); fanOn();", font=font(MONO, 42), fill=(150, 255, 170), anchor="lm")
        v = ease((local - 12) / 8)
        if v > 0:
            bw = int(940 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"GAS\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 20) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1780), "Follow @The IOT Engineer", 54, WHT, stroke=5)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-maxrate", "18M", "-bufsize", "36M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
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
        for on in (ON1, ON2):                                      # punch-in + shake on the alarm
            a = f - on
            if 0 <= a < 10:
                z += 0.05 * (1 - a / 10) ** 2
                dx = 16 * np.sin(a * 2.5) * (1 - a / 10)
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.22 * vig)
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
