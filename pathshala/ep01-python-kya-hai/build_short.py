#!/usr/bin/env python3
"""Renders "Python Ki Pathshala" EP01 "Python kya hai?" as a 25 s 9:16 short.

Style decoded from Python_ki_Pathshala_EP01_Short_25s.mp4, re-themed light:
cream background with drifting code glyphs, dark navy kinetic captions at the
top with the keyword on a yellow marker box, pop-in cards with overshoot,
whip-pan cuts, a ray burst on the reveal, a beat drop after a riser, a silent
gap before the final slam, a series tag on top, a progress bar at the bottom
and a "NEXT EPISODE + FOLLOW" end card that loops back into the hook.

Everything is drawn procedurally: graphics, an original 128 BPM track and
synthesised SFX. The voice-over comes from make_voice.py (work/vo_*.wav).

Run:   python3 pathshala/ep01-python-kya-hai/make_voice.py --models <dir>
       python3 pathshala/ep01-python-kya-hai/build_short.py [--preview]
Needs: pip install numpy scipy opencv-python-headless pillow soundfile ; ffmpeg.
Output: output/PythonKiPathshala-EP01-Python-Kya-Hai.mp4 and output/cover.jpg
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
NAME = "PythonKiPathshala-EP01-Python-Kya-Hai.mp4"

W, H, FPS = 1080, 1920, 30
SR = 48000
BPM = 128
BEAT = 60 / BPM


def kb(k):
    """Time of beat k on the music grid."""
    return k * BEAT


DUR = 25.0
SCENES = [("hook", 0), ("ask", 6), ("drop", 11), ("def", 14), ("simple", 24),
          ("uses", 33), ("best", 41), ("end", 49)]
CUTS = [kb(b) for _, b in SCENES] + [DUR]
SLAM = kb(47)                     # "PYTHON!" impact inside the "best" scene

# ---------------------------------------------------------------- palette
CREAM = (255, 249, 236)
TINTS = {"hook": (238, 245, 255), "ask": (238, 245, 255), "drop": (255, 243, 204),
         "def": (238, 245, 255), "simple": (255, 249, 236), "uses": (255, 244, 214),
         "best": (255, 243, 204), "end": (238, 245, 255)}
NAVY = (15, 27, 61)
BLUE = (40, 96, 160)
YELLOW = (255, 210, 50)
RED = (232, 57, 70)
GREEN = (30, 160, 90)
PURPLE = (120, 70, 200)
GRAY = (110, 120, 140)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- voice + captions
# key: (start, latest end); captions are chunks, *word* = yellow marker highlight
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


def vo_clip(key):
    """Voice line fitted to its window (sped up without pitch change if needed)."""
    path = os.path.join(WORK, f"vo_{key}.wav")
    if not os.path.exists(path):
        return None
    a, sr = sf.read(path)
    if a.ndim > 1:
        a = a.mean(1)
    start, end = VO[key]
    rate = (len(a) / SR) / (end - start)
    if rate > 1.0:
        tmp = os.path.join(WORK, f"fit_{key}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", f"atempo={rate:.4f}", tmp], check=True)
        a, _ = sf.read(tmp)
    return a


@lru_cache(None)
def vo_dur(key):
    a = vo_clip(key)
    return len(a) / SR if a is not None else (VO[key][1] - VO[key][0]) * 0.92


@lru_cache(None)
def cap_times(key):
    """Start time of each caption chunk, spread over the spoken line by length."""
    chunks = CAPS[key]
    wts = [len(c.replace("*", "")) + (3 if c.rstrip()[-1] in ",.!?" else 1) for c in chunks]
    start, d = VO[key][0], vo_dur(key)
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
        times = cap_times(key)
        for i, ts in enumerate(times):
            if t >= ts - 0.02:
                best = (key, i, ts)
    if best is None:
        return None
    key, i, ts = best
    # hide the caption shortly after the line ends, unless the next line is near
    if t > VO[key][0] + vo_dur(key) + 0.6:
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
    """Scale for a pop-in with overshoot (0 before it starts)."""
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


def with_shadow(im, blur=18, offset=(0, 14), alpha=70, pad=40):
    """Adds a soft drop shadow under an RGBA sprite."""
    w, h = im.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", im.size, NAVY + (0,))
    sh.putalpha(a)
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


@lru_cache(None)
def card(w, h, r=34, fill=WHITE, border=NAVY, bw=5, shadow=True):
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, fill=fill + (255,),
                        outline=(border + (255,)) if border else None, width=bw * S if border else 0)
    im = ss_finish(im, w, h)
    return with_shadow(im) if shadow else im


@lru_cache(None)
def text(s, size, color=NAVY, which="mont"):
    f = font(size, which)
    x0, y0, x1, y1 = f.getbbox(s)
    im = Image.new("RGBA", (x1 - x0 + 8, y1 - y0 + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - x0, 4 - y0), s, font=f, fill=color + (255,))
    return im


@lru_cache(None)
def pill(s, size, fg=NAVY, bg=YELLOW, border=NAVY, padx=30, pady=16, which="mont", shadow=True):
    t = text(s, size, fg, which)
    w, h = t.width + 2 * padx, t.height + 2 * pady
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), h * S // 2, fill=bg + (255,),
                        outline=(border + (255,)) if border else None, width=8 if border else 0)
    im = ss_finish(im, w, h)
    im.alpha_composite(t, (padx, pady))
    return with_shadow(im, blur=10, offset=(0, 8), alpha=60, pad=24) if shadow else im


SEG_RE = re.compile(r"\*[^*]+\*|[^*\s]+")


@lru_cache(None)
def caption(chunk, maxw=990):
    segs = [(m[1:-1], True) if m.startswith("*") else (m, False) for m in SEG_RE.findall(chunk)]
    size = 92
    while True:
        f = font(size)
        sp = f.getlength(" ")
        widths = [f.getlength(s) + (44 if hl else 0) for s, hl in segs]
        total = sum(widths) + sp * (len(segs) - 1)
        if total <= maxw or size <= 50:
            break
        size -= 4
    S = 2
    fS = font(size * S)
    asc, desc = fS.getmetrics()
    hh = int((asc + desc) * 1.25)
    im = Image.new("RGBA", (int(total * S) + 40, hh + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 20
    for (s, hl), wd in zip(segs, widths):
        if hl:
            bb = fS.getbbox(s)
            top, bot = 10 + bb[1] - 18 * S // 2, 10 + bb[3] + 18 * S // 2
            d.rounded_rectangle((x, top, x + wd * S, bot), 16 * S, fill=YELLOW + (255,),
                                outline=NAVY + (255,), width=4 * S)
            d.text((x + 22 * S, 10), s, font=fS, fill=NAVY + (255,))
        else:
            d.text((x, 10), s, font=fS, fill=NAVY + (255,))
        x += int((wd + sp) * S)
    im = ss_finish(im, im.width // S, im.height // S)
    return with_shadow(im, blur=8, offset=(0, 6), alpha=40, pad=20)


@lru_cache(None)
def monitor(w, h):
    """Monitor frame; the screen (w x h) is left transparent-free light."""
    S = 2
    bez = 22
    tw, th = w + 2 * bez, h + 2 * bez + 150
    im = Image.new("RGBA", (tw * S, th * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw * S - 1, (h + 2 * bez) * S), 30 * S, fill=NAVY + (255,))
    d.rounded_rectangle((bez * S, bez * S, (bez + w) * S, (bez + h) * S), 12 * S, fill=(250, 252, 255, 255))
    cx = tw * S // 2
    d.polygon([(cx - 50 * S, (h + 2 * bez) * S), (cx + 50 * S, (h + 2 * bez) * S),
               (cx + 70 * S, (th - 30) * S), (cx - 70 * S, (th - 30) * S)], fill=NAVY + (255,))
    d.rounded_rectangle((cx - 150 * S, (th - 38) * S, cx + 150 * S, (th - 6) * S), 14 * S, fill=NAVY + (255,))
    return with_shadow(ss_finish(im, tw, th))


def monitor_screen_origin(cx, cy, w, h):
    """Top-left of the screen area for a monitor sprite pasted centred at (cx, cy)."""
    spr = monitor(w, h)
    return int(cx - spr.width / 2 + 40 + 22), int(cy - spr.height / 2 + 40 + 22)


@lru_cache(None)
def person(r=110):
    S = 2
    D = 2 * r * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=BLUE + (255,), outline=NAVY + (255,), width=6 * S)
    c = D // 2
    d.ellipse((c - 34 * S, c - 62 * S, c + 34 * S, c + 6 * S), fill=WHITE + (255,))
    d.chord((c - 66 * S, c + 14 * S, c + 66 * S, c + 140 * S), 180, 360, fill=WHITE + (255,))
    im = ss_finish(im, 2 * r, 2 * r)
    lab = text("YOU", 34, NAVY)
    out = Image.new("RGBA", (2 * r, 2 * r + 60), (0, 0, 0, 0))
    out.alpha_composite(im, (0, 0))
    out.alpha_composite(lab, (r - lab.width // 2, 2 * r + 12))
    return with_shadow(out, blur=12, alpha=50)


@lru_cache(None)
def py_badge(size=380):
    """Stylised two-tone 'Py' snake-block badge (original artwork, not the official logo)."""
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = s / 10
    # blue block (top-left) and yellow block (bottom-right), interlocked
    d.rounded_rectangle((u * 0.6, u * 0.6, u * 6.4, u * 6.4), int(u * 1.6), fill=BLUE + (255,),
                        outline=NAVY + (255,), width=int(u * 0.28))
    d.rounded_rectangle((u * 3.6, u * 3.6, u * 9.4, u * 9.4), int(u * 1.6), fill=YELLOW + (255,),
                        outline=NAVY + (255,), width=int(u * 0.28))
    d.rounded_rectangle((u * 3.6, u * 3.6, u * 6.4, u * 6.4), int(u * 0.5), fill=WHITE + (255,))
    d.ellipse((u * 1.6, u * 1.6, u * 2.6, u * 2.6), fill=WHITE + (255,))
    d.ellipse((u * 7.4, u * 7.4, u * 8.4, u * 8.4), fill=NAVY + (255,))
    f = font(int(u * 2.0), "mont")
    d.text((u * 5.0, u * 5.0), "Py", font=f, fill=NAVY + (255,), anchor="mm")
    return with_shadow(ss_finish(im, size, size), blur=20, alpha=80)


@lru_cache(None)
def rays(size=1700, n=18, color=YELLOW):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n * 0.9
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=color + (150,))
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - c, yy - c) / c
    fade = np.clip(1.15 - r, 0, 1) ** 1.3
    a = np.asarray(im.getchannel("A"), np.float32) * fade
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


@lru_cache(None)
def check_badge(r=56, ok=True):
    S = 2
    D = 2 * r * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, D - 1, D - 1), fill=(GREEN if ok else RED) + (255,), outline=NAVY + (255,), width=5 * S)
    w = int(D * 0.09)
    if ok:
        d.line([(D * 0.27, D * 0.52), (D * 0.44, D * 0.68), (D * 0.74, D * 0.34)], fill=WHITE + (255,),
               width=w, joint="curve")
    else:
        d.line([(D * 0.32, D * 0.32), (D * 0.68, D * 0.68)], fill=WHITE + (255,), width=w)
        d.line([(D * 0.68, D * 0.32), (D * 0.32, D * 0.68)], fill=WHITE + (255,), width=w)
    return with_shadow(ss_finish(im, 2 * r, 2 * r), blur=8, alpha=60, pad=20)


def icon(kind, size=150, phase=0.0, color=NAVY):
    """Small line icons; `phase` animates them (not cached)."""
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = int(s * 0.06)
    col = color + (255,)
    c = s / 2
    if kind == "globe":
        R = s * 0.42
        d.ellipse((c - R, c - R, c + R, c + R), outline=col, width=lw)
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
        d.text((c, c), "AI", font=font(int(s * 0.2)), fill=col, anchor="mm")
    elif kind == "chart":
        base = s * 0.82
        hs = [0.35, 0.55, 0.45, 0.75]
        for i, hgt in enumerate(hs):
            grow = ease_out(phase * 1.6 - i * 0.15)
            x0 = s * (0.14 + i * 0.19)
            d.rounded_rectangle((x0, base - s * hgt * grow, x0 + s * 0.13, base), int(s * 0.02),
                                fill=(BLUE if i % 2 else GREEN) + (255,), outline=col, width=lw // 2)
        d.line([(s * 0.08, base), (s * 0.92, base)], fill=col, width=lw)
    elif kind == "gear":
        n = 8
        Ro, Ri = s * 0.42, s * 0.32
        pts = []
        for i in range(n * 4):
            a = phase * 2 * math.pi / n * 2 + 2 * math.pi * i / (n * 4)
            r = Ro if (i % 4) in (1, 2) else Ri
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=(140, 150, 170, 255) if color == GRAY else GREEN + (255,), outline=col)
        d.ellipse((c - s * 0.13, c - s * 0.13, c + s * 0.13, c + s * 0.13), fill=WHITE + (255,), outline=col,
                  width=lw // 2)
    return ss_finish(im, size, size)


@lru_cache(None)
def trophy(size=420):
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = int(s * 0.02)
    o = NAVY + (255,)
    # handles
    d.arc((s * 0.08, s * 0.14, s * 0.38, s * 0.48), 90, 270, fill=o, width=int(s * 0.04))
    d.arc((s * 0.62, s * 0.14, s * 0.92, s * 0.48), 270, 90, fill=o, width=int(s * 0.04))
    d.chord((s * 0.2, -s * 0.22, s * 0.8, s * 0.62), 0, 180, fill=YELLOW + (255,), outline=o, width=lw)
    d.rectangle((s * 0.2, s * 0.08, s * 0.8, s * 0.2), fill=YELLOW + (255,), outline=o, width=lw)
    d.rectangle((s * 0.45, s * 0.6, s * 0.55, s * 0.74), fill=YELLOW + (255,), outline=o, width=lw)
    d.rounded_rectangle((s * 0.28, s * 0.74, s * 0.72, s * 0.9), int(s * 0.03), fill=BLUE + (255,), outline=o,
                        width=lw)
    d.text((s * 0.5, s * 0.33), "#1", font=font(int(s * 0.17)), fill=NAVY + (255,), anchor="mm")
    return with_shadow(ss_finish(im, size, size), blur=16, alpha=70)


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
    d.polygon(pts, fill=color + (255,), outline=NAVY + (255,), width=3 * S)
    return ss_finish(im, 2 * r, 2 * r)


@lru_cache(None)
def cursor(size=90):
    S = 2
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(0.1, 0.05), (0.1, 0.8), (0.3, 0.62), (0.45, 0.95), (0.58, 0.89), (0.43, 0.57), (0.7, 0.55)]
    d.polygon([(x * s, y * s) for x, y in pts], fill=WHITE + (255,), outline=NAVY + (255,), width=5 * S)
    return with_shadow(ss_finish(im, size, size), blur=6, alpha=70, pad=16)


# ---------------------------------------------------------------- code text
CODE = [
    [("mausam", NAVY), (" = ", GRAY), ('"barish"', GREEN)],
    [("if ", PURPLE), ("mausam", NAVY), (" == ", GRAY), ('"barish"', GREEN), (":", GRAY)],
    [("    ", NAVY), ("print", BLUE), ("(", GRAY), ('"Chhata le lo!"', GREEN), (")", GRAY)],
]
CODE_CHARS = [sum(len(s) for s, _ in line) for line in CODE]
CODE_TYPE_START, CODE_CPS = 0.25, 26.0


@lru_cache(None)
def code_line(li, n, size=44):
    """First n characters of code line li, syntax coloured."""
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


CONF_COLS = [YELLOW, BLUE, RED, GREEN, PURPLE, NAVY]


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
        x = cx + math.cos(ang) * sp * (1 - math.exp(-age * 4)) / 1.0
        y = cy + math.sin(ang) * sp * (1 - math.exp(-age * 4)) + 700 * age * age
        a = clamp(1.6 - age) * 255
        th = spin * age
        pts = [(x + sz * math.cos(th + k * math.pi / 2 + 0.5) * (1 if k % 2 else 0.5),
                y + sz * math.sin(th + k * math.pi / 2 + 0.5) * (1 if k % 2 else 0.5)) for k in range(4)]
        d.polygon(pts, fill=col + (int(a),))


def dashed(d, p0, p1, phase, col=NAVY, w=6, dash=22, gap=16):
    L = math.dist(p0, p1)
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    s = -((phase * (dash + gap)) % (dash + gap))
    while s < L:
        a, b = max(0, s), min(L, s + dash)
        if b > a:
            d.line([(p0[0] + ux * a, p0[1] + uy * a), (p0[0] + ux * b, p0[1] + uy * b)], fill=col + (255,), width=w)
        s += dash + gap


# ---------------------------------------------------------------- background
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
GLOW = np.clip(1.0 - np.hypot((XX - W / 2) / W, (YY - H * 0.45) / H) * 1.1, 0, 1)[..., None]
DOTS = (((XX % 54) - 27) ** 2 + ((YY % 54) - 27) ** 2 < 5).astype(np.float32)[..., None]
GLYPHS = list("{}[]()01:#=<>")
_rng = np.random.default_rng(7)
FLOAT = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.choice(GLYPHS), _rng.uniform(30, 70),
          _rng.uniform(15, 45)) for _ in range(34)]


def tint_at(t):
    name, tl, i = scene_at(t)
    cur = np.array(TINTS[name], np.float32)
    if i > 0 and tl < 0.25:
        prev = np.array(TINTS[SCENES[i - 1][0]], np.float32)
        cur = prev + (cur - prev) * ease(tl / 0.25)
    return cur


def background(t):
    tint = tint_at(t)
    base = tint * (0.95 + 0.05 * GLOW) + (255 - tint) * 0.55 * GLOW
    base = base * (1 - 0.06 * DOTS)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img)
    for x, y, g, sz, sp in FLOAT:
        yy = (y - t * sp) % (H + 100) - 50
        xx = x + 14 * math.sin(t * 0.8 + y)
        d.text((xx, yy), g, font=font(int(sz), "mono"), fill=tuple(int(c * 0.82) for c in tint) + (255,))
    return img


# ---------------------------------------------------------------- scenes
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
                c = BLUE if (col + row) % 3 else NAVY
                sd.text((14 + col * 53, y), bit, font=f, fill=c + (230,))
        L.alpha_composite(scr, (ox, oy))
    # big 0 / 1 tiles fly in on "0 AUR 1"
    t01 = cap_t("hook", 1)
    for k, (lab, bg, x) in enumerate((("0", YELLOW, 250), ("1", BLUE, 830))):
        age = t - t01 - k * 0.12
        if age > 0:
            sp = pill(lab, 120, fg=NAVY if bg == YELLOW else WHITE, bg=bg, padx=44, pady=26)
            yb = 1490 - 18 * math.sin((t - t01) * 5 + k)
            paste(L, sp, x, yb, pop(age), rot=(-8 if k == 0 else 8))
    # flying bits around
    rng = np.random.default_rng(11)
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(520, 720)
        ph = (tl * rng.uniform(0.35, 0.6) + rng.uniform(0, 1)) % 1
        r = r0 * (1 - ph)
        x, y = cx + r * math.cos(a), cy - 40 + r * math.sin(a) * 1.2
        if r > 280:
            d.text((x, y), "01"[i % 2], font=font(54, "mono"), fill=(NAVY if i % 2 else BLUE) + (int(200 * ph + 40),),
                   anchor="mm")


def sc_ask(L, t, tl):
    d = ImageDraw.Draw(L)
    zoom_creep = 1.0
    px, mx, y = 250, 790, 1060
    paste(L, person(), px, y + 25, pop(tl, 0.3))
    mw, mh = 360, 240
    paste(L, monitor(mw, mh), mx, y, pop(tl - 0.08, 0.3))
    if tl > 0.2:
        dashed(d, (px + 125, y - 20), (mx - 210, y - 20), tl * 2.5, w=7)
    # speech bubble from YOU
    age = tl - 0.35
    if age > 0:
        b = pill("Hello!", 56, fg=NAVY, bg=WHITE, padx=34, pady=20)
        paste(L, b, px + 20, y - 240, pop(age))
    # confused screen
    if tl > 0.25:
        ox, oy = monitor_screen_origin(mx, y, mw, mh)
        jit = 6 * math.sin(tl * 40) if 0.9 < tl < 1.3 else 0
        q = text("???", 96, RED)
        L.alpha_composite(q, (int(ox + mw / 2 - q.width / 2 + jit), int(oy + mh / 2 - q.height / 2)))
    # bouncing question mark between them
    age = tl - 0.7
    if age > 0:
        qm = pill("?", 120, fg=NAVY, bg=YELLOW, padx=46, pady=18)
        paste(L, qm, 520, 1380 - abs(math.sin(age * 7)) * 70, pop(age), rot=8 * math.sin(age * 5))
    return zoom_creep


def sc_drop(L, t, tl):
    r = rays()
    paste(L, r.rotate(tl * 25, Image.BICUBIC), 540, 930, 0.6 + 0.4 * ease_out(tl / 0.4), a=0.9)
    paste(L, py_badge(), 540, 900, 1.25 * back_out(tl / 0.38))
    age = tl - 0.18
    if age > 0:
        w = pill("Python", 150, fg=NAVY, bg=YELLOW, padx=48, pady=24)
        paste(L, w, 540, 1270, pop(age, 0.3), rot=-3)
    age = tl - 0.5
    if age > 0:
        sub = text("Simple  •  Powerful  •  Free", 46, NAVY)
        paste(L, sub, 540, 1420 + 30 * (1 - ease_out(age / 0.3)), 1, a=ease(age / 0.25))
    confetti(L, tl, 540, 900, n=70, seed=3)


def sc_def(L, t, tl):
    d = ImageDraw.Draw(L)
    t_prog = cap_t("def", 1)
    age = t - t_prog
    paste(L, pill("PROGRAMMING LANGUAGE", 50, fg=NAVY, bg=YELLOW, padx=36, pady=20), 540, 700,
          pop(age) if age > 0 else 0)
    px, mx, y = 210, 790, 1060
    mw, mh = 400, 270
    paste(L, person(), px, y + 25, pop(tl, 0.3))
    paste(L, monitor(mw, mh), mx, y, pop(tl - 0.06, 0.3))
    p0, p1 = (px + 120, y - 20), (mx - 230, y - 20)
    if tl > 0.15:
        dashed(d, p0, p1, tl * 2.0, col=BLUE, w=6)
    # code chip travels YOU -> computer
    t_go, t_arrive = cap_t("def", 3) - 0.3, cap_t("def", 3) + 0.45
    u = ease((t - t_go) / (t_arrive - t_go))
    if t > t_go - 0.25 and t < t_arrive + 0.15:
        chip = pill('print("Hi!")', 38, fg=NAVY, bg=WHITE, border=BLUE, padx=22, pady=14, which="mono")
        x = p0[0] + (p1[0] - p0[0]) * u + 40
        paste(L, chip, x, y - 20 - 60 * math.sin(math.pi * u), pop(t - t_go + 0.25, 0.25),
              a=1 - clamp((t - t_arrive) / 0.15))
    # screen types "Hi!" then check
    ox, oy = monitor_screen_origin(mx, y, mw, mh)
    if t > t_arrive:
        n = min(3, int((t - t_arrive) * 12) + 1)
        s = text("Hi!"[:n] + ("_" if int(t * 4) % 2 else " "), 92, NAVY, "mono")
        L.alpha_composite(s, (int(ox + 40), int(oy + mh / 2 - s.height / 2)))
        paste(L, check_badge(), mx + 200, y - 160, pop(t - t_arrive - 0.3))
    # instructions = code label on KAAM
    age = t - cap_t("def", 4)
    if age > 0:
        lab = pill("instructions  =  code", 44, fg=NAVY, bg=WHITE, border=NAVY, padx=34, pady=18, which="mono")
        paste(L, lab, 540, 1380 + 40 * (1 - ease_out(age / 0.3)), 1, a=ease(age / 0.2))


CODE_W, CODE_H = 940, 420


def code_type_n(tl):
    return int(max(0.0, tl - CODE_TYPE_START) * CODE_CPS)


def sc_simple(L, t, tl):
    cx, cy = 540, 960
    s = 0.85 + 0.15 * back_out(tl / 0.3)
    c = card(CODE_W, CODE_H, r=30)
    paste(L, c, cx, cy, s)
    if s < 0.99:
        return
    x0, y0 = int(cx - CODE_W / 2), int(cy - CODE_H / 2)
    d = ImageDraw.Draw(L)
    for k, col in enumerate((RED, YELLOW, GREEN)):
        d.ellipse((x0 + 34 + k * 40, y0 + 30, x0 + 58 + k * 40, y0 + 54), fill=col + (255,))
    L.alpha_composite(text("mausam.py", 30, GRAY, "mono"), (x0 + 170, y0 + 26))
    d.line([(x0 + 6, y0 + 80), (x0 + CODE_W - 6, y0 + 80)], fill=(225, 225, 235, 255), width=3)
    n = code_type_n(tl)
    for li in range(3):
        L.alpha_composite(text(str(li + 1), 34, (170, 175, 190), "mono"), (x0 + 30, y0 + 120 + li * 90))
        k = min(n, CODE_CHARS[li])
        if k > 0:
            im, w = code_line(li, k)
            L.alpha_composite(im, (x0 + 80, y0 + 112 + li * 90))
            if n < sum(CODE_CHARS) and n - k <= 0 and int(t * 6) % 2:
                d.rectangle((x0 + 84 + w, y0 + 118 + li * 90, x0 + 104 + w, y0 + 166 + li * 90), fill=BLUE + (255,))
        n -= CODE_CHARS[li]
    # terminal output
    t_out = CODE_TYPE_START + sum(CODE_CHARS) / CODE_CPS + 0.25
    age = tl - t_out
    if age > 0:
        term = card(CODE_W, 170, r=26, fill=NAVY, border=None)
        paste(L, term, cx, 1330 + 40 * (1 - ease_out(age / 0.25)), 1, a=ease(age / 0.15))
        if age > 0.12:
            L.alpha_composite(text("$ python mausam.py", 32, (160, 175, 210), "mono"), (x0 + 36, 1272))
            L.alpha_composite(text("Chhata le lo!", 46, YELLOW, "mono"), (x0 + 36, 1322))
    # ENGLISH JAISA sticker
    age = t - cap_t("simple", 1)
    if age > 0:
        paste(L, pill("English jaisa!", 52, fg=NAVY, bg=YELLOW, padx=30, pady=16), 760, 700, pop(age), rot=-7)
    age = t - cap_t("simple", 4)
    if age > 0:
        paste(L, check_badge(70), 920, 1080, pop(age), rot=-10 * (1 - clamp(age / 0.3)))


TILES = [("globe", "Websites", BLUE, 300, 880), ("chip", "AI", YELLOW, 780, 880),
         ("chart", "Data", GREEN, 300, 1300), ("gear", "Automation", PURPLE, 780, 1300)]


def sc_uses(L, t, tl):
    for i, (ic, lab, col, x, y) in enumerate(TILES):
        tp = cap_t("uses", i + 1)
        age = t - tp
        if age < 0:
            continue
        nxt = cap_t("uses", i + 2) if i < 3 else 1e9
        active = t < nxt + 0.05 or i == 3
        c = card(400, 370, r=36, border=col if active else (200, 200, 210), bw=8 if active else 4)
        s = pop(age) * (1.04 if active else 0.97)
        lift = -14 if active else 0
        paste(L, c, x, y + lift, s)
        if s > 0.6:
            paste(L, icon(ic, 170, phase=tl * 0.6 if ic != "chart" else age, color=NAVY), x, y - 40 + lift, s)
            paste(L, text(lab, 52, NAVY), x, y + 115 + lift, s)


BEST_LIST = ["Easy syntax", "Free & open source", "Huge community"]


def sc_best(L, t, tl):
    pre = t < SLAM
    if pre:
        paste(L, rays(color=(255, 230, 150)).rotate(-tl * 12, Image.BICUBIC), 540, 860, 0.7, a=0.6)
        paste(L, trophy(), 540, 840, pop(tl, 0.35))
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.55
            age = tl - 0.3 - k * 0.07
            paste(L, star(30 + (k % 2) * 8), 540 + 330 * math.cos(a), 880 + 330 * math.sin(a) * 0.9,
                  pop(age), rot=tl * 40 * (1 if k % 2 else -1))
        for k, s in enumerate(BEST_LIST):
            age = tl - 0.75 - k * 0.32
            if age > 0:
                row = card(620, 96, r=48, border=NAVY, bw=4)
                x = 540 + 700 * (1 - ease_out(age / 0.3))
                yy = 1200 + k * 120
                paste(L, row, x, yy, 1)
                paste(L, check_badge(30), x - 250, yy, pop(age - 0.1))
                paste(L, text(s, 44, NAVY), x + 30, yy, 1)
        return
    age = t - SLAM
    paste(L, rays().rotate(age * 30, Image.BICUBIC), 540, 980, 1.0)
    s = 1.0 + 2.2 * (1 - ease_out(age / 0.22))
    paste(L, pill("PYTHON!", 170, fg=NAVY, bg=YELLOW, padx=56, pady=30), 540, 980, s, a=clamp(age / 0.08), rot=-4)
    paste(L, py_badge(260), 540, 1340, pop(age - 0.15))
    confetti(L, age, 540, 980, n=90, seed=9, spread=1000)


def sc_end(L, t, tl):
    c = card(860, 460, r=40, border=NAVY, bw=6)
    s = back_out(tl / 0.35)
    paste(L, c, 540, 900, s)
    if s > 0.9:
        paste(L, pill("NEXT  •  EP 02", 44, fg=NAVY, bg=YELLOW, padx=28, pady=12), 540, 730, pop(tl - 0.1))
        paste(L, text("print()", 150, NAVY, "mono"), 540, 900, pop(tl - 0.18))
        paste(L, text("Pehla code likhna!", 48, BLUE), 540, 1035, 1, a=ease((tl - 0.3) / 0.2))
    # FOLLOW button with cursor click
    t_click = cap_t("end", 1) + 0.15
    age = tl - 0.35
    if age > 0:
        press = 1.0 - 0.1 * math.exp(-((t - t_click - 0.05) / 0.06) ** 2) if t > t_click - 0.1 else 1.0
        pulse = 1 + 0.04 * math.sin(t * 9) if t < t_click else 1.0
        btn = pill("FOLLOW", 64, fg=WHITE, bg=RED, border=NAVY, padx=70, pady=22)
        paste(L, btn, 540, 1300, pop(age) * press * pulse)
        if t > t_click:
            rr = (t - t_click) * 700
            d = ImageDraw.Draw(L)
            d.ellipse((540 - rr, 1300 - rr * 0.5, 540 + rr, 1300 + rr * 0.5), outline=RED + (int(clamp(1 - (t - t_click) / 0.5) * 200),), width=6)
        u = ease((t - (t_click - 0.6)) / 0.55)
        if t > t_click - 0.6:
            paste(L, cursor(), 900 - 300 * u, 1560 - 220 * u, 1)
    age = tl - 0.6
    if age > 0:
        paste(L, text("Roz ek naya Python concept", 44, NAVY), 540, 1470, 1, a=ease(age / 0.25))
        paste(L, text("@PythonKiPathshala", 42, BLUE), 540, 1535, 1, a=ease((age - 0.1) / 0.25))


SCENE_FN = {"hook": sc_hook, "ask": sc_ask, "drop": sc_drop, "def": sc_def, "simple": sc_simple,
            "uses": sc_uses, "best": sc_best, "end": sc_end}


# ---------------------------------------------------------------- camera / transitions
WHIP_CUTS = {1: 1, 3: 1, 4: -1, 5: 1, 7: 1}     # cut index -> direction
PUNCH_TIMES = [CUTS[2], SLAM, CUTS[6]]
SHAKE_TIMES = [(CUTS[2], 22), (SLAM, 30)]
FLASH_TIMES = [CUTS[2], SLAM]


def camera(t):
    name, tl, i = scene_at(t)
    s = 1.0 + 0.025 * clamp(tl / 3.0)                       # slow push-in
    if name == "ask":
        s += 0.08 * ease(tl / (CUTS[2] - CUTS[1]))            # tension creep before the drop
    for tp in PUNCH_TIMES:
        if 0 <= t - tp < 0.4:
            s += 0.12 * (1 - ease_out((t - tp) / 0.4))
    # beat bump on the downbeat after the drop
    if t > CUTS[2] and not (kb(46.5) <= t < SLAM):
        ph = (t / BEAT) % 1.0
        s += 0.006 * math.exp(-ph * 8)
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


def whip(frame, t):
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
        out = np.roll(frame, int(off), axis=1)
        k = int(10 + 90 * vel)
        return cv2.blur(out, (k, 1))
    return frame


def flash(frame, t):
    for tp in FLASH_TIMES:
        age = t - tp
        if 0 <= age < 0.22:
            a = 0.85 * (1 - age / 0.22) ** 2
            return (frame * (1 - a) + 255 * a).astype(np.uint8)
    return frame


# ---------------------------------------------------------------- UI overlay
def overlay_ui(img, t):
    paste(img, pill("PYTHON KI PATHSHALA  •  EP 01", 30, fg=NAVY, bg=WHITE, border=NAVY, padx=24, pady=12,
                    shadow=False), 540, 120)
    cap = active_caption(t)
    if cap:
        key, i, ts = cap
        age = t - ts
        sp = caption(CAPS[key][i])
        s = pop(age, 0.22, 0.12)
        paste(img, sp, 540, 330 + 30 * (1 - ease_out(age / 0.2)), s)
    d = ImageDraw.Draw(img)
    y = 1868
    d.rounded_rectangle((60, y, W - 60, y + 14), 7, fill=(222, 212, 188, 255))
    p = clamp(t / DUR)
    xe = 60 + (W - 120) * p
    if xe > 70:
        n = 24
        for k in range(n):
            a0 = 60 + (xe - 60) * k / n
            a1 = 60 + (xe - 60) * (k + 1) / n
            c = tuple(int(BLUE[j] + (YELLOW[j] - BLUE[j]) * (k / (n - 1))) for j in range(3))
            d.rectangle((a0, y, a1 + 1, y + 14), fill=c + (255,))


def render(t):
    name, tl, _ = scene_at(t)
    bg = background(t)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENE_FN[name](L, t, tl)
    bg.alpha_composite(L)
    frame = np.asarray(bg.convert("RGB"))
    frame = apply_camera(frame, *camera(t))
    img = Image.fromarray(frame).convert("RGBA")
    overlay_ui(img, t)
    frame = np.asarray(img.convert("RGB"))
    frame = whip(frame, t)
    frame = flash(frame, t)
    return np.ascontiguousarray(frame)


def render_idx(i):
    return render(i / FPS).tobytes()


# ---------------------------------------------------------------- audio
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
    f = 48 + 110 * np.exp(-tt * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7)
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
        f = (600 + 4500 * (k / 11 if up else 1 - k / 11))
        out[k * seg:(k + 1) * seg] = bp(x[k * seg:(k + 1) * seg + 0], f * 0.7, min(f * 1.4, 20000))[:seg]
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return out * e * 0.7


def pop_sfx(f0=520):
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    f = f0 + 700 * tt / 0.12
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.03) * 0.6


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
    noise = hp(RNG.normal(0, 1, n), 1500) * u ** 2 * 0.35
    f = 200 + 1400 * u ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 1.5 * 0.25
    return noise + tone


def impact():
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tt * 10)) / SR) * np.exp(-tt * 2.8)
    crash = hp(RNG.normal(0, 1, n), 3000) * np.exp(-tt * 3.0) * 0.35
    return boom * 0.9 + crash


def click_sfx():
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2200 * tt) * env_exp(n, 0.006) + hp(RNG.normal(0, 1, n), 4000) * env_exp(n, 0.003)) * 0.5


# A minor: Am F C G  (semitones from A4)
CHORDS = [(-24, [0, 3, 7]), (-28, [0, 4, 7]), (-21, [0, 4, 7]), (-26, [0, 4, 7])]


def music():
    n = int((DUR + 1) * SR)
    drums, bass, pad, arp = (np.zeros(n) for _ in range(4))
    K, C, Hh = kick(), clap(), hat()
    nbeats = int(DUR / BEAT) + 2
    gap = (kb(46.5), SLAM)
    ask = (CUTS[1], CUTS[2])
    for b in range(nbeats):
        tb = kb(b)
        if gap[0] <= tb < gap[1]:
            continue
        in_ask = ask[0] <= tb < ask[1]
        chord_root, ivs = CHORDS[(b // 4) % 4]
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
                x = lp(saw(nfreq(chord_root), nb) * env_exp(nb, 0.12), 380)
                add(bass, x, tb + h * BEAT, 0.6 if tb >= CUTS[2] else 0.4)
        else:
            # snare roll building into the drop
            k = (tb - ask[0]) / (ask[1] - ask[0])
            steps = 2 if k < 0.5 else 4
            for s_ in range(steps):
                add(drums, C, tb + s_ * BEAT / steps, 0.25 + 0.5 * k)
        # arp (16ths)
        tones = [chord_root + 24 + iv for iv in ivs] + [chord_root + 36]
        for s_ in range(4):
            if not (gap[0] <= tb + s_ * BEAT / 4 < gap[1]):
                add(arp, pluck(nfreq(tones[(b * 4 + s_) % 4])), tb + s_ * BEAT / 4, 0.18)
        if b % 4 == 0:
            nb = int(4 * BEAT * SR)
            x = sum(saw(nfreq(chord_root + 12 + iv), nb, dt) for iv in ivs for dt in (-0.004, 0.004))
            x = lp(x, 1400) * np.minimum(1, np.arange(nb) / (0.05 * SR)) * np.minimum(1, (nb - np.arange(nb)) / (0.1 * SR))
            add(pad, x, tb, 0.05)
    # kick sidechain pump on pad + arp
    pump = np.ones(n)
    for b in range(nbeats):
        tb = kb(b)
        if tb >= CUTS[2] and not (gap[0] <= tb < gap[1]):
            i = int(tb * SR)
            m = min(int(BEAT * SR), n - i)
            if m > 0:
                pump[i:i + m] = 1 - 0.6 * np.exp(-np.arange(m) / (0.09 * SR))
    hook_lp = np.ones(n)
    mix = drums + bass + (pad + arp) * pump
    # muffle the "ask" build like a closing filter, then open on the drop
    i0, i1 = int(ask[0] * SR), int(ask[1] * SR)
    mix[i0:i1] = lp(mix[i0:i1], 900) * 0.8
    del hook_lp
    mix[int(gap[0] * SR):int(gap[1] * SR)] *= 0.0
    return mix


def sfx_track():
    n = int((DUR + 1) * SR)
    s = np.zeros(n)
    for ci in WHIP_CUTS:
        add(s, whoosh(0.34), CUTS[ci] - 0.17, 0.55)
    add(s, riser(CUTS[2] - CUTS[1]), CUTS[1], 0.7)
    add(s, riser(SLAM - kb(44)), kb(44), 0.6)
    add(s, impact(), CUTS[2], 0.9)
    add(s, impact(), SLAM, 1.0)
    # hook: 0 / 1 tiles
    add(s, pop_sfx(500), cap_t("hook", 1), 0.5)
    add(s, pop_sfx(650), cap_t("hook", 1) + 0.12, 0.5)
    # ask: bubble, ???, question mark
    add(s, pop_sfx(600), CUTS[1] + 0.35, 0.4)
    add(s, pop_sfx(420), CUTS[1] + 0.7, 0.4)
    # def: pill, chip whoosh, typing, ding
    add(s, pop_sfx(560), cap_t("def", 1), 0.45)
    ta = cap_t("def", 3) + 0.45
    add(s, whoosh(0.5), ta - 0.65, 0.35)
    for k in range(3):
        add(s, tick(), ta + k / 12, 0.8)
    add(s, ding(), ta + 0.3, 0.7)
    add(s, pop_sfx(700), cap_t("def", 4), 0.35)
    # simple: typing ticks, output ding, sticker, check
    for k in range(sum(CODE_CHARS)):
        if k % 2 == 0:
            add(s, tick(), CUTS[4] + CODE_TYPE_START + k / CODE_CPS, 0.7)
    add(s, ding(), CUTS[4] + CODE_TYPE_START + sum(CODE_CHARS) / CODE_CPS + 0.3, 0.6)
    add(s, pop_sfx(520), cap_t("simple", 1), 0.5)
    add(s, ding(), cap_t("simple", 4), 0.5)
    # uses: one pop per tile, rising pitch
    for i in range(4):
        add(s, pop_sfx(480 + 90 * i), cap_t("uses", i + 1), 0.55)
    # best: list rows
    for k in range(3):
        add(s, whoosh(0.22), CUTS[6] + 0.7 + k * 0.32, 0.25)
        add(s, pop_sfx(640), CUTS[6] + 0.85 + k * 0.32, 0.3)
    # end: click on FOLLOW
    add(s, pop_sfx(560), CUTS[7] + 0.35, 0.4)
    add(s, click_sfx(), cap_t("end", 1) + 0.15, 0.9)
    add(s, ding(), cap_t("end", 1) + 0.2, 0.4)
    return s


def voice_track():
    n = int((DUR + 1) * SR)
    v = np.zeros(n)
    for key, (start, end) in VO.items():
        a = vo_clip(key)
        if a is None:
            continue
        add(v, a, start)
        print(f"  vo {key:7s} {start:6.2f}-{start + len(a) / SR:6.2f}s (window ends {end:6.2f})")
    return v


def build_audio(path):
    m, s, v = music(), sfx_track(), voice_track()
    env = np.abs(v)
    env = signal.lfilter([1 - math.exp(-1 / (0.25 * SR))], [1, -math.exp(-1 / (0.25 * SR))], env)
    env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
    duck = 1 - 0.6 * env
    mix = m / (np.abs(m).max() + 1e-9) * 0.55 * duck + s / (np.abs(s).max() + 1e-9) * 0.5 * (1 - 0.3 * env)
    if v.any():
        mix += v / np.abs(v).max() * 0.9
    mix = mix[: int(DUR * SR)]
    fade = int(0.12 * SR)
    mix[-fade:] *= np.linspace(1, 0.3, fade)
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    sf.write(path, np.stack([mix, mix], 1).astype(np.float32), SR)


# ---------------------------------------------------------------- cover
def cover(path):
    bg = background(0.0)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste(L, rays().rotate(8), 540, 900, 1.0, a=0.9)
    paste(L, py_badge(420), 540, 880)
    paste(L, pill("PYTHON", 150, fg=NAVY, bg=YELLOW, padx=50, pady=26), 540, 360, rot=-3)
    paste(L, text("KYA HAI?", 160, NAVY), 540, 560)
    paste(L, pill("Hinglish  •  25 sec  •  Beginners", 44, fg=NAVY, bg=WHITE, padx=30, pady=16), 540, 1290)
    paste(L, pill("EP 01", 70, fg=WHITE, bg=RED, padx=40, pady=18), 540, 1450, rot=3)
    bg.alpha_composite(L)
    overlay_ui(bg, -1)
    bg.convert("RGB").save(path, quality=92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="render a contact sheet of stills only")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    for key in VO:                          # warm the caption-timing cache before forking
        cap_times(key)
    if args.preview:
        ts = np.linspace(0.2, DUR - 0.1, 24)
        ims = [Image.fromarray(render(t)).resize((270, 480)) for t in ts]
        sheet = Image.new("RGB", (270 * 8, 480 * 3))
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % 8) * 270, (k // 8) * 480))
        sheet.save(os.path.join(WORK, "preview.jpg"), quality=85)
        print("wrote", os.path.join(WORK, "preview.jpg"))
        return
    wav = os.path.join(WORK, "mix.wav")
    build_audio(wav)
    silent = os.path.join(WORK, "video.mp4")
    nf = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, buf in enumerate(pool.imap(render_idx, range(nf), chunksize=4)):
            ff.stdin.write(buf)
            if k % 75 == 0:
                print(f"  frame {k}/{nf}")
    ff.stdin.close()
    ff.wait()
    out = os.path.join(OUT, NAME)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    cover(os.path.join(OUT, "cover.jpg"))
    print("wrote", out)


if __name__ == "__main__":
    main()
