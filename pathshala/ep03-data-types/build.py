#!/usr/bin/env python3
"""Renders Python Ki Pathshala EP03 "Python Data Types — 1 cheat sheet" (≈57 s, 9:16).

Editing style (the EP02 language, on a black glass board):
- black glass "lightboard" with glossy reflections; the handwriting glows
  (bloom) and the marker nib shines where it is writing;
- fixed yellow title box on top and a vertical "EP 03" on the left;
- the cheat sheet builds up ①②③④ one item at a time and nothing is erased;
- the camera follows the pen while it writes, and a duster wipes the board
  when the topic changes;
- the mascot gives a hint for every data type;
- sound: marker squeaks, thuds, dings, risers and booms over a lo-fi bed.

Timeline: hook/thumbnail -> "Data type = data ki KISM" (boxes + type()) ->
"9 TYPES, 4 FAMILY!" slam -> cheat sheet (9 types, 4 families) with a
"SCREENSHOT LE LO!" camera flash -> quiz "3.0 ka type?" with 3-2-1 -> end
screen LIKE / SHARE / SUBSCRIBE + "NEXT VIDEO: EP 04 input()".

Two versions are written: with the Hinglish voice-over (make_voice.py) and
music + SFX only (the video is complete without voice).

Run:   python3 pathshala/ep03-data-types/make_voice.py --models <dir>
       python3 pathshala/ep03-data-types/build.py [--preview]
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
_spec = importlib.util.spec_from_file_location("ep02", os.path.join(HERE, "..", "ep02-print", "build.py"))
E2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E2)                 # reuse EP02's drawing + sound helpers (mascot, fonts, SFX)
font, ss, paste, with_shadow = E2.font, E2.ss, E2.paste, E2.with_shadow
clamp, ease, ease_out, pop, back_out = E2.clamp, E2.ease, E2.ease_out, E2.pop, E2.back_out
mascot, bubble = E2.mascot, E2.bubble

OUT = os.path.join(HERE, "output")
WORK = os.path.join(HERE, "work")
NAME = "PythonKiPathshala-EP03-Data-Types"
W, H, FPS = 1080, 1920, 30
SR = 48000

# ---------------------------------------------------------------- palette (glowing marker on black glass)
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

# ---------------------------------------------------------------- timeline
VO_AT = {"l01": 0.10, "l02": 3.25, "l03": 5.80, "l04": 8.80, "l05": 13.70, "l06": 17.20, "l07": 24.80,
         "l08": 31.00, "l09": 35.05, "l10": 40.60, "l11a": 43.60, "l11b": 49.40, "l12": 51.40}
DUR = 56.8
SCENES = [("hook", 0.0), ("kism", 3.1), ("slam", 13.55), ("sheet", 17.0), ("quiz", 43.4), ("end", 51.2)]
CUTS = [s for _, s in SCENES] + [DUR]
WIPE = 0.45
WIPE_CUTS = [1, 2, 3, 4]               # duster between boards
COUNT_T0 = 46.35                        # quiz countdown 3-2-1
REVEAL = COUNT_T0 + 3.0
SHOT = 41.4                             # "SCREENSHOT LE LO!" camera flash


@lru_cache(None)
def vo_len(key):
    p = os.path.join(WORK, f"vo_{key}.wav")
    if os.path.exists(p):
        return sf.info(p).duration
    return 2.5


SPOKEN = {  # Devanagari lines, used to place each type at the moment it is spoken
    "l06": "पहली फ़ैमिली नंबर्स: इंट मतलब पूरा नंबर, फ़्लोट मतलब पॉइंट वाला, और कॉम्प्लेक्स में जे वाला इमेजिनरी पार्ट।",
    "l07": "दूसरी सीक्वेंस: स्ट्रिंग मतलब टेक्स्ट, लिस्ट जो बदल सकती है, और टपल जो फ़िक्स्ड रहता है।",
    "l08": "तीसरी मैपिंग: डिक्ट, जिसमें की और वैल्यू की जोड़ी होती है।",
    "l09": "और लास्ट में सेट, जिसमें डुप्लीकेट नहीं, और बूल: ट्रू या फ़ॉल्स, बस हाँ या ना।",
}


def said(line, word, lead=0.25):
    """Approximate moment `word` is spoken in a VO line (character-proportional)."""
    s = SPOKEN[line]
    return VO_AT[line] + vo_len(line) * s.index(word) / len(s) - lead


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return SCENES[i][0], t - CUTS[i], i
    return SCENES[-1][0], t - CUTS[-2], len(SCENES) - 1


# ---------------------------------------------------------------- cheat sheet layout
# family: (title, colour, header time, [(type, example, hint, time)])
FAMILIES = [
    ("NUMBERS", YEL, VO_AT["l06"] + 0.05, [
        ("int", "20", "Poora number!", said("l06", "इंट")),
        ("float", "3.14", "Point wala!", said("l06", "फ़्लोट")),
        ("complex", "2+3j", "j = imaginary", said("l06", "कॉम्प्लेक्स"))]),
    ("SEQUENCE", CYAN, VO_AT["l07"] + 0.05, [
        ("str", '"Hello"', "Quotes = text!", said("l07", "स्ट्रिंग")),
        ("list", "[1, 2, 3]", "Badal sakti hai!", said("l07", "लिस्ट")),
        ("tuple", "(1, 2, 3)", "Fixed! Badlega nahi", said("l07", "टपल"))]),
    ("MAPPING", PINK, VO_AT["l08"] + 0.05, [
        ("dict", '{"naam": "Riya"}', "Key : Value jodi", said("l08", "डिक्ट"))]),
    ("SET + BOOL", GREEN, VO_AT["l09"] + 0.05, [
        ("set", "{1, 2, 3}", "No duplicate!", said("l09", "सेट")),
        ("bool", "True / False", "Haan ya Na!", said("l09", "बूल"))]),
]
SHEET_TOP = 300
HDR_H, ROW_H, GAP = 86, 88, 22


def sheet_layout():
    """y position of every header and row."""
    y = SHEET_TOP
    out = []
    for fi, (title, col, th, rows) in enumerate(FAMILIES):
        out.append(("hdr", fi, y, th))
        y += HDR_H
        for ri, r in enumerate(rows):
            out.append(("row", (fi, ri), y, r[3]))
            y += ROW_H
        y += GAP
    return out


LAYOUT = sheet_layout()

# ---------------------------------------------------------------- write events (drive the pen + camera + squeaks)
# (t0, cps, x, y, text, size, font) — everything handwritten on the board
WRITES = []


def reg(t0, x, y, s, size, which="hand", cps=20.0):
    WRITES.append((t0, cps, x, y, s, size, which))
    return t0 + len(s) / cps


def build_writes():
    WRITES.clear()
    # kism board
    reg(VO_AT["l02"] + 0.1, 90, 300, "Data Type = data ki KISM", 70, cps=24)
    reg(VO_AT["l04"] + 0.6, 120, 1180, "type(20)", 60, "mono", cps=16)
    reg(VO_AT["l04"] + 2.4, 120, 1330, 'type("Riya")', 60, "mono", cps=16)
    # cheat sheet
    for kind, idx, y, th in LAYOUT:
        if kind == "hdr":
            title = FAMILIES[idx][0]
            reg(th, 175, y + 8, title, 66, "mont", cps=18)
        else:
            fi, ri = idx
            name, ex, hint, tt = FAMILIES[fi][3][ri]
            end = reg(tt, 150, y + 8, name, 62, cps=16)
            reg(end + 0.05, 420, y + 18, ex, 50, "mono", cps=22)
    # quiz
    reg(CUTS[4] + 0.6, 90, 470, "3.0 ka type kya hai?", 74, cps=22)


build_writes()


def text_w(s, size, which):
    return font(size, which).getlength(s)


def pen_at(t):
    """(x, y, colour) of the nib if something is being written at t, else None."""
    for t0, cps, x, y, s, size, which in WRITES:
        t1 = t0 + len(s) / cps
        if t0 <= t < t1:
            n = (t - t0) * cps
            return x + text_w(s[: int(n)], size, which) + 6, y + size * 0.62
    return None


# ---------------------------------------------------------------- glowing text
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


def circled(L, n, cx, cy, col, s=1.0):
    r = int(34 * s)
    if r <= 2:
        return
    d = ImageDraw.Draw(L)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (255,), width=5)
    f = font(int(44 * s), "mont")
    d.text((cx, cy + 1), str(n), font=f, fill=col + (255,), anchor="mm")


def glow_box(L, box, col, u=1.0, w=5, r=22, fill_a=40):
    """Neon rounded box drawn progressively (perimeter fraction u)."""
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
def box3d(label, col, w=300, h=230):
    """Neon outlined 3D 'dabba' with a label tab."""
    im = Image.new("RGBA", (w + 80, h + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dx, dy = 60, -45
    f = [(10, 70), (10 + w, 70), (10 + w, 70 + h), (10, 70 + h)]
    b = [(x + dx, y + dy) for x, y in f]
    d.polygon(f, fill=col + (28,))
    for (a1, a2) in ((b[0], b[1]), (b[1], b[2])):
        d.line([a1, a2], fill=col + (200,), width=4)
    for i in (0, 1, 2):
        d.line([f[i], b[i]], fill=col + (220,), width=4)
    d.polygon(f, outline=col + (255,))
    d.line(f + [f[0]], fill=col + (255,), width=6)
    t = text_tab(label, col)
    im.alpha_composite(t, (int(10 + w / 2 - t.width / 2), int(70 + h - t.height - 16)))
    return im


@lru_cache(None)
def text_tab(s, col):
    f = font(40, "mono")
    w = int(f.getlength(s)) + 30
    im = Image.new("RGBA", (w, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 59), 10, fill=col + (255,))
    d.text((15, 6), s, font=f, fill=NAVY + (255,))
    return im


@lru_cache(None)
def chip(s, col, size=56):
    f = font(size, "mono")
    w, h = int(f.getlength(s)) + 50, size + 34
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=(20, 26, 38, 235), outline=col + (255,), width=4)
    d.text((45, 26), s, font=f, fill=col + (255,))
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


# ---------------------------------------------------------------- board background
@lru_cache(None)
def glass_base():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array(GLASS, np.float32)[None, None, :] * np.ones((H, W, 1), np.float32)
    vign = np.clip(1 - np.hypot((xx - W / 2) / W, (yy - H * 0.45) / H) * 1.1, 0, 1)[..., None]
    img = base * (0.7 + 0.6 * vign) + np.array((14, 22, 40), np.float32) * vign * 0.8
    # faint smudges of old writing
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


def gloss(frame, t):
    """Moving diagonal reflections on the glass."""
    yy, xx = GRID
    g = np.zeros((H, W), np.float32)
    for k, (w, a, sp) in enumerate(((180, 0.06, 40), (60, 0.05, 55))):
        pos = (xx * 0.6 + yy * 0.8 - (t * sp + k * 900)) % 2600 - 1300
        g += a * np.exp(-(pos / w) ** 2)
    top = np.clip(1 - yy / (H * 0.5), 0, 1) * 0.04
    return np.clip(frame.astype(np.float32) + (g + top)[..., None] * 255, 0, 255).astype(np.uint8)


GRID = np.mgrid[0:H, 0:W].astype(np.float32)


# ---------------------------------------------------------------- scenes (drawn in board coordinates)
def sc_hook(L, t, tl):
    s = 1 + 0.03 * math.sin(tl * 4)          # frame 1 is the full thumbnail; it only breathes
    paste(L, gtext("PYTHON", 120, CHALK, "mont"), 540, 520, s)
    paste(L, gtext("DATA TYPES", 140, YEL, "mont"), 540, 680, s, rot=-2)
    paste(L, solid_pill("9 TYPES  •  1 CHEAT SHEET", 44, NAVY, CYAN), 540, 840)
    chips = [("20", YEL, 250, 1130), ("3.14", CYAN, 790, 1080), ('"Hi"', PINK, 300, 1390), ("True", GREEN, 760, 1360)]
    for k, (s_, c, x, y) in enumerate(chips):
        a = t * 1.6 + k * 1.7
        paste(L, chip(s_, c, 70), x + 18 * math.sin(a), y + 22 * math.cos(a * 0.8), 1,
              rot=6 * math.sin(a * 0.7))
    paste(L, solid_pill("EP 03", 56, WHITE, RED), 540, 1600, 1 + 0.05 * math.sin(tl * 6), rot=-3)


def sc_kism(L, t, tl):
    write(L, t, VO_AT["l02"] + 0.1, 90, 300, "Data Type = data ki KISM", 70, CHALK, cps=24)
    done = VO_AT["l02"] + 0.1 + 24 / 24
    if t > done + 0.1:
        f = font(70)
        x0 = 90 + f.getlength("Data Type = data ki ")
        u = ease((t - done - 0.1) / 0.3)
        ImageDraw.Draw(L).line([(x0, 395), (x0 + f.getlength("KISM") * u, 395)], fill=YEL + (255,), width=7)
        L.alpha_composite(gtext("KISM", 70, YEL), (int(x0) - 8, 292))
    # two boxes: int <- 20, str <- "Riya"
    for k, (lab, col, val, x, tv) in enumerate((("int", YEL, "20", 300, VO_AT["l03"] + 0.2),
                                                 ("str", CYAN, '"Riya"', 780, VO_AT["l03"] + 1.5))):
        age = t - (VO_AT["l02"] + 1.2 + k * 0.2)
        if age > 0:
            paste(L, box3d(lab, col), x, 760, pop(age))
        age = t - tv
        if age > 0:
            u = ease_out(age / 0.45)
            y = 520 + (700 - 520) * u if u < 1 else 700 + 6 * math.sin(age * 4)
            paste(L, chip(val, col, 52), x - 20, y, 1)
            arrow(L, (x - 20, 470), (x - 20, 580), (age - 0.4) / 0.2, col)
    # type() lines and outputs
    for k, (code, out, col, t0) in enumerate((("type(20)", "<class 'int'>", YEL, VO_AT["l04"] + 0.6),
                                              ('type("Riya")', "<class 'str'>", CYAN, VO_AT["l04"] + 2.4))):
        y = 1180 + 150 * k
        if write(L, t, t0, 120, y, code, 60, CHALK, "mono", cps=16):
            done = t0 + len(code) / 16
            arrow(L, (120 + text_w(code, 60, "mono") + 30, y + 40), (600, y + 40), (t - done) / 0.2, DIM, 5)
            if t > done + 0.25:
                paste(L, gtext(out, 50, col, "mono"), 600, y + 8, pop(t - done - 0.25), anchor="lt")


def sc_slam(L, t, tl):
    s = 1 + 2.4 * (1 - ease_out(tl / 0.22))
    paste(L, gtext("9 TYPES,", 150, YEL, "mont"), 540, 720, s, a=clamp(tl / 0.06), rot=-3)
    s2 = 1 + 2.4 * (1 - ease_out((tl - 0.35) / 0.22)) if tl > 0.35 else 0
    paste(L, gtext("4 FAMILY!", 150, CYAN, "mont"), 540, 900, s2, a=clamp((tl - 0.35) / 0.06), rot=2)
    for k, (title, col, *_ ) in enumerate(FAMILIES):
        age = tl - 1.2 - k * 0.25
        if age > 0:
            x, y = 290 + (k % 2) * 500, 1180 + (k // 2) * 170
            sp = solid_pill(f"{k + 1}  {title}", 40, NAVY, col)
            paste(L, sp, x, y, pop(age))
    sparks(L, tl, 540, 800)


def sparks(L, age, cx, cy, n=50, seed=4):
    if age < 0 or age > 1.2:
        return
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(L)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(300, 900)
        col = [YEL, CYAN, PINK, GREEN][rng.integers(4)]
        r0 = sp * (1 - math.exp(-age * 5))
        x, y = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        x2, y2 = cx + math.cos(a) * r0 * 0.85, cy + math.sin(a) * r0 * 0.85
        d.line([(x2, y2), (x, y)], fill=col + (int(255 * clamp(1.2 - age)),), width=5)


def sc_sheet(L, t, tl):
    for kind, idx, y, th in LAYOUT:
        if kind == "hdr":
            title, col, _, _ = FAMILIES[idx]
            age = t - th
            if age > -0.3:
                circled(L, idx + 1, 120, y + 46, col, pop(age + 0.3, 0.25))
            if write(L, t, th, 175, y + 8, title, 66, col, "mont", cps=18):
                tl_done = th + len(title) / 18
                u = ease((t - tl_done) / 0.3)
                ImageDraw.Draw(L).line([(175, y + 82), (175 + text_w(title, 66, "mont") * u, y + 82)],
                                       fill=col + (180,), width=4)
        else:
            fi, ri = idx
            name, ex, hint, tt = FAMILIES[fi][3][ri]
            col = FAMILIES[fi][1]
            if t > tt - 0.05:
                ImageDraw.Draw(L).ellipse((128, y + 40, 140, y + 52), fill=col + (255,))
            end = tt + len(name) / 16
            write(L, t, tt, 150, y + 8, name, 62, CHALK, cps=16)
            if t > end + 0.05:
                write(L, t, end + 0.05, 420, y + 18, ex, 50, col, "mono", cps=22)
    # SCREENSHOT LE LO! stamp
    age = t - SHOT
    if age > 0:
        s = 1 + 1.6 * (1 - ease_out(age / 0.2))
        paste(L, solid_pill("SCREENSHOT LE LO!", 58, NAVY, YEL), 560, 1620, s, rot=-4)


QUIZ_OPTS = [("A", "int"), ("B", "float"), ("C", "str")]


def sc_quiz(L, t, tl):
    s = back_out(tl / 0.35)
    paste(L, gtext("QUIZ TIME!", 130, YEL, "mont"), 540 + 6 * math.sin(tl * 40) * math.exp(-tl * 5), 330, s,
          rot=-3)
    write(L, t, CUTS[4] + 0.6, 90, 470, "3.0 ka type kya hai?", 74, CHALK, cps=22)
    for k, (letter, ans) in enumerate(QUIZ_OPTS):
        age = t - (CUTS[4] + 1.6 + k * 0.25)
        if age <= 0:
            continue
        y = 700 + k * 150
        right = ans == "float"
        col = (GREEN if right else RED) if t >= REVEAL else CHALK
        glow_box(L, (150, y - 55, 930, y + 55), col, ease(age / 0.3), w=5, r=28,
                 fill_a=60 if (t >= REVEAL and right) else 25)
        if age > 0.25:
            d = ImageDraw.Draw(L)
            d.ellipse((180, y - 32, 244, y + 32), outline=col + (255,), width=4)
            d.text((212, y), letter, font=font(40, "mont"), fill=col + (255,), anchor="mm")
            L.alpha_composite(gtext(ans, 64, col, "mono"), (290, int(y - 40)))
            if t >= REVEAL:
                paste(L, E2.tick_badge(36, right), 870, y, pop(t - REVEAL - k * 0.08))
    age = t - COUNT_T0
    if 0 < age < 3.0:
        k = min(2, int(age))
        R = 105
        ring = Image.new("RGBA", (2 * R + 30, 2 * R + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(ring)
        d.ellipse((15, 15, 2 * R + 15, 2 * R + 15), outline=(50, 58, 75, 255), width=12)
        d.arc((15, 15, 2 * R + 15, 2 * R + 15), -90, -90 + 360 * (1 - (age % 1.0)), fill=ORANGE + (255,), width=12)
        d.text((R + 15, R + 15), str(3 - k), font=font(120, "mont"), fill=CHALK + (255,), anchor="mm")
        paste(L, ring, 540, 1260, (1 + 0.2 * math.exp(-(age % 1) * 8)) * pop(age, 0.2))
    if t >= REVEAL:
        a = t - REVEAL
        paste(L, gtext("Kyunki POINT hai!", 72, GREEN), 540, 1260, pop(a - 0.3))
        paste(L, gtext("3.0  →  float", 60, YEL, "mono"), 540, 1380, pop(a - 0.6))
        sparks(L, a, 540, 850, seed=7)


def sc_end(L, t, tl):
    glow_box(L, (70, 200, 1010, 1560), CYAN, ease(tl / 0.5), w=6, r=34, fill_a=18)
    paste(L, gtext("Python ki", 70, CYAN), 540, 320, pop(tl - 0.1))
    paste(L, gtext("PATHSHALA", 110, YEL, "mont"), 540, 430, pop(tl - 0.2))
    write(L, t, CUTS[5] + 0.4, 190, 530, "Video achha laga?", 66, CHALK, cps=24)
    taps = [VO_AT["l12"] + 1.4, VO_AT["l12"] + 1.9, VO_AT["l12"] + 2.5]
    ys = [760, 900, 1040]
    btns = [("LIKE", "LIKED!", (40, 110, 230), (40, 110, 230)), ("SHARE", "SHARED!", (30, 160, 80), (30, 160, 80)),
            ("SUBSCRIBE", "SUBSCRIBED", (220, 40, 50), (95, 100, 112))]
    d = ImageDraw.Draw(L)
    for k, (a, b, c0, c1) in enumerate(btns):
        age = t - (CUTS[5] + 0.7 + k * 0.12)
        if age <= 0:
            continue
        on = t >= taps[k]
        press = 1 - 0.1 * math.exp(-((t - taps[k] - 0.03) / 0.05) ** 2)
        paste(L, E2.end_button(b if on else a, k, c1 if on else c0), 540, ys[k], pop(age) * press)
        if on and t - taps[k] < 0.45:
            rr = (t - taps[k]) * 600
            d.ellipse((540 - rr, ys[k] - rr * 0.3, 540 + rr, ys[k] + rr * 0.3),
                      outline=c1 + (int((1 - (t - taps[k]) / 0.45) * 200),), width=5)
    if t > CUTS[5] + 0.9:
        k = min(2, sum(1 for tp in taps if t > tp + 0.15))
        t0 = (taps[k - 1] + 0.15) if k else CUTS[5] + 0.9
        m = ease((t - t0) / 0.3)
        y0 = ys[k - 1] if k else 1300
        paste(L, E2.cursor(), 700 - 30 * (1 - m), y0 + (ys[k] - y0) * m + 50)
    age = t - (taps[2] + 0.5)
    if age > 0:
        nc = Image.new("RGBA", (560, 150), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nc)
        nd.rounded_rectangle((2, 2, 557, 147), 18, fill=(20, 26, 38, 255), outline=YEL + (255,), width=5)
        nc.alpha_composite(gtext("NEXT VIDEO", 30, YEL, "mont"), (18, 8))
        nc.alpha_composite(gtext("EP 04: input()", 54, CHALK, "mono"), (18, 58))
        paste(L, nc, 540 - 500 * (1 - ease_out(age / 0.35)), 1330, 1)


SCENE_FN = {"hook": sc_hook, "kism": sc_kism, "slam": sc_slam, "sheet": sc_sheet, "quiz": sc_quiz, "end": sc_end}

# ---------------------------------------------------------------- mascot hints (per type) + reactions
HINTS = [(0.5, "Chalo shuru!", "happy"), (VO_AT["l03"] + 0.3, "Alag dabba!", "happy"),
         (VO_AT["l04"] + 3.4, "Python batata hai!", "wow"), (CUTS[2] + 0.1, "Whoa!", "wow")]
for _fam in FAMILIES:
    for _name, _ex, _hint, _tt in _fam[3]:
        HINTS.append((_tt + 0.35, _hint, "happy"))
HINTS += [(CUTS[4] + 1.0, "Socho...", "happy"),
          (REVEAL + 0.1, "Sahi! float", "happy"), (CUTS[5] + 0.5, "Kal milte hain!", "happy")]
HINTS.sort()


def draw_mascot(L, t):
    blink = (t % 3.3) < 0.12
    msg, mood, age = None, "happy", 9
    for k, (tr, m, md) in enumerate(HINTS):
        nxt = HINTS[k + 1][0] if k + 1 < len(HINTS) else 1e9
        if tr <= t < min(tr + 2.0, nxt) and not (SHOT - 0.3 <= t < SHOT + 1.6):
            msg, mood, age = m, md, t - tr
    x, y = 935, 1700
    bob = 9 * math.sin(t * 3.0)
    squash = 1 + 0.06 * math.exp(-age * 6) if age < 1 else 1
    paste(L, mascot(blink, mood, 250), x, y + bob, squash, rot=3 * math.sin(t * 1.7))
    if msg:
        b = bubble(msg, 32)
        paste(L, b, min(x - 60 - b.width * 0.3, W - b.width / 2 - 10), y - 215 + bob, pop(age, 0.25),
              a=clamp((2.0 - age) / 0.2))


# ---------------------------------------------------------------- fixed UI
@lru_cache(None)
def title_box():
    f1, f2 = font(44, "mont"), font(30, "hand")
    w = int(max(f1.getlength("PYTHON DATA TYPES"), f2.getlength("9 types • 4 family • 1 cheat sheet"))) + 60
    im = Image.new("RGBA", (w, 118), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 117), 18, fill=YEL + (255,))
    d.text((w / 2, 36), "PYTHON DATA TYPES", font=f1, fill=NAVY + (255,), anchor="mm")
    d.text((w / 2, 88), "9 types • 4 family • 1 cheat sheet", font=f2, fill=NAVY + (255,), anchor="mm")
    return with_shadow(im, blur=10, alpha=120, pad=20)


@lru_cache(None)
def side_ep():
    im = Image.new("RGBA", (300, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((150, 40), "EP 03", font=font(64, "mont"), fill=YEL + (255,), anchor="mm")
    return im.rotate(90, expand=True)


@lru_cache(None)
def marker_pen():
    """Marker pen sprite, tip at the sprite's bottom-left corner region."""
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


# ---------------------------------------------------------------- camera (follows the pen)
def cam_target(t):
    name, tl, _ = scene_at(t)
    if name in ("sheet", "kism", "quiz"):
        p = pen_at(t)
        if p and not (name == "sheet" and t > SHOT - 1.2):
            z = 1.18 if name == "sheet" else 1.1
            return np.array([p[0] * 0.55 + W / 2 * 0.45, p[1]]), z
    return np.array([W / 2, H / 2]), 1.0


def camera(t):
    """Smoothed (centre, zoom): average of the target over the last 0.6 s."""
    acc_c, acc_z, wsum = np.zeros(2), 0.0, 0.0
    i0 = scene_at(t)[2]
    for k in range(12):
        tt = t - 0.05 * k
        if tt < CUTS[i0]:
            tt = CUTS[i0]
        c, z = cam_target(tt)
        wgt = 1.0 - k / 14
        acc_c += c * wgt
        acc_z += z * wgt
        wsum += wgt
    c, z = acc_c / wsum, acc_z / wsum
    # keep the frame inside the board
    hw, hh = W / 2 / z, H / 2 / z
    c[0] = clamp(c[0], hw, W - hw)
    c[1] = clamp(c[1], hh, H - hh)
    # punch on the slam and on the screenshot flash
    for tp, amp in ((CUTS[2], 0.12), (SHOT, 0.06), (REVEAL, 0.06)):
        if 0 <= t - tp < 0.35:
            z *= 1 + amp * (1 - ease_out((t - tp) / 0.35))
    return c, z


def apply_cam(frame, c, z, shake=(0, 0)):
    M = np.float32([[z, 0, W / 2 - c[0] * z + shake[0]], [0, z, H / 2 - c[1] * z + shake[1]]])
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shake_at(t):
    for tp, amp in ((CUTS[2], 26), (CUTS[2] + 0.35, 18), (REVEAL, 10)):
        a = t - tp
        if 0 <= a < 0.4:
            k = amp * math.exp(-a * 9)
            return k * math.sin(a * 83), k * math.cos(a * 71)
    return 0.0, 0.0


def bloom(rgba):
    """Glow for everything drawn on the board (the marker ink shines)."""
    a = np.asarray(rgba, np.float32)
    rgb = a[..., :3] * (a[..., 3:4] / 255)
    small = cv2.resize(rgb, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.GaussianBlur(small, (0, 0), 3)
    g2 = cv2.GaussianBlur(small, (0, 0), 9)
    g = cv2.resize(g1 * 0.9 + g2 * 0.7, (W, H), interpolation=cv2.INTER_LINEAR)
    return g


# ---------------------------------------------------------------- wipe (duster)
def wipe_alpha(L, t):
    for ci in WIPE_CUTS:
        dt = CUTS[ci] - t
        if 0 < dt <= WIPE:
            u = 1 - dt / WIPE
            a = np.asarray(L, np.float32).copy()
            a[..., 3] *= (1 - E2.wipe_mask(u)[..., 0])
            return Image.fromarray(a.astype(np.uint8), "RGBA"), u
    return L, None


def render(t):
    name, tl, _ = scene_at(t)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENE_FN[name](L, t, tl)
    L, wu = wipe_alpha(L, t)
    base = glass_base().astype(np.float32)
    glow = bloom(L)
    la = np.asarray(L, np.float32)
    alpha = la[..., 3:4] / 255
    frame = base + glow * 0.85
    frame = frame * (1 - alpha) + la[..., :3] * alpha
    # glowing marker nib (+ pen) while writing
    p = pen_at(t) if wu is None else None
    img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).convert("RGBA")
    if p:
        nib = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nib)
        flick = 1 + 0.15 * math.sin(t * 50)
        for r, a in ((50, 40), (32, 80), (18, 160)):
            rr = r * flick
            nd.ellipse((60 - rr, 60 - rr, 60 + rr, 60 + rr), fill=(255, 240, 170, a))
        nd.ellipse((52, 52, 68, 68), fill=(255, 255, 255, 255))
        nib = nib.filter(ImageFilter.GaussianBlur(4))
        paste(img, marker_pen(), p[0] + 72, p[1] - 92)
        paste(img, nib, p[0], p[1])
    frame = np.asarray(img.convert("RGB"))
    c, z = camera(t)
    frame = apply_cam(frame, c, z, shake_at(t))
    frame = gloss(frame, t)
    # fixed overlays (not moved by the camera)
    img = Image.fromarray(frame).convert("RGBA")
    paste(img, title_box(), 540, 95)
    paste(img, side_ep(), 34, H / 2)
    draw_mascot(img, t)
    for ci in WIPE_CUTS:
        dt = CUTS[ci] - t
        if 0 < dt <= WIPE:
            x, y = E2.wipe_path(1 - dt / WIPE)
            paste(img, E2.duster(), x, y, 1, rot=8 * math.sin(t * 30))
    frame = np.asarray(img.convert("RGB")).copy()
    # flashes: slam + camera shutter for the screenshot + quiz reveal
    for tp, amp, dur in ((CUTS[2], 0.75, 0.22), (SHOT, 0.95, 0.3), (REVEAL, 0.35, 0.18)):
        a = t - tp
        if 0 <= a < dur:
            k = amp * (1 - a / dur) ** 2
            frame = (frame * (1 - k) + 255 * k).astype(np.uint8)
    if 0 <= t - SHOT < 0.5:            # shutter frame corners
        d = ImageDraw.Draw(img2 := Image.fromarray(frame))
        for (x, y, sx, sy) in ((60, 220, 1, 1), (W - 60, 220, -1, 1), (60, H - 260, 1, -1), (W - 60, H - 260, -1, -1)):
            d.line([(x, y), (x + 90 * sx, y)], fill=WHITE, width=8)
            d.line([(x, y), (x, y + 90 * sy)], fill=WHITE, width=8)
        frame = np.asarray(img2)
    p = int(W * t / DUR)
    frame = frame.copy()
    frame[H - 10:, :p] = np.linspace(np.array(CYAN), np.array(YEL), max(p, 1))[None, :p].astype(np.uint8)
    return np.ascontiguousarray(frame)


def render_idx(i):
    return render(i / FPS).tobytes()


# ---------------------------------------------------------------- audio
add, env_exp, lp, hp, bp = E2.add, E2.env_exp, E2.lp, E2.hp, E2.bp
RNG = np.random.default_rng(11)
BPM = 88
BEAT = 60 / BPM


def lofi():
    """Lo-fi bed: swung drums, warm e-piano chords, round bass, vinyl crackle."""
    n = int((DUR + 1) * SR)
    drums, keys, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    K, Sn, Hh = E2.kick(), E2.snare(), E2.hat()
    chords = [(-9, [0, 4, 7, 11]), (-12, [0, 3, 7, 10]), (-16, [0, 4, 7, 11]), (-14, [0, 4, 7, 10])]
    gaps = [(CUTS[2] - 0.6, CUTS[2]), (REVEAL - 0.5, REVEAL)]
    for b in range(int(DUR / BEAT) + 2):
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
    idx = RNG.integers(0, n, int(DUR * 25))
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


def sfx_track():
    n = int((DUR + 1) * SR)
    s = np.zeros(n)
    # marker squeaks (cheen-cheen) during every write
    for t0, cps, x, y, txt, size, which in WRITES:
        t1 = t0 + len(txt) / cps
        k, tt = 0, t0
        while tt < t1:
            add(s, E2.squeak(0.16 + 0.08 * (k % 2)), tt, 0.22)
            tt += 0.24 + 0.08 * (k % 3)
            k += 1
    # hook
    add(s, E2.impact(), 0.0, 0.5)
    for k in range(4):
        add(s, E2.pop_sfx(520 + 80 * k), 0.45 + k * 0.12, 0.4)
    add(s, thud(), 0.9, 0.6)
    # wipes
    for ci in WIPE_CUTS:
        add(s, E2.rub(WIPE), CUTS[ci] - WIPE, 0.7)
    # kism boxes + chips land with a thud, outputs ding
    for k in range(2):
        add(s, thud(), VO_AT["l02"] + 1.2 + k * 0.2, 0.5)
    for tv in (VO_AT["l03"] + 0.2 + 0.45, VO_AT["l03"] + 1.5 + 0.45):
        add(s, thud(), tv, 0.7)
    for t0, code in ((VO_AT["l04"] + 0.6, "type(20)"), (VO_AT["l04"] + 2.4, 'type("Riya")')):
        add(s, E2.ding(), t0 + len(code) / 16 + 0.25, 0.45)
    # slam: riser in the gap, then boom x2
    add(s, E2.riser(0.6), CUTS[2] - 0.6, 0.7)
    add(s, E2.impact(), CUTS[2], 1.0)
    add(s, E2.impact(), CUTS[2] + 0.35, 0.7)
    for k in range(4):
        add(s, E2.pop_sfx(500 + 90 * k), CUTS[2] + 1.2 + k * 0.25, 0.4)
    # sheet: thud on each header, ding when each example completes
    for kind, idx, y, th in LAYOUT:
        if kind == "hdr":
            add(s, thud(), th, 0.6)
        else:
            fi, ri = idx
            name, ex, hint, tt = FAMILIES[fi][3][ri]
            add(s, E2.ding(), tt + len(name) / 16 + 0.05 + len(ex) / 22, 0.3)
    add(s, E2.riser(0.9), SHOT - 0.9, 0.5)
    add(s, shutter(), SHOT, 1.0)
    add(s, E2.impact(), SHOT, 0.4)
    # quiz
    add(s, E2.impact(), CUTS[4], 0.5)
    for k in range(3):
        add(s, E2.pop_sfx(560), CUTS[4] + 1.6 + k * 0.25, 0.35)
        add(s, E2.clock_tick(), COUNT_T0 + k, 0.7)
    add(s, E2.riser(0.5), REVEAL - 0.5, 0.5)
    add(s, E2.impact(), REVEAL, 0.6)
    add(s, E2.ding(), REVEAL + 0.05, 0.7)
    # end
    for k, tp in enumerate([VO_AT["l12"] + 1.4, VO_AT["l12"] + 1.9, VO_AT["l12"] + 2.5]):
        add(s, E2.click_sfx(), tp, 1.0)
        add(s, E2.pop_sfx(620 + 120 * k), tp + 0.03, 0.4)
        add(s, E2.bell() if k == 2 else E2.ding(), tp + 0.05, 0.4)
    add(s, E2.whoosh(0.35), VO_AT["l12"] + 3.0, 0.4)
    for tr, *_ in HINTS:
        add(s, E2.pop_sfx(780), tr, 0.22)
    return s


def voice_track():
    n = int((DUR + 1) * SR)
    v = np.zeros(n)
    keys = list(VO_AT)
    for i, key in enumerate(keys):
        path = os.path.join(WORK, f"vo_{key}.wav")
        if not os.path.exists(path):
            continue
        a, _ = sf.read(path)
        start = VO_AT[key]
        end = VO_AT[keys[i + 1]] - 0.08 if i + 1 < len(keys) else DUR - 0.25
        rate = (len(a) / SR) / (end - start)
        if rate > 1.0:
            tmp = os.path.join(WORK, f"fit_{key}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", f"atempo={rate:.4f}", tmp], check=True)
            a, _ = sf.read(tmp)
        add(v, a, start)
        print(f"  vo {key:5s} {start:6.2f}-{start + len(a) / SR:6.2f}s")
    return v


def build_audio(path, with_voice):
    m, s = lofi(), sfx_track()
    v = voice_track() if with_voice else np.zeros_like(m)
    m /= np.abs(m).max() + 1e-9
    s /= np.abs(s).max() + 1e-9
    if v.any():
        env = signal.lfilter([1 - math.exp(-1 / (0.25 * SR))], [1, -math.exp(-1 / (0.25 * SR))], np.abs(v))
        env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
        mix = m * 0.42 * (1 - 0.5 * env) + s * 0.5 * (1 - 0.25 * env) + v / np.abs(v).max() * 0.95
    else:
        mix = m * 0.6 + s * 0.6
    mix = mix[: int(DUR * SR)]
    fade = int(0.4 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    sf.write(path, np.stack([mix, mix], 1).astype(np.float32), SR)


# ---------------------------------------------------------------- thumbnail
def thumbnail(path):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sc_hook(L, 2.0, 2.0)
    paste(L, gtext("int • float • str • list • dict", 46, CHALK), 540, 960)
    base = glass_base().astype(np.float32)
    la = np.asarray(L, np.float32)
    al = la[..., 3:4] / 255
    frame = (base + bloom(L) * 0.85) * (1 - al) + la[..., :3] * al
    frame = gloss(np.clip(frame, 0, 255).astype(np.uint8), 0.0)
    img = Image.fromarray(frame).convert("RGBA")
    paste(img, title_box(), 540, 95)
    paste(img, side_ep(), 34, H / 2)
    paste(img, mascot(False, "wow", 300), 900, 1700)
    paste(img, bubble("Cheat sheet!", 40), 690, 1450)
    img.convert("RGB").save(path, quality=92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    glass_base()
    E2.board_base()
    thumbnail(os.path.join(OUT, "thumbnail.jpg"))
    if args.preview:
        ts = np.linspace(0.5, DUR - 0.2, 32)
        sheet = Image.new("RGB", (216 * 8, 384 * 4))
        for k, t in enumerate(ts):
            sheet.paste(Image.fromarray(render(t)).resize((216, 384)), ((k % 8) * 216, (k // 8) * 384))
        sheet.save(os.path.join(WORK, "preview.jpg"), quality=85)
        print("wrote", os.path.join(WORK, "preview.jpg"))
        return
    silent = os.path.join(WORK, "video.mp4")
    nf = int(round(DUR * FPS))
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
        wav = os.path.join(WORK, f"mix{suffix}.wav")
        build_audio(wav, voice)
        out = os.path.join(OUT, f"{NAME}{suffix}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
                        "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
        print("wrote", out)


if __name__ == "__main__":
    main()
