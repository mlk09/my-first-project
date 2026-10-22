#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED RGB colour mixer' short, same house style as the
rotary-encoder short: R / G / B flash hook ('1 LED = 16 million colours?'), callout tags, additive
mixing close-up with Venn circles, knob hue sweep with a colour wheel, brightness (PWM duty-cycle
graphic), knob press -> PARTY mode with confetti, live colour HUD, end card + Like / Share /
Subscribe outro. Colour notes (R = C, G = E, B = G), knob clicks, riser + drop, synth-pop groove.
Usage: python3 edit18/build_short.py [audio] [video]
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
from timeline import (FPS, N, SHOTS, PRESS, rgb, to255, name, mode, hue, bright,  # noqa: E402
                      hue_clicks, bright_clicks, ease)

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-rgb-color-mixer-SHORT.mp4")
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
    lay.alpha_composite(e5.emoji("🌈", 46), (W - 388, 46))


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
NOTE = {"R": 523.3, "G": 659.3, "B": 784.0}
HOOK_HITS = [(4, "R"), (20, "G"), (36, "B")]
MIX_HITS = [(SHOTS[2] + 4, "R"), (SHOTS[2] + 22, "G"), (SHOTS[2] + 40, "B")]
DROP = 52


def pluck(freq, dur=0.5):
    return fx.synth_note(freq, dur, "square", 6, 3000) * 0.5 + fx.synth_note(freq * 2, dur, "tri", 9, 5000) * 0.3


def sparkle():
    out = np.zeros(int(0.6 * SR))
    for i, fr in enumerate((1568, 2093, 2637, 3136)):
        fx.place(out, fx.synth_note(fr, 0.25, "tri", 14, 8000) * 0.4, i * 0.05, 1.0)
    return out


def music(total):
    """120 BPM bright synth-pop (C - G - Am - F); filtered until the hook rainbow, double-time hats in PARTY."""
    bpm, n = 120, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[261.6, 329.6, 392.0], [196.0, 246.9, 293.7], [220.0, 261.6, 329.6], [174.6, 220.0, 261.6]]
    roots = [65.4, 49.0, 55.0, 43.65]
    kick = fx.kick() * 0.5
    drop, party0, party1 = t(DROP), t(PRESS), t(SHOTS[6])
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        for s in range(2):
            fx.place(mel, fx.synth_note(ch[(pos + s) % 3] * 2, beat / 2 * 1.2, "saw", 8, 3000), t0 + s * beat / 2, 0.05)
        if t0 >= drop:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 260), t0, 0.6)
            fx.place(drums, kick, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.28)
            hs = 4 if party0 <= t0 < party1 else 2
            for s in range(hs):
                fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / hs, 0.05)
        b += 1
    mix = mel + bass + drums
    i = int(drop * SR)
    mix[:i] = fx.filt(mix[:i], "lowpass", 900)
    j0, j1 = int((party0 - 1.0) * SR), int(party0 * SR)                  # filter sweep into the drop
    for k_ in range(j0, j1, 2400):
        u = (k_ - j0) / (j1 - j0)
        mix[k_:k_ + 2400] = fx.filt(mix[k_:k_ + 2400], "lowpass", 600 + 6000 * u)
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    P(buf, fx.pop(), t(SHOTS[1] + 4), 0.25)
    for f0, ch in HOOK_HITS + MIX_HITS:                                 # colour notes
        P(buf, pluck(NOTE[ch]), t(f0), 0.45)
        P(buf, fx.pop(), t(f0), 0.2)
    P(buf, sparkle(), t(DROP), 0.4)
    P(buf, fx.boom()[: int(0.5 * SR)], t(DROP), 0.4)
    P(buf, sparkle(), t(MIX_HITS[2][0] + 1), 0.4)
    for f in range(1, N):
        if (SHOTS[3] <= f < SHOTS[4] and hue_clicks(f) != hue_clicks(f - 1)) or \
           (SHOTS[4] <= f < SHOTS[5] and bright_clicks(f) != bright_clicks(f - 1)):
            P(buf, detent_click(), t(f), 0.7)
            pitch = 900 + 40 * hue_clicks(f) if f < SHOTS[4] else 600 + 120 * (10 - bright_clicks(f))
            P(buf, beep(pitch, 0.04), t(f) + 0.02, 0.12)
    P(buf, fx.riser(1.0), t(PRESS) - 1.0, 0.35)
    P(buf, fx.pop(), t(PRESS), 0.5)
    P(buf, fx.boom()[: int(0.6 * SR)], t(PRESS), 0.5)
    P(buf, sparkle(), t(PRESS) + 0.05, 0.45)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
def led_col(f, lo=60):
    """LED colour as a vivid 0-255 tuple for graphics (never too dark)."""
    c = rgb(f)
    m = max(c) or 1
    return tuple(int(lo + (255 - lo) * x / m) if max(c) > 0 else 80 for x in c)


def hud(lay, d, f, y0=1590):
    """Live colour HUD: swatch, colour name, R / G / B mini bars (own style)."""
    col = led_col(f)
    d.rounded_rectangle((60, y0 - 120, W - 60, y0 + 120), 56, fill=(10, 12, 18, 225), outline=col + (230,), width=5)
    c255 = to255(rgb(f))
    d.ellipse((95, y0 - 85, 265, y0 + 85), fill=c255 + (255,), outline=WHT, width=5)
    txt(d, (300, y0 - 52), name(f), 76, col, stroke=7, anchor="lm")
    for i, (lab, v, cc) in enumerate(zip("RGB", c255, (RED, GRN, (60, 140, 255)))):
        y = y0 + 22 + i * 30
        d.text((300, y), lab, font=font(MONT, 26), fill=cc, anchor="lm")
        d.rounded_rectangle((340, y - 9, 840, y + 9), 9, fill=(255, 255, 255, 45))
        d.rounded_rectangle((340, y - 9, 340 + max(18, int(500 * v / 255)), y + 9), 9, fill=cc + (255,))
        d.text((W - 90, y), f"{v:3d}", font=font(MONT, 28), fill=WHT, anchor="rm")


def venn(lay, f, cx, cy, r=120):
    """Additive R / G / B circles that switch on with the mix shot."""
    l = f - SHOTS[2]
    layer = np.zeros((H, W, 3), np.float32)
    yy, xx = np.ogrid[0:H, 0:W]
    for k_, (on_at, col, ang) in enumerate(((4, (1, 0, 0), -90), (22, (0, 1, 0), 30), (40, (0, 0, 1), 150))):
        u = ease((l - on_at) / 5)
        if u <= 0:
            continue
        ox = cx + 0.55 * r * math.cos(math.radians(ang))
        oy = cy + 0.55 * r * math.sin(math.radians(ang))
        m = ((xx - ox) ** 2 + (yy - oy) ** 2) <= (r * u) ** 2
        layer[m] += np.array(col, np.float32)
    layer = np.clip(layer, 0, 1)
    a = (layer.max(2) > 0).astype(np.float32) * 0.92
    rgba = np.dstack([layer * 255, a * 255]).astype(np.uint8)
    lay.alpha_composite(Image.fromarray(rgba, "RGBA"))


_WHEEL = {}


def wheel(lay, d, f, cx, cy, r=130):
    """Rainbow hue ring with a pointer at the knob's hue."""
    if r not in _WHEEL:
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        rr = np.hypot(xx, yy)
        ang = (np.degrees(np.arctan2(xx, -yy)) + 360) % 360
        import colorsys
        rgbs = np.array([colorsys.hsv_to_rgb(a / 360, 1, 1) for a in range(361)])
        img = rgbs[ang.astype(int)] * 255
        a = ((rr <= r) & (rr >= r * 0.62)).astype(np.uint8) * 255
        _WHEEL[r] = Image.fromarray(np.dstack([img, a]).astype(np.uint8), "RGBA")
    d.ellipse((cx - r - 12, cy - r - 12, cx + r + 12, cy + r + 12), fill=(10, 12, 18, 220))
    lay.alpha_composite(_WHEEL[r], (int(cx - r), int(cy - r)))
    h = math.radians(hue(f))
    px, py = cx + r * 0.81 * math.sin(h), cy - r * 0.81 * math.cos(h)
    d.ellipse((px - 26, py - 26, px + 26, py + 26), fill=to255(rgb(f)) + (255,), outline=WHT, width=6)
    d.text((cx, cy), f"{hue(f):.0f}°", font=font(MONT, 46), fill=WHT, anchor="mm")


def pwm(lay, d, f, x0, y0, w=600, h=150):
    """PWM square wave whose duty cycle follows the brightness."""
    p = bright(f)
    d.rounded_rectangle((x0 - 30, y0 - 60, x0 + w + 30, y0 + h + 30), 30, fill=(10, 12, 18, 225), outline=YEL + (255,), width=5)
    d.text((x0, y0 - 30), "PWM", font=font(MONT, 34), fill=YEL, anchor="lm")
    d.text((x0 + w, y0 - 30), f"{p * 100:.0f}% ON", font=font(MONT, 34), fill=WHT, anchor="rm")
    per = w / 4
    pts = []
    for k_ in range(4):
        xa = x0 + k_ * per
        xb = xa + per * p
        pts += [(xa, y0 + h), (xa, y0 + 10), (xb, y0 + 10), (xb, y0 + h), (xa + per, y0 + h)]
    d.line(pts, fill=led_col(f, 120) + (255,), width=8, joint="curve")


def confetti(lay, f):
    a = f - PRESS
    if a < 0:
        return
    d = ImageDraw.Draw(lay)
    rng_ = np.random.default_rng(11)
    cols = [RED, YEL, GRN, CYAN, (200, 120, 255), ORG]
    for k_ in range(90):
        x0 = rng_.uniform(0, W)
        vy = rng_.uniform(14, 30)
        y = -40 + vy * a - rng_.uniform(0, 400)
        x = x0 + rng_.uniform(20, 60) * math.sin(a * 0.25 + k_)
        if -40 < y < H:
            ang = a * 0.3 + k_
            w_ = 18 * abs(math.cos(ang)) + 4
            d.rectangle((x - w_ / 2, y - 5, x + w_ / 2, y + 5), fill=cols[k_ % 6] + (255,))


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "esp": ((320, 860), (220, 660), "ESP32", "PWM dimaag"),
    "oled": ((650, 860), (880, 780), "OLED", "R G B values"),
    "led": ((594, 470), (850, 560), "RGB LED", "KY-016 + ball"),
    "knob": ((370, 1300), (250, 1560), "Knob", "Color / Brightness"),
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
        txt(d, (W / 2, 215), "1 LED =", 80 * s, WHT, stroke=8)
        for k_, (f0, ch) in enumerate(HOOK_HITS):                         # R G B chips
            u = pop_s(f - f0, 5)
            if u > 0:
                cx = W / 2 + (k_ - 1) * 190
                c = (RED, GRN, (60, 140, 255))[k_]
                cx = W / 2 + (k_ - 1) * 150
                d.ellipse((cx - 55 * u, 325 - 55 * u, cx + 55 * u, 325 + 55 * u), fill=c + (255,), outline=WHT, width=5)
                if u > 0.9:
                    txt(d, (cx, 325), ch, 64, WHT, stroke=5)
        s2 = pop_s(f - DROP, 6)
        if s2 > 0:
            txt(d, (W / 2, 1200), "16 MILLION", 120 * s2, YEL, stroke=11)
            txt(d, (W / 2, 1325), "COLORS?", 120 * s2, led_col(f), stroke=11)
        hud(lay, d, f)
    elif i == 1:
        label(lay, d, "ESP32 RGB Mixer", None, local, y=230, em="🌈")
        for j, key in enumerate(("led", "esp", "oled", "knob")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 7) / 10))
    elif i == 2:
        l = local
        title = "RED" if l < 22 else "RED + GREEN = YELLOW" if l < 40 else "R + G + B = WHITE"
        size = 92 if l < 22 else 66 if l < 40 else 76
        col = RED if l < 22 else YEL if l < 40 else WHT
        start = 4 if l < 22 else 22 if l < 40 else 40
        s = pop_s(l - start, 6)
        txt(d, (W / 2, 260), title, size * s, col, stroke=8)
        if l < 22:
            d.rounded_rectangle((W / 2 - 330, 330, W / 2 + 330, 410), 40, fill=(0, 0, 0, 170))
            d.text((W / 2, 370), "Rang milao = naya rang", font=font(BOLD, 46), fill=WHT, anchor="mm")
        venn(lay, f, W / 2, 1240, 125)
        d = ImageDraw.Draw(lay)
        hud(lay, d, f)
    elif i == 3:
        label(lay, d, "Knob = COLOR", "Ghumao aur rang badlo", local, y=280, em="🎛️")
        if local > 6:
            wheel(lay, d, f, W - 200, 1180)
        hud(lay, d, f)
    elif i == 4:
        if f < PRESS:
            label(lay, d, "Knob = DIMMER", "PWM se brightness kam / zyada", local, y=280, em="💡")
            if local > 6:
                pwm(lay, d, f, 440, 1120, w=520, h=130)
        hud(lay, d, f)
    elif i == 5:
        s = pop_s(f - PRESS, 6)
        txt(d, (W / 2, 260), "PARTY MODE!", 124 * s, led_col(f), stroke=12)
        if s > 0.9:
            tw = d.textlength("PARTY MODE!", font=font(MONT, 124))
            lay.alpha_composite(e5.emoji("🎉", 100), (int(W / 2 + tw / 2 - 20), 300))
            d.rounded_rectangle((W / 2 - 320, 350, W / 2 + 320, 430), 40, fill=(0, 0, 0, 170))
            d.text((W / 2, 390), "Knob dabao = Rainbow!", font=font(BOLD, 46), fill=WHT, anchor="mm")
        confetti(lay, f)
        d = ImageDraw.Draw(lay)
        hud(lay, d, f)
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y_ / 700)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        d = ImageDraw.Draw(lay)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Circuit FREE", 78 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130, col=led_col(f))
        v = ease((local - 5) / 8)
        if v > 0:
            d.rounded_rectangle((90, 380, 90 + (W - 180) * v, 600), 30, fill=(12, 16, 24, 235), outline=CYAN + (255,), width=4)
            if v > 0.9:
                d.text((130, 430), "ledcWrite(R_PIN, r);", font=font(MONO, 46), fill=(255, 120, 120), anchor="lm")
                d.text((130, 490), "ledcWrite(G_PIN, g);", font=font(MONO, 46), fill=(150, 255, 170), anchor="lm")
                d.text((130, 550), "ledcWrite(B_PIN, b);", font=font(MONO, 46), fill=(140, 190, 255), anchor="lm")
        v = ease((local - 12) / 8)
        if v > 0:
            bw = int(900 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"RGB\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
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
    hits = [f0 for f0, _ in HOOK_HITS + MIX_HITS] + [DROP, PRESS]
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
        for h0 in hits:                                            # punch-in on every colour hit
            a = f - h0
            if 0 <= a < 8:
                z += (0.06 if h0 in (DROP, PRESS) else 0.035) * (1 - a / 8) ** 2
        if PRESS <= f < SHOTS[6]:                                  # party: beat bounce
            z += 0.012 * abs(math.sin((f - PRESS) * math.pi / 6))
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        c = np.array(led_col(f), np.float32)                       # edge glow in the LED colour
        k_ = 0.16 if mode(f) == "party" else 0.1
        x = x * (1 - k_ * vig) + c * k_ * vig
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
