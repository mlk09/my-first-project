#!/usr/bin/env python3
"""Post for Part 2: grade, letterbox, transitions, trailer-style gold cards, captions, mux.

Reuses Part 1's grade, letterbox and transition code (edit3/build_final.py) and
adds the glitched episode card, gold text cards, dialogue + narration captions,
the "PART 3 COMING SOON" card and the subscribe card.
Run: python3 part2/post_p2.py [--still 12 47 ...]
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit3"))
sys.path.insert(0, HERE)
_argv, sys.argv = sys.argv, [sys.argv[0]]
import build_final as BF  # noqa: E402  (grade, Frames, whip_blur, trunk_wipe, smooth, window, over)
sys.argv = _argv
from timeline_p2 import CARDS, DURATION, FPS, NARRATION, NFRAMES, TRANSITIONS  # noqa: E402

W, H, PW, PH, TOP = BF.W, BF.H, BF.PW, BF.PH, BF.TOP
GOLD_FONT = os.path.join(HERE, "assets", "LuckiestGuy.ttf")
HANDLE = "@BoltsSpookyTales"
SYNC = json.load(open(os.path.join(HERE, "work", "sync.json")))
WORK = os.path.join(HERE, "work")
smooth, window = BF.smooth, BF.window
GOLD, GOLD_DARK = (255, 196, 64), (120, 60, 0)


def gold_text(text, size, w=W, h=None, sub=None):
    h = h or int(size * 1.6)
    f = ImageFont.truetype(GOLD_FONT, size)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), text, font=f)
    x, y = (w - (bb[2] - bb[0])) // 2 - bb[0], (h - (bb[3] - bb[1])) // 2 - bb[1]
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, y), text, font=f, fill=(255, 140, 0, 160))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(size // 6)))
    d.text((x, y + size // 18), text, font=f, fill=GOLD_DARK + (255,))  # chunky drop shadow
    d.text((x, y), text, font=f, fill=GOLD + (255,), stroke_width=max(2, size // 30), stroke_fill=(70, 30, 0, 255))
    return np.asarray(im).astype(np.float32) / 255


CARD_IMG = {txt: gold_text(txt, 150) for _, _, txt in CARDS}
EP_TOP = gold_text("BOLT'S SPOOKY TALES", 120)
EP_SUB = gold_text("PART 2", 90)
P3_TOP = gold_text("BOLT'S SPOOKY TALES", 130)
P3_SUB = gold_text("PART 3 - COMING SOON", 70)


# ---------------------------------------------------------------- colourful title
CANDY = [(255, 80, 170), (255, 215, 40), (80, 240, 170), (80, 190, 255), (255, 140, 40), (190, 110, 255)]
STROKE = (40, 10, 60)


def letter_img(ch, size, col):
    f = ImageFont.truetype(GOLD_FONT, size)
    pad = size // 3
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = d0.textbbox((0, 0), ch, font=f, stroke_width=size // 12)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x, y = pad - bb[0], pad - bb[1]
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, y), ch, font=f, fill=col + (230,), stroke_width=size // 12, stroke_fill=col + (230,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(size // 7)))
    d = ImageDraw.Draw(im)
    d.text((x, y + size // 16), ch, font=f, fill=STROKE + (255,), stroke_width=size // 12, stroke_fill=STROKE + (255,))
    d.text((x, y), ch, font=f, fill=col + (255,), stroke_width=size // 12, stroke_fill=STROKE + (255,))
    hl = tuple(min(255, c + 90) for c in col)  # candy-shine highlight on the upper half
    shine = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shine).text((x, y), ch, font=f, fill=hl + (255,))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((0, 0, w, y + (bb[3] - bb[1]) * 0.42), fill=150)
    im.paste(shine, (0, 0), Image.composite(shine.split()[3], Image.new("L", (w, h), 0), mask))
    return im


TITLE_WORDS = "MIDNIGHT CANDY"
TITLE_LETTERS = []
_TF = ImageFont.truetype(GOLD_FONT, 165)
_x = 0
for _i, _ch in enumerate(TITLE_WORDS):
    if _ch == " ":
        _x += 55
        continue
    _im = letter_img(_ch, 165, CANDY[len(TITLE_LETTERS) % len(CANDY)])
    _adv = _TF.getlength(_ch) + 14
    TITLE_LETTERS.append([_im, int(_x + _adv / 2 - _im.width / 2)])
    _x += _adv
TITLE_W = int(_x)
TOP_LINE = gold_text("THE MYSTERY OF THE", 82)
PART_PILL = gold_text("PART 2", 64)


def draw_title(canvas, t):
    if not 9.15 <= t < 15.0:
        return
    out = smooth((15.0 - t) / 0.35)
    BF.over(canvas, TOP_LINE, 0, 285 + int(20 * (1 - smooth((t - 9.2) / 0.4))), smooth((t - 9.2) / 0.4) * out)
    pil = Image.fromarray((canvas.clip(0, 1) * 255).astype(np.uint8)).convert("RGBA")
    x0 = (W - TITLE_W) // 2
    for k, (im, x) in enumerate(TITLE_LETTERS):
        u = (t - 9.6 - k * 0.08) / 0.35
        if u <= 0:
            continue
        pop = 1 + 1.70158 * 1.4 * (min(u, 1) - 1) ** 3 + 1.70158 * (min(u, 1) - 1) ** 2 if u < 1 else 1.0
        s = max(0.05, pop) * (1 + 0.03 * np.sin(t * 4 + k))
        bob = int(10 * np.sin(t * 3 + k * 0.7))
        li = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
        if out < 1:
            li.putalpha(li.split()[3].point(lambda v: int(v * out)))
        cx, cy = x0 + x + im.width // 2, 520 + bob
        pil.alpha_composite(li, (cx - li.width // 2, cy - li.height // 2))
    canvas[:] = np.asarray(pil.convert("RGB")).astype(np.float32) / 255
    BF.over(canvas, PART_PILL, 0, 700, smooth((t - 10.9) / 0.4) * out)


# ---------------------------------------------------------------- sparkles
def star_sprite(n=64):
    yy, xx = np.mgrid[-n:n, -n:n].astype(np.float32) / n
    r = np.hypot(xx, yy)
    core = np.exp(-r * r * 30)
    rays = np.exp(-np.abs(xx) * 22) * np.exp(-np.abs(yy) * 2.5) + np.exp(-np.abs(yy) * 22) * np.exp(-np.abs(xx) * 2.5)
    return np.clip(core + 0.8 * rays, 0, 1)


STAR = star_sprite()
SPARKLE_WINDOWS = [(4.4, 6.6), (9.2, 15.0), (29.2, 33.0), (81.0, 86.0), (108.2, 110.5), (115.0, 127.0),
                   (132.0, 155.0), (170.0, 175.0)]
_rs = np.random.default_rng(21)
SPARKS = [(_rs.uniform(0, 1), _rs.uniform(0.05, 0.95), _rs.uniform(0, 30), _rs.uniform(0.25, 0.8), _rs.uniform(0, 1))
          for _ in range(70)]


def sparkles(canvas, t):
    amt = max(window(t, a, b, 0.4) for a, b in SPARKLE_WINDOWS)
    if amt <= 0:
        return
    import colorsys
    for x, y, ph, size, hue in SPARKS:
        tw = max(0.0, np.sin(t * 4.0 + ph)) ** 3
        if tw < 0.05:
            continue
        sz = int(20 + 70 * size * tw)
        sp = np.asarray(Image.fromarray((STAR * 255).astype(np.uint8)).resize((2 * sz, 2 * sz), Image.BILINEAR)
                        ).astype(np.float32)[..., None] / 255
        col = np.array(colorsys.hsv_to_rgb((hue + t * 0.05) % 1, 0.55, 1.0), np.float32)
        px = int(x * W + 40 * np.sin(t * 0.7 + ph))
        py = int(TOP + y * PH - (t * 25 + ph * 40) % 120)
        x0, y0, x1, y1 = px - sz, py - sz, px + sz, py + sz
        if x0 < 0 or y0 < TOP or x1 > W or y1 > TOP + PH:
            continue
        canvas[y0:y1, x0:x1] = 1 - (1 - canvas[y0:y1, x0:x1]) * (1 - sp * col * amt * tw * 0.9)


def gradient_bg(c1, c2):
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    r = np.clip(np.hypot((xx - PW / 2) / (PW * 0.6), (yy - PH / 2) / (PH * 0.75)), 0, 1)[..., None]
    return (np.array(c1, np.float32) * (1 - r) + np.array(c2, np.float32) * r)


CARD_BG = {"WHO TOOK": gradient_bg((0.45, 0.08, 0.5), (0.05, 0.02, 0.12)),
           "THE CANDY?": gradient_bg((0.05, 0.4, 0.45), (0.02, 0.04, 0.1)),
           "TOGETHER": gradient_bg((0.65, 0.25, 0.05), (0.15, 0.03, 0.12))}
EP_BG = gradient_bg((0.35, 0.1, 0.45), (0.03, 0.02, 0.08))


# ---------------------------------------------------------------- captions
def cap_image(text, dialogue):
    font = ImageFont.truetype(BF.FONT_ROUND, 44)
    col = (255, 207, 84) if dialogue else (255, 255, 255)
    tmp = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    if d.textlength(text, font=font) > W - 240:  # long story lines: two rows
        words = text.split()
        cut = min(range(1, len(words)), key=lambda k: abs(d.textlength(" ".join(words[:k]), font=font)
                                                            - d.textlength(" ".join(words[k:]), font=font)))
        font = ImageFont.truetype(BF.FONT_ROUND, 40)
        rows = [" ".join(words[:cut]), " ".join(words[cut:])]
    else:
        rows = [text]
    lh = font.size + 10
    for i, row in enumerate(rows):
        bb = d.textbbox((0, 0), row, font=font)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        y = (140 - lh * len(rows)) // 2 + i * lh + (lh - (bb[3] - bb[1])) // 2 - bb[1]
        d.text((x, y), row, font=font, fill=col + (255,), stroke_width=2, stroke_fill=(10, 8, 14, 255))
    return np.asarray(tmp).astype(np.float32) / 255


NAMES = {"bolt": "Bolt", "boo": "Boo", "granny": "Granny Gloom", "shadow": "???"}
DIALOG_STARTS = sorted(c["t0"] - 0.1 for c in SYNC["captions"]) + [178.0]
CAPS = []
for n in SYNC.get("narration", []):  # spoken story-poem lines, white
    nxt = min(s for s in DIALOG_STARTS + [m["t0"] for m in SYNC["narration"]] if s > n["t0"] + 0.01)
    CAPS.append((n["t0"] - 0.05, min(n["t1"] + 0.5, nxt - 0.12), cap_image(n["text"], False)))
if not CAPS:
    CAPS = [(t0, t1, cap_image(txt, False)) for t0, t1, txt in NARRATION]
for c in SYNC["captions"]:
    CAPS.append((c["t0"] - 0.1, max(c["t1"] + 0.6, c["t0"] + 1.4),
                 cap_image(f'{NAMES[c["who"]]}: "{c["text"]}"', True)))
CAPS.append((178.0, 180.0, cap_image("Subscribe for Part 3!   " + HANDLE, False)))


def handle_img():
    font = ImageFont.truetype(BF.FONT_ROUND, 26)
    im = Image.new("RGBA", (420, 60), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 14), HANDLE, font=font, fill=(255, 255, 255, 110))
    return np.asarray(im).astype(np.float32) / 255


HANDLE_IMG = handle_img()


def glitchy(img, t, f):
    """Subtle RGB-split + slice glitch for the episode card."""
    r = np.random.default_rng(f)
    amt = 10 if (t < 0.6 or 3.3 < t < 3.9 or r.random() < 0.08) else 2
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], amt, 1)
    out[..., 2] = np.roll(img[..., 2], -amt, 1)
    if amt > 2:
        for _ in range(4):
            a = r.integers(0, img.shape[0] - 30)
            n = r.integers(4, 26)
            out[a:a + n] = np.roll(out[a:a + n], r.integers(-40, 40), 1)
    out[::3] *= 0.92
    return out


def picture(fr, f):
    t = f / FPS
    if t < 4.0:
        return EP_BG * BF.VIGNETTE
    for c0, c1, txt in CARDS:  # colourful gradient behind each trailer card
        if c0 - 0.15 <= t < c1 + 0.1:
            return CARD_BG[txt] * BF.VIGNETTE
    img = fr.get(f).copy()
    for c, kind in TRANSITIONS.items():
        d = t - c
        if kind == "whip" and abs(d) < 0.25:
            img = BF.whip_blur(img, 1 - abs(d) / 0.25, 1 if d < 0 else -1)
        elif kind == "dip" and abs(d) < 0.4:
            img *= smooth(abs(d) / 0.4)
        elif kind == "trunk" and abs(d) < 0.4:
            img = BF.trunk_wipe(img, d)
    img = BF.grade(img)
    lum = (img @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    img = lum + (img - lum) * 1.2  # extra colour pop
    fl = window(t, 57.0, 57.3, 0.03) * 0.85 + window(t, 57.45, 57.55, 0.03) * 0.5
    for c, kind in TRANSITIONS.items():
        if kind == "flash" and 0 <= t - c < 0.35:
            fl = max(fl, 1 - (t - c) / 0.35)
    if fl > 0:
        img = img + (1 - img) * fl
    return img


def compose(fr, f):
    t = f / FPS
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[TOP:TOP + PH] = BF.add_grain(picture(fr, f), f)
    canvas[TOP:TOP + PH] *= smooth(t / 0.5) * (1 - smooth((t - 179.0) / 1.0))
    if t < 4.0:  # glitched episode card
        a = smooth((t - 0.2) / 0.4) * (1 - smooth((t - 3.6) / 0.35))
        BF.over(canvas, EP_TOP, 0, 400, a)
        BF.over(canvas, EP_SUB, 0, 560, a * smooth((t - 0.8) / 0.4))
        canvas[TOP:TOP + PH] = glitchy(canvas[TOP:TOP + PH], t, f)
    for c0, c1, txt in CARDS:  # trailer-style gold cards: punch in, hold, out
        if c0 <= t < c1:
            u = (t - c0) / (c1 - c0)
            a = smooth(u / 0.15) * (1 - smooth((u - 0.85) / 0.15))
            img = CARD_IMG[txt]
            s = 1.0 + 0.06 * u
            pil = Image.fromarray((img * 255).astype(np.uint8))
            pil = pil.resize((int(pil.width * s), int(pil.height * s)), Image.BICUBIC)
            arr = np.asarray(pil).astype(np.float32) / 255
            x0 = (W - arr.shape[1]) // 2
            if x0 < 0:
                arr = arr[:, -x0:-x0 + W]
                x0 = 0
            BF.over(canvas, arr, x0, (H - arr.shape[0]) // 2, a)
    draw_title(canvas, t)
    sparkles(canvas, t)
    if 170.0 <= t < 175.0:  # PART 3 COMING SOON
        a = smooth((t - 170.3) / 0.6) * (1 - smooth((t - 174.6) / 0.35))
        BF.over(canvas, P3_TOP, 0, 380, a)
        BF.over(canvas, P3_SUB, 0, 560, a * smooth((t - 171.2) / 0.5))
    for t0, t1, im in CAPS:
        if t0 - 0.05 <= t <= t1 + 0.05:
            a = window(t, t0, t1, 0.2)
            BF.over(canvas, im, 0, H - 140 + int(8 * (1 - smooth((t - t0) / 0.25))), a)
    if 4.0 < t < 175.0:
        BF.over(canvas, HANDLE_IMG, W - 430, 40, window(t, 4.0, 175.0, 1.0))
    return (canvas.clip(0, 1) * 255).astype(np.uint8)


def main():
    fr = BF.Frames(os.path.join(WORK, "frames"))
    if len(sys.argv) > 2 and sys.argv[1] == "--still":
        for x in sys.argv[2:]:
            Image.fromarray(compose(fr, int(float(x) * FPS))).save(os.path.join(WORK, f"post_{x}.png"))
        return
    out = os.path.join(HERE, "output", "Bolts-Spooky-Tales-Part-2-Midnight-Candy.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", os.path.join(WORK, "mix.wav"), "-c:v", "libx264", "-preset", "slow", "-crf", "19",
           "-maxrate", "7M", "-bufsize", "14M", "-tune", "animation", "-pix_fmt", "yuv420p",
           "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(NFRAMES):
        p.stdin.write(compose(fr, f).tobytes())
        if f % 480 == 0:
            print(f"{f / FPS:6.1f}s", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
