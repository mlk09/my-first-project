#!/usr/bin/env python3
"""19.5 s + 2.5 s outro = 22 s 'ESP32 + OLED + DHT11 temperature-controlled LED' short, same house
style as the rotary-encoder short: hot coffee mug in the hook (LED ON), callout tags, DHT11 close-up,
knob sets the limit (30 -> 28 degC), heat-up with red LED + buzzer, cool-down with LED OFF, live
thermometer HUD, end card + Like / Share / Subscribe outro. DHT ticks, knob clicks, alarm beeps,
whooshes, chill-tech groove.
Usage: python3 edit16/build_short.py [audio] [video]
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
from timeline import FPS, N, SHOTS, temp, hum, limit, hot, mug, busy, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-dht11-temperature-SHORT.mp4")
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
    lay.alpha_composite(e5.emoji("🌡️", 46), (W - 388, 46))


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
SW = [f for f in range(1, N) if hot(f) != hot(f - 1)]          # LED switch frames: on, off, on, off
ON1, OFF1, ON2, OFF2 = SW[:4]


def alarm():
    """Piezo buzzer: two quick square beeps."""
    return np.concatenate([beep(2400, 0.07, True), np.zeros(int(0.05 * SR)), beep(2400, 0.07, True)])


def tick():
    n = int(0.012 * SR)
    tt = np.arange(n) / SR
    return fx.filt(fx.noise(n, 5), "highpass", 4000) * np.exp(-tt * 400)


def slide(dur):
    """Ceramic mug sliding over the mat."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 12), "bandpass", [300, 2200])
    return x * np.sin(np.pi * np.minimum(1, tt / dur)) * 0.6


def music(total):
    """100 BPM chill-tech groove (plucked arps + sub); filtered until the first LED ON."""
    bpm, n = 100, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [196.0, 246.9, 293.7], [164.8, 207.7, 246.9]]
    roots = [55.0, 43.65, 49.0, 41.2]
    kick = fx.kick() * 0.5
    drop = t(ON1)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        for s in range(4):
            note = ch[(pos * 2 + s) % 3] * (2 if s % 2 else 4)
            fx.place(mel, fx.synth_note(note, beat / 4 * 1.6, "tri", 9, 3200), t0 + s * beat / 4, 0.09)
        if t0 >= drop:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.95, "saw", 3, 200), t0, 0.5)
            if pos in (0, 2) or (pos == 3 and bar % 2):
                fx.place(drums, kick, t0, 0.8)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.25)
            for s in range(4):
                fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / 4, 0.035 if s % 2 else 0.05)
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
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    P(buf, fx.pop(), t(SHOTS[1] + 4), 0.25)
    for f0 in (2, SHOTS[4] + 2):                                   # mug slides in, lands
        P(buf, slide(0.6), t(f0), 0.35)
        P(buf, fx.ding()[: int(0.25 * SR)], t(f0 + 14), 0.18)
    for f0 in (46, SHOTS[5] + 4):                                  # mug slides away
        P(buf, slide(0.5), t(f0), 0.3)
    for f in range(SHOTS[2], SHOTS[3]):                            # DHT11 reads
        if busy(f) and not busy(f - 1):
            P(buf, tick(), t(f), 0.35)
    for f in range(1, N):
        if limit(f) != limit(f - 1):
            P(buf, detent_click(), t(f), 0.7)
            P(buf, beep(1500, 0.05), t(f) + 0.03, 0.18)
    for on in (ON1, ON2):                                          # LED ON: hit + buzzer
        P(buf, fx.boom()[: int(0.5 * SR)], t(on), 0.45)
        for k_ in range(4):
            P(buf, alarm(), t(on) + k_ * 0.45, 0.32)
    for off in (OFF1, OFF2):                                       # LED OFF: all-OK chirp
        P(buf, ok_beep(), t(off), 0.3)
    P(buf, fx.ding(), t(OFF2 + 2), 0.35)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
TLO, THI = 24.0, 37.0
BLU = (70, 150, 255)


def hud(lay, d, f, y0=1590):
    """Live thermometer HUD: temperature, limit marker on a heat bar, LED state pill (own style)."""
    tc, lim, on = temp(f), limit(f), hot(f)
    d.rounded_rectangle((60, y0 - 120, W - 60, y0 + 120), 56, fill=(10, 12, 18, 225), outline=(255, 255, 255, 140), width=3)
    lay.alpha_composite(e5.emoji("🌡️", 76), (96, int(y0 - 88)))
    txt(d, (370, y0 - 48), f"{tc:.1f}°C", 92, RED if on else WHT, stroke=8)
    on_age = min(f - x for x in SW if x <= f) if any(x <= f for x in SW) else 99
    s = 1 + 0.25 * max(0, 1 - on_age / 6)
    pw, ph = 300 * s, 92 * s
    cx, cy = W - 250, y0 - 48
    d.rounded_rectangle((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), 46,
                        fill=(RED if on else BLU) + (255,), outline=WHT, width=4)
    d.text((cx, cy), "LED ON" if on else "LED OFF", font=font(MONT, 52 * s), fill=WHT, anchor="mm",
           stroke_width=3, stroke_fill=(0, 0, 0))
    x0, x1, by = 110, W - 110, y0 + 58                                # heat bar
    def bx(v):
        return x0 + (min(max(v, TLO), THI) - TLO) / (THI - TLO) * (x1 - x0)
    for i in range(40):
        u = i / 39
        col = tuple(int(a + (b - a) * u) for a, b in zip((60, 160, 255), (255, 60, 50)))
        xa = x0 + (x1 - x0) * i / 40
        d.rectangle((xa, by - 14, xa + (x1 - x0) / 40 + 1, by + 14), fill=col + (90,))
    d.rounded_rectangle((x0, by - 14, bx(tc), by + 14), 14, fill=(RED if on else CYAN) + (255,))
    lx = bx(lim)
    d.line((lx, by - 34, lx, by + 30), fill=YEL, width=6)
    d.text((lx, by - 50), f"SET {lim:.0f}°", font=font(MONT, 30), fill=YEL, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))


def heat_waves(lay, f, cx, cy, amt):
    """Wavy heat/steam lines rising from the mug."""
    if amt <= 0.02:
        return
    d = ImageDraw.Draw(lay)
    for j in range(3):
        ph = (f * 0.09 + j * 0.33) % 1.0
        pts = []
        for s in range(14):
            v = s / 13
            y = cy - 10 - (v * 0.6 + ph) * 120
            x = cx + (j - 1) * 46 + 16 * math.sin(v * 7 + f * 0.25 + j)
            pts.append((x, y))
        a = int(200 * amt * math.sin(math.pi * ph))
        d.line(pts, fill=(255, 255, 255, max(0, a)), width=8, joint="curve")


TAGS = {   # shot-1 anchors on the top-down wide (measured on the render)
    "esp": ((320, 860), (220, 660), "ESP32", "Dimaag"),
    "oled": ((650, 860), (880, 720), "OLED", "Live Temp"),
    "dht": ((590, 500), (850, 470), "DHT11", "Temp + Humidity"),
    "knob": ((370, 1300), (250, 1560), "Knob", "Limit set"),
    "leds": ((640, 1280), (820, 1560), "LEDs", "HOT / OK"),
}
MUG_XY = (860, 560)                   # hook / heat shot mug top (measured on the render)


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
    on = hot(f)
    if i in (0, 4):
        heat_waves(lay, f, *(MUG_XY if i == 0 else (830, 500)), ease((mug(f) - 0.6) / 0.4))
        d = ImageDraw.Draw(lay)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Garam coffee paas laao", 70 * s, WHT, stroke=7)
        if s > 0.9:
            lay.alpha_composite(e5.emoji("☕", 80), (W // 2 - 40, 300))
        s2 = pop_s(f - ON1, 6)
        if s2 > 0:
            txt(d, (W / 2, 470), "LED ON!", 150 * s2, RED, stroke=13)
            if s2 > 0.9:
                tw = d.textlength("LED ON!", font=font(MONT, 150))
                lay.alpha_composite(e5.emoji("🔥", 120), (int(W / 2 + tw / 2 + 10), 400))
        hud(lay, d, f)
    elif i == 1:
        label(lay, d, "ESP32 Temp Controller", None, local, y=230, em=None)
        for j, key in enumerate(("dht", "esp", "oled", "knob", "leds")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 6) / 10))
    elif i == 2:
        label(lay, d, "DHT11 Sensor", "Temperature + Humidity dono", local, y=280, em="🌡️")
        v = ease((local - 14) / 8)
        if v > 0:
            for j, (nm, val, col) in enumerate((("TEMP", f"{temp(f):.1f}°C", ORG), ("HUM", f"{hum(f):.0f}%", CYAN))):
                cx = W / 2 + (j * 2 - 1) * 250
                d.rounded_rectangle((cx - 210 * v, 1180, cx + 210 * v, 1400), 40, fill=(10, 12, 18, 225), outline=col + (255,), width=5)
                if v > 0.9:
                    d.text((cx, 1230), nm, font=font(MONT, 40), fill=col, anchor="mm")
                    txt(d, (cx, 1325), val, 84, WHT, stroke=6)
            if (f % 12) < 4 and v > 0.9:
                d.text((W / 2, 1460), "● reading...", font=font(BOLD, 40), fill=(150, 255, 170), anchor="mm")
        hud(lay, d, f)
    elif i == 3:
        label(lay, d, "Knob = LIMIT", "Knob ghumao, limit set karo", local, y=280, em="🎛️")
        lim = limit(f)
        ch = [x for x in range(SHOTS[3], f + 1) if limit(x) != limit(x - 1)]
        s = 1 + 0.3 * max(0, 1 - (f - ch[-1]) / 6) if ch else 1
        v = ease((local - 8) / 6)
        if v > 0:
            d.rounded_rectangle((W / 2 - 260 * v, 730, W / 2 + 260 * v, 930), 50, fill=(10, 12, 18, 225), outline=YEL + (255,), width=6)
            if v > 0.9:
                d.text((W / 2, 772), "SET LIMIT", font=font(MONT, 40), fill=YEL, anchor="mm")
                txt(d, (W / 2, 860), f"{lim:.0f}°C", 100 * s, WHT, stroke=8)
        hud(lay, d, f)
    elif i == 4:
        if not on:
            label(lay, d, "Coffee wapas!", "Temperature badh raha hai...", local, y=280, em="☕")
        else:
            s = pop_s(f - ON2, 6)
            txt(d, (W / 2, 250), f"{limit(f):.0f}°C PAAR!", 120 * s, RED, stroke=11)
            if s > 0.9:
                d.rounded_rectangle((W / 2 - 360, 340, W / 2 + 360, 430), 45, fill=(0, 0, 0, 180))
                d.text((W / 2 - 30, 385), "Red LED ON + Buzzer", font=font(BOLD, 50), fill=WHT, anchor="mm")
                lay.alpha_composite(e5.emoji("🔊", 70), (int(W / 2 + 260), 350))
            if (f - ON2) % 11 < 5 and f - ON2 < 45:
                txt(d, (870, 1250), "BEEP!", 70, YEL, stroke=7)
        hud(lay, d, f)
    elif i == 5:
        if f < OFF2:
            label(lay, d, "Coffee hatao", "Thanda ho raha hai...", local, y=280, em="❄️")
        else:
            s = pop_s(f - OFF2, 6)
            txt(d, (W / 2, 250), "LED OFF", 140 * s, CYAN, stroke=12)
            if s > 0.9:
                tw = d.textlength("LED OFF", font=font(MONT, 140))
                lay.alpha_composite(e5.emoji("❄️", 100), (int(W / 2 + tw / 2 + 10), 195))
            tag(lay, d, (583, 1318), (800, 1000), "Blue LED", "Sab OK", ease((f - OFF2 - 4) / 10))
        hud(lay, d, f)
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
        if v > 0:                                                  # the whole logic in one card
            d.rounded_rectangle((90, 380, 90 + (W - 180) * v, 560), 30, fill=(12, 16, 24, 235), outline=CYAN + (255,), width=4)
            if v > 0.9:
                d.text((130, 430), "if (temp > setTemp)", font=font(MONO, 50), fill=(255, 190, 90), anchor="lm")
                d.text((170, 505), "digitalWrite(LED, HIGH);", font=font(MONO, 44), fill=(150, 255, 170), anchor="lm")
        v = ease((local - 12) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"TEMP\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
        w_ = ease((local - 20) / 8)
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
        for on in (ON1, ON2):                                      # punch-in + shake on LED ON
            a = f - on
            if 0 <= a < 10:
                z += 0.05 * (1 - a / 10) ** 2
                dx = 14 * np.sin(a * 2.5) * (1 - a / 10)
        for off in (OFF1, OFF2):
            a = f - off
            if 0 <= a < 8:
                z += 0.03 * (1 - a / 8) ** 2
        if z > 1.0 or dx:
            fr = zoom(fr, z, dx=dx)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        if SHOTS[1] > f or SHOTS[4] <= f < SHOTS[6]:
            if hot(f):                                             # pulsing red edge glow while HOT
                k_ = 0.16 + 0.08 * math.sin(f * 0.5)
                x = x * (1 - k_ * vig) + np.array(RED, np.float32) * k_ * vig
            elif f >= OFF2 and f - OFF2 < 30:                      # cool blue after LED OFF
                k_ = 0.2 * (1 - (f - OFF2) / 30)
                x = x * (1 - k_ * vig) + np.array(BLU, np.float32) * k_ * vig
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
