#!/usr/bin/env python3
"""EP01 "Python kya hai?" re-themed to the dark cutting-mat look (music + SFX, no voice-over).

Theme decoded from the WhatsApp reference reel (The IOT Engineer, ESP32 + OLED):
dark teal cutting-mat grid seen in perspective, white bold captions with the
keyword in yellow / cyan / green, a cyan subtitle pill, dark glass cards with
thin cyan borders, OLED-style dark screens, blur-focus transitions between
scenes, a channel tag pill top-right, a blue/yellow progress bar, and an end
screen where a hand taps LIKE -> LIKED, SHARE -> green, SUBSCRIBE -> SUBSCRIBED
over a darkened, blurred background.

Timeline: 0.94 s thumbnail -> 25 s lesson (beat-synced, same story as the light
version) -> 4.2 s LIKE / SHARE / SUBSCRIBE.

Everything is drawn procedurally; the music and SFX are synthesised.
Run:   python3 pathshala/ep01-dark-mat/build.py [--preview]
Needs: pip install numpy scipy opencv-python-headless pillow soundfile ; ffmpeg.
Output: output/PythonKiPathshala-EP01-Dark.mp4 and output/thumbnail.jpg
"""
import argparse
import math
import os
import re
import subprocess
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
WORK = os.path.join(HERE, "work")
MONT = os.path.join(HERE, "..", "..", "edit", "assets", "fonts", "Montserrat-Black.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAME = "PythonKiPathshala-EP01-Dark.mp4"

W, H, FPS = 1080, 1920, 30
SR = 48000
BPM = 128
BEAT = 60 / BPM


def kb(k):
    """Time of beat k on the lesson's music grid (lesson time, not video time)."""
    return k * BEAT


INTRO = 2 * BEAT                   # thumbnail hold, two beats so the grid stays continuous
DUR = 25.0                         # lesson
OUTRO = 9 * BEAT                   # LIKE / SHARE / SUBSCRIBE (~4.2 s)
TOTAL = INTRO + DUR + OUTRO
SCENES = [("hook", 0), ("ask", 6), ("drop", 11), ("def", 14), ("simple", 24),
          ("uses", 33), ("best", 41), ("end", 49)]
CUTS = [kb(b) for _, b in SCENES] + [DUR]
SLAM = kb(47)

# ---------------------------------------------------------------- palette
INK = (255, 255, 255)              # text on the mat
NAVY = (15, 27, 61)                # text on yellow / white pills
BLUE = (40, 120, 230)
YELLOW = (255, 210, 50)
CYAN = (40, 210, 240)
RED = (238, 60, 60)
GREEN = (40, 190, 100)
PURPLE = (160, 110, 240)
GRAY = (140, 150, 165)
WHITE = (255, 255, 255)
GLASS = (16, 24, 32)               # card fill
SCREEN = (8, 12, 16)               # OLED screen
HL = [YELLOW, CYAN, GREEN]         # caption keyword colours, rotated per line
# per-scene mat colour (keeps the reference's per-scene tint shifts)
TINTS = {"hook": (22, 74, 66), "ask": (18, 62, 70), "drop": (24, 80, 64), "def": (20, 70, 68),
         "simple": (18, 64, 62), "uses": (22, 74, 66), "best": (26, 78, 60), "end": (18, 62, 70)}

# ---------------------------------------------------------------- captions (no voice: timed to read)
# key: (start, end) of the caption block; *word* = coloured keyword
VO = {
    "hook": (0.10, kb(6) - 0.05),
    "ask": (kb(6) + 0.08, kb(11) - 0.06),
    "drop": (kb(11) + 0.03, kb(14) - 0.05),
    "def": (kb(14) + 0.10, kb(24) - 0.06),
    "simple": (kb(24) + 0.08, kb(33) - 0.06),
    "uses": (kb(33) + 0.08, kb(41) - 0.06),
    "best": (kb(41) + 0.06, kb(47) - 0.08),
    "python": (kb(47), kb(49) - 0.05),
    "end": (kb(49) + 0.10, DUR - 0.12),
}
CAPS = {
    "hook": ["COMPUTER SIRF", "*0 AUR 1*", "SAMAJHTA HAI!"],
    "ask": ["TOH HUM USSE", "BAAT *KAISE*", "KAREIN?"],
    "drop": ["*PYTHON* SE!"],
    "def": ["PYTHON EK", "*PROGRAMMING*", "LANGUAGE HAI,", "JISSE COMPUTER KO", "*KAAM* BOLTE HAIN."],
    "simple": ["AUR YEH BILKUL", "*ENGLISH* JAISI", "*SIMPLE* HAI.", "PADHTE HI", "*SAMAJH* AA GAYA NA?"],
    "uses": ["ISSE BANTE HAIN", "*WEBSITES*,", "*AI*,", "*DATA*", "AUR *AUTOMATION*!"],
    "best": ["ISLIYE BEGINNERS KI", "*NO.1* CHOICE HAI..."],
    "python": ["*PYTHON!*"],
    "end": ["NEXT: *print()*", "*FOLLOW* KARO!"],
}
KEY_ORDER = list(CAPS)


@lru_cache(None)
def cap_times(key):
    """Start time of each chunk, spread over the block by length (reading pace)."""
    chunks = CAPS[key]
    wts = [len(c.replace("*", "")) + (3 if c.rstrip()[-1] in ",.!?" else 1) for c in chunks]
    start, end = VO[key]
    d = (end - start) * 0.9
    out, acc = [], 0.0
    for w in wts:
        out.append(start + d * acc / sum(wts))
        acc += w
    return out


def cap_t(key, i):
    return cap_times(key)[i]


def active_caption(t):
    best = None
    for key in CAPS:
        if t < VO[key][0] - 0.02:
            continue
        for i, ts in enumerate(cap_times(key)):
            if t >= ts - 0.02:
                best = (key, i, ts)
    if best is None or t > VO[best[0]][1] + 0.4:
        return None
    return best


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def pop(age, dur=0.32, over=0.14):
    if age < 0:
        return 0.0
    x = clamp(age / dur)
    if x >= 1:
        return 1.0
    return 1 + (over * math.sin(math.pi * x) - (1 - x) ** 2.4) if x > 0 else 0.0


def back_out(x, s=2.2):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def scene_at(t):
    for i in range(len(SCENES)):
        if CUTS[i] <= t < CUTS[i + 1]:
            return SCENES[i][0], t - CUTS[i], i
    return SCENES[-1][0], t - CUTS[-2], len(SCENES) - 1


# ---------------------------------------------------------------- sprites
@lru_cache(None)
def font(size, which="mont"):
    return ImageFont.truetype({"mont": MONT, "mono": MONO, "sans": SANS}[which], size)


def ss_finish(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def with_shadow(im, blur=18, offset=(0, 14), alpha=150, pad=40):
    w, h = im.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(a)
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


@lru_cache(None)
def card(w, h, r=30, fill=GLASS, border=CYAN, bw=3, alpha=225, shadow=True):
    """Dark glass panel with a thin glowing border."""
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, fill=fill + (alpha,),
                        outline=(border + (255,)) if border else None, width=bw * S if border else 0)
    im = ss_finish(im, w, h)
    if border:
        glow = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((20, 20, w + 19, h + 19), r, outline=border + (110,), width=8)
        glow = glow.filter(ImageFilter.GaussianBlur(9))
        glow.alpha_composite(im, (20, 20))
        im = glow
    return with_shadow(im, pad=40) if shadow else im


@lru_cache(None)
def text(s, size, color=INK, which="mont", stroke=0):
    f = font(size, which)
    x0, y0, x1, y1 = f.getbbox(s, stroke_width=stroke)
    im = Image.new("RGBA", (x1 - x0 + 8, y1 - y0 + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - x0, 4 - y0), s, font=f, fill=color + (255,), stroke_width=stroke,
                            stroke_fill=(0, 0, 0, 255))
    return im


@lru_cache(None)
def pill(s, size, fg=NAVY, bg=YELLOW, border=None, padx=30, pady=16, which="mont", shadow=True):
    t = text(s, size, fg, which)
    w, h = t.width + 2 * padx, t.height + 2 * pady
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=bg + (255,),
                        outline=(border + (255,)) if border else None, width=6 if border else 0)
    im = ss_finish(im, w, h)
    im.alpha_composite(t, (padx, pady))
    return with_shadow(im, blur=10, offset=(0, 8), alpha=150, pad=24) if shadow else im


SEG_RE = re.compile(r"\*[^*]+\*|[^*\s]+")


@lru_cache(None)
def caption(chunk, hl_col=YELLOW, maxw=990):
    """White bold caption with a dark outline; the *keyword* is coloured."""
    segs = [(m[1:-1], True) if m.startswith("*") else (m, False) for m in SEG_RE.findall(chunk)]
    size = 96
    while True:
        f = font(size)
        sp = f.getlength(" ")
        widths = [f.getlength(s) for s, _ in segs]
        total = sum(widths) + sp * (len(segs) - 1)
        if total <= maxw or size <= 50:
            break
        size -= 4
    S = 2
    fS = font(size * S)
    asc, desc = fS.getmetrics()
    sw = 5 * S
    im = Image.new("RGBA", (int(total * S) + 60, asc + desc + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 30
    for (s, hl), wd in zip(segs, widths):
        d.text((x, 20), s, font=fS, fill=(hl_col if hl else INK) + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
        x += int((wd + sp) * S)
    im = ss_finish(im, im.width // S, im.height // S)
    return with_shadow(im, blur=10, offset=(0, 8), alpha=170, pad=24)


@lru_cache(None)
def monitor(w, h):
    """Dark monitor with an OLED-black screen."""
    S = 2
    bez = 22
    tw, th = w + 2 * bez, h + 2 * bez + 150
    im = Image.new("RGBA", (tw * S, th * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw * S - 1, (h + 2 * bez) * S), 30 * S, fill=(44, 50, 60, 255),
                        outline=(90, 100, 115, 255), width=3 * S)
    d.rounded_rectangle((bez * S, bez * S, (bez + w) * S, (bez + h) * S), 12 * S, fill=SCREEN + (255,),
                        outline=CYAN + (120,), width=2 * S)
    cx = tw * S // 2
    d.polygon([(cx - 50 * S, (h + 2 * bez) * S), (cx + 50 * S, (h + 2 * bez) * S),
               (cx + 70 * S, (th - 30) * S), (cx - 70 * S, (th - 30) * S)], fill=(44, 50, 60, 255))
    d.rounded_rectangle((cx - 150 * S, (th - 38) * S, cx + 150 * S, (th - 6) * S), 14 * S, fill=(60, 66, 78, 255))
    return with_shadow(ss_finish(im, tw, th))


def monitor_screen_origin(cx, cy, w, h):
    spr = monitor(w, h)
    return int(cx - spr.width / 2 + 40 + 22), int(cy - spr.height / 2 + 40 + 22)


@lru_cache(None)
def person(r=110):
    S = 2
    D = 2 * r * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=BLUE + (255,), outline=CYAN + (255,), width=5 * S)
    c = D // 2
    d.ellipse((c - 34 * S, c - 62 * S, c + 34 * S, c + 6 * S), fill=WHITE + (255,))
    d.chord((c - 66 * S, c + 14 * S, c + 66 * S, c + 140 * S), 180, 360, fill=WHITE + (255,))
    im = ss_finish(im, 2 * r, 2 * r)
    lab = text("YOU", 34, INK)
    out = Image.new("RGBA", (2 * r, 2 * r + 60), (0, 0, 0, 0))
    out.alpha_composite(im, (0, 0))
    out.alpha_composite(lab, (r - lab.width // 2, 2 * r + 12))
    return with_shadow(out, blur=12)


@lru_cache(None)
def py_badge(size=380):
    """Stylised two-tone 'Py' block badge (original artwork, not the official logo)."""
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 10
    d.rounded_rectangle((u * 0.6, u * 0.6, u * 6.4, u * 6.4), int(u * 1.6), fill=BLUE + (255,),
                        outline=WHITE + (255,), width=int(u * 0.22))
    d.rounded_rectangle((u * 3.6, u * 3.6, u * 9.4, u * 9.4), int(u * 1.6), fill=YELLOW + (255,),
                        outline=WHITE + (255,), width=int(u * 0.22))
    d.rounded_rectangle((u * 3.6, u * 3.6, u * 6.4, u * 6.4), int(u * 0.5), fill=WHITE + (255,))
    d.ellipse((u * 1.6, u * 1.6, u * 2.6, u * 2.6), fill=WHITE + (255,))
    d.ellipse((u * 7.4, u * 7.4, u * 8.4, u * 8.4), fill=NAVY + (255,))
    d.text((u * 5.0, u * 5.0), "Py", font=font(int(u * 2.0)), fill=NAVY + (255,), anchor="mm")
    return with_shadow(ss_finish(im, size, size), blur=22)


@lru_cache(None)
def rays(size=1700, n=18, color=CYAN, alpha=90):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n * 0.9
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=color + (alpha,))
    yy, xx = np.mgrid[0:size, 0:size]
    fade = np.clip(1.15 - np.hypot(xx - c, yy - c) / c, 0, 1) ** 1.3
    im.putalpha(Image.fromarray((np.asarray(im.getchannel("A"), np.float32) * fade).astype(np.uint8)))
    return im


@lru_cache(None)
def check_badge(r=56, ok=True):
    S = 2
    D = 2 * r * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=(GREEN if ok else RED) + (255,), outline=WHITE + (255,), width=4 * S)
    w = int(D * 0.09)
    if ok:
        d.line([(D * 0.27, D * 0.52), (D * 0.44, D * 0.68), (D * 0.74, D * 0.34)], fill=WHITE + (255,),
               width=w, joint="curve")
    else:
        d.line([(D * 0.32, D * 0.32), (D * 0.68, D * 0.68)], fill=WHITE + (255,), width=w)
        d.line([(D * 0.68, D * 0.32), (D * 0.32, D * 0.68)], fill=WHITE + (255,), width=w)
    return with_shadow(ss_finish(im, 2 * r, 2 * r), blur=8, pad=20)


def icon(kind, size=150, phase=0.0, color=WHITE):
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = int(s * 0.06)
    col = color + (255,)
    c = s / 2
    if kind == "globe":
        R = s * 0.42
        d.ellipse((c - R, c - R, c + R, c + R), outline=CYAN + (255,), width=lw)
        d.line([(c - R, c), (c + R, c)], fill=col, width=lw)
        for k in (-1, 1):
            d.line([(c - R * 0.86, c + k * R * 0.5), (c + R * 0.86, c + k * R * 0.5)], fill=col, width=lw // 2)
        for off in (phase % 1.0, (phase + 0.5) % 1.0):
            rx = abs(math.cos(math.pi * off)) * R
            d.ellipse((c - rx, c - R, c + rx, c + R), outline=col, width=lw // 2 + 2)
    elif kind == "chip":
        R = s * 0.27
        g = 0.75 + 0.25 * math.sin(phase * 2 * math.pi)
        for i in range(4):
            p = c - R + (i + 0.5) * 2 * R / 4
            for a, b in (((p, c - R - s * 0.12), (p, c - R)), ((p, c + R), (p, c + R + s * 0.12)),
                         ((c - R - s * 0.12, p), (c - R, p)), ((c + R, p), (c + R + s * 0.12, p))):
                d.line([a, b], fill=col, width=lw // 2 + 2)
        d.rounded_rectangle((c - R, c - R, c + R, c + R), int(s * 0.05), fill=(int(255 * g), 210, 50, 255),
                            outline=col, width=lw)
        d.text((c, c), "AI", font=font(int(s * 0.2)), fill=NAVY + (255,), anchor="mm")
    elif kind == "chart":
        base = s * 0.82
        for i, hgt in enumerate([0.35, 0.55, 0.45, 0.75]):
            grow = ease_out(phase * 1.6 - i * 0.15)
            x0 = s * (0.14 + i * 0.19)
            d.rounded_rectangle((x0, base - s * hgt * grow, x0 + s * 0.13, base), int(s * 0.02),
                                fill=(CYAN if i % 2 else GREEN) + (255,))
        d.line([(s * 0.08, base), (s * 0.92, base)], fill=col, width=lw)
    elif kind == "gear":
        n = 8
        Ro, Ri = s * 0.42, s * 0.32
        pts = []
        for i in range(n * 4):
            a = phase * 2 * math.pi / n * 2 + 2 * math.pi * i / (n * 4)
            r = Ro if (i % 4) in (1, 2) else Ri
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=PURPLE + (255,), outline=col)
        d.ellipse((c - s * 0.13, c - s * 0.13, c + s * 0.13, c + s * 0.13), fill=GLASS + (255,), outline=col,
                  width=lw // 2)
    return ss_finish(im, size, size)


@lru_cache(None)
def trophy(size=420):
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = int(s * 0.015)
    o = WHITE + (255,)
    d.arc((s * 0.08, s * 0.14, s * 0.38, s * 0.48), 90, 270, fill=YELLOW + (255,), width=int(s * 0.04))
    d.arc((s * 0.62, s * 0.14, s * 0.92, s * 0.48), 270, 90, fill=YELLOW + (255,), width=int(s * 0.04))
    d.chord((s * 0.2, -s * 0.22, s * 0.8, s * 0.62), 0, 180, fill=YELLOW + (255,), outline=o, width=lw)
    d.rectangle((s * 0.2, s * 0.08, s * 0.8, s * 0.2), fill=YELLOW + (255,), outline=o, width=lw)
    d.rectangle((s * 0.45, s * 0.6, s * 0.55, s * 0.74), fill=YELLOW + (255,), outline=o, width=lw)
    d.rounded_rectangle((s * 0.28, s * 0.74, s * 0.72, s * 0.9), int(s * 0.03), fill=BLUE + (255,), outline=o,
                        width=lw)
    d.text((s * 0.5, s * 0.33), "#1", font=font(int(s * 0.17)), fill=NAVY + (255,), anchor="mm")
    return with_shadow(ss_finish(im, size, size), blur=16)


@lru_cache(None)
def star(r=34, color=YELLOW):
    S = 2
    D = 2 * r * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = D / 2 if i % 2 == 0 else D / 4.6
        pts.append((D / 2 + rr * math.cos(a), D / 2 + rr * math.sin(a)))
    d.polygon(pts, fill=color + (255,), outline=WHITE + (255,), width=2 * S)
    return ss_finish(im, 2 * r, 2 * r)


@lru_cache(None)
def hand(size=120):
    """Pointing hand cursor (index finger up), like the reference's tap hand."""
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    skin, o = (255, 205, 80, 255), (60, 40, 10, 255)
    w = 4 * S
    d.rounded_rectangle((s * 0.36, s * 0.02, s * 0.54, s * 0.62), int(s * 0.09), fill=skin, outline=o, width=w)
    for i, top in enumerate((0.36, 0.40, 0.46)):
        x0 = s * (0.54 + i * 0.14)
        d.rounded_rectangle((x0 - s * 0.02, s * top, x0 + s * 0.14, s * 0.7), int(s * 0.07), fill=skin, outline=o,
                            width=w)
    d.rounded_rectangle((s * 0.2, s * 0.44, s * 0.38, s * 0.72), int(s * 0.08), fill=skin, outline=o, width=w)
    d.rounded_rectangle((s * 0.24, s * 0.56, s * 0.94, s * 0.98), int(s * 0.16), fill=skin, outline=o, width=w)
    d.rectangle((s * 0.38, s * 0.5, s * 0.9, s * 0.66), fill=skin)
    return with_shadow(ss_finish(im, size, size), blur=6, pad=16)


@lru_cache(None)
def cursor(size=90):
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(0.1, 0.05), (0.1, 0.8), (0.3, 0.62), (0.45, 0.95), (0.58, 0.89), (0.43, 0.57), (0.7, 0.55)]
    d.polygon([(x * s, y * s) for x, y in pts], fill=WHITE + (255,), outline=(0, 0, 0, 255), width=5 * S)
    return with_shadow(ss_finish(im, size, size), blur=6, pad=16)


def ui_icon(kind, size, col):
    """Thumb / share-arrow / bell glyphs for the end-screen buttons."""
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = col + (255,)
    if kind == "like":
        d.rounded_rectangle((s * 0.05, s * 0.45, s * 0.28, s * 0.95), int(s * 0.05), fill=c)
        d.rounded_rectangle((s * 0.34, s * 0.42, s * 0.95, s * 0.95), int(s * 0.12), fill=c)
        d.polygon([(s * 0.34, s * 0.5), (s * 0.5, s * 0.05), (s * 0.66, s * 0.12), (s * 0.6, s * 0.45)], fill=c)
    elif kind == "share":
        w = int(s * 0.13)
        d.line([(s * 0.15, s * 0.85), (s * 0.8, s * 0.2)], fill=c, width=w)
        d.polygon([(s * 0.42, s * 0.12), (s * 0.9, s * 0.1), (s * 0.88, s * 0.58)], fill=c)
    elif kind == "bell":
        d.chord((s * 0.18, s * 0.08, s * 0.82, s * 0.9), 180, 360, fill=c)
        d.rectangle((s * 0.18, s * 0.48, s * 0.82, s * 0.74), fill=c)
        d.polygon([(s * 0.08, s * 0.8), (s * 0.92, s * 0.8), (s * 0.82, s * 0.7), (s * 0.18, s * 0.7)], fill=c)
        d.ellipse((s * 0.4, s * 0.8, s * 0.6, s * 0.98), fill=c)
    return ss_finish(im, size, size)


@lru_cache(None)
def ui_button(label, kind, bg, fg, w=640, h=132):
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=bg + (255,))
    im = ss_finish(im, w, h)
    ic = ui_icon(kind, 66, YELLOW if kind in ("like", "bell") and bg in (WHITE, RED, (70, 74, 82)) else fg)
    t = text(label, 58, fg)
    x0 = (w - (ic.width + 22 + t.width)) // 2
    im.alpha_composite(ic, (x0, (h - ic.height) // 2))
    im.alpha_composite(t, (x0 + ic.width + 22, (h - t.height) // 2))
    return with_shadow(im, blur=12, offset=(0, 10), alpha=170, pad=30)


# ---------------------------------------------------------------- code text (dark editor colours)
KW, STR, FN, TXT, OP = (198, 120, 221), (152, 205, 121), (97, 175, 239), (230, 235, 240), (150, 160, 175)
CODE = [
    [("mausam", TXT), (" = ", OP), ('"barish"', STR)],
    [("if ", KW), ("mausam", TXT), (" == ", OP), ('"barish"', STR), (":", OP)],
    [("    ", TXT), ("print", FN), ("(", OP), ('"Chhata le lo!"', STR), (")", OP)],
]
CODE_CHARS = [sum(len(s) for s, _ in line) for line in CODE]
CODE_TYPE_START, CODE_CPS = 0.25, 26.0


@lru_cache(None)
def code_line(li, n, size=44):
    f = font(size, "mono")
    im = Image.new("RGBA", (1000, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x, left = 0, n
    for s, col in CODE[li]:
        part = s[:max(0, left)]
        if part:
            d.text((x, 4), part, font=f, fill=col + (255,))
            x += f.getlength(part)
        left -= len(s)
    return im, x


# ---------------------------------------------------------------- compositing helpers
def paste(L, spr, cx, cy, s=1.0, a=1.0, rot=0.0):
    if a <= 0.01 or s <= 0.01:
        return
    im = spr
    if abs(s - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if a < 0.99:
        im = im.copy()
        im.putalpha(im.getchannel("A").point([int(v * a) for v in range(256)]))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(L.width, x + im.width), min(L.height, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return
    L.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


CONF_COLS = [YELLOW, CYAN, RED, GREEN, PURPLE, WHITE]


def confetti(L, age, cx, cy, n=60, seed=1, spread=900):
    if age < 0 or age > 1.6:
        return
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(L)
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(0.35, 1.0) * spread
        col = CONF_COLS[rng.integers(len(CONF_COLS))]
        sz = rng.uniform(10, 22)
        spin = rng.uniform(-8, 8)
        x = cx + math.cos(ang) * sp * (1 - math.exp(-age * 4))
        y = cy + math.sin(ang) * sp * (1 - math.exp(-age * 4)) + 700 * age * age
        a = clamp(1.6 - age) * 255
        th = spin * age
        pts = [(x + sz * math.cos(th + k * math.pi / 2 + 0.5) * (1 if k % 2 else 0.5),
                y + sz * math.sin(th + k * math.pi / 2 + 0.5) * (1 if k % 2 else 0.5)) for k in range(4)]
        d.polygon(pts, fill=col + (int(a),))


def dashed(d, p0, p1, phase, col=CYAN, w=6, dash=22, gap=16):
    L = math.dist(p0, p1)
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    s = -((phase * (dash + gap)) % (dash + gap))
    while s < L:
        a, b = max(0, s), min(L, s + dash)
        if b > a:
            d.line([(p0[0] + ux * a, p0[1] + uy * a), (p0[0] + ux * b, p0[1] + uy * b)], fill=col + (255,), width=w)
        s += dash + gap


# ---------------------------------------------------------------- background: cutting mat in perspective
MAT_W, MAT_H = 2200, 2600


@lru_cache(None)
def mat_lines():
    """Grid line mask (float 0..1) for a flat cutting mat, plus ruler ticks on one edge."""
    m = Image.new("L", (MAT_W, MAT_H), 0)
    d = ImageDraw.Draw(m)
    step = 64
    for i in range(0, MAT_W, step):
        d.line([(i, 0), (i, MAT_H)], fill=255 if (i // step) % 5 == 0 else 120, width=3 if (i // step) % 5 == 0 else 2)
    for j in range(0, MAT_H, step):
        d.line([(0, j), (MAT_W, j)], fill=255 if (j // step) % 5 == 0 else 120, width=3 if (j // step) % 5 == 0 else 2)
    for j in range(0, MAT_H, step // 4):
        d.line([(0, j), (28 if j % step else 56, j)], fill=200, width=2)
    return np.asarray(m, np.float32) / 255.0


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = np.clip(1.0 - np.hypot((XX - W / 2) / W, (YY - H * 0.42) / H) * 1.25, 0, 1)[..., None]


def tint_at(t):
    name, tl, i = scene_at(t)
    cur = np.array(TINTS[name], np.float32)
    if i > 0 and tl < 0.3:
        prev = np.array(TINTS[SCENES[i - 1][0]], np.float32)
        cur = prev + (cur - prev) * ease(tl / 0.3)
    return cur


def mat_frame(t, tint):
    """Perspective view of the mat; the camera drifts slowly across it."""
    lines = mat_lines()
    ox = 300 + 60 * math.sin(t * 0.25)
    oy = 200 + 40 * t
    src = np.float32([[ox, oy], [ox + 1600, oy], [ox + 1600, oy + 2000], [ox, oy + 2000]])
    tilt = 230
    dst = np.float32([[-tilt, -60], [W + tilt, -60], [W + 60, H + 40], [-60, H + 40]])
    M = cv2.getPerspectiveTransform(src, dst)
    g = cv2.warpPerspective(lines, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)[..., None]
    base = tint[None, None, :] * (0.55 + 0.75 * VIGN)
    lc = np.minimum(tint * 1.9 + 25, 255)
    img = base * (1 - 0.55 * g) + lc * 0.55 * g
    # darker top (like the reference's depth-of-field falloff)
    img *= (0.7 + 0.3 * np.clip(YY / (H * 0.35), 0, 1))[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


def background(t):
    return Image.fromarray(mat_frame(t, tint_at(t)), "RGB").convert("RGBA")


# ---------------------------------------------------------------- scenes (lesson time t)
def sc_hook(L, t, tl):
    d = ImageDraw.Draw(L)
    cx, cy, sw, sh = 540, 1010, 600, 380
    s = 0.86 + 0.14 * back_out(tl / 0.35)
    paste(L, monitor(sw, sh), cx, cy, s)
    if s > 0.98:
        ox, oy = monitor_screen_origin(cx, cy, sw, sh)
        scr = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        sd = ImageDraw.Draw(scr)
        f = font(40, "mono")
        rng = np.random.default_rng(3)
        for col in range(11):
            spd = rng.uniform(140, 320)
            off = rng.uniform(0, 400)
            for row in range(-1, 9):
                y = (row * 48 + off + tl * spd) % (sh + 48) - 48
                bit = "01"[(col * 7 + row * 3 + int(tl * 6)) % 2]
                c = CYAN if (col + row) % 3 else GREEN
                sd.text((14 + col * 53, y), bit, font=f, fill=c + (230,))
        L.alpha_composite(scr, (ox, oy))
    t01 = cap_t("hook", 1)
    for k, (lab, bg, x) in enumerate((("0", YELLOW, 250), ("1", CYAN, 830))):
        age = t - t01 - k * 0.12
        if age > 0:
            yb = 1490 - 18 * math.sin((t - t01) * 5 + k)
            paste(L, pill(lab, 120, fg=NAVY, bg=bg, padx=44, pady=26), x, yb, pop(age), rot=(-8 if k == 0 else 8))
    rng = np.random.default_rng(11)
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(520, 720)
        ph = (tl * rng.uniform(0.35, 0.6) + rng.uniform(0, 1)) % 1
        r = r0 * (1 - ph)
        x, y = cx + r * math.cos(a), cy - 40 + r * math.sin(a) * 1.2
        if r > 280:
            d.text((x, y), "01"[i % 2], font=font(54, "mono"), fill=(CYAN if i % 2 else YELLOW) + (int(200 * ph + 40),),
                   anchor="mm")


def sc_ask(L, t, tl):
    d = ImageDraw.Draw(L)
    px, mx, y = 250, 790, 1060
    paste(L, person(), px, y + 25, pop(tl, 0.3))
    mw, mh = 360, 240
    paste(L, monitor(mw, mh), mx, y, pop(tl - 0.08, 0.3))
    if tl > 0.2:
        dashed(d, (px + 125, y - 20), (mx - 210, y - 20), tl * 2.5, w=7)
    age = tl - 0.35
    if age > 0:
        paste(L, pill("Hello!", 56, fg=NAVY, bg=WHITE, padx=34, pady=20), px + 20, y - 240, pop(age))
    if tl > 0.25:
        ox, oy = monitor_screen_origin(mx, y, mw, mh)
        jit = 6 * math.sin(tl * 40) if 0.9 < tl < 1.3 else 0
        q = text("???", 96, RED)
        L.alpha_composite(q, (int(ox + mw / 2 - q.width / 2 + jit), int(oy + mh / 2 - q.height / 2)))
    age = tl - 0.7
    if age > 0:
        paste(L, pill("?", 120, fg=NAVY, bg=YELLOW, padx=46, pady=18), 520, 1380 - abs(math.sin(age * 7)) * 70,
              pop(age), rot=8 * math.sin(age * 5))


def sc_drop(L, t, tl):
    paste(L, rays(color=YELLOW, alpha=70).rotate(tl * 25, Image.BICUBIC), 540, 930, 0.6 + 0.4 * ease_out(tl / 0.4))
    paste(L, py_badge(), 540, 900, 1.25 * back_out(tl / 0.38))
    age = tl - 0.18
    if age > 0:
        paste(L, pill("Python", 150, fg=NAVY, bg=YELLOW, padx=48, pady=24), 540, 1270, pop(age, 0.3), rot=-3)
    age = tl - 0.5
    if age > 0:
        paste(L, pill("Simple  •  Powerful  •  Free", 40, fg=NAVY, bg=CYAN, padx=34, pady=14), 540,
              1420 + 30 * (1 - ease_out(age / 0.3)), 1, a=ease(age / 0.25))
    confetti(L, tl, 540, 900, n=70, seed=3)


def sc_def(L, t, tl):
    d = ImageDraw.Draw(L)
    age = t - cap_t("def", 1)
    paste(L, pill("PROGRAMMING LANGUAGE", 50, fg=NAVY, bg=CYAN, padx=36, pady=20), 540, 700,
          pop(age) if age > 0 else 0)
    px, mx, y = 210, 790, 1060
    mw, mh = 400, 270
    paste(L, person(), px, y + 25, pop(tl, 0.3))
    paste(L, monitor(mw, mh), mx, y, pop(tl - 0.06, 0.3))
    p0, p1 = (px + 120, y - 20), (mx - 230, y - 20)
    if tl > 0.15:
        dashed(d, p0, p1, tl * 2.0, col=CYAN, w=6)
    t_go, t_arrive = cap_t("def", 3) - 0.3, cap_t("def", 3) + 0.45
    u = ease((t - t_go) / (t_arrive - t_go))
    if t_go - 0.25 < t < t_arrive + 0.15:
        chip = pill('print("Hi!")', 38, fg=NAVY, bg=WHITE, border=CYAN, padx=22, pady=14, which="mono")
        x = p0[0] + (p1[0] - p0[0]) * u + 40
        paste(L, chip, x, y - 20 - 60 * math.sin(math.pi * u), pop(t - t_go + 0.25, 0.25),
              a=1 - clamp((t - t_arrive) / 0.15))
    ox, oy = monitor_screen_origin(mx, y, mw, mh)
    if t > t_arrive:
        n = min(3, int((t - t_arrive) * 12) + 1)
        s = text("Hi!"[:n] + ("_" if int(t * 4) % 2 else " "), 92, CYAN, "mono")
        L.alpha_composite(s, (int(ox + 40), int(oy + mh / 2 - s.height / 2)))
        paste(L, check_badge(), mx + 200, y - 160, pop(t - t_arrive - 0.3))
    age = t - cap_t("def", 4)
    if age > 0:
        lab = pill("instructions  =  code", 44, fg=NAVY, bg=YELLOW, padx=34, pady=18, which="mono")
        paste(L, lab, 540, 1380 + 40 * (1 - ease_out(age / 0.3)), 1, a=ease(age / 0.2))


CODE_W, CODE_H = 940, 420


def code_type_n(tl):
    return int(max(0.0, tl - CODE_TYPE_START) * CODE_CPS)


def sc_simple(L, t, tl):
    cx, cy = 540, 960
    s = 0.85 + 0.15 * back_out(tl / 0.3)
    paste(L, card(CODE_W, CODE_H, r=26, fill=(22, 26, 34), alpha=245), cx, cy, s)
    if s < 0.99:
        return
    x0, y0 = int(cx - CODE_W / 2), int(cy - CODE_H / 2)
    d = ImageDraw.Draw(L)
    for k, col in enumerate((RED, YELLOW, GREEN)):
        d.ellipse((x0 + 34 + k * 40, y0 + 30, x0 + 58 + k * 40, y0 + 54), fill=col + (255,))
    L.alpha_composite(text("mausam.py", 30, GRAY, "mono"), (x0 + 170, y0 + 26))
    d.line([(x0 + 6, y0 + 80), (x0 + CODE_W - 6, y0 + 80)], fill=(50, 58, 70, 255), width=3)
    n = code_type_n(tl)
    for li in range(3):
        L.alpha_composite(text(str(li + 1), 34, (90, 100, 115), "mono"), (x0 + 30, y0 + 120 + li * 90))
        k = min(n, CODE_CHARS[li])
        if k > 0:
            im, w = code_line(li, k)
            L.alpha_composite(im, (x0 + 80, y0 + 112 + li * 90))
            if n < sum(CODE_CHARS) and n - k <= 0 and int(t * 6) % 2:
                d.rectangle((x0 + 84 + w, y0 + 118 + li * 90, x0 + 104 + w, y0 + 166 + li * 90), fill=CYAN + (255,))
        n -= CODE_CHARS[li]
    t_out = CODE_TYPE_START + sum(CODE_CHARS) / CODE_CPS + 0.25
    age = tl - t_out
    if age > 0:
        paste(L, card(CODE_W, 170, r=24, fill=(4, 6, 8), border=GREEN, alpha=250), cx,
              1330 + 40 * (1 - ease_out(age / 0.25)), 1, a=ease(age / 0.15))
        if age > 0.12:
            L.alpha_composite(text("$ python mausam.py", 32, GRAY, "mono"), (x0 + 36, 1272))
            L.alpha_composite(text("Chhata le lo!", 46, GREEN, "mono"), (x0 + 36, 1322))
    age = t - cap_t("simple", 1)
    if age > 0:
        paste(L, pill("English jaisa!", 52, fg=NAVY, bg=YELLOW, padx=30, pady=16), 760, 700, pop(age), rot=-7)
    age = t - cap_t("simple", 4)
    if age > 0:
        paste(L, check_badge(70), 920, 1080, pop(age), rot=-10 * (1 - clamp(age / 0.3)))


TILES = [("globe", "Websites", CYAN, 300, 880), ("chip", "AI", YELLOW, 780, 880),
         ("chart", "Data", GREEN, 300, 1300), ("gear", "Automation", PURPLE, 780, 1300)]


def sc_uses(L, t, tl):
    for i, (ic, lab, col, x, y) in enumerate(TILES):
        age = t - cap_t("uses", i + 1)
        if age < 0:
            continue
        nxt = cap_t("uses", i + 2) if i < 3 else 1e9
        active = t < nxt + 0.05 or i == 3
        c = card(400, 370, r=34, border=col if active else (70, 80, 95), bw=4 if active else 2)
        s = pop(age) * (1.04 if active else 0.97)
        lift = -14 if active else 0
        paste(L, c, x, y + lift, s)
        if s > 0.6:
            paste(L, icon(ic, 170, phase=tl * 0.6 if ic != "chart" else age), x, y - 40 + lift, s)
            paste(L, text(lab, 52, col if active else INK), x, y + 115 + lift, s)


BEST_LIST = ["Easy syntax", "Free & open source", "Huge community"]


def sc_best(L, t, tl):
    if t < SLAM:
        paste(L, rays(color=YELLOW, alpha=55).rotate(-tl * 12, Image.BICUBIC), 540, 860, 0.7)
        paste(L, trophy(), 540, 840, pop(tl, 0.35))
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.55
            paste(L, star(30 + (k % 2) * 8), 540 + 330 * math.cos(a), 880 + 330 * math.sin(a) * 0.9,
                  pop(tl - 0.3 - k * 0.07), rot=tl * 40 * (1 if k % 2 else -1))
        for k, s in enumerate(BEST_LIST):
            age = tl - 0.75 - k * 0.32
            if age > 0:
                x = 540 + 700 * (1 - ease_out(age / 0.3))
                yy = 1200 + k * 120
                paste(L, card(620, 96, r=48, border=GREEN, bw=2), x, yy, 1)
                paste(L, check_badge(30), x - 250, yy, pop(age - 0.1))
                paste(L, text(s, 44, INK), x + 30, yy, 1)
        return
    age = t - SLAM
    paste(L, rays(color=YELLOW, alpha=90).rotate(age * 30, Image.BICUBIC), 540, 980, 1.0)
    s = 1.0 + 2.2 * (1 - ease_out(age / 0.22))
    paste(L, pill("PYTHON!", 170, fg=NAVY, bg=YELLOW, padx=56, pady=30), 540, 980, s, a=clamp(age / 0.08), rot=-4)
    paste(L, py_badge(260), 540, 1340, pop(age - 0.15))
    confetti(L, age, 540, 980, n=90, seed=9, spread=1000)


def sc_end(L, t, tl):
    s = back_out(tl / 0.35)
    paste(L, card(860, 460, r=36, border=CYAN, bw=3), 540, 900, s)
    if s > 0.9:
        paste(L, pill("NEXT  •  EP 02", 44, fg=NAVY, bg=YELLOW, padx=28, pady=12), 540, 730, pop(tl - 0.1))
        paste(L, text("print()", 150, CYAN, "mono"), 540, 900, pop(tl - 0.18))
        paste(L, text("Pehla code likhna!", 48, INK), 540, 1035, 1, a=ease((tl - 0.3) / 0.2))
    t_click = cap_t("end", 1) + 0.15
    age = tl - 0.35
    if age > 0:
        press = 1.0 - 0.1 * math.exp(-((t - t_click - 0.05) / 0.06) ** 2) if t > t_click - 0.1 else 1.0
        pulse = 1 + 0.04 * math.sin(t * 9) if t < t_click else 1.0
        paste(L, pill("FOLLOW", 64, fg=WHITE, bg=RED, padx=70, pady=22), 540, 1300, pop(age) * press * pulse)
        if t > t_click:
            rr = (t - t_click) * 700
            ImageDraw.Draw(L).ellipse((540 - rr, 1300 - rr * 0.5, 540 + rr, 1300 + rr * 0.5),
                                      outline=RED + (int(clamp(1 - (t - t_click) / 0.5) * 200),), width=6)
        u = ease((t - (t_click - 0.6)) / 0.55)
        if t > t_click - 0.6:
            paste(L, cursor(), 900 - 300 * u, 1560 - 220 * u, 1)
    age = tl - 0.6
    if age > 0:
        paste(L, text("Roz ek naya Python concept", 44, INK), 540, 1470, 1, a=ease(age / 0.25))
        paste(L, text("@PythonKiPathshala", 42, CYAN), 540, 1535, 1, a=ease((age - 0.1) / 0.25))


SCENE_FN = {"hook": sc_hook, "ask": sc_ask, "drop": sc_drop, "def": sc_def, "simple": sc_simple,
            "uses": sc_uses, "best": sc_best, "end": sc_end}

# ---------------------------------------------------------------- camera / transitions (lesson time)
WHIP_CUTS = {4: -1}                        # one whip, like the reference
BLUR_CUTS = [1, 3, 5, 7]                   # reference's main move: defocus blur through the cut
PUNCH_TIMES = [CUTS[2], SLAM, CUTS[6]]
SHAKE_TIMES = [(CUTS[2], 22), (SLAM, 30)]
FLASH_TIMES = [CUTS[2], SLAM]


def camera(t):
    name, tl, i = scene_at(t)
    s = 1.0 + 0.025 * clamp(tl / 3.0)
    if name == "ask":
        s += 0.08 * ease(tl / (CUTS[2] - CUTS[1]))
    for tp in PUNCH_TIMES:
        if 0 <= t - tp < 0.4:
            s += 0.12 * (1 - ease_out((t - tp) / 0.4))
    if t > CUTS[2] and not (kb(46.5) <= t < SLAM):
        s += 0.006 * math.exp(-((t / BEAT) % 1.0) * 8)
    dx = dy = 0.0
    for tp, amp in SHAKE_TIMES:
        age = t - tp
        if 0 <= age < 0.45:
            k = amp * math.exp(-age * 9)
            dx += k * math.sin(age * 83)
            dy += k * math.cos(age * 71)
    return s, dx, dy


def apply_camera(frame, s, dx, dy):
    if abs(s - 1) < 1e-4 and abs(dx) < 0.1 and abs(dy) < 0.1:
        return frame
    M = np.float32([[s, 0, W / 2 * (1 - s) + dx], [0, s, H / 2 * (1 - s) + dy]])
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def defocus(frame, amount):
    """Fast heavy blur (downscale -> blur -> upscale), amount 0..1."""
    if amount <= 0.02:
        return frame
    small = cv2.resize(frame, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    k = 1 + 2 * int(1 + 12 * amount)
    small = cv2.GaussianBlur(small, (k, k), 0)
    big = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    a = clamp(amount * 1.6)
    return (frame * (1 - a) + big * a).astype(np.uint8)


def transitions(frame, t):
    for ci in BLUR_CUTS:
        dt = t - CUTS[ci]
        if -0.16 <= dt < 0.2:
            amt = 1 - (abs(dt) / (0.16 if dt < 0 else 0.2))
            frame = defocus(frame, ease(amt))
            # small zoom-through for energy
            s = 1 + 0.06 * ease(amt)
            return apply_camera(frame, s, 0, 0)
    for ci, dirn in WHIP_CUTS.items():
        tc = CUTS[ci]
        if tc - 0.1 <= t < tc:
            u = ease_in((t - (tc - 0.1)) / 0.1)
            off, vel = -dirn * u * W * 0.3, 1.0
        elif tc <= t < tc + 0.18:
            u = (t - tc) / 0.18
            off, vel = dirn * (1 - ease_out(u)) * W * 0.45, 1 - u
        else:
            continue
        return cv2.blur(np.roll(frame, int(off), axis=1), (int(10 + 90 * vel), 1))
    return frame


def flash(frame, t):
    for tp in FLASH_TIMES:
        age = t - tp
        if 0 <= age < 0.22:
            a = 0.8 * (1 - age / 0.22) ** 2
            return (frame * (1 - a) + 255 * a).astype(np.uint8)
    return frame


# ---------------------------------------------------------------- UI overlay
def channel_tag(img):
    paste(img, pill("Python Ki Pathshala", 26, fg=NAVY, bg=WHITE, padx=20, pady=10), 880, 70)


def progress(img, p):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 8), fill=(0, 0, 0, 120))
    xe = W * clamp(p)
    n = 24
    for k in range(n):
        a0, a1 = xe * k / n, xe * (k + 1) / n
        c = tuple(int(BLUE[j] + (YELLOW[j] - BLUE[j]) * (k / (n - 1))) for j in range(3))
        d.rectangle((a0, 0, a1 + 1, 8), fill=c + (255,))


def overlay_ui(img, t, T):
    channel_tag(img)
    cap = active_caption(t)
    if cap:
        key, i, ts = cap
        age = t - ts
        sp = caption(CAPS[key][i], HL[KEY_ORDER.index(key) % len(HL)])
        paste(img, sp, 540, 300 + 30 * (1 - ease_out(age / 0.2)), pop(age, 0.22, 0.12))
    progress(img, T / TOTAL)


def render_lesson(t, T):
    name, tl, _ = scene_at(t)
    bg = background(t)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENE_FN[name](L, t, tl)
    bg.alpha_composite(L)
    frame = apply_camera(np.asarray(bg.convert("RGB")), *camera(t))
    img = Image.fromarray(frame).convert("RGBA")
    overlay_ui(img, t, T)
    frame = transitions(np.asarray(img.convert("RGB")), t)
    return flash(frame, t)


# ---------------------------------------------------------------- thumbnail (first frames)
def thumbnail_img(t=0.0):
    bg = Image.fromarray(mat_frame(1.0, np.array(TINTS["drop"], np.float32)), "RGB").convert("RGBA")
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste(L, rays(color=YELLOW, alpha=80).rotate(8 + t * 20, Image.BICUBIC), 540, 1030, 1.0)
    paste(L, text("PYTHON", 210, YELLOW, stroke=8), 540, 330)
    paste(L, text("KYA HAI?", 170, INK, stroke=8), 540, 540)
    paste(L, pill("Python Basics  •  Hinglish", 50, fg=NAVY, bg=CYAN, padx=40, pady=18), 540, 720)
    paste(L, py_badge(520), 540, 1080, 1 + 0.03 * math.sin(t * 6))
    paste(L, pill("EP 01", 80, fg=WHITE, bg=RED, padx=44, pady=20), 830, 1390, rot=8)
    paste(L, pill("25 sec mein samjho!", 54, fg=NAVY, bg=YELLOW, padx=36, pady=18), 540, 1560, rot=-3)
    paste(L, pill("@PythonKiPathshala", 34, fg=NAVY, bg=WHITE, padx=24, pady=12), 230, 1800)
    bg.alpha_composite(L)
    channel_tag(bg)
    return bg


def render_intro(T):
    img = thumbnail_img(T)
    s = 1.0 + 0.04 * T / INTRO
    progress(img, T / TOTAL)
    frame = apply_camera(np.asarray(img.convert("RGB")), s, 0, 0)
    left = INTRO - T
    if left < 0.16:
        frame = defocus(frame, ease(1 - left / 0.16))
    return frame


# ---------------------------------------------------------------- outro: LIKE / SHARE / SUBSCRIBE
TAPS = [0.75, 1.55, 2.35]          # outro time of each tap
BTN_Y = [850, 1015, 1180]


@lru_cache(None)
def outro_bg():
    """Darkened, blurred last lesson frame (like the reference's end screen)."""
    f = render_lesson(DUR - 0.05, INTRO + DUR)
    f = cv2.GaussianBlur(cv2.resize(f, (W // 4, H // 4)), (0, 0), 6)
    f = cv2.resize(f, (W, H)).astype(np.float32) * 0.35
    return f.astype(np.uint8)


def render_outro(u, T):
    img = Image.fromarray(outro_bg()).convert("RGBA")
    paste(img, text("Video pasand aaya?", 84, INK, stroke=5), 540, 520, pop(u - 0.05))
    # heart, drawn
    age = u - 0.2
    if age > 0:
        hs = Image.new("RGBA", (200, 180), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hs)
        hd.ellipse((10, 10, 105, 105), fill=RED + (255,))
        hd.ellipse((95, 10, 190, 105), fill=RED + (255,))
        hd.polygon([(16, 78), (184, 78), (100, 172)], fill=RED + (255,))
        paste(img, hs, 540, 660, pop(age) * (1 + 0.06 * math.sin(u * 10)) * 0.6)
    states = [("LIKE", "like", WHITE, NAVY, "LIKED", BLUE, WHITE),
              ("SHARE", "share", WHITE, NAVY, "SHARE", GREEN, WHITE),
              ("SUBSCRIBE", "bell", RED, WHITE, "SUBSCRIBED", (70, 74, 82), WHITE)]
    for k, (lab, ic, bg0, fg0, lab1, bg1, fg1) in enumerate(states):
        age = u - 0.25 - k * 0.12
        if age <= 0:
            continue
        tapped = u >= TAPS[k]
        b = ui_button(lab1 if tapped else lab, ic, bg1 if tapped else bg0, fg1 if tapped else fg0)
        press = 1.0 - 0.08 * math.exp(-((u - TAPS[k] - 0.03) / 0.05) ** 2)
        bump = 1 + 0.08 * math.exp(-((u - TAPS[k] - 0.12) / 0.07) ** 2)
        paste(img, b, 540, BTN_Y[k], pop(age) * press * bump)
        if tapped and u - TAPS[k] < 0.5:
            rr = (u - TAPS[k]) * 600
            ImageDraw.Draw(img).ellipse((540 - rr, BTN_Y[k] - rr * 0.35, 540 + rr, BTN_Y[k] + rr * 0.35),
                                        outline=bg1 + (int((1 - (u - TAPS[k]) / 0.5) * 220),), width=6)
    # the tapping hand moves from button to button
    if u > 0.45:
        k = min(2, max(0, sum(1 for tp in TAPS if u > tp + 0.25)))
        prev = max(0, k - 1)
        t0 = TAPS[k] - 0.35 if k else 0.45
        m = ease((u - t0) / 0.3)
        y0, y1 = (BTN_Y[prev] if k else 1500), BTN_Y[k]
        hx = 700 + 40 * (1 - m)
        hy = y0 + (y1 - y0) * m + 70
        dip = 14 * math.exp(-((u - TAPS[k]) / 0.06) ** 2)
        paste(img, hand(), hx, hy + dip, 1)
    paste(img, text("Roz ek naya Python concept", 42, INK), 540, 1400, 1, a=ease((u - 1.0) / 0.3))
    paste(img, pill("@PythonKiPathshala", 40, fg=NAVY, bg=YELLOW, padx=30, pady=14), 540, 1480, 1,
          a=ease((u - 1.1) / 0.3))
    channel_tag(img)
    progress(img, T / TOTAL)
    frame = np.asarray(img.convert("RGB"))
    if u < 0.18:
        frame = defocus(frame, ease(1 - u / 0.18))
    left = OUTRO - u
    if left < 0.25:
        frame = (frame * (0.4 + 0.6 * left / 0.25)).astype(np.uint8)
    return frame


def render(T):
    if T < INTRO:
        f = render_intro(T)
    elif T < INTRO + DUR:
        t = T - INTRO
        f = render_lesson(t, T)
        if t < 0.16:
            f = defocus(f, ease(1 - t / 0.16))
    else:
        f = render_outro(T - INTRO - DUR, T)
    return np.ascontiguousarray(f)


def render_idx(i):
    return render(i / FPS).tobytes()


# ---------------------------------------------------------------- audio (music + SFX only)
def nfreq(semi):
    return 440.0 * 2 ** (semi / 12)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp(x, f0, f1):
    b, a = signal.butter(2, [f0 / (SR / 2), f1 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def add(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += g * x[:n]


RNG = np.random.default_rng(5)


def kick():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-tt * 28)) / SR) * np.exp(-tt * 7)
    x[:200] += RNG.normal(0, 0.3, 200) * np.linspace(1, 0, 200)
    return x


def clap():
    n = int(0.25 * SR)
    x = bp(RNG.normal(0, 1, n), 900, 3500)
    e = np.zeros(n)
    for k, o in enumerate((0, 0.011, 0.022)):
        i = int(o * SR)
        e[i:] += env_exp(n - i, 0.012 if k < 2 else 0.07)
    return x * e * 0.6


def hat():
    n = int(0.06 * SR)
    return hp(RNG.normal(0, 1, n), 7000) * env_exp(n, 0.012) * 0.35


def saw(f, n, detune=0.0):
    tt = np.arange(n) / SR
    return 2 * ((tt * f * (1 + detune)) % 1.0) - 1


def pluck(f, dur=0.22):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + np.sin(2 * np.pi * 2 * f * tt) * 0.3
    return lp(x * env_exp(n, 0.07), 3200)


def whoosh(dur=0.35, up=True):
    n = int(dur * SR)
    x = RNG.normal(0, 1, n)
    out = np.zeros(n)
    seg = n // 12
    for k in range(12):
        f = 600 + 4500 * (k / 11 if up else 1 - k / 11)
        out[k * seg:(k + 1) * seg] = bp(x[k * seg:(k + 1) * seg], f * 0.7, min(f * 1.4, 20000))[:seg]
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5 * 0.7


def pop_sfx(f0=520):
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f0 + 700 * tt / 0.12) / SR) * env_exp(n, 0.03) * 0.6


def ding():
    n = int(0.8 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1318.5 * tt) + 0.5 * np.sin(2 * np.pi * 1975.5 * tt) + 0.2 * np.sin(2 * np.pi * 2637 * tt)
    return x * env_exp(n, 0.22) * 0.35


def tick():
    n = int(0.025 * SR)
    return hp(RNG.normal(0, 1, n), 2500) * env_exp(n, 0.004) * 0.35


def riser(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    return hp(RNG.normal(0, 1, n), 1500) * u ** 2 * 0.35 + np.sin(2 * np.pi * np.cumsum(200 + 1400 * u ** 2) / SR) * u ** 1.5 * 0.25


def impact():
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tt * 10)) / SR) * np.exp(-tt * 2.8)
    return boom * 0.9 + hp(RNG.normal(0, 1, n), 3000) * np.exp(-tt * 3.0) * 0.35


def click_sfx():
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * tt) * env_exp(n, 0.006) + hp(RNG.normal(0, 1, n), 4000) * env_exp(n, 0.003)) * 0.5


def bell_sfx():
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt) * g for f, g in ((880, 1), (1760, 0.5), (2637, 0.3), (3520, 0.15)))
    return x * env_exp(n, 0.3) * 0.3


CHORDS = [(-24, [0, 3, 7]), (-28, [0, 4, 7]), (-21, [0, 4, 7]), (-26, [0, 4, 7])]


def music(length):
    """Lesson-time music for `length` seconds (lesson + outro)."""
    n = int((length + 1) * SR)
    drums, bass, pad, arp = (np.zeros(n) for _ in range(4))
    K, C, Hh = kick(), clap(), hat()
    nbeats = int(length / BEAT) + 2
    gap = (kb(46.5), SLAM)
    ask = (CUTS[1], CUTS[2])
    for b in range(nbeats):
        tb = kb(b)
        if gap[0] <= tb < gap[1]:
            continue
        in_ask = ask[0] <= tb < ask[1]
        root, ivs = CHORDS[(b // 4) % 4]
        if not in_ask:
            add(drums, K, tb, 0.9)
            if b % 2 == 1 and tb >= CUTS[2]:
                add(drums, C, tb, 0.8)
            add(drums, Hh, tb + BEAT / 2, 0.9)
            if tb >= CUTS[2]:
                add(drums, Hh, tb + BEAT / 4, 0.4)
                add(drums, Hh, tb + 3 * BEAT / 4, 0.4)
            for h in (0, 0.5):
                nb = int(BEAT / 2 * SR)
                add(bass, lp(saw(nfreq(root), nb) * env_exp(nb, 0.12), 380), tb + h * BEAT, 0.6 if tb >= CUTS[2] else 0.4)
        else:
            k = (tb - ask[0]) / (ask[1] - ask[0])
            steps = 2 if k < 0.5 else 4
            for s_ in range(steps):
                add(drums, C, tb + s_ * BEAT / steps, 0.25 + 0.5 * k)
        tones = [root + 24 + iv for iv in ivs] + [root + 36]
        for s_ in range(4):
            if not (gap[0] <= tb + s_ * BEAT / 4 < gap[1]):
                add(arp, pluck(nfreq(tones[(b * 4 + s_) % 4])), tb + s_ * BEAT / 4, 0.18)
        if b % 4 == 0:
            nb = int(4 * BEAT * SR)
            x = sum(saw(nfreq(root + 12 + iv), nb, dt) for iv in ivs for dt in (-0.004, 0.004))
            x = lp(x, 1400) * np.minimum(1, np.arange(nb) / (0.05 * SR)) * np.minimum(1, (nb - np.arange(nb)) / (0.1 * SR))
            add(pad, x, tb, 0.05)
    pump = np.ones(n)
    for b in range(nbeats):
        tb = kb(b)
        if tb >= CUTS[2] and not (gap[0] <= tb < gap[1]):
            i = int(tb * SR)
            m = min(int(BEAT * SR), n - i)
            if m > 0:
                pump[i:i + m] = 1 - 0.6 * np.exp(-np.arange(m) / (0.09 * SR))
    mix = drums + bass + (pad + arp) * pump
    i0, i1 = int(ask[0] * SR), int(ask[1] * SR)
    mix[i0:i1] = lp(mix[i0:i1], 900) * 0.8
    mix[int(gap[0] * SR):int(gap[1] * SR)] = 0.0
    return mix


def sfx_track(length):
    """Lesson + outro SFX in lesson time."""
    n = int((length + 1) * SR)
    s = np.zeros(n)
    for ci in BLUR_CUTS + list(WHIP_CUTS):
        add(s, whoosh(0.34), CUTS[ci] - 0.17, 0.55)
    add(s, riser(CUTS[2] - CUTS[1]), CUTS[1], 0.7)
    add(s, riser(SLAM - kb(44)), kb(44), 0.6)
    add(s, impact(), CUTS[2], 0.9)
    add(s, impact(), SLAM, 1.0)
    add(s, pop_sfx(500), cap_t("hook", 1), 0.5)
    add(s, pop_sfx(650), cap_t("hook", 1) + 0.12, 0.5)
    add(s, pop_sfx(600), CUTS[1] + 0.35, 0.4)
    add(s, pop_sfx(420), CUTS[1] + 0.7, 0.4)
    add(s, pop_sfx(560), cap_t("def", 1), 0.45)
    ta = cap_t("def", 3) + 0.45
    add(s, whoosh(0.5), ta - 0.65, 0.35)
    for k in range(3):
        add(s, tick(), ta + k / 12, 0.8)
    add(s, ding(), ta + 0.3, 0.7)
    add(s, pop_sfx(700), cap_t("def", 4), 0.35)
    for k in range(sum(CODE_CHARS)):
        if k % 2 == 0:
            add(s, tick(), CUTS[4] + CODE_TYPE_START + k / CODE_CPS, 0.7)
    add(s, ding(), CUTS[4] + CODE_TYPE_START + sum(CODE_CHARS) / CODE_CPS + 0.3, 0.6)
    add(s, pop_sfx(520), cap_t("simple", 1), 0.5)
    add(s, ding(), cap_t("simple", 4), 0.5)
    for i in range(4):
        add(s, pop_sfx(480 + 90 * i), cap_t("uses", i + 1), 0.55)
    for k in range(3):
        add(s, whoosh(0.22), CUTS[6] + 0.7 + k * 0.32, 0.25)
        add(s, pop_sfx(640), CUTS[6] + 0.85 + k * 0.32, 0.3)
    add(s, pop_sfx(560), CUTS[7] + 0.35, 0.4)
    add(s, click_sfx(), cap_t("end", 1) + 0.15, 0.9)
    add(s, ding(), cap_t("end", 1) + 0.2, 0.4)
    # outro
    add(s, whoosh(0.4), DUR - 0.2, 0.5)
    add(s, pop_sfx(520), DUR + 0.25, 0.45)
    for k, tp in enumerate(TAPS):
        add(s, click_sfx(), DUR + tp, 1.0)
        add(s, pop_sfx(620 + 120 * k), DUR + tp + 0.03, 0.5)
        add(s, bell_sfx() if k == 2 else ding(), DUR + tp + 0.05, 0.6)
    return s


def build_audio(path):
    L = DUR + OUTRO
    m, s = music(L), sfx_track(L)
    body = m / (np.abs(m).max() + 1e-9) * 0.62 + s / (np.abs(s).max() + 1e-9) * 0.6
    body = body[: int(L * SR)]
    intro = np.zeros(int(INTRO * SR) + 1)
    add(intro, pop_sfx(700), 0.02, 0.5)
    add(intro, riser(INTRO - 0.1), 0.1, 0.5)
    add(intro, whoosh(0.3), INTRO - 0.2, 0.4)
    mix = np.concatenate([intro[: int(INTRO * SR)], body])
    fade = int(0.3 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    sf.write(path, np.stack([mix, mix], 1).astype(np.float32), SR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="contact sheet of stills only")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    for key in CAPS:
        cap_times(key)
    thumbnail_img(0.0).convert("RGB").save(os.path.join(OUT, "thumbnail.jpg"), quality=92)
    if args.preview:
        ts = list(np.linspace(0.3, TOTAL - 0.2, 24))
        ims = [Image.fromarray(render(t)).resize((270, 480)) for t in ts]
        sheet = Image.new("RGB", (270 * 8, 480 * 3))
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % 8) * 270, (k // 8) * 480))
        sheet.save(os.path.join(WORK, "preview.jpg"), quality=85)
        print("wrote", os.path.join(WORK, "preview.jpg"))
        return
    wav = os.path.join(WORK, "mix.wav")
    build_audio(wav)
    outro_bg()                              # cache before forking
    silent = os.path.join(WORK, "video.mp4")
    nf = int(round(TOTAL * FPS))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_idx, range(nf), chunksize=4)):
            ff.stdin.write(buf)
            if k % 150 == 0:
                print(f"  frame {k}/{nf}")
    ff.stdin.close()
    ff.wait()
    out = os.path.join(OUT, NAME)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
