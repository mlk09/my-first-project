#!/usr/bin/env python3
"""13 s LOOP 'ESP32 + OLED Car Racing' short in the new retention format (no menu, no countdown, no outro,
no blur transitions): gameplay + hook text from frame 0 ('Ye MOBILE nahi hai!'), the colour GAME CAM panel
always on screen, hard cuts with a small zoom punch, CLOSE CALL / +50 coin / NITRO / FINISH beats, NEW BEST
card, and a last shot that ends on the first frame's camera pose so the Short replays seamlessly. All text
stays inside the Shorts safe zone (top area, never under the title / buttons). Animated wooden-workbench
background behind the transparent 3D console render. Chiptune + engine / coin / whoosh / nitro SFX.
Usage: python3 edit30/build_short.py [audio] [video]
"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402
from timeline import (FPS, N, SHOTS, HIGH_OLD, NITRO_AT, FINISH, DODGE, COINS, PX, CAR_W, COIN_COL,  # noqa: E402
                      game, final_score, ease)
import gamegfx  # noqa: E402
from workbench import workbench  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-car-racing-game-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
OUTRO = 0
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
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"), cv2.IMREAD_UNCHANGED)
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"), cv2.IMREAD_UNCHANGED)
    return _grade(with_tunnel(im, f))


def with_tunnel(im, f):
    """Transparent console render (BGRA, shadow-caught) over the animated wooden workbench backdrop."""
    if im.ndim == 2 or im.shape[2] < 4:
        return im
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    a = im[..., 3:4].astype(np.float32) / 255
    bg = cv2.cvtColor(workbench(f), cv2.COLOR_RGB2BGR).astype(np.float32)
    return (im[..., :3].astype(np.float32) * a + bg * (1 - a)).clip(0, 255).astype(np.uint8)


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





def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🏎️", 46), (W - 388, 46))


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
RAINBOW = [(255, 40, 40), (255, 120, 20), (255, 210, 20), (80, 240, 60), (30, 230, 190), (40, 120, 255),
           (130, 60, 255), (255, 60, 170)]             # same palette as the rotary-encoder LED Flow short
CRASH = FINISH
BEST_AT = FINISH + 12
SCORE_AT = [fp for fp, _ in COINS if fp < N]
CLOSE_AT = [fp for fp, _ in DODGE if fp < N]
PINK, ORANGE = (255, 90, 200), (255, 150, 30)


def sq(freq, dur, duty=0.5, vol=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.where((tt * freq) % 1 < duty, 1.0, -1.0)
    return x * np.minimum(1, tt / 0.002) * np.minimum(1, (dur - tt) / 0.01) * vol








def point_snd():
    """Classic coin: two square notes."""
    return np.concatenate([sq(988, 0.06, 0.25), sq(1319, 0.18, 0.25)]) * np.exp(-np.arange(int(0.24 * SR)) / SR * 6)


def hit_snd():
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    return (fx.filt(fx.noise(n, 5), "lowpass", 1200) * np.exp(-tt * 18) + np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 12)) * 0.9





def fanfare8():
    out = np.zeros(int(1.4 * SR))
    for i, (fr, d) in enumerate(((784, 0.1), (988, 0.1), (1175, 0.1), (1568, 0.45), (1319, 0.12), (1568, 0.6))):
        fx.place(out, sq(fr, d, 0.25, 0.45), [0, 0.1, 0.2, 0.3, 0.75, 0.87][i], 1.0)
    return out


def music(total):
    """140 BPM 8-bit chiptune (square lead + pulse arps + tri bass + noise drums); filtered in the menu."""
    bpm, n = 140, int(total * SR)
    beat = 60 / bpm
    lead, arp, bass, drums = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    prog = [(261.6, [523.3, 659.3, 784.0]), (220.0, [440.0, 523.3, 659.3]), (174.6, [349.2, 440.0, 523.3]),
            (196.0, [392.0, 493.9, 587.3])]
    melody = [784, 0, 659, 784, 880, 784, 659, 523, 587, 659, 587, 523, 494, 523, 587, 0]
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        root, ch = prog[bar % 4]
        for s in range(4):                                         # 16th-note arps
            fx.place(arp, sq(ch[(pos * 4 + s) % 3], beat / 4 * 0.9, 0.125, 0.12), t0 + s * beat / 4, 1.0)
        for s in range(2):
            m = melody[(b * 2 + s) % len(melody)]
            if m:
                fx.place(lead, sq(m, beat / 2 * 0.85, 0.5, 0.16), t0 + s * beat / 2, 1.0)
        fx.place(bass, fx.synth_note(root / 2, beat * 0.9, "tri", 2, 900) * 0.5, t0, 1.0)
        nz = int(0.05 * SR)
        k = fx.filt(fx.noise(nz, b), "lowpass", 300) * np.exp(-np.arange(nz) / SR * 60)
        if pos in (0, 2):
            fx.place(drums, k * 1.4, t0, 1.0)
        if pos in (1, 3):
            fx.place(drums, fx.filt(fx.noise(nz, b + 99), "bandpass", [1500, 6000]) * np.exp(-np.arange(nz) / SR * 40), t0, 0.5)
        fx.place(drums, fx.filt(fx.noise(nz // 3, b + 7), "highpass", 7000), t0 + beat / 2, 0.15)
        b += 1
    mix = lead + arp + bass + drums
    for a0, a1 in ((NITRO_AT - 10, NITRO_AT), (CRASH, CRASH + 10)):  # filtered dips before NITRO / at FINISH
        i0, i1 = int(t(a0) * SR), int(t(a1) * SR)
        mix[i0:i1] = fx.filt(mix[i0:i1], "lowpass", 1000)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.45)                 # hard impact on frame 0 (hook)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.25, s) * 0.6, max(0, t(s) - 0.12), 0.35)
    # engine: detuned saws whose pitch follows the car speed
    n = int(total * SR)
    tt = np.arange(n) / SR
    fr = np.array([game(min(N - 1, int(x * FPS)))["speed"] for x in tt[::480]])
    fr = np.interp(tt, tt[::480], fr) * 22 + 55
    ph = np.cumsum(fr) / SR
    eng = ((ph % 1) * 2 - 1) + ((ph * 1.01 % 1) * 2 - 1) * 0.7 + np.sin(2 * np.pi * ph * 0.5) * 0.8
    eng = fx.filt(eng, "lowpass", 900) * 0.10
    buf[:n] += eng[: len(buf)]
    for k_, f in enumerate(SCORE_AT):
        P(buf, point_snd(), t(f), 0.55)
    for f in CLOSE_AT:
        P(buf, fx.whoosh(0.22, f) * 0.9, t(f) - 0.08, 0.6)
        P(buf, sq(1400, 0.05, 0.25, 0.3), t(f), 0.3)
    P(buf, fx.riser(0.6), t(NITRO_AT) - 0.5, 0.35)
    P(buf, detent_click(), t(NITRO_AT - 2), 0.8)
    P(buf, fx.boom()[: int(0.6 * SR)], t(NITRO_AT), 0.5)
    P(buf, fx.boom()[: int(0.5 * SR)], t(CRASH), 0.45)
    P(buf, fanfare8(), t(CRASH) + 0.05, 0.7)
    P(buf, fx.ding(), t(BEST_AT), 0.5)
    return buf


# ================================================================== graphics
PX0, PY0, PW, PH = 40, 360, 1000, 500          # HD game-cam panel


def glow_col(f):
    if CRASH <= f < CRASH + 16:
        return np.array(YEL, np.float32), 0.26 * (1 - (f - CRASH) / 16) + 0.1
    if NITRO_AT <= f < NITRO_AT + 10:
        return np.array((60, 140, 255), np.float32), 0.3 * (1 - (f - NITRO_AT) / 10) + 0.12
    u = (f / 8.0) % len(RAINBOW)
    i = int(u)
    a = np.array(RAINBOW[i], np.float32)
    b_ = np.array(RAINBOW[(i + 1) % len(RAINBOW)], np.float32)
    return a + (b_ - a) * (u - i), 0.15


def rainbow_bar(fr, p):
    fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
    n = len(RAINBOW)
    for j in range(n):
        fr[0:10, j * W // n: min(p, (j + 1) * W // n)] = RAINBOW[j]


def panel(lay, f, s=1.0):
    """Rounded 'GAME CAM' card with the full-colour game frame, score, nitro meter, close-call chip and coin pops."""
    if s <= 0.02:
        return
    g = gamegfx.draw_hd(f, PW, PH).convert("RGBA")
    gs = game(f)
    dd = ImageDraw.Draw(g)
    dd.rounded_rectangle((18, PH - 78, 450, PH - 18), 30, fill=(0, 0, 0, 160))
    txt(dd, (40, PH - 48), f"SCORE {gs['score']:04d}   HI {HIGH_OLD}", 40, WHT, stroke=5, anchor="lm")
    w, h = int(PW * s), int(PH * s)
    g = g.resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), int(34 * s), fill=255)
    x0, y0 = int(PX0 + PW / 2 - w / 2), int(PY0 + PH / 2 - h / 2)
    sh = Image.new("RGBA", (w + 40, h + 40))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, h + 26), int(36 * s), fill=(0, 0, 0, 150))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (x0 - 20, y0 - 20))
    lay.paste(g, (x0, y0), m)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x0 + w - 1, y0 + h - 1), int(34 * s), outline=YEL + (255,), width=max(2, int(9 * s)))
    if s < 0.9:
        return
    d.rounded_rectangle((x0 + 22, y0 - 26, x0 + 290, y0 + 26), 26, fill=RED + (255,), outline=WHT, width=3)
    d.ellipse((x0 + 40, y0 - 9, x0 + 58, y0 + 9), fill=WHT if (f // 6) % 2 == 0 else (255, 160, 160))
    d.text((x0 + 175, y0), "GAME CAM", font=font(MONT, 32), fill=WHT, anchor="mm")
    # nitro meter chip (top-right of the card)
    full = gs["nitro"]
    blink = full and (f // 3) % 2 == 0
    d.rounded_rectangle((x0 + w - 330, y0 - 26, x0 + w - 22, y0 + 26), 26, fill=((60, 140, 255) if blink else (20, 24, 36)) + (255,), outline=WHT, width=3)
    d.text((x0 + w - 250, y0), "NITRO", font=font(MONT, 30), fill=WHT, anchor="mm")
    for k in range(COIN_COL):
        on = full or gs["meter"] > k
        d.rounded_rectangle((x0 + w - 170 + k * 46, y0 - 13, x0 + w - 134 + k * 46, y0 + 13), 6,
                            fill=(ORANGE if on else (70, 74, 90)) + (255,))
    for cf in CLOSE_AT:                                              # CLOSE CALL chip
        a = f - cf
        if 0 <= a < 14:
            u = pop_s(a, 4)
            cx, cy = x0 + w - 200, y0 + h - 52
            d.rounded_rectangle((cx - 175 * u, cy - 36 * u, cx + 175 * u, cy + 36 * u), 36, fill=RED + (255,), outline=WHT, width=4)
            if u > 0.9:
                d.text((cx, cy), "CLOSE CALL! +20", font=font(MONT, 34), fill=WHT, anchor="mm")
    for sf in SCORE_AT:                                              # +50 coin pop above the car
        a = f - sf
        if 0 <= a < 12:
            cx = x0 + (PX + CAR_W / 2) * w / 128
            yy = y0 + gs["py"] * h / 64 - 70 - a * 6
            r = 42 * pop_s(a, 4) * (1 - max(0, a - 8) / 4)
            if r > 4:
                d.ellipse((cx - r, yy - r, cx + r, yy + r), fill=(255, 205, 40, 255), outline=(150, 90, 0, 255), width=5)
                d.text((cx, yy), "+50", font=font(MONT, int(r * 0.75)), fill=(120, 60, 0, 255), anchor="mm")


def confetti(lay, f, f0):
    a = f - f0
    if a < 0:
        return
    d = ImageDraw.Draw(lay)
    rng_ = np.random.default_rng(5)
    for k_ in range(110):
        x0 = rng_.uniform(0, W)
        vy = rng_.uniform(14, 30)
        y = -40 + vy * a - rng_.uniform(0, 400)
        x = x0 + rng_.uniform(20, 60) * math.sin(a * 0.25 + k_)
        if -40 < y < H:
            ang = a * 0.3 + k_
            w_ = 18 * abs(math.cos(ang)) + 4
            d.rectangle((x - w_ / 2, y - 5, x + w_ / 2, y + 5), fill=RAINBOW[k_ % 8] + (255,))


def head(lay, d, text, y, size, col, em=None, s=1.0, dx=None):
    """Caption auto-fitted so text + emoji stay inside x = 60..1020, centred as one group."""
    es_ = (size * 0.95 + 10) if em else 0
    size = min(size, size * 960 / (d.textlength(text, font=font(MONT, size)) + es_))
    es = int(size * 0.95)
    cx = W / 2 - ((es + 10) / 2 if em else 0)
    txt(d, (cx, y), text, size * s, col, stroke=max(6, int(size / 9)))
    if em and s > 0.9:
        tw = d.textlength(text, font=font(MONT, size))
        lay.alpha_composite(e5.emoji(em, es), (int(cx + tw / 2 + 10), int(y - es * 0.55)))


GEM = os.path.join(WORK, "gem")              # frames of the user's Gemini AI clip (hand turning the knob)
CARD_Y = 400


def clip_card(lay, f, i, local):
    """Shots 0-1: the AI-generated hand-on-knob clip as a full-width card (whole frame kept, watermark visible)."""
    p = os.path.join(GEM, f"{f + 1:04d}.png")
    if not os.path.exists(p):
        return False
    c = Image.open(p).convert("RGB").resize((1040, 585), Image.LANCZOS)
    s = 1.0 if i == 0 else pop_s(local + 6, 6)
    w, h = int(1040 * s), int(585 * s)
    c = c.resize((w, h), Image.LANCZOS)
    x0, y0 = (W - w) // 2, CARD_Y + (585 - h) // 2
    sh = Image.new("RGBA", (w + 60, h + 60))
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, w + 30, h + 40), 34, fill=(0, 0, 0, 170))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (x0 - 30, y0 - 30))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=255)
    lay.paste(c, (x0, y0), m)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x0 + w - 1, y0 + h - 1), 30, outline=YEL + (255,), width=8)
    return True


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    g = Image.new("L", (1, H))
    g.putdata([int(170 * max(0, 1 - y_ / 520)) for y_ in range(H)])
    lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    d = ImageDraw.Draw(lay)
    if i == 0:                                     # HOOK: full text from the very first frame
        pulse = 1 + 0.04 * math.sin(f * 0.6)
        head(lay, d, "Ye MOBILE nahi hai!", 175, 84, YEL, "😱", pulse)
        head(lay, d, "ESP32 pe RACING GAME", 275, 66, PINK, "🏁")
    elif i == 1:
        head(lay, d, "Knob = Steering!", 185, 88, CYAN, "🎛️", pop_s(local, 5))
        v = ease((local - 4) / 5)
        if v > 0:
            tw = d.textlength("Ghumao aur car chalao", font=font(BOLD, 46)) + 60
            d.rounded_rectangle((W / 2 - tw / 2, 245, W / 2 + tw / 2, 312), 34, fill=(0, 0, 0, int(190 * v)))
            d.text((W / 2, 279), "Ghumao aur car chalao", font=font(BOLD, 46), fill=(235, 240, 255, int(255 * v)), anchor="mm")
    elif i == 2:
        full = SCORE_AT[COIN_COL - 1]
        if f < full:
            head(lay, d, "Traffic se bacho!", 200, 84, WHT, "💨", pop_s(local, 5))
        elif f < NITRO_AT:
            head(lay, d, "Knob dabao = NITRO!", 200, 76, ORANGE, "👆", pop_s(f - full, 5))
        else:
            head(lay, d, "NITRO!", 200, 130, (90, 170, 255), "🔥", pop_s(f - NITRO_AT, 5))
    elif i == 3:
        head(lay, d, "Speed DOUBLE!", 200, 100, (90, 170, 255), "⚡", pop_s(local, 5))
    elif i == 4:
        if f < CRASH:
            head(lay, d, "Last push...", 200, 96, WHT, "🏁", pop_s(local, 5))
        elif f < BEST_AT:
            head(lay, d, "FINISH!", 200, 130, GRN, "🏁", pop_s(f - CRASH, 5))
        else:
            head(lay, d, "NEW BEST!", 190, 110, YEL, "🏆", pop_s(f - BEST_AT, 6))
            v = ease((f - BEST_AT - 3) / 6)
            if v > 0:
                d.rounded_rectangle((W / 2 - 380 * v, 880, W / 2 + 380 * v, 1110), 50, fill=(10, 12, 18, 235), outline=YEL + (255,), width=6)
                if v > 0.9:
                    d.text((W / 2 - 180, 930), "SCORE", font=font(MONT, 38), fill=CYAN, anchor="mm")
                    d.text((W / 2 + 180, 930), "PEHLE", font=font(MONT, 38), fill=CYAN, anchor="mm")
                    txt(d, (W / 2 - 180, 1030), str(final_score()), 110, GRN, stroke=8)
                    txt(d, (W / 2 + 180, 1030), str(HIGH_OLD), 110, (200, 205, 215), stroke=8)
            confetti(lay, f, BEST_AT)
    else:                                          # loop shot: question + CTA, all inside the safe zone
        head(lay, d, "Tumhara score kitna?", 195, 76, YEL, "👇", pop_s(local, 5))
        v = ease((local - 6) / 6)
        if v > 0:
            bw = int(800 * v)
            cx = W / 2 - 50
            d.rounded_rectangle((cx - bw / 2, 900, cx + bw / 2, 1010), 55, fill=YEL + (255,))
            if v > 0.9:
                d.text((cx, 955), "Comment \"GAME\" = Code FREE", font=font(MONT, 44), fill=INK, anchor="mm")
    if not (i <= 1 and clip_card(lay, f, i, local)):
        panel(lay, f)
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
        fr = load3d(f)
        z = 1.0
        for h0, amp in [(sf, 0.015) for sf in SCORE_AT] + [(cf, 0.02) for cf in CLOSE_AT] + \
                [(NITRO_AT, 0.06), (CRASH, 0.06), (BEST_AT, 0.04)] + [(s_, 0.05) for s_ in SHOTS[1:]]:
            a = f - h0
            if 0 <= a < 6:                                         # hard cut + small zoom punch (no blur)
                z += amp * (1 - a / 6) ** 2
        if z > 1.0:
            fr = zoom(fr, z)
        x = fr.astype(np.float32) * (1 - 0.22 * vig)
        c, k_ = glow_col(f)
        x = x * (1 - k_ * vig) + c * k_ * vig
        if 0 <= f - CRASH < 4:                                     # white flash at the finish
            x = x + (255 - x) * 0.45 * (1 - (f - CRASH) / 4)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
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
