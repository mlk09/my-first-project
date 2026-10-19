#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED Rock-Paper-Scissors Robot' short, same house style as the
rotary-encoder short: robot spin in the hook, callout tags, 4 rounds (pick with the knob, 3-2-1, robot
box spins, YOU WIN / BOT WINS), live BOT : YOU scoreboard, champion confetti, end card + Like / Share /
Subscribe outro. Knob clicks, countdown beeps, servo whirr, win jingle / lose trombone, fanfare.
Usage: python3 edit15/build_short.py [audio] [video]
"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "edit"))
import build_edit as fx  # noqa: E402
from timeline import (FPS, N, SHOTS, ROUNDS, CHOICES, EMO, PRESS, CD, REVEAL, HOOK_SPIN,  # noqa: E402
                      knob_choice, pressed, phase, round_at, score, winner, ease)

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-rock-paper-scissors-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
CHAMP = ROUNDS[-1][0] + REVEAL + 14
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
    lay.alpha_composite(e5.emoji("🎮", 46), (W - 388, 46))


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
def whirr(dur):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = fx.signal.sawtooth(2 * np.pi * (190 + 40 * np.sin(2 * np.pi * 6 * tt)) * tt)
    x = fx.filt(x, "bandpass", [150, 2500]) + 0.3 * fx.filt(fx.noise(n, 4), "bandpass", [2000, 6000])
    return x * np.minimum(1, tt / 0.05) * np.minimum(1, (dur - tt) / 0.08) * 0.4


def jingle(up=True):
    notes = [784, 988, 1175, 1568] if up else [392, 370, 349, 294]
    out = np.zeros(int(0.7 * SR))
    for i, fr in enumerate(notes):
        nt = fx.synth_note(fr, 0.22 if up else 0.3, "square" if up else "saw", 7 if up else 4, 3500 if up else 1200) * 0.4
        fx.place(out, nt, i * (0.09 if up else 0.14), 1.0)
    return out


def fanfare():
    out = np.zeros(int(1.6 * SR))
    for i, (fr, d) in enumerate(((523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.6))):
        for h, a in ((1, 0.4), (2, 0.15), (3, 0.08)):
            fx.place(out, fx.synth_note(fr * h, d + 0.2, "saw", 3, 4000) * a, [0, 0.12, 0.24, 0.36][i], 1.0)
    return out


def music(total):
    """118 BPM game-show groove (8-bit leads); filtered until the first round; extra energy at the final."""
    bpm, n = 118, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[261.6, 329.6, 392.0], [293.7, 349.2, 440.0], [220.0, 261.6, 329.6], [196.0, 246.9, 293.7]]
    roots = [65.4, 73.4, 55.0, 49.0]
    kick = fx.kick() * 0.5
    drop = t(HOOK_SPIN[1])
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        for s in range(4):
            fx.place(mel, fx.synth_note(ch[(pos + s) % 3] * 2, beat / 4 * 1.4, "square", 14, 2800), t0 + s * beat / 4, 0.06)
        if t0 >= drop:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 240), t0, 0.6)
            if pos in (0, 2):
                fx.place(drums, kick, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.28)
            for s in range(2):
                fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / 2, 0.05)
        b += 1
    mix = mel + bass + drums
    i = int(drop * SR)
    mix[:i] = fx.filt(mix[:i], "lowpass", 900)
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.3), 0.0, 0.3)
    P(buf, whirr(t(HOOK_SPIN[1] - HOOK_SPIN[0])), t(HOOK_SPIN[0]), 0.5)
    P(buf, fx.boom()[: int(0.5 * SR)], t(HOOK_SPIN[1]), 0.45)
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    P(buf, fx.pop(), t(SHOTS[1] + 4), 0.25)
    for f in range(1, N):
        if knob_choice(f) != knob_choice(f - 1):
            P(buf, detent_click(), t(f), 0.6)
    for i, (s, _, _) in enumerate(ROUNDS):
        P(buf, fx.pop(), t(s + PRESS), 0.4)                               # press
        for k_ in range(3):                                                  # 3-2-1 beeps
            P(buf, beep(880, 0.08), t(s + CD + 8 * k_), 0.35)
        P(buf, whirr(t(REVEAL - CD - 4)), t(s + CD + 4), 0.5)
        P(buf, beep(1760, 0.14), t(s + REVEAL), 0.4)
        w = winner(i)
        P(buf, jingle(w == "YOU"), t(s + REVEAL + 2), 0.55)
        if w == "YOU":
            P(buf, fx.ding(), t(s + REVEAL + 4), 0.3)
    P(buf, fanfare(), t(CHAMP), 0.6)
    P(buf, fx.boom()[: int(0.6 * SR)], t(CHAMP), 0.4)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
def scoreboard(lay, d, f, y0=1560):
    """Big BOT : YOU score with robot / player emojis (own style)."""
    bot, you = score(f)
    i, l = round_at(f)
    bump = 0
    if i is not None and REVEAL <= l < REVEAL + 8:
        bump = 0.18 * (1 - (l - REVEAL) / 8)
    d.rounded_rectangle((W / 2 - 400, y0 - 90, W / 2 + 400, y0 + 90), 60, fill=(10, 12, 18, 220), outline=(255, 255, 255, 140), width=3)
    lay.alpha_composite(e5.emoji("🤖", 120), (int(W / 2 - 380), int(y0 - 62)))
    lay.alpha_composite(e5.emoji("🧑", 120), (int(W / 2 + 260), int(y0 - 62)))
    sz = 130 * (1 + bump)
    txt(d, (W / 2 - 110, y0), str(bot), sz, RED if bot > you else WHT, stroke=10)
    txt(d, (W / 2, y0 - 6), ":", 110, WHT, stroke=8)
    txt(d, (W / 2 + 110, y0), str(you), sz, GRN if you > bot else WHT, stroke=10)


def confetti(lay, f):
    a = f - CHAMP
    if a < 0:
        return
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(7)
    cols = [RED, YEL, GRN, CYAN, (200, 120, 255), ORG]
    for k_ in range(90):
        x0 = rng.uniform(0, W)
        vy = rng.uniform(14, 30)
        sway = rng.uniform(20, 60)
        y = -40 + vy * a - rng.uniform(0, 400)
        x = x0 + sway * math.sin(a * 0.25 + k_)
        if -40 < y < H:
            c = cols[k_ % len(cols)]
            ang = a * 0.3 + k_
            w_, h_ = 18 * abs(math.cos(ang)) + 4, 10
            d.rectangle((x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), fill=c + (255,))


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "esp": ((200, 830), (220, 600), "ESP32", "Dimaag"),
    "oled": ((480, 850), (560, 600), "OLED", "Score + Result"),
    "robot": ((930, 800), (870, 440), "Servo + Box", "Robot ka haath"),
    "knob": ((180, 1250), (250, 1520), "Knob", "Tumhari chaal"),
}


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i < 6:
        g = Image.new("L", (1, H))
        g.putdata([int(140 * max(0, 1 - y_ / 560)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    ph, n = phase(f)
    r, rl = round_at(f)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Robot vs Insaan", 84 * s, WHT, stroke=8)
        s2 = pop_s(f - HOOK_SPIN[1], 6)
        if s2 > 0:
            txt(d, (W / 2, 380), "ROCK PAPER SCISSORS!", 70 * s2, YEL, stroke=8)
            if s2 > 0.9:
                lay.alpha_composite(e5.emoji("✊", 90), (W // 2 - 190, 440))
                lay.alpha_composite(e5.emoji("✋", 90), (W // 2 - 45, 440))
                lay.alpha_composite(e5.emoji("✌️", 90), (W // 2 + 100, 440))
        v = ease((local - 34) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 330, 1620, W / 2 + 330, 1720), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1670), "Pehle 3 jeeto = WINNER", font=font(MONT, 44), fill=INK, anchor="mm")
    elif i == 1:
        label(lay, d, "ESP32 Game Robot", None, local, y=300, em="🎮")
        for j, key in enumerate(("esp", "oled", "robot", "knob")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 7) / 10))
    elif i in (2, 3, 4, 5):
        if r is not None:
            _, p, bch = ROUNDS[r]
            title = "FINAL ROUND!" if r == len(ROUNDS) - 1 else f"ROUND {r + 1}"
            if ph == "select":
                label(lay, d, title, "Knob ghuma ke chaal chuno", rl, y=300, em="🎛️")
            elif ph == "count":
                txt(d, (W / 2, 300), title, 84, WHT, stroke=8)
                s = pop_s((rl - CD) % 8, 4)
                txt(d, (W / 2, 470), str(n), 220 * s, YEL, stroke=14)
            elif ph == "result":
                w = winner(r)
                s = pop_s(rl - REVEAL, 6)
                msg = {"YOU": "TUM JEETE!", "BOT": "ROBOT JEETA!", "TIE": "TIE!"}[w]
                txt(d, (W / 2, 280), msg, 116 * s, GRN if w == "YOU" else RED, stroke=11)
                if s > 0.9:
                    lay.alpha_composite(e5.emoji(EMO[CHOICES[p]], 100), (W // 2 - 230, 350))
                    txt(d, (W / 2, 400), "vs", 64, WHT, stroke=6)
                    lay.alpha_composite(e5.emoji(EMO[CHOICES[bch]], 100), (W // 2 + 130, 350))
                    d.text((W // 2 - 180, 475), "TUM", font=font(MONT, 34), fill=WHT, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
                    d.text((W // 2 + 180, 475), "ROBOT", font=font(MONT, 34), fill=WHT, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
            elif ph == "champ":
                s = pop_s(f - CHAMP, 7)
                txt(d, (W / 2, 290), "CHAMPION!", 140 * s, YEL, stroke=12)
                if s > 0.9:
                    lay.alpha_composite(e5.emoji("🏆", 120), (W // 2 - 60, 370))
        scoreboard(lay, d, f)
        confetti(lay, f)
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y_ / 700)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        confetti(lay, f)
        d = ImageDraw.Draw(lay)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Circuit FREE", 78 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130)
        v = ease((local - 10) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"GAME\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 18) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1780), "Follow @The IOT Engineer", 54, WHT, stroke=5)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2).clip(0, 1)[..., None].astype(np.float32)
    for f in range(TOTAL):
        if f >= N:
            fr = outro(f - N)
            if f - N < 4:
                k_ = 1 - (f - N) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 20 * k_), 1 + 0.06 * k_)
            fr[0:10, :] = YEL
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z, dx = 1.0, 0.0
        r, rl = round_at(f)
        if pressed(f):
            z += 0.02
        if r is not None:
            a = rl - REVEAL
            if 0 <= a < 10:
                z += 0.05 * (1 - a / 10) ** 2
                if winner(r) == "BOT":
                    dx = 16 * np.sin(a * 2.5) * (1 - a / 10)
        a = f - CHAMP
        if 0 <= a < 10:
            z += 0.05 * (1 - a / 10) ** 2
        a = f - HOOK_SPIN[1]
        if 0 <= a < 8:
            z += 0.04 * (1 - a / 8) ** 2
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        if r is not None and REVEAL <= rl and phase(f)[0] == "result":   # result edge glow
            c = np.array(GRN if winner(r) == "YOU" else RED, np.float32)
            k_ = 0.2 * max(0.3, 1 - (rl - REVEAL) / 24)
            x = x * (1 - k_ * vig) + c * k_ * vig
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = max(0.0, 1 - abs(dd + 0.5) / 4)
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / TOTAL)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p] = YEL
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
