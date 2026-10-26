#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED Flappy Bird' short, same house style as the rotary-encoder
short but in native 1080x1920 HD: the 3D OLED console plus a crisp full-colour 'game cam' panel that
plays the exact same game frame (gamegfx.draw_hd), knob turn = level, knob press = flap, +1 coin pops,
3-2-1, GAME OVER shake, NEW HIGH SCORE confetti, rainbow edge glow + progress bar like the LED Flow
short, end card + Like / Share / Subscribe outro. 8-bit chiptune, flap / point / hit / die SFX.
Usage: python3 edit22/build_short.py [audio] [video]
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
from timeline import (FPS, N, SHOTS, START, PLAY0, LEVELS, LEVEL_CLICKS, HIGH_OLD, game, phase,  # noqa: E402
                      level, countdown, crash_frame, final_score, flapping, ease)
import gamegfx  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-flappy-bird-game-SHORT.mp4")
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
    lay.alpha_composite(e5.emoji("🐦", 46), (W - 388, 46))


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
RAINBOW = [(255, 40, 40), (255, 120, 20), (255, 210, 20), (80, 240, 60), (30, 230, 190), (40, 120, 255),
           (130, 60, 255), (255, 60, 170)]             # same palette as the rotary-encoder LED Flow short
CRASH = crash_frame()
BEST_AT = CRASH + 26
SCORE_AT = [f for f in range(1, N) if game(f) and game(f - 1) and game(f)["score"] > game(f - 1)["score"]]
FLAPS = [f for f in range(N) if flapping(f)]


def sq(freq, dur, duty=0.5, vol=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.where((tt * freq) % 1 < duty, 1.0, -1.0)
    return x * np.minimum(1, tt / 0.002) * np.minimum(1, (dur - tt) / 0.01) * vol


def flap_snd():
    """Wing 'swoop': quick upward noise sweep + soft blip."""
    n = int(0.09 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 31), "bandpass", [900, 4000]) * np.sin(np.pi * tt / 0.09)
    return x * 0.6 + np.sin(2 * np.pi * (500 + 4000 * tt) * tt) * np.exp(-tt * 40) * 0.3


def point_snd():
    """Classic coin: two square notes."""
    return np.concatenate([sq(988, 0.06, 0.25), sq(1319, 0.18, 0.25)]) * np.exp(-np.arange(int(0.24 * SR)) / SR * 6)


def hit_snd():
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    return (fx.filt(fx.noise(n, 5), "lowpass", 1200) * np.exp(-tt * 18) + np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 12)) * 0.9


def die_snd():
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    fr = 700 * np.exp(-tt * 3)
    x = np.where((np.cumsum(fr) / SR) % 1 < 0.5, 1.0, -1.0)
    return x * np.minimum(1, (0.6 - tt) / 0.05) * 0.35


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
    for a0, a1 in ((SHOTS[2], PLAY0), (CRASH, CRASH + 12)):        # filtered menu / crash dip
        i0, i1 = int(t(a0) * SR), int(t(a1) * SR)
        mix[i0:i1] = fx.filt(mix[i0:i1], "lowpass", 1000)
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.3), 0.0, 0.25)
    for s in SHOTS[1:]:
        if s not in (SHOTS[4],):
            P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    P(buf, fx.pop(), t(SHOTS[1] + 4), 0.25)
    for f in FLAPS:
        P(buf, flap_snd(), t(f), 0.32)
    for f in SCORE_AT:
        P(buf, point_snd(), t(f), 0.5)
    for c, _ in LEVEL_CLICKS:
        P(buf, detent_click(), t(c + 2), 0.7)
        P(buf, sq(1200, 0.05, 0.25, 0.3), t(c + 3), 0.6)
    P(buf, detent_click(), t(START - 8), 0.6)
    P(buf, fx.pop(), t(START), 0.5)
    for k_ in range(3):
        P(buf, sq(880, 0.1, 0.5, 0.4), t(START + 8 * k_), 0.7)
    P(buf, sq(1760, 0.25, 0.5, 0.4), t(PLAY0), 0.7)
    P(buf, hit_snd(), t(CRASH), 0.8)
    P(buf, fx.boom()[: int(0.5 * SR)], t(CRASH), 0.35)
    P(buf, die_snd(), t(CRASH) + 0.25, 0.6)
    hook_dead = next((f for f in range(SHOTS[1]) if game(f)["state"] == "DEAD"), None)
    if hook_dead:
        P(buf, hit_snd(), t(hook_dead), 0.6)
    P(buf, fanfare8(), t(BEST_AT), 0.7)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
PX0, PY0, PW, PH = 40, 330, 1000, 500          # HD game-cam panel


def glow_col(f):
    if CRASH <= f < CRASH + 16:
        return np.array(RED, np.float32), 0.26 * (1 - (f - CRASH) / 16) + 0.1
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


def panel(lay, f, s=1.0, shake=0.0):
    """Rounded 'GAME CAM' card with the full-colour game frame, score and flap chip."""
    if s <= 0.02:
        return
    g = gamegfx.draw_hd(f, PW, PH).convert("RGBA")
    dd = ImageDraw.Draw(g)
    sc = game(f)["score"] if game(f) else 0
    if game(f):
        txt(dd, (PW / 2, 62), str(sc), 92, WHT, stroke=8)
    w, h = int(PW * s), int(PH * s)
    g = g.resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), int(34 * s), fill=255)
    cx, cy = PX0 + PW / 2 + shake, PY0 + PH / 2
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    sh = Image.new("RGBA", (w + 40, h + 40))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, h + 26), int(36 * s), fill=(0, 0, 0, 150))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (x0 - 20, y0 - 20))
    lay.paste(g, (x0, y0), m)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x0 + w - 1, y0 + h - 1), int(34 * s), outline=YEL + (255,), width=max(2, int(9 * s)))
    if s > 0.9:
        d.rounded_rectangle((x0 + 22, y0 - 26, x0 + 290, y0 + 26), 26, fill=RED + (255,), outline=WHT, width=3)
        d.ellipse((x0 + 40, y0 - 9, x0 + 58, y0 + 9), fill=WHT if (f // 6) % 2 == 0 else (255, 160, 160))
        d.text((x0 + 175, y0), "GAME CAM", font=font(MONT, 32), fill=WHT, anchor="mm")
        if flapping(f) or (f >= 1 and flapping(f - 1)):
            d.rounded_rectangle((x0 + w - 270, y0 + h - 86, x0 + w - 24, y0 + h - 22), 32, fill=CYAN + (255,), outline=WHT, width=3)
            d.text((x0 + w - 147, y0 + h - 54), "FLAP!", font=font(MONT, 40), fill=INK, anchor="mm")
        for sf in SCORE_AT:                                           # +1 coin pop
            a = f - sf
            if 0 <= a < 14:
                yy = y0 + 150 - a * 6
                al = int(255 * (1 - a / 14))
                d.ellipse((x0 + 300 - 34, yy - 34, x0 + 300 + 34, yy + 34), fill=(255, 205, 40, al), outline=(150, 90, 0, al), width=5)
                d.text((x0 + 300, yy), "+1", font=font(MONT, 40), fill=(120, 60, 0, al), anchor="mm")


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


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "oled": ((660, 860), (840, 560), "OLED", "Game screen"),
    "esp": ((420, 850), (230, 600), "ESP32", "Game engine"),
    "knob": ((370, 1300), (300, 1600), "Knob", "Turn = level, Press = FLAP"),
    "bz": ((740, 1300), (820, 1450), "Buzzer + LEDs", "Sound + score"),
}


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i < 6:
        g = Image.new("L", (1, H))
        g.putdata([int(150 * max(0, 1 - y_ / 520)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    ph = phase(f)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 200), "ESP32 pe GAME!", 96 * s, YEL, stroke=10)
        if s > 0.9:
            tw = d.textlength("ESP32 pe GAME!", font=font(MONT, 96))
            lay.alpha_composite(e5.emoji("🐦", 90), (int(W / 2 + tw / 2 + 8), 150))
        panel(lay, f, pop_s(local - 6, 8))
    elif i == 1:
        label(lay, d, "Flappy Bird on ESP32", None, local, y=230, em=None)
        for j, key in enumerate(("oled", "esp", "knob", "bz")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 7) / 10))
    elif i == 2:
        if f < START:
            label(lay, d, "Knob = LEVEL", "Ghumao aur level chuno", local, y=230, em="🎛️")
            for k_, lv in enumerate(LEVELS):
                act = k_ == level(f)
                cx = 200 + k_ * 340
                sz = 1.12 if act else 1.0
                d.rounded_rectangle((cx - 150 * sz, 420 - 55 * sz, cx + 150 * sz, 420 + 55 * sz), 50,
                                    fill=((GRN, YEL, RED)[k_] if act else (60, 64, 76)) + (255,), outline=WHT if act else None, width=5)
                d.text((cx, 420), lv, font=font(MONT, int(50 * sz)), fill=INK if act else (170, 175, 190), anchor="mm")
        else:
            label(lay, d, "Knob dabao = START", None, f - START, y=230, em="👆")
            cd = countdown(f)
            if cd:
                s = pop_s((f - START) % 8, 4)
                txt(d, (W / 2, 560), str(cd), 260 * s, YEL, stroke=16)
    elif i == 3:
        s = pop_s(local, 6)
        txt(d, (W / 2, 190), "Press = FLAP!", 84 * s, CYAN, stroke=9)
        if s > 0.9:
            tw = d.textlength("Press = FLAP!", font=font(MONT, 84))
            lay.alpha_composite(e5.emoji("🐦", 80), (int(W / 2 + tw / 2 + 8), 145))
        if local < 6:
            txt(d, (W / 2, 580), "GO!", 200 * pop_s(local, 4), GRN, stroke=14)
        else:
            panel(lay, f)
    elif i == 4:
        sh = 18 * math.sin((f - CRASH) * 2.6) * max(0, 1 - (f - CRASH) / 12) if f >= CRASH else 0
        if f < CRASH:
            txt(d, (W / 2, 190), "Press = FLAP!", 84, CYAN, stroke=9)
            panel(lay, f)
        else:
            panel(lay, f, shake=sh)
            s = pop_s(f - CRASH, 6)
            txt(d, (W / 2 - 40, 200), "GAME OVER", 120 * s, RED, stroke=12)
            if s > 0.9:
                tw = d.textlength("GAME OVER", font=font(MONT, 120))
                lay.alpha_composite(e5.emoji("💥", 100), (int(W / 2 - 40 + tw / 2 + 8), 145))
    elif i == 5:
        s = pop_s(f - BEST_AT, 7)
        txt(d, (W / 2, 190), "NEW HIGH SCORE!", 92 * s, YEL, stroke=10)
        if s > 0.9:
            lay.alpha_composite(e5.emoji("🏆", 130), (W // 2 - 65, 260))
        v = ease((f - BEST_AT - 6) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 380 * v, 420, W / 2 + 380 * v, 660), 50, fill=(10, 12, 18, 230), outline=YEL + (255,), width=6)
            if v > 0.9:
                d.text((W / 2 - 180, 470), "SCORE", font=font(MONT, 38), fill=CYAN, anchor="mm")
                d.text((W / 2 + 180, 470), "BEST", font=font(MONT, 38), fill=CYAN, anchor="mm")
                txt(d, (W / 2 - 180, 565), str(final_score()), 110, WHT, stroke=8)
                txt(d, (W / 2 + 180, 565), str(final_score()), 110, GRN, stroke=8)
                d.text((W / 2 + 180, 625), f"(pehle {HIGH_OLD})", font=font(BOLD, 30), fill=(200, 205, 215), anchor="mm")
        confetti(lay, f, BEST_AT)
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y_ / 700)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        d = ImageDraw.Draw(lay)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Circuit FREE", 78 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130)
        v = ease((local - 5) / 8)
        if v > 0:
            d.rounded_rectangle((90, 380, 90 + (W - 180) * v, 560), 30, fill=(12, 16, 24, 235), outline=CYAN + (255,), width=4)
            if v > 0.9:
                d.text((130, 430), "if (knobPressed()) vel = -2.6;", font=font(MONO, 40), fill=(255, 190, 90), anchor="lm")
                d.text((130, 505), "vel += 0.3;  birdY += vel;", font=font(MONO, 40), fill=(150, 255, 170), anchor="lm")
        v = ease((local - 12) / 8)
        if v > 0:
            bw = int(940 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"GAME\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 20) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1780), "Follow @The IOT Engineer", 54, WHT, stroke=5)
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
        if f >= N:
            fr = outro(f - N)
            if f - N < 4:
                k_ = 1 - (f - N) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 20 * k_), 1 + 0.06 * k_)
            rainbow_bar(fr, W)
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z, dx = 1.0, 0.0
        for h0, amp in [(sf, 0.012) for sf in SCORE_AT] + [(START, 0.04), (PLAY0, 0.05), (BEST_AT, 0.05)]:
            a = f - h0
            if 0 <= a < 8:
                z += amp * (1 - a / 8) ** 2
        a = f - CRASH
        if 0 <= a < 12:
            z += 0.06 * (1 - a / 12) ** 2
            dx = 22 * np.sin(a * 2.6) * (1 - a / 12)
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.22 * vig)
        c, k_ = glow_col(f)
        x = x * (1 - k_ * vig) + c * k_ * vig
        if 0 <= f - CRASH < 4:                                     # white hit flash
            x = x + (255 - x) * 0.5 * (1 - (f - CRASH) / 4)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4 and s != SHOTS[4]:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
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
