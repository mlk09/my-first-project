#!/usr/bin/env python3
"""Renders MLexplorer Reel #01 "1 TAP = PARTY MODE" as an animated 20 s explainer.

Everything is drawn procedurally (no downloaded footage, images or music):
an ESP32 DevKit, a WS2812B strip with LED bloom and desk reflection, a phone
running the remote app, the wiring (data via 330R to GPIO 5, 5 V adapter,
common GND), the Bluetooth data packet, captions, an original 128 BPM synth
track and synthesised SFX. Scene cuts sit on the music's beat grid.

Run:   python3 reels/01-esp32-party-mode/build_reel.py [--voice my_vo.wav] [--preview]
Needs: pip install numpy scipy opencv-python-headless pillow ; ffmpeg on PATH.
Output: reels/01-esp32-party-mode/output/MLexplorer-Reel01-PartyMode.mp4
"""
import argparse
import colorsys
import math
import os
import subprocess
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
WORK = os.path.join(HERE, "work")
MONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEJAVU_CHARS = set("✓→Ω")   # glyphs Montserrat lacks; keep them in their own segment

W, H, FPS = 1080, 1920, 30
SR = 48000
BPM = 128
BEAT = 60 / BPM
T0 = 0.5                     # the first downbeat = the hook's "PARTY" burst


def kb(k):
    """Time of beat k on the music grid."""
    return T0 + k * BEAT


DUR = round(kb(42) + 0.12, 3)                    # ~20.3 s
CUTS = [0.0, kb(4), kb(7), kb(14), kb(20), kb(27), kb(34), kb(38), DUR]
SCENES = ["hook", "how", "parts", "wiring", "colours", "dataflow", "finale", "end"]

YELLOW = (1.0, 0.83, 0.0)
WHITE = (1.0, 1.0, 1.0)
RED = (0.95, 0.20, 0.18)
GREEN = (0.18, 0.86, 0.42)
BLUE = (0.20, 0.52, 1.0)
CYAN = (0.25, 0.9, 1.0)

N_LED = 20
STRIP_X0, STRIP_X1, STRIP_Y = 120, 960, 1430
LED_X = np.linspace(STRIP_X0 + 22, STRIP_X1 - 22, N_LED)

# phone taps: (time, button)
TAPS = [(T0 - 0.08, "PARTY"), (kb(21), "RED"), (kb(23), "GREEN"), (kb(25), "BLUE"),
        (kb(28), "RED"), (kb(35) - 0.08, "PARTY")]


# ============================================================== small utils
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def pop_scale(age):
    if age < 0:
        return 0.0
    if age < 0.08:
        return 0.6 + 0.55 * age / 0.08
    if age < 0.18:
        return 1.15 - 0.15 * (age - 0.08) / 0.10
    return 1.0


def hsv(h, s=1.0, v=1.0):
    return np.array(colorsys.hsv_to_rgb(h % 1.0, s, v), np.float32)


def bezier(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, np.float32) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def path_point(pts, u):
    """Point and unit tangent at fraction u of a polyline's length."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    d = min(max(u, 0), 1) * cum[-1]
    i = min(np.searchsorted(cum, d, side="right") - 1, len(seg) - 1)
    f = (d - cum[i]) / max(seg[i], 1e-6)
    p = pts[i] + f * (pts[i + 1] - pts[i])
    tng = (pts[i + 1] - pts[i]) / max(seg[i], 1e-6)
    return p, tng


def path_prefix(pts, u):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    d = min(max(u, 0), 1) * cum[-1]
    keep = pts[cum <= d]
    p, _ = path_point(pts, u)
    return np.vstack([keep, p[None]]) if len(keep) else p[None]


# ================================================================== sprites
@lru_cache(None)
def font(size, dejavu=False):
    return ImageFont.truetype(DEJAVU if dejavu else MONT, size)


def to_np(img):
    return np.asarray(img, np.uint8).copy()


@lru_cache(None)
def text_sprite(lines, size=110, stroke=None, max_w=860):
    """lines = ((("TEXT", (r,g,b)), ...), ...) -> RGBA sprite with stroke + shadow."""
    stroke = stroke if stroke is not None else max(4, size // 14)
    lh = int(size * 1.08)

    def fnt(seg, s):
        dj = any(ch in DEJAVU_CHARS for ch in seg)
        return font(int(s * (0.9 if dj else 1)), dj)

    widths = [sum(fnt(s, size).getlength(s) for s, _ in ln) for ln in lines]
    s_eff = size
    if max(widths) > max_w:
        s_eff = int(size * max_w / max(widths))
        widths = [sum(fnt(s, s_eff).getlength(s) for s, _ in ln) for ln in lines]
        lh = int(s_eff * 1.08)
        stroke = max(4, s_eff // 14)
    pad = stroke + 24
    w = int(max(widths)) + 2 * pad
    h = lh * len(lines) + 2 * pad
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(base), ImageDraw.Draw(shadow)
    for li, ln in enumerate(lines):
        x = pad + (w - 2 * pad - widths[li]) / 2
        y = pad + li * lh
        for seg, col in ln:
            f = fnt(seg, s_eff)
            yo = (s_eff - f.size) * 0.5
            c = tuple(int(255 * v) for v in col) + (255,)
            ds.text((x + 6, y + yo + 8), seg, font=f, fill=(0, 0, 0, 170),
                    stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
            d.text((x, y + yo), seg, font=f, fill=c, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
            x += f.getlength(seg)
    sh = to_np(shadow)
    sh[..., 3] = cv2.GaussianBlur(sh[..., 3], (0, 0), 6)
    out = Image.alpha_composite(Image.fromarray(sh), base)
    return to_np(out)


BTN = ["RED", "GREEN", "BLUE", "PARTY", "OFF"]
BTN_COL = {"RED": (229, 57, 53), "GREEN": (46, 204, 113), "BLUE": (47, 128, 237),
           "OFF": (58, 63, 85)}
PH_W, PH_H = 420, 820
BTN_Y0, BTN_H, BTN_GAP = 236, 92, 20


def btn_center(name):
    i = BTN.index(name)
    return PH_W / 2, BTN_Y0 + i * (BTN_H + BTN_GAP) + BTN_H / 2


@lru_cache(None)
def phone_sprite(pressed=None):
    img = Image.new("RGBA", (PH_W, PH_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, PH_W - 1, PH_H - 1), 58, fill=(14, 14, 18, 255),
                        outline=(78, 84, 104, 255), width=6)
    d.rounded_rectangle((14, 14, PH_W - 15, PH_H - 15), 46, fill=(9, 12, 26, 255))
    d.ellipse((PH_W / 2 - 9, 30, PH_W / 2 + 9, 48), fill=(30, 32, 40, 255))
    d.text((PH_W / 2, 92), "MLexplorer", font=font(36), fill=(255, 212, 0, 255), anchor="mm")
    d.text((PH_W / 2, 134), "LED REMOTE", font=font(22), fill=(235, 238, 255, 255), anchor="mm")
    d.rounded_rectangle((95, 162, PH_W - 95, 200), 19, fill=(18, 60, 40, 255))
    d.ellipse((112, 175, 124, 187), fill=(46, 230, 120, 255))
    d.text((PH_W / 2 + 10, 181), "CONNECTED", font=font(18), fill=(160, 255, 200, 255), anchor="mm")
    for name in BTN:
        cx, cy = btn_center(name)
        box = (50, cy - BTN_H / 2, PH_W - 50, cy + BTN_H / 2)
        k = 1.25 if name == pressed else 1.0
        if name == "PARTY":
            grad = np.zeros((BTN_H, int(box[2] - box[0]), 4), np.uint8)
            for x in range(grad.shape[1]):
                grad[:, x, :3] = (hsv(x / grad.shape[1] * 0.85, 0.85, 1.0) * 255 * min(k, 1.2) / 1.2 * 1.0).clip(0, 255)
            grad[..., 3] = 255
            mask = Image.new("L", (grad.shape[1], BTN_H), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, grad.shape[1] - 1, BTN_H - 1), 26, fill=255)
            g = Image.fromarray(grad)
            g.putalpha(mask)
            img.alpha_composite(g, (int(box[0]), int(box[1])))
        else:
            c = tuple(min(255, int(v * k)) for v in BTN_COL[name]) + (255,)
            d.rounded_rectangle(box, 26, fill=c)
        if name == pressed:
            d.rounded_rectangle(box, 26, outline=(255, 255, 255, 255), width=6)
        d.text((cx, cy), name, font=font(40), fill=(255, 255, 255, 255), anchor="mm",
               stroke_width=2, stroke_fill=(0, 0, 0, 120))
    return to_np(img)


ESP_W, ESP_H = 300, 560
ESP_PIN_Y = np.linspace(118, 514, 15)


def esp_pin(side, idx):
    """Pin position in sprite coordinates. Right side (top->bottom) of a 30-pin
    DevKit V1: D23 D22 TX0 RX0 D21 D19 D18 D5 TX2 RX2 D4 D2 D15 GND 3V3."""
    return (ESP_W - 24 if side == "R" else 24), ESP_PIN_Y[idx]


D5, GND_R = 7, 13


@lru_cache(None)
def esp32_sprite(blue_on=False):
    img = Image.new("RGBA", (ESP_W, ESP_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, ESP_W - 1, ESP_H - 1), 18, fill=(22, 24, 30, 255),
                        outline=(52, 56, 66, 255), width=3)
    d.rectangle((48, 14, 252, 92), fill=(24, 32, 52, 255))
    zig = [(62, 70), (62, 30), (92, 30), (92, 70), (122, 70), (122, 30), (152, 30), (152, 70),
           (182, 70), (182, 30), (212, 30), (212, 70), (238, 70)]
    d.line(zig, fill=(214, 170, 70, 255), width=5)
    for y in range(92, 268):
        v = int(196 + 22 * math.sin((y - 92) / 176 * math.pi))
        d.line((48, y, 252, y), fill=(v, v + 3, v + 8, 255))
    d.rectangle((48, 92, 252, 268), outline=(140, 146, 154, 255), width=3)
    d.text((150, 158), "ESP32-WROOM-32", font=font(18), fill=(70, 72, 78, 255), anchor="mm")
    d.text((150, 192), "Wi-Fi + BT", font=font(16), fill=(96, 98, 106, 255), anchor="mm")
    for side in "LR":
        for i in range(15):
            x, y = esp_pin(side, i)
            d.rectangle((x - 9, y - 9, x + 9, y + 9), fill=(10, 10, 12, 255))
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(222, 182, 84, 255))
    d.rectangle((118, 330, 182, 394), fill=(8, 8, 10, 255), outline=(40, 40, 46, 255))
    for (x, y) in ((80, 300), (210, 300), (80, 440), (215, 445), (150, 300)):
        d.rectangle((x, y, x + 16, y + 8), fill=(170, 150, 120, 255))
    d.rectangle((90, 418, 104, 428), fill=(255, 60, 50, 255))
    d.rectangle((196, 418, 210, 428), fill=(60, 140, 255, 255) if blue_on else (40, 48, 70, 255))
    for x in (64, 236):
        d.rectangle((x - 16, 482, x + 16, 514), fill=(190, 190, 196, 255))
        d.ellipse((x - 9, 489, x + 9, 507), fill=(40, 40, 44, 255))
    d.rectangle((118, 512, 182, 559), fill=(200, 204, 212, 255), outline=(120, 124, 130, 255))
    d.text((64, 470), "EN", font=font(12), fill=(200, 200, 200, 255), anchor="mm")
    d.text((236, 470), "BOOT", font=font(12), fill=(200, 200, 200, 255), anchor="mm")
    return to_np(img)


@lru_cache(None)
def adapter_sprite():
    img = Image.new("RGBA", (220, 320), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for x in (70, 132):
        d.rectangle((x, 0, x + 18, 44), fill=(196, 198, 204, 255))
    d.rounded_rectangle((0, 40, 219, 319), 30, fill=(20, 20, 24, 255), outline=(70, 72, 84, 255), width=4)
    d.text((110, 140), "5V", font=font(78), fill=(255, 255, 255, 255), anchor="mm")
    d.text((110, 214), "3A", font=font(46), fill=(255, 212, 0, 255), anchor="mm")
    d.text((110, 268), "DC OUTPUT", font=font(17), fill=(150, 152, 166, 255), anchor="mm")
    return to_np(img)


@lru_cache(None)
def background():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.array([0.020, 0.030, 0.085], np.float32)
    bot = np.array([0.045, 0.040, 0.120], np.float32)
    bg = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3)).copy()
    grid = np.zeros((H, W, 3), np.uint8)
    vx, vy, y0 = 540, 980, 1330           # desk plane with a perspective grid
    for i in range(-14, 15):
        cv2.line(grid, (vx + i * 18, y0), (vx + i * 150, H), (90, 60, 150), 2, cv2.LINE_AA)
    for k in range(1, 12):
        yy = int(y0 + (H - y0) * (k / 11) ** 1.6)
        cv2.line(grid, (0, yy), (W, yy), (90, 60, 150), 2, cv2.LINE_AA)
    bg[y0:] += np.array([0.010, 0.006, 0.030], np.float32)
    bg += grid.astype(np.float32) / 255 * 0.22
    cv2.line(bg, (0, y0), (W, y0), (0.25, 0.18, 0.45), 2, cv2.LINE_AA)
    return bg


# ================================================================ compositing
def blit(dst, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.003 or scale <= 0.01:
        return
    if rot:
        h, w = spr.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
        c, s = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(h * s + w * c) + 2, int(h * c + w * s) + 2
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        spr = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    elif abs(scale - 1) > 1e-3:
        h, w = spr.shape[:2]
        spr = cv2.resize(spr, (max(1, int(w * scale)), max(1, int(h * scale))),
                         interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    h, w = spr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb:
        return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32) / 255
    a = s[..., 3:4] * alpha
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + s[..., :3] * a


def blit_overlay(dst, ov):
    a = ov[..., 3:4].astype(np.float32) / 255
    if not a.any():
        return
    ys, xs = np.nonzero(ov[..., 3])
    ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    a = a[ya:yb, xa:xb]
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + ov[ya:yb, xa:xb, :3].astype(np.float32) / 255 * a


def caption(dst, t, t_in, lines, y, size=110, x=540, t_out=None):
    age = t - t_in
    if age < 0 or (t_out is not None and t >= t_out):
        return
    spr = text_sprite(lines, size)
    blit(dst, spr, x, y, pop_scale(age), min(1.0, age / 0.05))


def C(*segs):
    """One caption line from alternating text, colour pairs."""
    return tuple(segs)


# ============================================================ LEDs and light
class Light:
    """Quarter-resolution additive light layer (bloom, reflections, rays)."""
    Q = 4

    def __init__(self):
        self.core = np.zeros((H // self.Q, W // self.Q, 3), np.float32)
        self.wide = np.zeros_like(self.core)
        self.rays = np.zeros_like(self.core)

    def point(self, x, y, col, core=1.0, wide=1.0):
        xi, yi = int(x / self.Q), int(y / self.Q)
        if 0 <= xi < self.core.shape[1] and 0 <= yi < self.core.shape[0]:
            self.core[yi, xi] += np.asarray(col, np.float32) * core
            self.wide[yi, xi] += np.asarray(col, np.float32) * wide

    def apply(self, frame, ambient=None):
        acc = cv2.GaussianBlur(self.core, (0, 0), 2.6) * 30.0
        acc += cv2.GaussianBlur(self.wide, (0, 0), 14) * 150.0
        if self.rays.any():
            acc += cv2.GaussianBlur(self.rays, (0, 0), 1.6)
        frame += cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)
        if ambient is not None:
            frame += np.asarray(ambient, np.float32) * 0.11


def strip_colours(t, mode, col=None, fill=1.0, from_right=True, flash=0.0):
    cols = np.zeros((N_LED, 3), np.float32)
    if mode == "party":
        for i in range(N_LED):
            cols[i] = hsv(i / N_LED * 0.9 - t * 0.55)
    elif mode == "solid":
        n = int(round(fill * N_LED))
        idx = range(N_LED - n, N_LED) if from_right else range(n)
        for i in idx:
            cols[i] = col
    elif mode == "dim_rainbow":
        for i in range(N_LED):
            cols[i] = hsv(i / N_LED * 0.9) * 0.35
    return cols * (1 + flash)


def draw_strip(frame, light, cols, y=STRIP_Y, reflect=True, wires=True):
    x0, x1 = STRIP_X0, STRIP_X1
    cv2.rectangle(frame, (x0, y - 30), (x1, y + 30), (0.06, 0.06, 0.07), -1)
    cv2.rectangle(frame, (x0, y - 30), (x1, y + 30), (0.20, 0.20, 0.24), 2)
    if wires:
        for k, c in enumerate(((0.96, 0.77, 0.10), (0.90, 0.22, 0.20), (0.55, 0.57, 0.62))):
            yy = y - 14 + k * 14
            cv2.line(frame, (x1, yy), (x1 + 40, yy), (0.72, 0.48, 0.25), 6)
            cv2.line(frame, (x1 + 40, yy), (W + 10, yy + (k - 1) * 30), c, 8, cv2.LINE_AA)
    for i, x in enumerate(LED_X):
        c = cols[i]
        on = float(np.max(c))
        xi = int(x)
        cv2.rectangle(frame, (xi - 18, y - 18), (xi + 18, y + 18), (0.78, 0.78, 0.80), -1)
        if on > 0.02:
            core = np.clip(c * 0.65 + on * 0.45, 0, 1.6)
            cv2.circle(frame, (xi, y), 15, tuple(float(v) for v in core), -1, cv2.LINE_AA)
            light.point(x, y, c, 1.0, 1.0)
            if reflect:
                for k, a in ((70, 0.35), (100, 0.22), (130, 0.12)):
                    light.point(x, y + k, c, 0.25 * a, 0.9 * a)
        else:
            cv2.circle(frame, (xi, y), 13, (0.55, 0.55, 0.58), -1, cv2.LINE_AA)
            cv2.circle(frame, (xi, y), 4, (0.35, 0.35, 0.38), -1)
    return cols.mean(axis=0)


def rays(light, t, t0, cx, cy, n=22, dur=0.9, seed=0):
    age = t - t0
    if not 0 <= age < dur:
        return
    rng = np.random.default_rng(seed)
    a = (1 - age / dur) ** 2
    L = 300 + 1400 * ease_out(age / dur)
    for i in range(n):
        ang = rng.uniform(math.pi * 1.02, math.pi * 1.98)
        col = hsv(i / n) * a * rng.uniform(0.4, 1.0)
        p0 = (int(cx / 4), int(cy / 4))
        p1 = (int((cx + math.cos(ang) * L) / 4), int((cy + math.sin(ang) * L) / 4))
        cv2.line(light.rays, p0, p1, tuple(float(v) for v in col), 2, cv2.LINE_AA)


def sparkles(light, t, t0, n=40, seed=3):
    if t < t0:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        x, y = rng.uniform(80, 1000), rng.uniform(420, 1360)
        ph, sp = rng.uniform(0, 6.28), rng.uniform(3, 7)
        v = max(0.0, math.sin((t - t0) * sp + ph)) ** 6 * min(1, (t - t0) / 0.3)
        if v > 0.01:
            light.point(x, y, hsv(rng.uniform()) * 0.6 + 0.4, 0.5 * v, 0.06 * v)


# ======================================================================= phone
def draw_phone(frame, t, cx, cy, scale, rot=0.0):
    pressed = None
    for tt, name in TAPS:
        if tt <= t < tt + 0.32:
            pressed = name
    blit(frame, phone_sprite(pressed), cx, cy, scale, rot=rot)
    # finger approach + ripple
    for tt, name in TAPS:
        bx, by = btn_center(name)
        r = math.radians(-rot)
        dx, dy = (bx - PH_W / 2) * scale, (by - PH_H / 2) * scale
        px = cx + dx * math.cos(r) - dy * math.sin(r)
        py = cy + dx * math.sin(r) + dy * math.cos(r)
        a = t - tt
        if -0.28 < a < 0.0:
            k = (a + 0.28) / 0.28
            ov = np.zeros((H, W, 4), np.uint8)
            cv2.circle(ov, (int(px), int(py)), int(70 - 25 * k), (255, 255, 255, int(110 * k)), -1, cv2.LINE_AA)
            blit_overlay(frame, ov)
        elif 0 <= a < 0.45:
            k = a / 0.45
            ov = np.zeros((H, W, 4), np.uint8)
            cv2.circle(ov, (int(px), int(py)), int(30 + 120 * ease_out(k)),
                       (255, 255, 255, int(230 * (1 - k))), 6, cv2.LINE_AA)
            blit_overlay(frame, ov)


def esp_screen(cx, cy, scale, pin):
    x, y = pin
    return cx + (x - ESP_W / 2) * scale, cy + (y - ESP_H / 2) * scale


# ====================================================================== scenes
def scene_hook(t, f, L):
    flash = max(0.0, 1 - (t - T0) / 0.6) * 0.8 if t >= T0 else 0.0
    cols = strip_colours(t, "party", flash=flash) if t >= T0 else strip_colours(t, "off")
    amb = draw_strip(f, L, cols)
    rays(L, t, T0, 540, STRIP_Y, seed=1)
    draw_phone(f, t, 540, 870, 1.0)
    caption(f, t, 0.0, (C(("1 TAP =", WHITE)),), 245, 120)
    caption(f, t, T0, (C(("PARTY MODE", YELLOW)),), 375, 128)
    return amb


@lru_cache(None)
def frozen_hook():
    f = background().copy()
    L = Light()
    t = CUTS[1] - 0.01
    amb = scene_hook(t, f, L)
    L.apply(f, amb)
    f = cv2.GaussianBlur(np.clip(f, 0, 1), (0, 0), 9)
    return f * 0.38


def scene_how(t, f, L):
    f[:] = frozen_hook()
    a = t - CUTS[1]
    # rewind streaks
    if a < 0.35:
        ov = np.zeros((H, W, 4), np.uint8)
        rng = np.random.default_rng(int(a * 100))
        for _ in range(14):
            y = int(rng.uniform(0, H))
            cv2.line(ov, (0, y), (W, y), (255, 255, 255, int(90 * (1 - a / 0.35))), int(rng.uniform(2, 8)))
        blit_overlay(f, ov)
    caption(f, t, CUTS[1], (C(("KAISE?", YELLOW)),), 820, 190)
    caption(f, t, CUTS[1] + 2 * BEAT, (C(("SIRF ", WHITE), ("3 CHEEZEIN", CYAN)),), 1040, 96)
    return None


def scene_parts(t, f, L):
    s0 = CUTS[2]
    caption(f, t, s0, (C(("3 CHEEZEIN", YELLOW)),), 250, 110)
    items = [(kb(8), "esp"), (kb(9.5), "strip"), (kb(11), "adapter")]
    amb = None
    for i, (ti, kind) in enumerate(items):
        a = t - ti
        if a < 0:
            continue
        k = ease_out(a / 0.35)
        if kind == "esp":
            blit(f, esp32_sprite(False), 270, 800 + 80 * (1 - k), 0.78, k)
            caption(f, t, ti + 0.05, (C(("1 ", YELLOW), ("ESP32", WHITE)),), 1075, 62, x=270)
            caption(f, t, ti + 0.12, (C(("BLUETOOTH BUILT-IN", CYAN)),), 1140, 36, x=270)
        elif kind == "adapter":
            blit(f, adapter_sprite(), 810, 820 + 80 * (1 - k), 0.95, k)
            caption(f, t, ti + 0.05, (C(("3 ", YELLOW), ("5V ADAPTER", WHITE)),), 1075, 62, x=810)
            caption(f, t, ti + 0.12, (C(("2-3 AMP", CYAN)),), 1140, 36, x=810)
        else:
            cols = strip_colours(t, "party") * min(1.0, a / 0.3) * 0.75
            amb = draw_strip(f, L, cols, wires=False)
            caption(f, t, ti + 0.05, (C(("2 ", YELLOW), ("WS2812B RGB STRIP", WHITE)),), 1290, 58)
    return amb


ESP_W_POS = (300, 690, 0.8)       # wiring scene: ESP32 centre + scale
ADP_POS = (840, 700, 0.8)


def wiring_paths():
    ex, ey, es = ESP_W_POS
    d5 = esp_screen(ex, ey, es, esp_pin("R", D5))
    gnd = esp_screen(ex, ey, es, esp_pin("R", GND_R))
    ax, ay, asc = ADP_POS
    a_out = (ax, ay + 140 * asc)
    din, v5, gnd_s = (STRIP_X1 - 10, STRIP_Y - 14), (STRIP_X1 - 10, STRIP_Y), (STRIP_X1 - 10, STRIP_Y + 14)
    data = bezier(d5, (d5[0] + 260, d5[1] + 40), (din[0] - 380, din[1] - 260), din)
    pwr = bezier((a_out[0] - 14, a_out[1]), (a_out[0] - 14, a_out[1] + 220), (v5[0] + 10, v5[1] - 300), v5)
    g1 = bezier((a_out[0] + 14, a_out[1]), (a_out[0] + 30, a_out[1] + 260), (gnd_s[0] + 30, gnd_s[1] - 260), gnd_s)
    g2 = bezier(gnd, (gnd[0] + 140, gnd[1] + 60), (gnd_s[0] - 360, gnd_s[1] - 60), gnd_s)
    return data, pwr, g1, g2, d5, gnd


def draw_wire(ov, pts, col, w=12):
    p = pts.astype(np.int32).reshape(-1, 1, 2)
    if len(p) > 1:
        cv2.polylines(ov, [p], False, (0, 0, 0, 255), w + 6, cv2.LINE_AA)
        cv2.polylines(ov, [p], False, col + (255,), w, cv2.LINE_AA)


def draw_resistor(ov, pts, u=0.32):
    p, tg = path_point(pts, u)
    n = np.array([-tg[1], tg[0]])
    a, b = (p - tg * 34).astype(int), (p + tg * 34).astype(int)
    cv2.line(ov, tuple(a), tuple(b), (0, 0, 0, 255), 30, cv2.LINE_AA)
    cv2.line(ov, tuple(a), tuple(b), (214, 190, 150, 255), 24, cv2.LINE_AA)
    for off, c in ((-18, (255, 140, 0)), (-8, (255, 140, 0)), (2, (120, 70, 30)), (20, (212, 175, 55))):
        q = p + tg * off
        cv2.line(ov, tuple((q - n * 12).astype(int)), tuple((q + n * 12).astype(int)), c + (255,), 5)
    return p


def scene_wiring(t, f, L):
    s0 = CUTS[3]
    ex, ey, es = ESP_W_POS
    ax, ay, asc = ADP_POS
    blit(f, esp32_sprite(False), ex, ey, es)
    blit(f, adapter_sprite(), ax, ay, asc)
    amb = draw_strip(f, L, strip_colours(t, "off"), wires=False)
    data, pwr, g1, g2, d5, gnd = wiring_paths()
    ov = np.zeros((H, W, 4), np.uint8)
    pd = ease((t - kb(14.5)) / (BEAT * 1.6))
    pp = ease((t - kb(16.5)) / (BEAT * 1.2))
    pg = ease((t - kb(17.2)) / (BEAT * 1.4))
    if pp > 0:
        draw_wire(ov, path_prefix(pwr, pp), (229, 57, 53))
    if pg > 0:
        draw_wire(ov, path_prefix(g1, pg), (140, 145, 158))
        draw_wire(ov, path_prefix(g2, pg), (140, 145, 158))
    if pd > 0:
        draw_wire(ov, path_prefix(data, pd), (245, 197, 24))
        if pd > 0.4:
            rp = draw_resistor(ov, data)
    for pin, tt, col in ((d5, kb(14.5), (245, 197, 24)), (gnd, kb(17.2), (180, 185, 196))):
        if t >= tt:
            pulse = 0.5 + 0.5 * math.sin((t - tt) * 10)
            cv2.circle(ov, (int(pin[0]), int(pin[1])), int(14 + 6 * pulse), col + (255,), 4, cv2.LINE_AA)
    blit_overlay(f, ov)
    caption(f, t, s0, (C(("WIRING", YELLOW)),), 250, 110)
    caption(f, t, kb(15), (C(("DATA", (0.96, 0.77, 0.10)), (" → ", WHITE), ("GPIO 5", WHITE)),), 1010, 58, x=560)
    if pd > 0.4:
        caption(f, t, kb(16), (C(("330Ω", WHITE)),), int(rp[1]) - 60, 40, x=int(rp[0]) + 20)
    caption(f, t, kb(16.5), (C(("5V", RED), (" → ", WHITE), ("STRIP", WHITE)),), 1180, 50, x=760)
    caption(f, t, kb(18), (C(("GND COMMON ", WHITE), ("✓", GREEN)),), 372, 76)
    return amb


def scene_colours(t, f, L):
    seq = [(kb(21), "RED", RED), (kb(23), "GREEN", GREEN), (kb(25), "BLUE", BLUE)]
    cur = None
    for tt, name, col in seq:
        if t >= tt:
            cur = (tt, name, col)
    if cur:
        a = t - cur[0]
        cols = strip_colours(t, "solid", np.array(cur[2], np.float32), flash=max(0, 0.7 - a * 2))
    else:
        cols = strip_colours(t, "off")
    amb = draw_strip(f, L, cols)
    draw_phone(f, t, 540, 860, 0.82)
    if cur:
        caption(f, t, cur[0], (C((cur[1], cur[2])),), 270, 150)
    else:
        caption(f, t, CUTS[4], (C(("APP ", WHITE), ("CONNECTED", GREEN)),), 270, 90)
    return amb


DF_PH = (230, 640, 0.52)
DF_ESP = (800, 660, 0.72)


def df_paths():
    px, py, ps = DF_PH
    ex, ey, es = DF_ESP
    a = (px + PH_W * ps / 2 + 10, py - 60)
    b = (ex - ESP_W * es / 2 - 10, ey - 120)
    air = bezier(a, (a[0] + 120, a[1] - 260), (b[0] - 120, b[1] - 260), b)
    d5 = esp_screen(ex, ey, es, esp_pin("R", D5))
    din = (STRIP_X1 - 10, STRIP_Y - 14)
    wire = bezier(d5, (d5[0] + 140, d5[1] + 60), (din[0] + 60, din[1] - 360), din)
    return air, wire


def scene_dataflow(t, f, L):
    s0 = CUTS[5]
    t_send, t_esp, t_strip, t_fill = kb(28), kb(29.5), kb(30.5), kb(31)
    ex, ey, es = DF_ESP
    air, wire = df_paths()
    ov = np.zeros((H, W, 4), np.uint8)
    draw_wire(ov, wire, (245, 197, 24), 9)
    blit_overlay(f, ov)
    blue = t_esp <= t < t_esp + 0.35
    blit(f, esp32_sprite(blue), ex, ey, es)
    if blue:
        L.point(*esp_screen(ex, ey, es, (203, 423)), (0.25, 0.5, 1.0), 2.0, 0.4)
    L.point(*esp_screen(ex, ey, es, (97, 423)), (1.0, 0.2, 0.15), 0.8, 0.1)
    fill = ease((t - t_strip) / (t_fill - t_strip + 0.15))
    cols = strip_colours(t, "solid", np.array(RED, np.float32), fill=fill) if t >= t_strip else strip_colours(t, "off")
    amb = draw_strip(f, L, cols)
    draw_phone(f, t, *DF_PH)
    # Bluetooth waves + packet
    if t_send <= t < t_esp + 0.2:
        ov = np.zeros((H, W, 4), np.uint8)
        a0 = air[0]
        for k in range(3):
            r = ((t - t_send) * 260 + k * 60) % 180 + 30
            al = int(200 * (1 - (r - 30) / 180))
            cv2.ellipse(ov, (int(a0[0]), int(a0[1])), (int(r), int(r)), 0, -60, 60,
                        (90, 190, 255, al), 5, cv2.LINE_AA)
        blit_overlay(f, ov)
    pk = None
    if t_send <= t < t_esp:
        pk, _ = path_point(air, ease((t - t_send) / (t_esp - t_send)))
    elif t_esp <= t < t_strip:
        pk, _ = path_point(wire, ease((t - t_esp) / (t_strip - t_esp)))
    if pk is not None:
        L.point(pk[0], pk[1], (1.0, 0.85, 0.2), 4.0, 0.6)
        blit(f, text_sprite((C(("R", YELLOW)),), 90), pk[0], pk[1])
    caption(f, t, s0, (C(("ANDAR KYA ", WHITE), ("HOTA HAI?", YELLOW)),), 250, 92)
    caption(f, t, t_send, (C(("APP: ", WHITE), ("'R'", YELLOW), (" BHEJA", WHITE)),), 1010, 64, t_out=t_esp)
    caption(f, t, t_esp, (C(("ESP32: ", WHITE), ("READ KIYA", CYAN)),), 1010, 64, t_out=t_fill)
    caption(f, t, t_fill, (C(("HAR LED KA ", WHITE), ("APNA CHIP", YELLOW)),), 1010, 64)
    caption(f, t, t_fill + 0.1, (C(("= RED", RED),),), 1120, 64)
    return amb


def scene_finale(t, f, L):
    tb = kb(35)
    flash = max(0.0, 1 - (t - tb) / 0.6) * 0.9 if t >= tb else 0.0
    cols = strip_colours(t, "party", flash=flash) if t >= tb else strip_colours(t, "solid", np.array(RED, np.float32))
    amb = draw_strip(f, L, cols)
    rays(L, t, tb, 540, STRIP_Y, seed=5)
    sparkles(L, t, tb)
    draw_phone(f, t, 330, 840, 0.72, rot=7)
    caption(f, t, CUTS[6], (C(("'P'", YELLOW), (" BHEJA =", WHITE)),), 250, 100)
    caption(f, t, tb, (C(("PARTY MODE ", YELLOW), ("✓", GREEN)),), 372, 110)
    return amb


def scene_end(t, f, L):
    cols = strip_colours(t, "party")
    amb = draw_strip(f, L, cols)
    sparkles(L, t, CUTS[7] - 1, n=30, seed=9)
    s0 = CUTS[7]
    caption(f, t, s0, (C(("NEXT EPISODE", YELLOW)),), 330, 64)
    caption(f, t, s0 + 0.12, (C(("PHONE ", WHITE), ("TILT", CYAN)),), 470, 120)
    caption(f, t, s0 + 0.24, (C(("= COLOUR?", WHITE)),), 600, 120)
    caption(f, t, kb(39.5), (C(("TILT", CYAN), (" ya ", WHITE), ("MUSIC?", YELLOW)),), 800, 84)
    caption(f, t, kb(39.5) + 0.1, (C(("COMMENT KARO", WHITE)),), 900, 64)
    a = t - kb(40.5)
    if a >= 0:
        s = pop_scale(a)
        ov = np.zeros((H, W, 4), np.uint8)
        cv2.rectangle(ov, (190, 1050), (890, 1250), (255, 212, 0, 255), -1, cv2.LINE_AA)
        ov = cv2.GaussianBlur(ov, (0, 0), 0.8)
        sub = ov[1050:1251, 190:891].copy()
        blit(f, sub, 540, 1150, s)
        blit(f, text_sprite((C(("FOLLOW", (0.05, 0.05, 0.1))),), 54, stroke=0), 540, 1105, s)
        blit(f, text_sprite((C(("MLexplorer", (0.05, 0.05, 0.1))),), 84, stroke=0), 540, 1185, s)
    return amb


SCENE_FN = {"hook": scene_hook, "how": scene_how, "parts": scene_parts, "wiring": scene_wiring,
            "colours": scene_colours, "dataflow": scene_dataflow, "finale": scene_finale, "end": scene_end}

# global camera: zoom punches (time, amount) and shakes (time, strength)
PUNCH = [(T0, 0.10), (kb(4), 0.08), (kb(21), 0.04), (kb(23), 0.04), (kb(25), 0.04), (kb(35), 0.11)]
SHAKE = [(T0, 14), (kb(4), 10), (kb(35), 16)]
FLASH_AT = [T0, kb(4), kb(35)]


def render(i):
    t = i / FPS
    si = max(k for k in range(len(SCENES)) if CUTS[k] <= t)
    f = background().copy()
    L = Light()
    amb = SCENE_FN[SCENES[si]](t, f, L)
    L.apply(f, amb)
    if SCENES[si] != "end":
        blit(f, text_sprite((C(("ML", YELLOW), ("explorer", WHITE)),), 34, stroke=3), 140, 170, 1.0, 0.8)
    # camera
    z = 1.0 + 0.05 * (1 - ease((t - CUTS[si]) / 0.3))          # settle-in after each cut
    if SCENES[si] == "finale":
        z += 0.06 * ease((t - CUTS[si]) / (CUTS[si + 1] - CUTS[si]))
    for tt, amt in PUNCH:
        if 0 <= t - tt < 0.35:
            z += amt * (1 - (t - tt) / 0.35) ** 2
    dx = dy = 0.0
    for tt, s in SHAKE:
        a = t - tt
        if 0 <= a < 0.3:
            k = s * (1 - a / 0.3)
            dx += k * math.sin(a * 90)
            dy += k * math.cos(a * 73)
    M = np.array([[z, 0, (1 - z) * W / 2 + dx], [0, z, (1 - z) * H / 2 + dy]], np.float32)
    f = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fl = 0.0
    for tt in FLASH_AT:
        if 0 <= t - tt < 0.15:
            fl = max(fl, 0.55 * (1 - (t - tt) / 0.15))
    for c in CUTS[1:-1]:
        if 0 <= t - c < 0.07:
            fl = max(fl, 0.25 * (1 - (t - c) / 0.07))
    f = np.clip(f, 0, 1)
    if fl:
        f = f + (1 - f) * fl
    return (f * 255 + 0.5).astype(np.uint8).tobytes()


# ======================================================================= audio
def env_exp(n, rate):
    return np.exp(-np.arange(n) / SR * rate)


def noise(n, seed=0):
    return np.random.default_rng(seed).standard_normal(n)


def filt(x, kind, fq, order=4):
    return signal.sosfilt(signal.butter(order, fq, btype=kind, fs=SR, output="sos"), x)


def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i < 0:
        x, i = x[-i:], 0
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += gain * x


def kick():
    n = int(0.38 * SR)
    t = np.arange(n) / SR
    fr = 45 + 120 * np.exp(-t * 32)
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 8)
    x[:96] += noise(96, 1) * 0.4 * np.linspace(1, 0, 96)
    return np.tanh(1.6 * x)


def clap():
    n = int(0.25 * SR)
    x = filt(noise(n, 2), "bandpass", [900, 3200])
    e = sum(np.roll(env_exp(n, 30), int(d * SR)) * (np.arange(n) >= d * SR) for d in (0, .009, .018))
    return x * e * 0.9


def hat(seed):
    n = int(0.06 * SR)
    return filt(noise(n, seed), "highpass", 7000) * env_exp(n, 70)


def synth_note(freq, dur, kind="saw", decay=10.0, cutoff=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "saw":
        x = signal.sawtooth(2 * np.pi * freq * t) + 0.5 * signal.sawtooth(2 * np.pi * freq * 1.005 * t)
    elif kind == "square":
        x = signal.square(2 * np.pi * freq * t, 0.35)
    else:
        x = signal.sawtooth(2 * np.pi * freq * t, 0.5)
    x *= np.exp(-t * decay) * np.minimum(1, t / 0.003)
    return filt(x, "lowpass", cutoff, 2) if cutoff else x


def music(total):
    """Original 128 BPM synth-pop loop (Am-F-C-G), first downbeat at T0."""
    n = int(total * SR)
    drums, tonal = np.zeros(n), np.zeros(n)
    chords = [(110.0, [220.0, 261.63, 329.63]), (87.31, [174.61, 220.0, 261.63]),
              (130.81, [261.63, 329.63, 392.0]), (98.0, [196.0, 246.94, 293.66])]
    k, c = kick(), clap()
    b = 0
    while kb(b) < total:
        t = kb(b)
        bar, pos = divmod(b, 4)
        root, tones = chords[bar % 4]
        place(drums, k, t, 1.0)
        if pos in (1, 3):
            place(drums, c, t, 0.55)
        for s in range(4):
            place(drums, hat(b * 4 + s), t + s * BEAT / 4, 0.32 if s == 2 else 0.14)
        place(tonal, synth_note(root / 2, BEAT * 0.45, "saw", 6, 380), t + BEAT / 2, 0.55)
        for s in range(4):
            fr = tones[[0, 1, 2, 1][s]] * 2
            place(tonal, synth_note(fr, BEAT / 4 * 1.6, "square", 18, 3200), t + s * BEAT / 4, 0.10)
        if pos == 0:  # pad
            for fr in tones:
                place(tonal, synth_note(fr, BEAT * 4, "tri", 0.6, 1800), t, 0.06)
        b += 1
    tb = (np.arange(n) / SR - T0) % BEAT
    mix = drums * 0.9 + tonal * (1 - 0.55 * np.exp(-tb * 14))
    # "KAISE?" freeze: muffle the track like a paused record
    a, z = int(CUTS[1] * SR), int((CUTS[2] - 0.05) * SR)
    seg = filt(mix[a:z], "lowpass", 500, 2) * 0.7
    xf = int(0.03 * SR)
    ramp = np.linspace(0, 1, xf)
    seg[:xf] = mix[a:a + xf] * (1 - ramp) + seg[:xf] * ramp
    seg[-xf:] = seg[-xf:] * (1 - ramp) + mix[z - xf:z] * ramp
    mix[a:z] = seg
    fade = int(0.25 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def whoosh(dur=0.32, seed=0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = noise(n, seed)
    e = np.sin(np.pi * t ** 0.7) ** 2
    return (filt(x, "bandpass", [300, 1200]) * (1 - t) + filt(x, "bandpass", [1200, 6000]) * t) * e * 1.4


def pop():
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    fr = 500 + 900 * t / t[-1]
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 70) * 0.8


def tap():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (filt(noise(n, 11), "bandpass", [1500, 6000]) * np.exp(-t * 160) * 0.9
            + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) * 0.4)


def boom():
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    fr = 42 + 70 * np.exp(-t * 12)
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 3.5)
    x += filt(noise(n, 7), "lowpass", 1500) * np.exp(-t * 18) * 0.6
    return np.tanh(1.8 * x)


def ding():
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * fr * t) * np.exp(-t * d)
            for fr, a, d in ((2637, 1.0, 4.0), (5274, 0.35, 7.0), (3951, 0.2, 9.0)))
    return x * np.minimum(1, t / 0.002) * 0.5


def sparkle_sfx(seed=4):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for _ in range(16):
        s = int(rng.uniform(0, 0.6) * SR)
        fr = rng.uniform(3000, 7000)
        m = n - s
        tt = np.arange(m) / SR
        x[s:] += np.sin(2 * np.pi * fr * tt) * np.exp(-tt * 25) * 0.25
    return x * np.exp(-t * 2)


def riser(dur):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = filt(noise(n, 9), "highpass", 1500) * t ** 2 * 0.5
    fr = 200 + 1400 * t ** 2
    return x + np.sin(2 * np.pi * np.cumsum(fr) / SR) * t ** 2 * 0.25


def blip(fr):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    return signal.square(2 * np.pi * fr * t) * np.exp(-t * 50) * 0.25


def scratch():
    n = int(0.35 * SR)
    t = np.linspace(0, 1, n)
    fr = 900 * (1 - t) ** 2 + 80
    x = signal.sawtooth(2 * np.pi * np.cumsum(fr) / SR) * (1 - t)
    return filt(x, "bandpass", [200, 3000]) * 0.6


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    place(buf, riser(T0), 0, 0.5)
    for tt, _ in TAPS:
        place(buf, tap(), tt, 0.8)
    for tt in (T0, kb(35)):
        place(buf, boom(), tt, 0.9)
        place(buf, sparkle_sfx(), tt + 0.05, 0.7)
    place(buf, scratch(), CUTS[1], 0.8)
    place(buf, boom()[: int(0.5 * SR)], CUTS[1] + 0.02, 0.5)
    for i, c in enumerate(CUTS[2:-1]):
        if c != kb(34):
            place(buf, whoosh(0.30, i), c - 0.22, 0.5)
    for tt in (kb(8), kb(9.5), kb(11), kb(15), kb(16), kb(16.5), kb(28), kb(29.5), kb(31),
               kb(38), kb(38) + 0.12, kb(38) + 0.24, kb(39.5)):
        place(buf, pop(), tt, 0.35)
    for tt in (kb(21), kb(23), kb(25)):
        place(buf, boom()[: int(0.45 * SR)], tt, 0.45)
    for tt in (kb(18), kb(40.5)):
        place(buf, ding(), tt, 0.55)
    for k in range(10):                              # data packet blips
        place(buf, blip(1200 + 120 * k), kb(28) + k * (kb(30.5) - kb(28)) / 10, 0.5)
    place(buf, riser(kb(35) - kb(33)), kb(33), 0.6)
    return buf


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", "pipe:", path], input=pcm.tobytes(), check=True)


def build_audio(voice=None):
    total = DUR + 0.05
    mus, sfx = os.path.join(WORK, "music.wav"), os.path.join(WORK, "sfx.wav")
    write_wav(mus, music(total))
    write_wav(sfx, sfx_track(total) * 0.9)
    out = os.path.join(WORK, "mix.wav")
    tail = f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,apad=whole_dur={DUR:.3f}[out]"
    if voice:
        fc = ("[2:a]highpass=f=85,acompressor=threshold=-20dB:ratio=3:attack=4:release=70:makeup=2,"
              "loudnorm=I=-16:TP=-2,aformat=sample_rates=48000:channel_layouts=stereo,asplit[vox][key];"
              "[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
              "[mus][key]sidechaincompress=threshold=0.05:ratio=4:attack=10:release=260[musd];"
              "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.7[sfx];"
              "[vox][musd][sfx]amix=inputs=3:normalize=0," + tail)
        inputs = ["-i", mus, "-i", sfx, "-i", voice]
    else:
        fc = ("[0:a]loudnorm=I=-17:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
              "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.9[sfx];"
              "[mus][sfx]amix=inputs=2:normalize=0," + tail)
        inputs = ["-i", mus, "-i", sfx]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]",
                    "-t", f"{DUR:.3f}", out], check=True)
    return out


# ======================================================================= main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", help="optional voice-over WAV/M4A, starting at 0 s")
    ap.add_argument("--preview", action="store_true", help="write a few stills only")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    n = int(round(DUR * FPS))
    if args.preview:
        for t in (0.2, 1.0, 3.2, 5.9, 9.4, 10.6, 14.4, 15.4, 17.3, 19.9):
            fr = np.frombuffer(render(int(t * FPS)), np.uint8).reshape(H, W, 3)
            cv2.imwrite(os.path.join(WORK, f"still_{t:05.1f}.jpg"), fr[..., ::-1])
        print("stills in", WORK)
        return
    mix = build_audio(args.voice)
    out = os.path.join(OUT, "MLexplorer-Reel01-PartyMode.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:", "-i", mix,
                           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                           "-profile:v", "high", "-movflags", "+faststart",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    with Pool(args.workers) as pool:
        for k, buf in enumerate(pool.imap(render, range(n), chunksize=4)):
            ff.stdin.write(buf)
            if k % 60 == 0:
                print(f"frame {k}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
