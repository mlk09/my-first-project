#!/usr/bin/env python3
"""Python Basics EP 01 - "Python kya hai?"  (1080x1920 YouTube Short)

Style decoded from Screenrecorder-2026-10-08-13-52-36-538.mp4 (the "Dark Code"
Python short) and pushed further:
  * dark code-editor world, VS Code Dark+ syntax colours, live typing + cursor
  * word-by-word karaoke captions at the top (white caps, spoken word yellow,
    keywords on a yellow marker)
  * pop-in motion graphics, camera push-ins, whip / zoom-through transitions,
    impact flashes + screen shake
  * original synthesised music bed (drops on "Python!") + SFX on every action

Voice:
  Put your recording in edit7/voice/ep01.(m4a|wav|mp3).  It is split into the 6
  script lines at its 5 longest pauses and every scene is stretched to fit your
  delivery.  Without a recording the timeline uses a natural speaking pace (a
  record-along cut: read the captions as they light up).

Usage:  python3 edit7/build_short.py [--preview]
"""
import glob
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit"))
import build_edit as fx  # noqa: E402  (synth + sfx helpers from the first edit)

WORK = os.path.join(HERE, "work")
OUT_DIR = os.path.join(HERE, "output")
FONTS = os.path.join(HERE, "assets", "fonts")
W, H, FPS, SR = 1080, 1920, 30, 48000
HANDLE = "@The IOT Engineer"

CAP = os.path.join(FONTS, "Poppins-ExtraBold.ttf")
BLACK = os.path.join(FONTS, "Poppins-Black.ttf")
MONO = os.path.join(FONTS, "JetBrainsMono-Bold.ttf")
MONO_R = os.path.join(FONTS, "JetBrainsMono-Regular.ttf")

# colours
BG = (22, 23, 27)
EDITOR = (30, 31, 34)
YEL = (255, 214, 10)
PY_BLUE = (55, 118, 171)
PY_YEL = (255, 212, 59)
WHITE = (255, 255, 255)
GREY = (140, 146, 158)
GREEN = (46, 204, 113)
RED = (255, 71, 87)
CYAN = (86, 182, 255)
ORANGE = (255, 149, 0)
PURPLE = (155, 89, 255)

# ------------------------------------------------------------------ script
# The voice script, unchanged.  One entry per scene.
LINES = [
    "Instagram, Netflix aur AI… in sab mein ek common cheez hai. Python!",
    "Python ek programming language hai. Matlab computer ko instructions dene ki language.",
    "Iski sabse badi khoobi? Yeh English jaisi simple dikhti hai. Isliye beginners ke liye best hai.",
    "Python se websites banti hain, AI aur chatbots bante hain, games bante hain, "
    "aur boring kaam automatic ho jaate hain.",
    "Dekho, yeh code bhi Python mein hai, aur aap isse padh kar hi samajh gaye ki yeh kya karega.",
    "Yahi hai Python ki power!",
]
MIN_DUR = [4.2, 4.2, 5.4, 6.6, 7.2, 2.6]
END_DUR = 2.6
# words that get the yellow marker box when spoken
KEYWORDS = {"python", "python!", "ai", "ai…", "programming", "language", "language.", "instructions",
            "english", "simple", "beginners", "best", "websites", "chatbots", "games", "automatic",
            "code", "power!", "netflix", "instagram"}

CODE = ['print("Python is used in:")', 'print("Websites")', 'print("AI")',
        'print("Games")', 'print("Automation")']
OUTPUT = ["Python is used in:", "Websites", "AI", "Games", "Automation"]


# ------------------------------------------------------------------ timing
def voice_file():
    for ext in ("m4a", "wav", "mp3", "aac", "ogg"):
        p = glob.glob(os.path.join(HERE, "voice", f"ep01.{ext}"))
        if p:
            return p[0]
    return None


def load_audio(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def split_voice(x):
    """Return 6 (start, end) sample ranges, cut at the 5 longest pauses."""
    hop = SR // 100
    b = fx.filt(x, "bandpass", [200, 3800])
    r = np.sqrt(np.convolve(b ** 2, np.ones(hop) / hop, "same"))[::hop]
    db = 20 * np.log10(r + 1e-9)
    lo, hi = np.percentile(db, 10), np.percentile(db, 95)
    speech = db > lo + 0.35 * (hi - lo)
    idx = np.flatnonzero(speech)
    first, last = idx[0], idx[-1]
    gaps, i = [], first
    while i < last:
        if not speech[i]:
            j = i
            while not speech[j]:
                j += 1
            gaps.append((j - i, i, j))
            i = j
        else:
            i += 1
    override = os.path.join(HERE, "voice", "ep01_splits.json")
    if os.path.exists(override):   # manual cut points in seconds, if auto-split misfires
        cuts = json.load(open(override))
        bounds = [first / 100] + cuts + [last / 100 + 0.01]
        segs = [(bounds[k], bounds[k + 1]) for k in range(len(LINES))]
    else:
        top = sorted(sorted(gaps, reverse=True)[: len(LINES) - 1], key=lambda g: g[1])
        if len(top) < len(LINES) - 1:
            sys.exit("voice: could not find 5 pauses between the 6 lines - add voice/ep01_splits.json")
        edges = [first] + [v for g in top for v in (g[1], g[2])] + [last + 1]
        segs = [(edges[2 * k] / 100, edges[2 * k + 1] / 100) for k in range(len(LINES))]
    return [(max(0, int((a - 0.06) * SR)), min(len(x), int((b + 0.12) * SR))) for a, b in segs]


def build_timing():
    vf = voice_file()
    lines = []
    if vf:
        x = load_audio(vf)
        segs = split_voice(x)
        durs = [max(MIN_DUR[k], (b - a) / SR + 0.32) for k, (a, b) in enumerate(segs)]
    else:
        x, segs = None, None
        durs = [max(MIN_DUR[k], 0.34 * len(LINES[k].split()) + 0.6) for k in range(len(LINES))]
    t = 0.25                                       # tiny lead-in before the first word
    for k, text in enumerate(LINES):
        words = text.split()
        speak = ((segs[k][1] - segs[k][0]) / SR - 0.15) if segs else durs[k] - 0.4
        wts = [len(w.strip(",.?!…")) + 1.6 + (3.5 if w[-1] in ",.?!…" else 0) for w in words]
        cum = np.concatenate([[0], np.cumsum(wts)])[:-1] / sum(wts) * speak
        lines.append({"start": t, "dur": durs[k], "words": words,
                      "wt": [t + 0.06 + c for c in cum]})
        t += durs[k]
    total = t + END_DUR
    if x is not None:   # lay the voice lines on the new timeline
        voice = np.zeros(int((total + 0.1) * SR), np.float32)
        for k, (a, b) in enumerate(segs):
            fx.place(voice, x[a:b], lines[k]["start"], 1.0)
        fx.write_wav(os.path.join(WORK, "voice.wav"), voice)
    return lines, total, x is not None


# ------------------------------------------------------------------ helpers
@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def back(t, s=1.9):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def pop(age, dur=0.32):
    """scale for a pop-in that started `age` seconds ago"""
    if age < 0:
        return 0.0
    return back(age / dur)


def paste(base, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.02 or alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(im.width, base.width - x), min(im.height, base.height - y)
    if ex <= sx or ey <= sy:
        return
    base.alpha_composite(im.crop((sx, sy, ex, ey)), (x + sx, y + sy))


SS = 3   # supersampling for vector shapes


@lru_cache(None)
def rrect(w, h, r, fill, outline=None, ow=0, grad=None, shadow=0):
    """Anti-aliased rounded rectangle (optionally vertical gradient + drop shadow)."""
    pad = shadow * 2
    im = Image.new("RGBA", ((w + 2 * pad) * SS, (h + 2 * pad) * SS))
    d = ImageDraw.Draw(im)
    box = (pad * SS, pad * SS, (pad + w) * SS - 1, (pad + h) * SS - 1)
    if grad:
        g = Image.new("RGBA", (1, 2))
        g.putpixel((0, 0), grad[0] + (255,))
        g.putpixel((0, 1), grad[1] + (255,))
        g = g.resize((w * SS, h * SS), Image.BILINEAR)
        m = Image.new("L", (w * SS, h * SS))
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), r * SS, fill=255)
        im.paste(g, (pad * SS, pad * SS), m)
        if outline:
            d.rounded_rectangle(box, r * SS, outline=outline, width=ow * SS)
    else:
        d.rounded_rectangle(box, r * SS, fill=fill, outline=outline, width=ow * SS)
    im = im.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        m = im.getchannel("A").filter(ImageFilter.GaussianBlur(shadow))
        sh.putalpha(m.point(lambda v: int(v * 0.65)))
        out = Image.new("RGBA", im.size)
        out.alpha_composite(sh, (0, shadow // 2))
        out.alpha_composite(im)
        return out
    return im


def text_img(txt, fpath, size, fill, stroke=0, sfill=(0, 0, 0), glow=None):
    f = font(fpath, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    pad = 30 if glow else 4
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad))
    d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    if glow:
        g = Image.new("RGBA", im.size, glow + (0,))
        g.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(14)))
        out = Image.new("RGBA", im.size)
        out.alpha_composite(g)
        out.alpha_composite(g)
        out.alpha_composite(im)
        return out
    return im


text_cached = lru_cache(None)(text_img)


def icon_canvas(size):
    im = Image.new("RGBA", (size * SS, size * SS))
    return im, ImageDraw.Draw(im), SS * size


def done(im, size):
    return im.resize((size, size), Image.LANCZOS)


def icon_globe(size, phase=0.0, col=WHITE):
    im, d, s = icon_canvas(size)
    w = int(s * 0.055)
    c, r = s / 2, s * 0.42
    d.ellipse((c - r, c - r, c + r, c + r), outline=col, width=w)
    for k in range(3):
        f = math.cos(phase + k * math.pi / 3)
        rx = abs(f) * r
        if rx > w:
            d.ellipse((c - rx, c - r, c + rx, c + r), outline=col, width=w)
    d.line((c, c - r, c, c + r), fill=col, width=w)
    for yy in (-0.45, 0, 0.45):
        hw = math.sqrt(max(0, 1 - yy * yy)) * r
        d.line((c - hw, c + yy * r, c + hw, c + yy * r), fill=col, width=w)
    return done(im, size)


def icon_robot(size, blink=False, col=WHITE):
    im, d, s = icon_canvas(size)
    w = int(s * 0.055)
    d.line((s * .5, s * .12, s * .5, s * .26), fill=col, width=w)
    d.ellipse((s * .44, s * .06, s * .56, s * .18), fill=col)
    d.rounded_rectangle((s * .18, s * .26, s * .82, s * .78), s * .12, outline=col, width=w)
    d.rounded_rectangle((s * .08, s * .42, s * .18, s * .62), s * .03, fill=col)
    d.rounded_rectangle((s * .82, s * .42, s * .92, s * .62), s * .03, fill=col)
    for ex in (.37, .63):
        if blink:
            d.line((s * (ex - .07), s * .47, s * (ex + .07), s * .47), fill=col, width=w)
        else:
            d.ellipse((s * (ex - .07), s * .40, s * (ex + .07), s * .54), fill=col)
    d.rounded_rectangle((s * .34, s * .62, s * .66, s * .68), s * .03, fill=col)
    return done(im, size)


def icon_gamepad(size, col=WHITE):
    im, d, s = icon_canvas(size)
    w = int(s * 0.055)
    d.rounded_rectangle((s * .06, s * .28, s * .94, s * .74), s * .2, outline=col, width=w)
    t = s * .06
    d.rectangle((s * .26 - t / 2, s * .51 - t * 1.6, s * .26 + t / 2, s * .51 + t * 1.6), fill=col)
    d.rectangle((s * .26 - t * 1.6, s * .51 - t / 2, s * .26 + t * 1.6, s * .51 + t / 2), fill=col)
    for bx, by in ((.70, .43), (.80, .53), (.70, .61), (.60, .53)):
        d.ellipse((s * bx - t * .8, s * by - t * .8, s * bx + t * .8, s * by + t * .8), fill=col)
    return done(im, size)


def icon_gear(size, ang=0.0, col=WHITE):
    im, d, s = icon_canvas(size)
    c = s / 2
    pts = []
    n = 8
    for k in range(n * 4):
        a = ang + k / (n * 4) * 2 * math.pi
        r = s * (0.44 if (k % 4) in (1, 2) else 0.33)
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=col)
    r = s * .14
    d.ellipse((c - r, c - r, c + r, c + r), fill=(0, 0, 0, 0))
    return done(im, size)


def icon_chip(size, col=WHITE):
    im, d, s = icon_canvas(size)
    w = int(s * 0.05)
    d.rounded_rectangle((s * .22, s * .22, s * .78, s * .78), s * .07, outline=col, width=w)
    for k in range(4):
        p = s * (.32 + k * .12)
        for a, b in ((s * .06, s * .22), (s * .78, s * .94)):
            d.line((p, a, p, b), fill=col, width=w)
            d.line((a, p, b, p), fill=col, width=w)
    f = font(BLACK, int(s * .22))
    d.text((s / 2, s / 2), "AI", font=f, fill=col, anchor="mm")
    return done(im, size)


def icon_camera(size, col=WHITE):
    im, d, s = icon_canvas(size)
    w = int(s * 0.07)
    d.rounded_rectangle((s * .12, s * .12, s * .88, s * .88), s * .24, outline=col, width=w)
    d.ellipse((s * .32, s * .32, s * .68, s * .68), outline=col, width=w)
    d.ellipse((s * .68, s * .22, s * .76, s * .30), fill=col)
    return done(im, size)


def icon_play(size, col=WHITE):
    im, d, s = icon_canvas(size)
    w = int(s * 0.06)
    d.rounded_rectangle((s * .08, s * .2, s * .92, s * .8), s * .12, outline=col, width=w)
    d.polygon([(s * .42, s * .36), (s * .42, s * .64), (s * .64, s * .5)], fill=col)
    return done(im, size)


def icon_person(size, col=WHITE):
    im, d, s = icon_canvas(size)
    d.ellipse((s * .32, s * .08, s * .68, s * .44), fill=col)
    d.pieslice((s * .12, s * .5, s * .88, s * 1.26), 180, 360, fill=col)
    return done(im, size)


def icon_check(size, ok=True):
    im, d, s = icon_canvas(size)
    col = GREEN if ok else RED
    d.ellipse((0, 0, s - 1, s - 1), fill=col)
    w = int(s * .12)
    if ok:
        d.line([(s * .27, s * .52), (s * .44, s * .69), (s * .74, s * .34)], fill=WHITE, width=w, joint="curve")
    else:
        d.line((s * .3, s * .3, s * .7, s * .7), fill=WHITE, width=w)
        d.line((s * .7, s * .3, s * .3, s * .7), fill=WHITE, width=w)
    return done(im, size)


@lru_cache(None)
def cached_icon(name, size, *a):
    return globals()["icon_" + name](size, *a)


# ------------------------------------------------------------------ syntax highlight
KW_COL = {"print": (220, 220, 170), "str": (86, 156, 214)}
BR_COL = [(255, 215, 0), (218, 112, 214), (23, 159, 255)]


def tokens(line):
    out, i, depth = [], 0, 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            j = line.find('"', i + 1)
            j = len(line) if j < 0 else j + 1
            out.append((line[i:j], (206, 145, 120)))
            i = j
        elif ch in "([{":
            out.append((ch, BR_COL[depth % 3]))
            depth += 1
            i += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
            out.append((ch, BR_COL[depth % 3]))
            i += 1
        elif ch.isalpha() or ch == "_":
            j = i
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            w = line[i:j]
            out.append((w, KW_COL.get(w, (156, 220, 254))))
            i = j
        else:
            out.append((ch, (212, 212, 212)))
            i += 1
    return out


def draw_code(d, x, y, line, fsize, upto=None):
    """draws (possibly partially typed) code; returns x of the end"""
    f = font(MONO, fsize)
    shown = line if upto is None else line[:upto]
    cx = x
    n = 0
    for tok, col in tokens(line):
        if n >= len(shown):
            break
        part = tok[: len(shown) - n]
        d.text((cx, y), part, font=f, fill=col, anchor="ls")
        cx += f.getlength(part)
        n += len(tok)
    return cx


# ------------------------------------------------------------------ captions
def chunks(line):
    """group words into caption chunks of max 3 words, breaking after punctuation"""
    out, cur = [], []
    for i, w in enumerate(line["words"]):
        cur.append(i)
        if len(cur) == 3 or w[-1] in ",.?!…":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def draw_caption(fr, line, lt_abs):
    words, wt = line["words"], line["wt"]
    ch = None
    for c in chunks(line):
        if wt[c[0]] - 0.04 <= lt_abs:
            ch = c
    if ch is None:
        return
    age = lt_abs - wt[ch[0]]
    cur = max(i for i in ch if wt[i] - 0.04 <= lt_abs)
    size = 80
    f = font(CAP, size)
    labels = [words[i].upper() for i in ch]
    space = f.getlength(" ")
    tw = sum(f.getlength(s) for s in labels) + space * (len(labels) - 1)
    if tw > 980:
        size = int(size * 980 / tw)
        f = font(CAP, size)
        space = f.getlength(" ")
        tw = sum(f.getlength(s) for s in labels) + space * (len(labels) - 1)
    lay = Image.new("RGBA", (W, 260))
    d = ImageDraw.Draw(lay)
    x = (W - tw) / 2
    cy = 130
    for i, lab in zip(ch, labels):
        lw = f.getlength(lab)
        active = i == cur
        key = words[i].lower().strip(",.?") in KEYWORDS or words[i].lower() in KEYWORDS
        if active and key:
            d.rounded_rectangle((x - 12, cy - size * 0.62, x + lw + 12, cy + size * 0.56), 16, fill=YEL)
            d.text((x, cy), lab, font=f, fill=(15, 15, 15), anchor="lm")
        else:
            col = YEL if active else WHITE
            d.text((x, cy), lab, font=f, fill=col, anchor="lm", stroke_width=7, stroke_fill=(0, 0, 0))
        x += lw + space
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .7)))
    out = Image.new("RGBA", lay.size)
    out.alpha_composite(sh, (0, 8))
    out.alpha_composite(lay)
    s = 0.75 + 0.25 * back(age / 0.22) if age < 0.22 else 1.0
    paste(fr, out, W / 2, 330, s, clamp(age / 0.08))


# ------------------------------------------------------------------ background
_rng = np.random.default_rng(7)
PARTICLES = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(18, 46), _rng.uniform(15, 40),
              _rng.choice(list("{}()[]<>=:#\"'+*/01")), _rng.uniform(0.05, 0.13)) for _ in range(34)]


@lru_cache(None)
def grid_img():
    im = Image.new("RGBA", (W, H + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, H + 80, 80):
        for x in range(40, W, 80):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 255, 255, 22))
    return im


@lru_cache(None)
def glow_img(col):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = Image.new("L", (W, H))
    ImageDraw.Draw(a).ellipse((W * .5 - 620, H * .52 - 620, W * .5 + 620, H * .52 + 620), fill=110)
    a = a.filter(ImageFilter.GaussianBlur(220))
    im.paste(Image.new("RGBA", (W, H), col + (255,)), (0, 0), a)
    return im


def background(t, accent):
    fr = Image.new("RGBA", (W, H), BG + (255,))
    fr.alpha_composite(glow_img(accent))
    off = int(t * 18) % 80
    fr.alpha_composite(grid_img().crop((0, off, W, off + H)))
    d = ImageDraw.Draw(fr)
    for (x, y, sz, sp, ch, al) in PARTICLES:
        yy = (y - t * sp) % (H + 100) - 50
        d.text((x, yy), ch, font=font(MONO, int(sz)), fill=(255, 255, 255, int(255 * al)))
    return fr


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .7)) ** 2)
    return np.clip(1.0 - 0.45 * r ** 2.2, 0.45, 1)[..., None]


GRAIN = [np.random.default_rng(s).normal(0, 4.5, (H // 2, W // 2, 1)).astype(np.float32) for s in range(6)]


# ------------------------------------------------------------------ scenes
# each scene draws onto a transparent stage and returns optional camera params
def kwa(line, sub):
    """absolute time of the first word containing `sub`"""
    for i, w in enumerate(line["words"]):
        if sub.lower() in w.lower():
            return line["wt"][i]
    raise KeyError(sub)


def kw(line, sub):
    """same, relative to the start of the line's scene"""
    return kwa(line, sub) - line["start"]


def app_card(name, col1, col2, icon):
    c = rrect(300, 300, 64, None, (255, 255, 255, 60), 3, (col1, col2), 26).copy()
    paste(c, cached_icon(icon, 150), c.width / 2, c.height / 2 - 18)
    lab = text_cached(name, CAP, 40, WHITE)
    paste(c, lab, c.width / 2, c.height / 2 + 100)
    return c


@lru_cache(None)
def hook_cards():
    return [app_card("Instagram", (131, 58, 180), (253, 140, 50), "camera"),
            app_card("Netflix", (60, 10, 14), (229, 9, 20), "play"),
            app_card("AI", (0, 120, 220), (0, 200, 170), "chip")]


@lru_cache(None)
def python_title():
    a = text_img("Python", BLACK, 190, PY_YEL, 11, PY_BLUE, glow=PY_YEL)
    return a


def rays(st, cx, cy, t, col, n=18, alpha=70, r=1400):
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    for k in range(n):
        a0 = t * 0.4 + k * 2 * math.pi / n
        a1 = a0 + math.pi / n * 0.55
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=col + (alpha,))
    st.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)))


def scene_hook(st, line, t):
    tp = kw(line, "Python")
    tc = kw(line, "common")
    times = [kw(line, "Instagram"), kw(line, "Netflix"), kw(line, "AI")]
    xs, y = [195, 540, 885], 980
    fly = ease_io((t - tp + 0.05) / 0.22)
    d = ImageDraw.Draw(st)
    if tc <= t < tp + 0.1:      # converging dashed lines to the question mark
        p = ease_out((t - tc) / 0.5)
        for x in xs:
            for s in np.arange(0, p, 0.08):
                a = (x + (540 - x) * s, y + 190 + 230 * s)
                b = (x + (540 - x) * min(p, s + 0.04), y + 190 + 230 * min(p, s + 0.04))
                d.line([a, b], fill=YEL + (255,), width=8)
        q = text_cached("?", BLACK, 150, YEL, 8, (0, 0, 0))
        paste(st, q, 540, 1500, pop(t - tc - 0.3), 1 - fly)
    for k, (c, x, t0) in enumerate(zip(hook_cards(), xs, times)):
        s = pop(t - t0, 0.36)
        wob = math.sin((t - t0) * 9) * 7 * math.exp(-(t - t0) * 4) if t > t0 else 0
        bob = math.sin(t * 2.4 + k) * 10
        cx, cy = x + (540 - x) * fly, (y + bob) + (1050 - y - bob) * fly
        paste(st, c, cx, cy, s * (1 - 0.8 * fly), 1 - fly, [-6, 0, 6][k] + wob)
    if t >= tp - 0.02:
        age = t - tp
        rays(st, 540, 1050, t, PY_YEL, alpha=int(60 * clamp(age / 0.2)))
        s = 1 + 1.3 * (1 - ease_out(age / 0.2)) if age < 0.2 else 1 + 0.03 * math.sin(age * 5)
        paste(st, python_title(), 540, 1050, s, clamp(age / 0.06))
        sub = text_cached("1 language. Har jagah.", CAP, 50, WHITE, 5, (0, 0, 0))
        paste(st, sub, 540, 1250, pop(age - 0.35), 1)
    zoom = 1.0 + 0.04 * clamp(t / line["dur"])
    return {"zoom": zoom, "cy": 1050}


@lru_cache(None)
def monitor_img(txt):
    im = Image.new("RGBA", (340, 330))
    paste(im, rrect(320, 220, 22, (45, 48, 56), (120, 130, 150), 6), 170, 115)
    paste(im, rrect(280, 180, 12, (12, 14, 18)), 170, 115)
    d = ImageDraw.Draw(im)
    d.rectangle((150, 225, 190, 280), fill=(120, 130, 150))
    d.rounded_rectangle((90, 278, 250, 300), 10, fill=(120, 130, 150))
    if txt:
        d.text((170, 115), txt, font=font(MONO, 44), fill=GREEN, anchor="mm")
    return im


def scene_language(st, line, t):
    d = ImageDraw.Draw(st)
    tprog = kw(line, "programming")
    tins = kw(line, "instructions")
    tcomp = kw(line, "computer")
    chip = rrect(760, 110, 55, None, None, 0, ((40, 90, 200), (110, 60, 220)), 20)
    lab = text_cached("PROGRAMMING LANGUAGE", CAP, 50, WHITE)
    c2 = chip.copy()
    paste(c2, lab, c2.width / 2, c2.height / 2 + 2)
    paste(st, c2, 540, 640, pop(t - tprog), 1)
    # you -> computer diagram
    a0 = 0.05
    paste(st, rrect(240, 240, 120, (40, 44, 54), CYAN, 6), 220, 1020, pop(t - a0))
    paste(st, cached_icon("person", 130, CYAN), 220, 1035, pop(t - a0))
    paste(st, text_cached("YOU", CAP, 46, CYAN), 220, 1185, pop(t - a0 - .1))
    arrived = t > tins + 0.75
    bounce = 1 + 0.08 * math.sin((t - tcomp) * 18) * math.exp(-(t - tcomp) * 5) if t > tcomp else 1
    paste(st, monitor_img("Hello!" if arrived else ""), 850, 1020, pop(t - a0 - .15) * bounce)
    paste(st, text_cached("COMPUTER", CAP, 46, GREEN), 850, 1205, pop(t - a0 - .25))
    # track
    p = ease_out((t - 0.3) / 0.5)
    if p > 0:
        x0, x1 = 360, 670
        d.line((x0, 1020, x0 + (x1 - x0) * p, 1020), fill=(255, 255, 255, 60), width=6)
        if p > 0.95:
            d.polygon([(x1, 1000), (x1 + 34, 1020), (x1, 1040)], fill=(255, 255, 255, 120))
    for k, cmd in enumerate(['print()', 'if', 'for']):
        t0 = tins + k * 0.28
        if t >= t0:
            q = ((t - t0) / 0.7) % 1.6
            if q <= 1:
                pill = rrect(150, 62, 31, YEL)
                pc = pill.copy()
                ImageDraw.Draw(pc).text((75, 31), cmd, font=font(MONO, 30), fill=(15, 15, 15), anchor="mm")
                paste(st, pc, 360 + 330 * ease_io(q), 1020 - 40 * math.sin(q * math.pi), 1, 1 - max(0, q - .85) / .15)
    if t > tins:
        note = text_cached("instructions = code", MONO_R, 44, WHITE)
        paste(st, note, 540, 1360, pop(t - tins - 0.1))
    return {"zoom": 1.0 + 0.05 * ease_io(t / line["dur"]), "cy": 1000}


@lru_cache(None)
def java_card():
    c = rrect(940, 360, 30, (30, 31, 36), (70, 74, 84), 3, None, 20).copy()
    d = ImageDraw.Draw(c)
    d.text((80, 88), "Doosri languages", font=font(CAP, 36), fill=GREY, anchor="lm")
    code = ['public class Main {', '  public static void main(String[] a) {',
            '    System.out.println("Hello");', '  }', '}']
    for k, ln in enumerate(code):
        draw_code(d, 80, 160 + k * 48, ln, 30)
    return c


@lru_cache(None)
def py_card():
    c = rrect(940, 260, 30, (24, 40, 34), GREEN, 5, None, 20).copy()
    d = ImageDraw.Draw(c)
    d.text((80, 92), "Python", font=font(CAP, 40), fill=GREEN, anchor="lm")
    draw_code(d, 80, 230, 'print("Hello")', 62)
    return c


@lru_cache(None)
def stamp_img():
    c = rrect(760, 130, 20, None, YEL, 9).copy()
    paste(c, text_img("BEGINNERS KE LIYE BEST", CAP, 54, YEL), c.width / 2, c.height / 2 + 3)
    return c


def scene_simple(st, line, t):
    te, ts, tb = kw(line, "English"), kw(line, "simple"), kw(line, "beginners")
    dim = 1 - 0.45 * clamp((t - ts) / 0.3)
    paste(st, java_card(), 540, 760, pop(t - 0.05), dim)
    paste(st, text_cached("5 lines", CAP, 40, RED), 820, 615, pop(t - ts), 1)
    s = pop(t - te)
    glow = 1 + 0.025 * math.sin(t * 6) if t > ts else 1
    paste(st, py_card(), 540, 1125, s * glow)
    paste(st, text_cached("1 line", CAP, 40, GREEN), 830, 1035, pop(t - ts - .05), 1)
    paste(st, cached_icon("check", 110, False), 960, 600, pop(t - ts, .25))
    paste(st, cached_icon("check", 110, True), 960, 1020, pop(t - ts - .12, .25))
    if t > tb - 0.02:
        age = t - tb
        sc = 1 + 1.2 * (1 - ease_out(age / 0.16)) if age < 0.16 else 1
        paste(st, stamp_img(), 540, 1420, sc, clamp(age / 0.05), -6)
    return {"zoom": 1.0 + 0.04 * ease_io(t / line["dur"]), "cy": 1050}


TILES = [("Websites", ORANGE, "globe"), ("AI & Chatbots", CYAN, "robot"),
         ("Games", PURPLE, "gamepad"), ("Automation", GREEN, "gear")]


def scene_uses(st, line, t):
    tw = [kw(line, "websites"), kw(line, "chatbots") - 0.25, kw(line, "games"), kw(line, "boring")]
    pos = [(300, 820), (780, 820), (300, 1270), (780, 1270)]
    active = max([k for k in range(4) if t >= tw[k]], default=-1)
    for k, ((name, col, ic), (x, y), t0) in enumerate(zip(TILES, pos, tw)):
        on = k == active
        c = rrect(430, 410, 46, (34, 36, 44), col if on else (70, 74, 84), 7 if on else 3, None, 22).copy()
        if ic == "globe":
            icon = icon_globe(190, t * 1.6, col)
        elif ic == "robot":
            icon = icon_robot(190, (t % 2.2) < 0.12, col)
        elif ic == "gear":
            icon = icon_gear(190, t * 1.4, col)
        else:
            icon = cached_icon("gamepad", 190, col)
        wig = math.sin(t * 10) * 4 if (ic == "gamepad" and on) else 0
        paste(c, icon, c.width / 2, c.height / 2 - 40, 1, 1, wig)
        paste(c, text_cached(name, CAP, 46, WHITE), c.width / 2, c.height / 2 + 125)
        s = pop(t - t0, 0.34) * (1.05 if on else 1.0)
        paste(st, c, x, y + math.sin(t * 2 + k) * 6, s, 1 if on or active < 0 else 0.72)
    return {"zoom": 1.0 + 0.05 * ease_io(t / line["dur"]), "cy": 1045}


CPS = 30.0      # typing speed (chars / second)


def code_schedule(line):
    t0 = 0.25
    starts, t = [], t0
    for ln in CODE:
        starts.append(t)
        t += len(ln) / CPS + 0.12
    tend = t
    tsel = max(kw(line, "padh"), tend + 0.05)
    trun = max(kw(line, "samajh"), tsel + 0.7)
    return starts, tend, tsel, trun


@lru_cache(None)
def editor_frame():
    c = rrect(940, 1000, 26, EDITOR, (60, 63, 72), 3, None, 26).copy()
    d = ImageDraw.Draw(c)
    pad = 52   # = shadow padding of rrect
    d.rectangle((pad + 3, pad + 3, c.width - pad - 4, pad + 70), fill=(24, 25, 28))
    for k, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((pad + 28 + k * 38, pad + 24, pad + 50 + k * 38, pad + 46), fill=col)
    d.rounded_rectangle((pad + 160, pad + 12, pad + 400, pad + 70), 8, fill=EDITOR)
    d.text((pad + 280, pad + 42), "uses.py", font=font(MONO_R, 30), fill=WHITE, anchor="mm")
    return c


def scene_code(st, line, t):
    starts, tend, tsel, trun = code_schedule(line)
    ed = editor_frame().copy()
    d = ImageDraw.Draw(ed)
    ox, oy, lh, fs = 140, 200, 78, 44
    cur_line, cur_x = 0, ox
    if tsel <= t < tsel + 0.6:      # selection sweep, like the reference
        p = ease_out((t - tsel) / 0.35)
        for k, ln in enumerate(CODE):
            wpx = font(MONO, fs).getlength(ln) * p
            d.rectangle((ox - 6, oy + k * lh - 50, ox + wpx, oy + k * lh + 16), fill=(38, 79, 120))
    for k, ln in enumerate(CODE):
        d.text((ox - 50, oy + k * lh), str(k + 1), font=font(MONO_R, 34), fill=(110, 118, 129), anchor="rs")
        if t < starts[k]:
            break
        n = int((t - starts[k]) * CPS)
        x_end = draw_code(d, ox, oy + k * lh, ln, fs, min(n, len(ln)))
        cur_line, cur_x = k, x_end
    if t < trun and (t % 0.8 < 0.45 or t < tend):
        d.rectangle((cur_x + 2, oy + cur_line * lh - 44, cur_x + 6, oy + cur_line * lh + 10), fill=WHITE)
    # run button
    bx, by = 800, 88
    pressed = trun <= t < trun + 0.12
    d.rounded_rectangle((bx - 70, by - 30, bx + 70, by + 30), 12,
                        fill=(30, 140, 70) if pressed else (39, 174, 96))
    d.polygon([(bx - 40, by - 14), (bx - 40, by + 14), (bx - 16, by)], fill=WHITE)
    d.text((bx + 18, by + 1), "Run", font=font(CAP, 30), fill=WHITE, anchor="mm")
    # terminal
    tp = ease_out((t - trun - 0.1) / 0.3)
    if tp > 0:
        ty = 640 + int((1 - tp) * 60)
        d.rectangle((55, ty, ed.width - 56, ed.height - 70), fill=(20, 21, 24))
        d.line((55, ty, ed.width - 56, ty), fill=(60, 63, 72), width=3)
        d.text((90, ty + 40), "TERMINAL", font=font(MONO, 26), fill=GREY, anchor="lm")
        d.text((90, ty + 95), "$ python uses.py", font=font(MONO_R, 36), fill=GREY, anchor="lm")
        for k, o in enumerate(OUTPUT):
            to = trun + 0.35 + k * 0.2
            if t >= to:
                a = int(255 * clamp((t - to) / 0.1))
                d.text((90 + 14 * (1 - ease_out((t - to) / 0.15)), ty + 160 + k * 50), o,
                       font=font(MONO, 40), fill=(GREEN if k else WHITE) + (a,), anchor="lm")
    s = pop(t, 0.4)
    paste(st, ed, 540, 1010, s)
    # mouse pointer flying to Run
    if trun - 0.45 < t < trun + 0.5:
        q = ease_io((t - trun + 0.45) / 0.45)
        rx, ry = 540 - ed.width / 2 + bx, 1010 - ed.height / 2 + by     # Run button on stage
        px, py = 820 + (rx - 820) * q, 1450 + (ry - 1450) * q
        pd = ImageDraw.Draw(st)
        pts = [(0, 0), (0, 52), (14, 40), (24, 62), (34, 58), (24, 36), (42, 36)]
        pd.polygon([(px + a, py + b) for a, b in pts], fill=WHITE, outline=(0, 0, 0))
    # camera follows the cursor while typing, then frames the terminal
    if t < trun:
        cy, zoom = 520 + cur_line * lh + 200 + 10, 1.0 + 0.08 * ease_io(t / 0.8)
    else:
        q = ease_io((t - trun) / 0.5)
        cy, zoom = (520 + cur_line * lh + 210) * (1 - q) + 1150 * q, 1.08 - 0.06 * q
    return {"zoom": zoom, "cy": cy}


def scene_power(st, line, t):
    tpy, tpw = kw(line, "Python"), kw(line, "power")
    rays(st, 540, 1060, t, YEL, n=22, alpha=int(70 * clamp((t - tpw) / 0.15)))
    paste(st, text_cached("YAHI HAI", CAP, 90, WHITE, 6, (0, 0, 0)), 540, 820, pop(t - 0.02))
    paste(st, text_cached("PYTHON KI", BLACK, 130, PY_YEL, 9, PY_BLUE), 540, 960, pop(t - tpy))
    if t >= tpw - 0.02:
        age = t - tpw
        s = 1 + 1.5 * (1 - ease_out(age / 0.18)) if age < 0.18 else 1 + 0.025 * math.sin(age * 9)
        paste(st, text_img("POWER!", BLACK, 220, YEL, 10, (0, 0, 0), glow=ORANGE), 540, 1170, s,
              clamp(age / 0.05), -4)
    return {"zoom": 1.0 + 0.06 * ease_io(t / line["dur"]), "cy": 1000}


def scene_end(st, t):
    paste(st, text_cached("PYTHON BASICS", CAP, 56, GREY), 540, 640, pop(t))
    card = rrect(900, 300, 40, None, (255, 255, 255, 50), 3, ((40, 90, 200), (110, 60, 220)), 24).copy()
    paste(card, text_img("NEXT: EP 02", CAP, 48, YEL), card.width / 2, card.height / 2 - 70)
    paste(card, text_img("VARIABLES", BLACK, 120, WHITE), card.width / 2, card.height / 2 + 35)
    paste(st, card, 540, 880, pop(t - 0.12, .4))
    tc = 1.15
    followed = t >= tc
    btn = rrect(560, 130, 65, (60, 60, 66) if followed else RED)
    b = btn.copy()
    paste(b, text_img("FOLLOWING" if followed else "FOLLOW", CAP, 54, WHITE), b.width / 2, b.height / 2 + 3)
    press = 0.9 if tc <= t < tc + 0.1 else 1
    paste(st, b, 540, 1230, pop(t - 0.4) * press)
    if 0.55 < t < tc + 0.5:
        q = ease_io((t - 0.55) / (tc - 0.55))
        px, py = 900 - 240 * q, 1500 - 250 * q
        d = ImageDraw.Draw(st)
        pts = [(0, 0), (0, 52), (14, 40), (24, 62), (34, 58), (24, 36), (42, 36)]
        d.polygon([(px + a, py + bb) for a, bb in pts], fill=WHITE, outline=(0, 0, 0))
    paste(st, text_cached("Roz ek naya Python concept", CAP, 46, WHITE), 540, 1390, pop(t - 0.6))
    paste(st, text_cached(HANDLE, CAP, 44, GREY), 540, 1470, pop(t - 0.75))
    return {"zoom": 1.0 + 0.03 * ease_io(t / END_DUR), "cy": 1000}


SCENES = [scene_hook, scene_language, scene_simple, scene_uses, scene_code, scene_power]
ACCENT = [PURPLE, (40, 90, 200), (20, 120, 70), ORANGE, (40, 90, 200), (200, 150, 0), PURPLE]
# transition INTO scene k+1 at boundary k
TRANS = ["zoom", "whip_l", "whip_u", "zoom", "flash", "whip_l"]
TR = 0.16   # half length of a transition (s)


# ------------------------------------------------------------------ compositor
def impacts(lines):
    """(time, strength) for shake + flash"""
    return [(kwa(lines[0], "Python"), 1.0), (kwa(lines[2], "beginners"), 0.5),
            (kwa(lines[5], "power"), 1.0), (lines[4]["start"] + code_schedule(lines[4])[3], 0.25)]


def stage_at(lines, total, t):
    """render the moving stage for absolute time t -> (stage, accent idx, scene idx)"""
    bounds = [ln["start"] for ln in lines] + [lines[-1]["start"] + lines[-1]["dur"]]
    k = len(lines)
    for i in range(len(lines)):
        if t < bounds[i + 1]:
            k = i
            break
    st = Image.new("RGBA", (W, H))
    lt = t - (bounds[k] if k < len(lines) else bounds[-1])
    if k < len(lines):
        cam = SCENES[k](st, lines[k], lt)
    else:
        cam = scene_end(st, lt)
    return st, cam, k, bounds


def camera(st, zoom, cy, dx=0.0, dy=0.0, rot=0.0):
    M = cv2.getRotationMatrix2D((W / 2, cy), rot, zoom)
    M[1, 2] += (H * 0.52 - cy) * 0.35 + dy
    M[0, 2] += dx
    a = np.asarray(st)
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def mblur(a, length, horizontal=True):
    length = int(length)
    if length < 3:
        return a
    k = np.ones((1, length), np.float32) / length
    if not horizontal:
        k = k.T
    return cv2.filter2D(a, -1, k)


def render_frame(args):
    i, lines, total = args
    t = i / FPS
    st, cam, k, bounds = stage_at(lines, total, t)
    zoom, cy = cam["zoom"], cam["cy"]
    dx = dy = rot = 0.0
    blur, horiz, flash = 0, True, 0.0
    # transitions around each boundary
    for b_i in range(1, len(bounds)):
        b = bounds[b_i]
        if abs(t - b) < TR:
            kind = TRANS[b_i - 1]
            u = (t - b) / TR        # -1..1
            e = (1 - abs(u))
            if kind.startswith("whip"):
                q = ease_io(u + 1) if u < 0 else -ease_io(1 - u)   # 0 -> 1 out, -1 -> 0 in
                if kind == "whip_l":
                    dx = -W * 0.6 * q
                else:
                    horiz = False
                    dy = -H * 0.5 * q
                blur = 140 * e
            elif kind == "zoom":
                zoom *= (1 + 1.6 * ease_io(u + 1)) if u < 0 else (1 - 0.3 * ease_io(1 - u))
                blur, horiz = 0, True
                flash = max(flash, 0.35 * e)
            elif kind == "flash":
                flash = max(flash, 0.9 * e)
                zoom *= 1 + 0.15 * e
    # impacts: shake + flash
    for ti, s in IMPACTS:
        a = t - ti
        if 0 <= a < 0.4:
            amp = 26 * s * (1 - a / 0.4)
            dx += amp * math.sin(a * 95)
            dy += amp * math.cos(a * 77)
            rot += 1.2 * s * math.sin(a * 60) * (1 - a / 0.4)
            flash = max(flash, 0.65 * s * max(0, 1 - a / 0.18))
    acc = ACCENT[min(k, len(ACCENT) - 1)]
    bg = background(t, acc)
    bgz = camera(bg, 1.0 + (zoom - 1) * 0.25, H / 2, dx * 0.3, dy * 0.3)
    sa = camera(st, zoom, cy, dx, dy, rot)
    if blur:
        sa = mblur(sa, blur, horiz)
    fr = Image.fromarray(bgz)
    fr.alpha_composite(Image.fromarray(sa))
    # captions + HUD (not affected by camera)
    if k < len(lines):
        draw_caption(fr, lines[k], t)
    pill = rrect(400, 64, 32, (0, 0, 0, 140), (255, 255, 255, 60), 2)
    pc = pill.copy()
    ImageDraw.Draw(pc).text((200, 33), "PYTHON BASICS • EP 01", font=font(CAP, 28), fill=YEL, anchor="mm")
    fr.alpha_composite(pc, (W // 2 - 200, 140))
    # grade: flash, vignette, grain
    a = np.asarray(fr.convert("RGB")).astype(np.float32)
    if flash > 0:
        a = a + (255 - a) * flash
    a = a * vignette()
    g = GRAIN[i % len(GRAIN)]
    a += cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    return np.clip(a, 0, 255).astype(np.uint8).tobytes()


# ------------------------------------------------------------------ audio
def music(total, drop, power):
    """Upbeat lo-fi tech bed, 112 bpm, Am-F-C-G.  Sparse intro, full drop on "Python!"."""
    bpm = 112
    beat = 60 / bpm
    n = int(total * SR)
    pads, bass, drums, arp = (np.zeros(n) for _ in range(4))
    chords = [(110.0, [220.0, 261.63, 329.63]), (87.31, [174.61, 220.0, 261.63]),
              (130.81, [261.63, 329.63, 392.0]), (98.0, [196.0, 246.94, 293.66])]
    k = fx.kick()
    cl = fx.clap()
    b = 0
    while b * beat < total:
        tb = b * beat
        bi, pos = divmod(b, 4)
        root, tones = chords[bi % 4]
        full = tb >= drop - 0.02 and not (power - beat * 1.0 <= tb < power - 0.02)
        if pos == 0:
            for f in tones:
                fx.place(pads, fx.synth_note(f, beat * 4.2, "saw", 0.6, 1500), tb, 0.10)
        if full:
            fx.place(drums, k, tb, 0.9)
            if pos in (1, 3):
                fx.place(drums, cl, tb, 0.45)
            for s in range(2):
                fx.place(bass, fx.synth_note(root, beat * 0.42, "saw", 6, 400), tb + s * beat / 2, 0.5)
        for s in range(4):
            if full or tb > drop - beat * 4:
                fx.place(drums, fx.hat(b * 4 + s), tb + s * beat / 4, 0.12 if s % 2 else 0.06)
            f = tones[[0, 1, 2, 1][s]] * 2
            fx.place(arp, fx.synth_note(f, beat / 4 * 1.3, "square", 18, 3000 if full else 1400),
                     tb + s * beat / 4, 0.07 if full else 0.05)
        b += 1
    tt = (np.arange(n) / SR) % beat
    pump = 1 - 0.4 * np.exp(-tt * 9)
    mix = (pads + arp) * pump + bass * pump + drums * 0.8
    fade = int(1.0 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / (np.max(np.abs(mix)) + 1e-9) * 0.9


def key_click(seed):
    nn = int(0.035 * SR)
    x = fx.filt(fx.noise(nn, seed), "bandpass", [1800, 7000]) * fx.env_exp(nn, 150)
    return x * (0.5 + 0.3 * np.random.default_rng(seed).random())


def mouse_click():
    nn = int(0.05 * SR)
    return fx.filt(fx.noise(nn, 99), "bandpass", [2500, 9000]) * fx.env_exp(nn, 260) * 0.9


def thud():
    nn = int(0.35 * SR)
    tt = np.arange(nn) / SR
    return np.sin(2 * np.pi * (60 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) * 0.9


def note_pop(f):
    nn = int(0.25 * SR)
    tt = np.arange(nn) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 14) * 0.5


def sfx_track(lines, total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    L = lines
    bounds = [ln["start"] for ln in L] + [L[-1]["start"] + L[-1]["dur"]]
    for i, b in enumerate(bounds[1:]):
        P(buf, fx.whoosh(0.34, i), b - 0.2, 0.6)
    # hook
    for j, w in enumerate(("Instagram", "Netflix", "AI")):
        P(buf, fx.pop(), kwa(L[0], w), 0.7)
        P(buf, note_pop([523.25, 659.25, 783.99][j]), kwa(L[0], w), 0.35)
    tc, tp = kwa(L[0], "common"), kwa(L[0], "Python")
    P(buf, fx.riser(max(0.3, tp - tc)), tc, 0.4)
    P(buf, fx.boom(), tp, 1.0)
    P(buf, fx.pop(), tp + 0.35, 0.4)
    # language
    P(buf, fx.pop(), kwa(L[1], "programming"), 0.6)
    ti = kwa(L[1], "instructions")
    for j in range(3):
        P(buf, fx.whoosh(0.22, 10 + j), ti + j * 0.28, 0.25)
    P(buf, fx.ding(), ti + 0.75, 0.35)
    # simple
    P(buf, fx.pop(), L[2]["start"] + 0.05, 0.4)
    P(buf, fx.pop(), kwa(L[2], "English"), 0.5)
    ts = kwa(L[2], "simple")
    P(buf, thud(), ts, 0.5)
    P(buf, fx.ding(), ts + 0.12, 0.35)
    P(buf, thud(), kwa(L[2], "beginners"), 0.9)
    P(buf, fx.boom()[: int(0.4 * SR)], kwa(L[2], "beginners"), 0.5)
    # uses
    for j, w in enumerate(("websites", "chatbots", "games", "boring")):
        tt = kwa(L[3], w) - (0.25 if w == "chatbots" else 0)
        P(buf, fx.pop(), tt, 0.6)
        P(buf, note_pop([523.25, 587.33, 659.25, 783.99][j]), tt, 0.4)
    # code
    starts, tend, tsel, trun = code_schedule(L[4])
    s0 = L[4]["start"]
    P(buf, fx.pop(), s0, 0.4)
    for k, ln in enumerate(CODE):
        for c in range(len(ln)):
            if ln[c] != " ":
                P(buf, key_click(k * 50 + c), s0 + starts[k] + c / CPS, 0.35)
    P(buf, fx.whoosh(0.25, 30), s0 + tsel, 0.25)
    P(buf, mouse_click(), s0 + trun, 0.9)
    for k in range(len(OUTPUT)):
        P(buf, note_pop(880 + k * 110), s0 + trun + 0.35 + k * 0.2, 0.3)
    P(buf, fx.ding(), s0 + trun + 0.35 + len(OUTPUT) * 0.2, 0.4)
    # power
    tpw = kwa(L[5], "power")
    P(buf, fx.pop(), kwa(L[5], "Python"), 0.5)
    P(buf, fx.riser(0.8), tpw - 0.8, 0.35)
    P(buf, fx.boom(), tpw, 1.0)
    # end card
    e0 = bounds[-1]
    P(buf, fx.pop(), e0 + 0.12, 0.5)
    P(buf, fx.pop(), e0 + 0.4, 0.4)
    P(buf, mouse_click(), e0 + 1.15, 0.9)
    P(buf, fx.ding(), e0 + 1.2, 0.5)
    return buf


def build_audio(lines, total, has_voice):
    drop = kwa(lines[0], "Python")
    power = kwa(lines[5], "power")
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total, drop, power))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(lines, total) * 0.8)
    out = os.path.join(WORK, "mix.wav")
    if has_voice:
        fc = ("[0:a]highpass=f=85,afftdn=nf=-28,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.2:g=3,"
              "acompressor=threshold=-20dB:ratio=3:attack=4:release=70:makeup=2,"
              "loudnorm=I=-16:TP=-2:LRA=7,aformat=sample_rates=48000:channel_layouts=stereo,asplit[vox][key];"
              "[1:a]loudnorm=I=-21:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
              "[mus][key]sidechaincompress=threshold=0.04:ratio=4:attack=10:release=250[musd];"
              "[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.75[sfx];"
              "[vox][musd][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1:LRA=9,aresample=48000[out]")
        ins = ["-i", os.path.join(WORK, "voice.wav")]
    else:
        fc = ("[0:a]loudnorm=I=-18:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[mus];"
              "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.9[sfx];"
              "[mus][sfx]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=9,aresample=48000[out]")
        ins = []
    fx.run(["ffmpeg", "-v", "error", "-y", *ins, "-i", os.path.join(WORK, "music.wav"),
            "-i", os.path.join(WORK, "sfx.wav"), "-filter_complex", fc, "-map", "[out]",
            "-t", f"{total:.3f}", out])
    return out


# ------------------------------------------------------------------ main
IMPACTS = []


def init_worker(imp):
    IMPACTS[:] = imp


def main():
    preview = "--preview" in sys.argv
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    lines, total, has_voice = build_timing()
    json.dump({"lines": lines, "total": total, "voice": has_voice},
              open(os.path.join(WORK, "timing.json"), "w"), indent=1)
    print(f"timeline {total:.2f}s  voice={'yes' if has_voice else 'no (record-along cut)'}")
    mix = build_audio(lines, total, has_voice)
    n = int(total * FPS)
    name = "python-ep01-SHORT.mp4" if has_voice else "python-ep01-SHORT-record-along.mp4"
    out = os.path.join(OUT_DIR, name if not preview else "preview.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", mix,
                            "-c:v", "libx264", "-preset", "veryfast" if preview else "slow",
                            "-crf", "28" if preview else "20", "-maxrate", "14M", "-bufsize", "28M", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out],
                           stdin=subprocess.PIPE)
    imp = impacts(lines)
    frames = range(0, n, 3 if preview else 1)
    with Pool(os.cpu_count(), initializer=init_worker, initargs=(imp,)) as pool:
        for j, fb in enumerate(pool.imap(render_frame, ((i, lines, total) for i in frames), chunksize=4)):
            reps = 3 if preview else 1
            for _ in range(reps):
                enc.stdin.write(fb)
            if j % 60 == 0:
                print(f"  frame {j * reps}/{n}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
