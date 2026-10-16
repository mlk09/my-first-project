#!/usr/bin/env python3
"""Shared engine for Python Ki Pathshala glass-board shorts (the EP03 look).

Look: black glass lightboard with moving reflections, glowing handwriting
(bloom) and a shining marker nib, a yellow title box on top, a vertical
"EP xx" on the left, the snake mascot giving hints, a camera that follows the
pen, duster wipes between boards, a LIKE / SHARE / SUBSCRIBE end screen, and
the episode thumbnail held for the first second (so Facebook picks it as the
cover). Sound: marker squeaks, key clicks for code, thuds, pops, dings,
risers and booms over an original lo-fi bed. Master -14 LUFS.

An episode script defines its content as module attributes and calls
`run(sys.modules[__name__])`. Attributes used:

  NAME, OUT, WORK, TITLE1, TITLE2, EP_LABEL, NEXT_TITLE
  DUR (lesson length), SCENES [(name, start)], SCENE_FN {name: fn(L, t, tl)}
  VO_AT {key: start}         voice lines (work/vo_<key>.wav), lesson time
  WIPE_CUTS [cut indices]    duster wipes into those scenes
  FOLLOW {scene: zoom}       scenes where the camera follows the pen
  HINTS [(t, text, mood)]    mascot bubbles; QUIET [(t0, t1)] hides them
  FLASHES [(t, amp, dur, rgb)], PUNCHES [(t, amp)], SHAKES [(t, amp)]
  MUSIC_GAPS [(t0, t1)]      silences in the music (before a boom)
  sfx(buf)                   episode-specific SFX (lesson time)
  thumb(L)                   draws the thumbnail content on a W x H layer
Writes are registered with `reg()` / `Line()` at import time of the episode.
"""
import argparse
import importlib.util
import math
import os
import subprocess
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("ep02build", os.path.join(HERE, "ep02-print", "build.py"))
E2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E2)                 # fonts, mascot, base SFX
font, ss, paste, with_shadow = E2.font, E2.ss, E2.paste, E2.with_shadow
clamp, ease, ease_out, pop, back_out = E2.clamp, E2.ease, E2.ease_out, E2.pop, E2.back_out
mascot, bubble = E2.mascot, E2.bubble
add, env_exp, lp, hp, bp = E2.add, E2.env_exp, E2.lp, E2.hp, E2.bp

W, H, FPS = 1080, 1920, 30
SR = 48000
INTRO = 1.0                  # thumbnail hold at the start of the video
WIPE = 0.45
BLOOM = 0.6

GLASS = (10, 13, 19)
CHALK = (238, 244, 255)
YEL = (255, 214, 60)
CYAN = (70, 220, 255)
PINK = (255, 96, 176)
GREEN = (100, 245, 150)
ORANGE = (255, 150, 60)
RED = (255, 80, 80)
DIM = (150, 160, 180)
NAVY = (15, 22, 45)
WHITE = (255, 255, 255)
PURPLE = (190, 140, 255)

EP = None                    # the episode module, set by run()


# ---------------------------------------------------------------- timeline
def cuts():
    return [s for _, s in EP.SCENES] + [EP.DUR]


def scene_at(t):
    c = cuts()
    for i in range(len(EP.SCENES)):
        if c[i] <= t < c[i + 1]:
            return EP.SCENES[i][0], t - c[i], i
    return EP.SCENES[-1][0], t - c[-2], len(EP.SCENES) - 1


def scene_start(name):
    return dict(EP.SCENES)[name]


@lru_cache(None)
def vo_len(work, key):
    p = os.path.join(work, f"vo_{key}.wav")
    return sf.info(p).duration if os.path.exists(p) else 2.5


def said(work, vo_at, key, spoken, word, lead=0.25):
    """Approximate moment `word` is spoken in a VO line (character-proportional)."""
    return vo_at[key] + vo_len(work, key) * spoken.index(word) / len(spoken) - lead


# ---------------------------------------------------------------- write registry (drives pen, camera, squeaks)
WRITES = []


def reg(t0, x, y, s, size, which="hand", cps=20.0):
    WRITES.append((t0, cps, x, y, s, size, which))
    return t0 + len(s) / cps


def text_w(s, size, which):
    return font(size, which).getlength(s)


def pen_at(t):
    for t0, cps, x, y, s, size, which in WRITES:
        t1 = t0 + len(s) / cps
        if t0 <= t < t1:
            n = (t - t0) * cps
            return x + text_w(s[: int(n)], size, which) + 6, y + size * 0.62
    return None


class Line:
    """A line made of coloured segments that is written left to right (registered on creation)."""

    def __init__(self, segs, x, y, t0, size=44, which="mono", cps=18.0):
        self.segs, self.x, self.y, self.size, self.which, self.cps = segs, x, y, size, which, cps
        self.parts = []
        tt, xx = t0, x
        for s, col in segs:
            if s:
                reg(tt, xx, y, s, size, which, cps)
            self.parts.append((tt, xx, s, col))
            tt += len(s) / cps
            xx += text_w(s, size, which)
        self.t0, self.end, self.width = t0, tt, xx - x

    def draw(self, L, t, a=1.0):
        for tt, xx, s, col in self.parts:
            if s and t > tt:
                n = min(len(s), int((t - tt) * self.cps))
                if n > 0:
                    im = gtext(s, self.size, col, self.which, n)
                    if a < 0.99:
                        paste(L, im, xx - 8, self.y - 8, 1, a, anchor="lt")
                    else:
                        L.alpha_composite(im, (int(xx) - 8, int(self.y) - 8))

    def x_of(self, k):
        """x of the start of segment k."""
        return self.parts[k][1]


# ---------------------------------------------------------------- drawing helpers
@lru_cache(None)
def gtext(s, size, color, which="hand", n=None):
    s2 = s if n is None else s[:n]
    f = font(size, which)
    x0, y0, x1, y1 = f.getbbox(s if s else " ")
    im = Image.new("RGBA", (max(4, int(f.getlength(s)) + 30), y1 + 30), (0, 0, 0, 0))
    if s2:
        ImageDraw.Draw(im).text((8, 8), s2, font=f, fill=color + (255,))
    return im


def write(L, t, t0, x, y, s, size, color, which="hand", cps=20.0):
    n = int(max(0.0, t - t0) * cps)
    if n <= 0:
        return False
    L.alpha_composite(gtext(s, size, color, which, min(n, len(s))), (int(x) - 8, int(y) - 8))
    return n >= len(s)


def underline(L, t, t0, x, y, w, col, dur=0.3, width=6):
    u = ease((t - t0) / dur)
    if u > 0:
        ImageDraw.Draw(L).line([(x, y), (x + w * u, y)], fill=col + (255,), width=width)


def circled(L, n, cx, cy, col, s=1.0):
    r = int(34 * s)
    if r <= 2:
        return
    d = ImageDraw.Draw(L)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (255,), width=5)
    d.text((cx, cy + 1), str(n), font=font(int(44 * s), "mont"), fill=col + (255,), anchor="mm")


def glow_box(L, box, col, u=1.0, w=5, r=22, fill_a=40):
    if u <= 0:
        return
    d = ImageDraw.Draw(L)
    x0, y0, x1, y1 = box
    if u >= 1:
        d.rounded_rectangle(box, r, fill=col + (fill_a,), outline=col + (255,), width=w)
        return
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    left = 2 * ((x1 - x0) + (y1 - y0)) * u
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if left <= 0:
            break
        f = min(1, left / seg)
        d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=col + (255,), width=w)
        left -= seg


def arrow(L, p0, p1, u, col, w=6):
    if u <= 0:
        return
    d = ImageDraw.Draw(L)
    x = p0[0] + (p1[0] - p0[0]) * clamp(u)
    y = p0[1] + (p1[1] - p0[1]) * clamp(u)
    d.line([p0, (x, y)], fill=col + (255,), width=w)
    if u >= 1:
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for s in (-1, 1):
            d.line([(x, y), (x - 26 * math.cos(a + s * 0.5), y - 26 * math.sin(a + s * 0.5))], fill=col + (255,),
                   width=w)


@lru_cache(None)
def chip(s, col, size=56, which="mono"):
    f = font(size, which)
    w, h = int(f.getlength(s)) + 50, size + 34
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=(20, 26, 38, 235), outline=col + (255,), width=4)
    d.text((45, 26 if which == "mono" else 22), s, font=f, fill=col + (255,))
    return im


@lru_cache(None)
def solid_pill(s, size, fg, bg, which="mont", padx=34, pady=14):
    f = font(size, which)
    x0, y0, x1, y1 = f.getbbox(s)
    w, h = x1 - x0 + 2 * padx, y1 - y0 + 2 * pady
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=bg + (255,))
    im = ss(im, w, h)
    ImageDraw.Draw(im).text((padx - x0, pady - y0), s, font=f, fill=fg + (255,))
    return im


@lru_cache(None)
def keycap(label="ENTER", size=46):
    f = font(size, "mont")
    w, h = int(f.getlength(label)) + 60, size + 50
    im = Image.new("RGBA", (w + 20, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 18, 10 + w, 18 + h), 18, fill=(40, 46, 60, 255))
    d.rounded_rectangle((10, 6, 10 + w, 6 + h), 18, fill=(70, 78, 96, 255), outline=CHALK + (255,), width=3)
    d.text((10 + w / 2, 6 + h / 2), label, font=f, fill=CHALK + (255,), anchor="mm")
    return im


def panel(L, box, title, t_on, t, col=CYAN, run_at=None):
    """Glass code editor / terminal panel with a title and an optional ▶ Run button."""
    u = ease((t - t_on) / 0.35)
    if u <= 0:
        return
    glow_box(L, box, col, u, w=4, r=24, fill_a=30)
    if u >= 1:
        x0, y0, x1, y1 = box
        d = ImageDraw.Draw(L)
        for k, c in enumerate((RED, YEL, GREEN)):
            d.ellipse((x0 + 26 + k * 32, y0 + 22, x0 + 46 + k * 32, y0 + 42), fill=c + (255,))
        L.alpha_composite(gtext(title, 30, DIM, "mono"), (x0 + 140, y0 + 12))
        d.line([(x0 + 4, y0 + 62), (x1 - 4, y0 + 62)], fill=col + (90,), width=2)
        if run_at is not None:
            press = 1 - 0.15 * math.exp(-((t - run_at) / 0.06) ** 2)
            paste(L, solid_pill("▶ Run", 30, NAVY, GREEN, "mono", 18, 8), x1 - 90, y0 + 32, press)


# ---------------------------------------------------------------- board background
@lru_cache(None)
def glass_base():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array(GLASS, np.float32)[None, None, :] * np.ones((H, W, 1), np.float32)
    vign = np.clip(1 - np.hypot((xx - W / 2) / W, (yy - H * 0.45) / H) * 1.1, 0, 1)[..., None]
    img = base * (0.7 + 0.6 * vign) + np.array((14, 22, 40), np.float32) * vign * 0.8
    rng = np.random.default_rng(9)
    sm = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(sm)
    for _ in range(14):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        d.line([(x + k * 50, y + 20 * math.sin(k)) for k in range(7)], fill=int(rng.uniform(10, 22)), width=22,
               joint="curve")
    img += np.asarray(sm.filter(ImageFilter.GaussianBlur(10)), np.float32)[..., None] * np.array((0.6, 0.7, 1.0))
    img += rng.normal(0, 1.2, (H, W, 1)).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


GRID = np.mgrid[0:H, 0:W].astype(np.float32)


def gloss(frame, t):
    yy, xx = GRID
    g = np.zeros((H, W), np.float32)
    for k, (w, a, sp) in enumerate(((180, 0.06, 40), (60, 0.05, 55))):
        pos = (xx * 0.6 + yy * 0.8 - (t * sp + k * 900)) % 2600 - 1300
        g += a * np.exp(-(pos / w) ** 2)
    g += np.clip(1 - yy / (H * 0.5), 0, 1) * 0.04
    return np.clip(frame.astype(np.float32) + g[..., None] * 255, 0, 255).astype(np.uint8)


def bloom(rgba):
    a = np.asarray(rgba, np.float32)
    rgb = a[..., :3] * (a[..., 3:4] / 255)
    small = cv2.resize(rgb, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(small, (0, 0), 3) * 0.9 + cv2.GaussianBlur(small, (0, 0), 9) * 0.7
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)


def composite(L, bloom_k=BLOOM, base_k=1.0, ink_k=1.0):
    base = glass_base().astype(np.float32) * base_k
    la = np.asarray(L, np.float32)
    al = la[..., 3:4] / 255
    frame = (base + bloom(L) * bloom_k) * (1 - al) + la[..., :3] * al * ink_k
    return np.clip(frame, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- fixed UI
@lru_cache(None)
def title_box(t1, t2):
    f1, f2 = font(44, "mont"), font(30, "hand")
    w = int(max(f1.getlength(t1), f2.getlength(t2))) + 60
    im = Image.new("RGBA", (w, 118), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 117), 18, fill=YEL + (255,))
    d.text((w / 2, 36), t1, font=f1, fill=NAVY + (255,), anchor="mm")
    d.text((w / 2, 88), t2, font=f2, fill=NAVY + (255,), anchor="mm")
    return with_shadow(im, blur=10, alpha=120, pad=20)


@lru_cache(None)
def side_ep(label):
    im = Image.new("RGBA", (300, 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((150, 40), label, font=font(64, "mont"), fill=YEL + (255,), anchor="mm")
    return im.rotate(90, expand=True)


@lru_cache(None)
def marker_pen():
    S = 2
    w, h = 70, 260
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10 * S, 0, 60 * S, 190 * S), 18 * S, fill=(235, 238, 245, 255), outline=(120, 128, 140, 255),
                        width=2 * S)
    d.rectangle((10 * S, 150 * S, 60 * S, 190 * S), fill=(40, 44, 54, 255))
    d.polygon([(14 * S, 190 * S), (56 * S, 190 * S), (40 * S, 245 * S), (30 * S, 245 * S)], fill=(60, 64, 74, 255))
    d.rectangle((30 * S, 236 * S, 40 * S, 258 * S), fill=(255, 255, 255, 255))
    return ss(im, w, h).rotate(-35, Image.BICUBIC, expand=True)


MASCOT_XY = (930, 1600)      # bottom-right, above Facebook's caption strip


def draw_mascot(L, t):
    blink = (t % 3.3) < 0.12
    msg, mood, age = None, "happy", 9
    hints = sorted(EP.HINTS)
    quiet = any(a <= t < b for a, b in getattr(EP, "QUIET", []))
    for k, (tr, m, md) in enumerate(hints):
        nxt = hints[k + 1][0] if k + 1 < len(hints) else 1e9
        if tr <= t < min(tr + 2.0, nxt) and not quiet:
            msg, mood, age = m, md, t - tr
    x, y = MASCOT_XY
    bob = 9 * math.sin(t * 3.0)
    squash = 1 + 0.06 * math.exp(-age * 6) if age < 1 else 1
    paste(L, mascot(blink, mood, 230), x, y + bob, squash, rot=3 * math.sin(t * 1.7))
    if msg:
        b = bubble(msg, 32)
        paste(L, b, min(x - 60 - b.width * 0.3, W - b.width / 2 - 10), y - 200 + bob, pop(age, 0.25),
              a=clamp((2.0 - age) / 0.2))


# ---------------------------------------------------------------- end screen (shared)
def end_taps():
    s = scene_start("end")
    return [s + 1.5, s + 2.1, s + 2.7]


def sc_end(L, t, tl):
    s0 = scene_start("end")
    glow_box(L, (70, 220, 1010, 1520), CYAN, ease(tl / 0.5), w=6, r=34, fill_a=18)
    paste(L, gtext("Python ki", 70, CYAN), 540, 340, pop(tl - 0.1))
    paste(L, gtext("PATHSHALA", 110, YEL, "mont"), 540, 450, pop(tl - 0.2))
    write(L, t, s0 + 0.4, 190, 550, "Video achha laga?", 66, CHALK, cps=24)
    taps, ys = end_taps(), [780, 920, 1060]
    btns = [("LIKE", "LIKED!", (40, 110, 230), (40, 110, 230)), ("SHARE", "SHARED!", (30, 160, 80), (30, 160, 80)),
            ("SUBSCRIBE", "SUBSCRIBED", (220, 40, 50), (95, 100, 112))]
    d = ImageDraw.Draw(L)
    for k, (a, b, c0, c1) in enumerate(btns):
        age = t - (s0 + 0.7 + k * 0.12)
        if age <= 0:
            continue
        on = t >= taps[k]
        press = 1 - 0.1 * math.exp(-((t - taps[k] - 0.03) / 0.05) ** 2)
        paste(L, E2.end_button(b if on else a, k, c1 if on else c0), 540, ys[k], pop(age) * press)
        if on and t - taps[k] < 0.45:
            rr = (t - taps[k]) * 600
            d.ellipse((540 - rr, ys[k] - rr * 0.3, 540 + rr, ys[k] + rr * 0.3),
                      outline=c1 + (int((1 - (t - taps[k]) / 0.45) * 200),), width=5)
    if t > s0 + 0.9:
        k = min(2, sum(1 for tp in taps if t > tp + 0.15))
        t0 = (taps[k - 1] + 0.15) if k else s0 + 0.9
        m = ease((t - t0) / 0.3)
        y0 = ys[k - 1] if k else 1300
        paste(L, E2.cursor(), 700 - 30 * (1 - m), y0 + (ys[k] - y0) * m + 50)
    age = t - (taps[2] + 0.5)
    if age > 0:
        nc = Image.new("RGBA", (620, 150), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nc)
        nd.rounded_rectangle((2, 2, 617, 147), 18, fill=(20, 26, 38, 255), outline=YEL + (255,), width=5)
        nc.alpha_composite(gtext("NEXT VIDEO", 30, YEL, "mont"), (18, 8))
        nc.alpha_composite(gtext(EP.NEXT_TITLE, 52, CHALK, "mont"), (18, 58))
        paste(L, nc, 540 - 500 * (1 - ease_out(age / 0.35)), 1330, 1)


# ---------------------------------------------------------------- camera
def cam_target(t):
    name, tl, _ = scene_at(t)
    z = EP.FOLLOW.get(name)
    if z:
        p = pen_at(t)
        if p and not any(a <= t < b for a, b in getattr(EP, "NO_FOLLOW", [])):
            return np.array([p[0] * 0.55 + W / 2 * 0.45, p[1]]), z
    return np.array([W / 2, H / 2]), 1.0


def camera(t):
    acc_c, acc_z, wsum = np.zeros(2), 0.0, 0.0
    c0 = cuts()[scene_at(t)[2]]
    for k in range(12):
        tt = max(c0, t - 0.05 * k)
        c, z = cam_target(tt)
        wgt = 1.0 - k / 14
        acc_c += c * wgt
        acc_z += z * wgt
        wsum += wgt
    c, z = acc_c / wsum, acc_z / wsum
    hw, hh = W / 2 / z, H / 2 / z
    c[0] = clamp(c[0], hw, W - hw)
    c[1] = clamp(c[1], hh, H - hh)
    for tp, amp in EP.PUNCHES:
        if 0 <= t - tp < 0.35:
            z *= 1 + amp * (1 - ease_out((t - tp) / 0.35))
    return c, z


def apply_cam(frame, c, z, shake=(0, 0)):
    M = np.float32([[z, 0, W / 2 - c[0] * z + shake[0]], [0, z, H / 2 - c[1] * z + shake[1]]])
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shake_at(t):
    for tp, amp in EP.SHAKES:
        a = t - tp
        if 0 <= a < 0.4:
            k = amp * math.exp(-a * 9)
            return k * math.sin(a * 83), k * math.cos(a * 71)
    return 0.0, 0.0


def defocus(frame, amount):
    if amount <= 0.02:
        return frame
    small = cv2.resize(frame, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    k = 1 + 2 * int(1 + 12 * amount)
    big = cv2.resize(cv2.GaussianBlur(small, (k, k), 0), (W, H), interpolation=cv2.INTER_LINEAR)
    a = clamp(amount * 1.6)
    return (frame * (1 - a) + big * a).astype(np.uint8)


# ---------------------------------------------------------------- frame rendering
def wipe_alpha(L, t):
    c = cuts()
    for ci in EP.WIPE_CUTS:
        dt = c[ci] - t
        if 0 < dt <= WIPE:
            u = 1 - dt / WIPE
            a = np.asarray(L, np.float32).copy()
            a[..., 3] *= (1 - E2.wipe_mask(u)[..., 0])
            return Image.fromarray(a.astype(np.uint8), "RGBA"), u
    return L, None


def overlay_fixed(img, T, t):
    paste(img, title_box(EP.TITLE1, EP.TITLE2), 540, 95)
    paste(img, side_ep(EP.EP_LABEL), 34, H / 2)
    if t is not None:
        draw_mascot(img, t)


def progress(frame, T):
    p = int(W * T / (INTRO + EP.DUR))
    frame[H - 10:, :p] = np.linspace(np.array(CYAN), np.array(YEL), max(p, 1))[None, :p].astype(np.uint8)


def render_lesson(t, T):
    name, tl, _ = scene_at(t)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    EP.SCENE_FN[name](L, t, tl)
    L, wu = wipe_alpha(L, t)
    img = Image.fromarray(composite(L)).convert("RGBA")
    p = pen_at(t) if wu is None else None
    if p:
        nib = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nib)
        flick = 1 + 0.15 * math.sin(t * 50)
        for r, a in ((50, 40), (32, 80), (18, 160)):
            rr = r * flick
            nd.ellipse((60 - rr, 60 - rr, 60 + rr, 60 + rr), fill=(255, 240, 170, a))
        nd.ellipse((52, 52, 68, 68), fill=(255, 255, 255, 255))
        paste(img, marker_pen(), p[0] + 72, p[1] - 92)
        paste(img, nib.filter(ImageFilter.GaussianBlur(4)), p[0], p[1])
    c, z = camera(t)
    frame = gloss(apply_cam(np.asarray(img.convert("RGB")), c, z, shake_at(t)), t)
    img = Image.fromarray(frame).convert("RGBA")
    overlay_fixed(img, T, t)
    c_ = cuts()
    for ci in EP.WIPE_CUTS:
        dt = c_[ci] - t
        if 0 < dt <= WIPE:
            x, y = E2.wipe_path(1 - dt / WIPE)
            paste(img, E2.duster(), x, y, 1, rot=8 * math.sin(t * 30))
    frame = np.asarray(img.convert("RGB")).astype(np.float32)
    for tp, amp, dur, col in EP.FLASHES:
        a = t - tp
        if 0 <= a < dur:
            k = amp * (1 - a / dur) ** 2
            frame = frame * (1 - k) + np.array(col, np.float32) * k
    return np.clip(frame, 0, 255).astype(np.uint8)


@lru_cache(None)
def thumb_frame():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    EP.thumb(L)
    # soft glow only, so the thumbnail text stays crisp (not over-bright)
    img = Image.fromarray(composite(L, bloom_k=0.28, base_k=0.85, ink_k=0.92)).convert("RGBA")
    overlay_fixed(img, 0, None)
    paste(img, mascot(False, "wow", 280), MASCOT_XY[0] - 20, MASCOT_XY[1])
    if getattr(EP, "THUMB_BUBBLE", None):
        paste(img, bubble(EP.THUMB_BUBBLE, 40), 700, MASCOT_XY[1] - 240)
    return np.asarray(img.convert("RGB"))


def render(T):
    if T < INTRO:
        frame = apply_cam(thumb_frame(), np.array([W / 2, H / 2]), 1.0 + 0.04 * T / INTRO)
        if INTRO - T < 0.18:
            frame = defocus(frame, ease(1 - (INTRO - T) / 0.18))
    else:
        t = T - INTRO
        frame = render_lesson(t, T)
        if t < 0.15:
            frame = defocus(frame, ease(1 - t / 0.15))
    frame = frame.copy()
    progress(frame, T)
    return np.ascontiguousarray(frame)


def render_idx(i):
    return render(i / FPS).tobytes()


# ---------------------------------------------------------------- audio
RNG = np.random.default_rng(11)
BPM = 88
BEAT = 60 / BPM


def lofi(length):
    n = int((length + 1) * SR)
    drums, keys, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    K, Sn, Hh = E2.kick(), E2.snare(), E2.hat()
    chords = [(-9, [0, 4, 7, 11]), (-12, [0, 3, 7, 10]), (-16, [0, 4, 7, 11]), (-14, [0, 4, 7, 10])]
    gaps = EP.MUSIC_GAPS
    for b in range(int(length / BEAT) + 2):
        tb = b * BEAT
        if any(g0 <= tb < g1 for g0, g1 in gaps):
            continue
        root, ivs = chords[(b // 4) % 4]
        if b % 4 in (0, 2) or (b % 8 == 7):
            add(drums, K, tb + (BEAT / 2 if b % 8 == 7 else 0), 0.75)
        if b % 2 == 1:
            add(drums, Sn, tb + 0.01, 0.35)
        for k in (0, 0.5):
            add(drums, Hh, tb + k * BEAT + (0.06 if k else 0), 0.5 if k else 0.3)
        if b % 4 == 0:
            for iv in ivs:
                add(keys, E2.epiano(E2.nfreq(root + 12 + iv), 4 * BEAT), tb + 0.02 * iv / 4, 0.1)
        nb = int(BEAT * SR * 0.95)
        add(bass, lp(np.sin(2 * np.pi * E2.nfreq(root - 12) * np.arange(nb) / SR), 250) * env_exp(nb, 0.4), tb, 0.45)
    mix = drums + lp(keys, 2500) + bass
    crackle = np.zeros(n)
    idx = RNG.integers(0, n, int(length * 25))
    crackle[idx] = RNG.normal(0, 0.25, len(idx))
    mix += lp(crackle, 5000) + lp(RNG.normal(0, 0.006, n), 1200)
    for g0, g1 in gaps:
        mix[int(g0 * SR):int(g1 * SR)] *= 0.0
    return mix


def thud():
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * np.cumsum(70 + 80 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 14) +
            lp(RNG.normal(0, 1, n), 900) * np.exp(-tt * 30) * 0.5)


def shutter():
    n = int(0.25 * SR)
    x = hp(RNG.normal(0, 1, n), 2000)
    e = np.zeros(n)
    for o in (0, 0.07):
        i = int(o * SR)
        e[i:] += env_exp(n - i, 0.012)
    return x * e * 0.8


def key_click():
    n = int(0.035 * SR)
    tt = np.arange(n) / SR
    return (bp(RNG.normal(0, 1, n), 1800, 6000) * env_exp(n, 0.006) + np.sin(2 * np.pi * 180 * tt) * env_exp(n, 0.01) * 0.4) * 0.6


def buzzer():
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    return lp(np.sign(np.sin(2 * np.pi * 110 * tt)) + 0.5 * np.sign(np.sin(2 * np.pi * 116 * tt)), 2500) * \
        np.minimum(1, (n - np.arange(n)) / (0.05 * SR)) * 0.35


def glitch():
    n = int(0.3 * SR)
    x = np.zeros(n)
    for k in range(6):
        i = RNG.integers(0, n - 2000)
        L_ = RNG.integers(400, 2000)
        x[i:i + L_] += np.sign(RNG.normal(0, 1, L_)) * RNG.uniform(0.2, 0.5)
    return hp(x, 800)


def blip(f=1200):
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * env_exp(n, 0.015) * 0.5


def base_sfx(s):
    """SFX every episode gets: writing sounds, wipes, mascot pops, slam/flash hits, end screen."""
    for t0, cps, x, y, txt, size, which in WRITES:
        t1 = t0 + len(txt) / cps
        if which == "mono":
            for k in range(len(txt)):
                if txt[k] != " ":
                    add(s, key_click(), t0 + k / cps, 0.35)
        else:
            k, tt = 0, t0
            while tt < t1:
                add(s, E2.squeak(0.16 + 0.08 * (k % 2)), tt, 0.22)
                tt += 0.24 + 0.08 * (k % 3)
                k += 1
    c = cuts()
    for ci in EP.WIPE_CUTS:
        add(s, E2.rub(WIPE), c[ci] - WIPE, 0.7)
    for tr, *_ in EP.HINTS:
        add(s, E2.pop_sfx(780), tr, 0.22)
    for k, tp in enumerate(end_taps()):
        add(s, E2.click_sfx(), tp, 1.0)
        add(s, E2.pop_sfx(620 + 120 * k), tp + 0.03, 0.4)
        add(s, E2.bell() if k == 2 else E2.ding(), tp + 0.05, 0.4)
    add(s, E2.whoosh(0.35), end_taps()[2] + 0.5, 0.4)


def voice_track(length):
    n = int((length + 1) * SR)
    v = np.zeros(n)
    keys = list(EP.VO_AT)
    for i, key in enumerate(keys):
        path = os.path.join(EP.WORK, f"vo_{key}.wav")
        if not os.path.exists(path):
            continue
        a, _ = sf.read(path)
        start = EP.VO_AT[key]
        end = EP.VO_AT[keys[i + 1]] - 0.08 if i + 1 < len(keys) else EP.DUR - 0.25
        rate = (len(a) / SR) / (end - start)
        if rate > 1.0:
            tmp = os.path.join(EP.WORK, f"fit_{key}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", f"atempo={min(rate, 1.6):.4f}", tmp],
                           check=True)
            a, _ = sf.read(tmp)
        add(v, a, start)
        print(f"  vo {key:5s} {start:6.2f}-{start + len(a) / SR:6.2f}s" + (f"  (x{rate:.2f})" if rate > 1 else ""))
    return v


def build_audio(path, with_voice):
    L = EP.DUR
    m = lofi(L)
    s = np.zeros_like(m)
    base_sfx(s)
    EP.sfx(s)
    v = voice_track(L) if with_voice else np.zeros_like(m)
    m /= np.abs(m).max() + 1e-9
    s /= np.abs(s).max() + 1e-9
    if v.any():
        env = signal.lfilter([1 - math.exp(-1 / (0.25 * SR))], [1, -math.exp(-1 / (0.25 * SR))], np.abs(v))
        env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
        body = m * 0.42 * (1 - 0.5 * env) + s * 0.5 * (1 - 0.25 * env) + v / np.abs(v).max() * 0.95
    else:
        body = m * 0.6 + s * 0.6
    body = body[: int(L * SR)]
    intro = np.zeros(int(INTRO * SR))
    add(intro, E2.impact(), 0.0, 0.35)
    add(intro, E2.pop_sfx(700), 0.05, 0.4)
    add(intro, E2.whoosh(0.3), INTRO - 0.22, 0.45)
    mix = np.concatenate([intro, body])
    fade = int(0.4 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    sf.write(path, np.stack([mix, mix], 1).astype(np.float32), SR)


# ---------------------------------------------------------------- main
def run(ep):
    global EP
    EP = ep
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    os.makedirs(EP.OUT, exist_ok=True)
    os.makedirs(EP.WORK, exist_ok=True)
    glass_base()
    E2.board_base()
    Image.fromarray(thumb_frame()).save(os.path.join(EP.OUT, "thumbnail.jpg"), quality=92)
    total = INTRO + EP.DUR
    if args.preview:
        ts = np.linspace(0.3, total - 0.2, 32)
        sheet = Image.new("RGB", (216 * 8, 384 * 4))
        for k, T in enumerate(ts):
            sheet.paste(Image.fromarray(render(T)).resize((216, 384)), ((k % 8) * 216, (k // 8) * 384))
        sheet.save(os.path.join(EP.WORK, "preview.jpg"), quality=85)
        print("wrote", os.path.join(EP.WORK, "preview.jpg"))
        return
    silent = os.path.join(EP.WORK, "video.mp4")
    nf = int(round(total * FPS))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_idx, range(nf), chunksize=4)):
            ff.stdin.write(buf)
            if k % 300 == 0:
                print(f"  frame {k}/{nf}")
    ff.stdin.close()
    ff.wait()
    for suffix, voice in (("", True), ("-music-only", False)):
        wav = os.path.join(EP.WORK, f"mix{suffix}.wav")
        build_audio(wav, voice)
        out = os.path.join(EP.OUT, f"{EP.NAME}{suffix}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
                        "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
        print("wrote", out)
