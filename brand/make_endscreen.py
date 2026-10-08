#!/usr/bin/env python3
"""Python ki Pathshala - end screen ("Agar video achha laga... Like, Share, Subscribe").

Writes to output/:
  endscreen_short_1080x1920.png   still end card for Shorts (9:16)
  endscreen_short_anim.mp4        5 s animated version with SFX - append to the end of any Short
  endscreen_16x9_1920x1080.jpg    for long videos; leaves room for YouTube end-screen elements

Usage:  python3 brand/make_endscreen.py ["EP 02: VARIABLES"]
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_brand as mb  # noqa: E402

sys.path.insert(0, os.path.join(mb.HERE, "..", "edit"))
import build_edit as fx  # noqa: E402  (sfx synth helpers)

NEXT = sys.argv[1] if len(sys.argv) > 1 else "EP 02: VARIABLES"
FPS, SR, DUR = 30, 48000, 5.0
BLUE, GREEN, RED, GREY = (40, 130, 255), (30, 180, 90), (235, 30, 40), (95, 99, 108)


# ------------------------------------------------------------------ icons (drawn at 3x, downsampled)
def _canvas(s):
    return Image.new("RGBA", (s * 3, s * 3)), 3 * s


def icon_like(s, filled):
    im, S = _canvas(s)
    d = ImageDraw.Draw(im)
    w = int(S * .075)
    col = (255, 255, 255)
    d.rounded_rectangle((S * .08, S * .45, S * .26, S * .92), S * .04, fill=col)            # cuff
    palm = [(S * .33, S * .47), (S * .52, S * .12), (S * .6, S * .1), (S * .66, S * .2),
            (S * .6, S * .4), (S * .86, S * .4), (S * .93, S * .5), (S * .86, S * .9), (S * .33, S * .9)]
    if filled:
        d.polygon(palm, fill=col)
    else:
        d.line(palm + [palm[0]], fill=col, width=w, joint="curve")
    return im.resize((s, s), Image.LANCZOS)


def icon_share(s):
    im, S = _canvas(s)
    d = ImageDraw.Draw(im)
    col = (255, 255, 255)
    pts = [(S * .74, S * .2), (S * .26, S * .5), (S * .74, S * .8)]
    d.line([pts[0], pts[1], pts[2]], fill=col, width=int(S * .08))
    for x, y in pts:
        r = S * .14
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    return im.resize((s, s), Image.LANCZOS)


def icon_bell(s, ang=0):
    im, S = _canvas(s)
    d = ImageDraw.Draw(im)
    col = (255, 255, 255)
    d.ellipse((S * .44, S * .06, S * .56, S * .18), fill=col)
    d.chord((S * .22, S * .14, S * .78, S * .7), 180, 360, fill=col)
    d.polygon([(S * .22, S * .42), (S * .78, S * .42), (S * .88, S * .76), (S * .12, S * .76)], fill=col)
    d.ellipse((S * .4, S * .74, S * .6, S * .92), fill=col)
    im = im.rotate(ang, Image.BICUBIC, center=(S / 2, S * .12))
    return im.resize((s, s), Image.LANCZOS)


def pointer(s):
    im, S = _canvas(s)
    d = ImageDraw.Draw(im)
    pts = [(0.1, 0.02), (0.1, 0.8), (0.3, 0.62), (0.45, 0.95), (0.6, 0.88), (0.45, 0.56), (0.72, 0.56)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=(255, 255, 255), outline=(0, 0, 0))
    d.line([(x * S, y * S) for x, y in pts + [pts[0]]], fill=(0, 0, 0), width=int(S * .03))
    return im.resize((s, s), Image.LANCZOS)


# ------------------------------------------------------------------ pieces
def button(label, col, icon, w, h, f):
    im = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", im.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 30, w + 20, h + 30), h // 2, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 20, h + 20), h // 2, fill=col, outline=(255, 255, 255), width=5)
    hi = Image.new("RGBA", im.size)
    ImageDraw.Draw(hi).rounded_rectangle((32, 26, w + 8, 20 + h * 0.45), h // 2, fill=(255, 255, 255, 45))
    im.alpha_composite(hi)
    isz = int(h * 0.56)
    im.alpha_composite(icon, (20 + int(h * 0.42), 20 + (h - isz) // 2))
    d.text((20 + h * 0.42 + isz + (w - h * 0.42 - isz) / 2 - 10, 20 + h / 2 + 3), label, font=f,
           fill=(255, 255, 255), anchor="mm")
    return im


def next_card(w, h, txt):
    im = Image.new("RGBA", (w + 40, h + 40))
    sh = Image.new("RGBA", im.size)
    ImageDraw.Draw(sh).rounded_rectangle((20, 32, w + 20, h + 32), 30, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 20, h + 20), 30, fill=(10, 34, 20), outline=mb.YEL, width=6)
    d.text((54, 72), "NEXT VIDEO", font=mb.font(mb.BALOO, int(h * .2), "ExtraBold"), fill=mb.YEL, anchor="lm")
    d.text((54, 72 + h * .36), txt, font=mb.font(mb.BALOO, int(h * .26), "ExtraBold"), fill=mb.WHITE, anchor="lm")
    ax = w - 40
    d.polygon([(ax - 50, 20 + h * .38), (ax, 20 + h * .5), (ax - 50, 20 + h * .62)], fill=mb.YEL)
    return im


def pop(age, dur=0.35):
    if age <= 0:
        return 0.0
    t = min(1.0, age / dur)
    s = 1.9
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def place(base, im, cx, cy, scale=1.0, rot=0):
    if scale <= 0.02:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    mb.paste_c(base, im, cx, cy, rot)


# ------------------------------------------------------------------ vertical (Shorts) end screen
W, H = 1080, 1920
BTN = [("LIKE", BLUE, 720), ("SHARE", GREEN, 920), ("SUBSCRIBE", RED, 1120)]
T_IN = [0.45, 0.65, 0.85]
T_LIKE, T_SUB, T_NEXT = 1.7, 2.6, 3.2


def static_layer():
    im = mb.board(W, H, seed=11)
    mb.doodles(im, [(">>>", 90, 120, 70, 0, "code"), ('print("Bye!")', 560, 1540, 46, -4, "code"),
                    ("{ }", 900, 300, 70, 8, "code"), ("for i in range(3):", 70, 1720, 42, 3, "code")])
    mb.glow(im, 540, 1000, 520, mb.YEL, 60)
    return im


_STATIC = {}


def frame(t, still=False):
    """still=True: the call-to-action state (buttons not yet clicked, next card shown, no cursor)"""
    if "v" not in _STATIC:
        _STATIC["v"] = static_layer()
        _STATIC["t1"] = mb.outlined("Python ki", mb.font(mb.BALOO, 92, "ExtraBold"), mb.YEL, 6, mb.DARK, 5, (120, 70, 0))
        _STATIC["t2"] = mb.outlined("PATHSHALA", mb.font(mb.BALOO, 120, "ExtraBold"), mb.WHITE, 7, mb.DARK, 7,
                                    (20, 70, 40), tex=True)
        _STATIC["q"] = mb.outlined("Agar video achha laga…", mb.font(mb.CHALK, 74), mb.WHITE, 5, mb.DARK, 0)
        _STATIC["m"] = mb.mascot(480)
    im = _STATIC["v"].copy()
    place(im, _STATIC["t1"], 470, 230, pop(t - 0.0), 2)
    place(im, _STATIC["t2"], 540, 335, pop(t - 0.1), 2)
    place(im, _STATIC["q"], 540, 520, pop(t - 0.25))
    f = mb.font(mb.BALOO, 70, "ExtraBold")
    liked, subbed = (False, False) if still else (t >= T_LIKE, t >= T_SUB)
    for k, ((label, col, y), t0) in enumerate(zip(BTN, T_IN)):
        if label == "LIKE":
            ic = icon_like(84, liked)
            lab = "LIKED!" if liked else "LIKE"
        elif label == "SHARE":
            ic, lab = icon_share(84), label
        else:
            ang = 22 * math.sin((t - T_SUB) * 24) * math.exp(-(t - T_SUB) * 3) if subbed else 0
            ic = icon_bell(84, ang)
            lab, col = ("SUBSCRIBED", GREY) if subbed else (label, col)
        b = button(lab, col, ic, 760, 150, f)
        press = 0.9 if (label == "LIKE" and T_LIKE <= t < T_LIKE + .1) or \
                       (label == "SUBSCRIBE" and T_SUB <= t < T_SUB + .1) else 1
        wob = math.sin(t * 3 + k) * 1.2 if t > 1.2 else 0
        place(im, b, 540, y, pop(t - t0) * press, wob)
    if liked and t < T_LIKE + 0.8 and not still:   # +1 floating
        a = (t - T_LIKE) / 0.8
        p = mb.outlined("+1", mb.font(mb.BALOO, 80, "ExtraBold"), mb.YEL, 5, mb.DARK)
        place(im, p, 880, 650 - 90 * a, 1 - 0.3 * a)
    if T_NEXT - 1.2 < t:   # next video card slides up
        q = min(1, (t - T_NEXT) / 0.35) if t >= T_NEXT else 0
        if q > 0:
            nc = next_card(620, 210, NEXT)
            ease = 1 - (1 - q) ** 3
            place(im, nc, 380, 1460 + 300 * (1 - ease), 1)
    place(im, _STATIC["m"], 860, 1560, pop(t - 0.5, 0.45))
    if t > 0.9:
        b = mb.bubble("Kal milte hain!", mb.font(mb.BALOO, 44, "ExtraBold"), 22)
        place(im, b, 850, 1290, pop(t - 1.0))
    # cursor: -> like -> subscribe
    path = [(0.9, (980, 1700)), (T_LIKE, (560, 750)), (T_LIKE + 0.35, (560, 750)), (T_SUB, (600, 1150)),
            (T_SUB + 0.6, (600, 1150)), (T_SUB + 1.2, (1150, 1500))]
    if path[0][0] < t < path[-1][0] and not still:
        for (ta, pa), (tb, pb) in zip(path, path[1:]):
            if ta <= t < tb:
                u = (t - ta) / (tb - ta)
                u = u * u * (3 - 2 * u)
                x, y = pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u
                cl = 0.85 if any(0 <= t - c < 0.12 for c in (T_LIKE, T_SUB)) else 1
                im.alpha_composite(pointer(int(110 * cl)), (int(x), int(y)))
                break
    mb.wood_frame(im, 26)
    return im


def sfx():
    n = int(DUR * SR)
    buf = np.zeros(n)
    P = fx.place
    P(buf, fx.whoosh(0.35, 1), 0.0, 0.6)
    P(buf, fx.pop(), 0.05, 0.5)
    P(buf, fx.pop(), 0.25, 0.5)
    for k, t0 in enumerate(T_IN):
        P(buf, fx.pop(), t0, 0.7)
        nn = int(0.25 * SR)
        tt = np.arange(nn) / SR
        f0 = [523.25, 659.25, 783.99][k]
        P(buf, np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 14) * 0.4, t0, 1)
    click = fx.filt(fx.noise(int(0.05 * SR), 99), "bandpass", [2500, 9000]) * fx.env_exp(int(0.05 * SR), 260)
    for tc in (T_LIKE, T_SUB):
        P(buf, click, tc, 0.9)
    P(buf, fx.ding(), T_LIKE + 0.05, 0.5)
    nn = int(1.2 * SR)   # bell ring
    tt = np.arange(nn) / SR
    ring = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, d in ((1760, 4), (2637, 6), (3520, 8)))
    P(buf, ring * 0.25 * (1 + 0.3 * np.sin(2 * np.pi * 12 * tt)), T_SUB + 0.05, 1)
    P(buf, fx.whoosh(0.3, 7), T_NEXT - 0.1, 0.5)
    P(buf, fx.pop(), T_NEXT + 0.2, 0.5)
    return buf / (np.max(np.abs(buf)) + 1e-9) * 0.8


def render_anim(path):
    wav = os.path.join(mb.OUT, "_endscreen.wav")
    fx.write_wav(wav, sfx())
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", path],
                           stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        enc.stdin.write(np.asarray(frame(i / FPS).convert("RGB")).tobytes())
    enc.stdin.close()
    enc.wait()
    os.remove(wav)


# ------------------------------------------------------------------ 16:9 end screen (long videos)
def wide():
    W2, H2 = 1920, 1080
    im = mb.board(W2, H2, seed=12)
    mb.doodles(im, [(">>>", 80, 80, 64, 0, "code"), ('print("Bye!")', 1450, 960, 44, -3, "code"),
                    ("{ }", 1760, 90, 64, 8, "code")])
    mb.glow(im, 960, 560, 600, mb.YEL, 50)
    mb.paste_c(im, mb.outlined("Agar video achha laga…", mb.font(mb.CHALK, 78), mb.WHITE, 5, mb.DARK), 960, 150)
    f = mb.font(mb.BALOO, 54, "ExtraBold")
    x = 360
    for lab, col, ic in (("LIKE", BLUE, icon_like(64, True)), ("SHARE", GREEN, icon_share(64)),
                         ("SUBSCRIBE", RED, icon_bell(64))):
        b = button(lab, col, ic, 560 if lab == "SUBSCRIBE" else 400, 112, f)
        mb.paste_c(im, b, x, 300)
        x += b.width / 2 + (330 if lab == "LIKE" else 400)
    # placeholders where YouTube end-screen elements go
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((180, 470, 180 + 820, 470 + 461), 26, outline=mb.YEL, width=6)
    d.text((590, 700), "NEXT VIDEO", font=mb.font(mb.BALOO, 70, "ExtraBold"), fill=mb.YEL, anchor="mm")
    d.text((590, 780), "(yahan video lagao)", font=mb.font(mb.BALOO, 34, "Bold"), fill=(255, 255, 255, 160), anchor="mm")
    d.ellipse((1140, 520, 1440, 820), outline=mb.WHITE, width=6)
    d.text((1290, 870), "SUBSCRIBE", font=mb.font(mb.BALOO, 40, "ExtraBold"), fill=mb.WHITE, anchor="mm")
    mb.paste_c(im, mb.mascot(520), 1660, 760)
    mb.paste_c(im, mb.bubble("Kal milte hain!", mb.font(mb.BALOO, 38, "ExtraBold"), 20), 1640, 445)
    mb.wood_frame(im, 26)
    return im


def main():
    os.makedirs(mb.OUT, exist_ok=True)
    frame(DUR, still=True).convert("RGB").save(os.path.join(mb.OUT, "endscreen_short_1080x1920.png"))
    wide().convert("RGB").save(os.path.join(mb.OUT, "endscreen_16x9_1920x1080.jpg"), quality=93)
    render_anim(os.path.join(mb.OUT, "endscreen_short_anim.mp4"))
    print("done")


if __name__ == "__main__":
    main()
