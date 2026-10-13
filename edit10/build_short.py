#!/usr/bin/env python3
"""16 s (+2.5 s outro) 'ESP32 + OLED over I2C' short, same house style as the door-lock / robot
shorts: OLED wakes up with HELLO! in the first 1.5 s, callout tags on the board, live SCL/SDA
waveform panel, address-scan payoff (MIL GAYA 0x3C), packet chips synced to the OLED, demo shot,
end card + Like / Share / Subscribe outro. Original music + data chirps while the bus is busy.
Usage: python3 edit10/build_short.py [audio] [video]
"""
import importlib.util
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
from timeline import FPS, N, SHOTS, BOOT, SCAN, FOUND, PACKET, PKT0, PKT_STEP, ADDR, busy, scan_addr, packet_step, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-oled-i2c-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
GRN, RED, ORG = (40, 230, 110), (255, 60, 60), (255, 140, 30)
SDA_C, SCL_C = (80, 150, 255), (255, 210, 40)
HELLO = 30                        # HELLO! appears on the OLED
OUTRO = 60
TOTAL = N + OUTRO
BTN_POP = (4, 10, 16)
BTN_PRESS = (24, 35, 46)


def font(p, s):
    return ImageFont.truetype(p, max(8, int(s)))


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


def t(f):
    return f / FPS


def beep(freq, dur, square=False):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * tt)) * 0.5 if square else np.sin(2 * np.pi * freq * tt)
    return x * np.minimum(1, tt / 0.003) * np.minimum(1, (dur - tt) / 0.01) * 0.6


def ok_beep():
    return np.concatenate([beep(2700, 0.09), np.zeros(int(0.04 * SR)), beep(3600, 0.16)])


def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
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
    lay.alpha_composite(e5.emoji("📟", 46), (W - 388, 46))


def zoom(fr, z, cx=W / 2, cy=H / 2, dx=0.0):
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    M[0, 2] += dx
    return cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


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
def chirp(seed):
    n = int(0.03 * SR)
    tt = np.arange(n) / SR
    f0 = 2400 + 900 * ((seed * 7919) % 5)
    return np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 140) * 0.5


def music(total):
    """116 BPM techy pluck groove; drop arrives when HELLO! hits the screen."""
    bpm, n = 116, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0],
              [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 392.0]]
    roots = [65.4, 55.0, 43.7, 49.0]
    kick = fx.kick() * 0.55
    drop = t(HELLO)
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        full = t0 >= drop - 0.05
        for s in range(4 if full else 2):
            fx.place(mel, fx.synth_note(ch[(pos * 2 + s) % 4] * 2, beat / 4 * 1.6, "square" if s % 2 else "tri", 10, 3000),
                     t0 + s * beat / (4 if full else 2), 0.1)
        if full:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 240), t0, 0.7)
            fx.place(drums, kick, t0, 0.85)
            if pos in (1, 3):
                fx.place(drums, fx.clap(), t0, 0.3)
        for s in range(4 if full else 2):
            fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / (4 if full else 2), 0.06 if full else 0.03)
        b += 1
    mix = mel + bass + drums
    i = int(drop * SR)
    mix[:i] = fx.filt(mix[:i], "lowpass", 1000)
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.35), 0.0, 0.35)
    P(buf, np.concatenate([beep(1320, 0.07), beep(1980, 0.12)]), t(BOOT), 0.45)          # OLED wakes
    P(buf, fx.boom()[: int(0.5 * SR)], t(HELLO), 0.45)
    for k_ in range(6):
        P(buf, fx.pop(), t(HELLO + 2 * k_), 0.18)                                          # letters type on
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for s in (SHOTS[1], SHOTS[2], SHOTS[5]):
        P(buf, fx.pop(), t(s + 4), 0.25)
    for f in range(0, N, 2):                                                                # data chirps
        if busy(f) and not (SCAN[0] <= f < FOUND):
            P(buf, chirp(f), t(f), 0.12)
    prev = -1
    for f in range(SCAN[0], FOUND + 1):                                                     # scan ticks
        a = scan_addr(f)
        if a != prev:
            P(buf, beep(900 + a * 12, 0.025), t(f), 0.2)
            prev = a
    P(buf, ok_beep(), t(FOUND), 0.55)
    P(buf, fx.ding(), t(FOUND + 2), 0.45)
    for i in range(len(PACKET)):
        P(buf, fx.pop(), t(PKT0 + i * PKT_STEP), 0.3)
        P(buf, beep(700 + 180 * i, 0.06), t(PKT0 + i * PKT_STEP), 0.25)
    P(buf, fx.ding(), t(SHOTS[6] + 14), 0.4)
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(N) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(N + a), 0.35)
    for a in BTN_PRESS:
        P(buf, ok_beep()[: int(0.09 * SR)] * 0.6, t(N + a), 0.4)
    P(buf, fx.ding(), t(N + BTN_PRESS[2] + 1), 0.5)
    return buf


# ================================================================== graphics
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


def wave_panel(d, f, y0=1330):
    """Live SCL (clock) + SDA (data) waveform, scrolling while the bus is busy."""
    d.rounded_rectangle((60, y0, W - 60, y0 + 330), 30, fill=(8, 12, 18, 210), outline=(60, 220, 255, 180), width=3)
    d.text((100, y0 + 40), "I2C BUS (live)", font=font(BOLD, 32), fill=(190, 200, 220), anchor="lm")
    rows = (("SCL", SCL_C, y0 + 140), ("SDA", SDA_C, y0 + 255))
    bits = [int(c) for c in f"{ADDR:07b}0" "1" "10100101"]
    x0, x1 = 200, W - 100
    shift = (f * 6) % 80 if busy(f) else 0
    for name, col, yc in rows:
        d.text((110, yc), name, font=font(MONT, 40), fill=col, anchor="mm")
        pts = []
        for i in range(-1, 14):
            xa = x0 + i * 60 - shift
            if name == "SCL":
                seq = [(xa, 1), (xa + 30, 1), (xa + 30, 0), (xa + 60, 0)] if busy(f) else [(xa, 1), (xa + 60, 1)]
            else:
                b = bits[(i + (f // 2 if busy(f) else 0)) % len(bits)] if busy(f) else 1
                seq = [(xa, b), (xa + 60, b)]
            for x, v in seq:
                if x0 <= x <= x1:
                    pts.append((x, yc + 30 - v * 60))
        if len(pts) > 1:
            d.line(pts, fill=col, width=6)


def packet_chips(d, f, y0=1380):
    st = packet_step(f)
    info = ["SDA girta hai = Start", f"0x{ADDR:02X} + Write", "OLED: 'Haan, main hoon!'", "Pixel data bytes", "SDA uthta hai = Stop"]
    cols = [(255, 120, 60), CYAN, GRN, (200, 120, 255), (255, 80, 120)]
    w_ = (W - 140) / 5
    for i, name in enumerate(PACKET):
        x0 = 70 + i * w_
        on = i <= st
        s = pop_s(f - PKT0 - i * PKT_STEP, 5) if on else 0
        d.rounded_rectangle((x0 + 6, y0, x0 + w_ - 6, y0 + 110), 22,
                            fill=(cols[i] + (240,)) if on else (30, 34, 46, 220), outline=WHT if i == st else None, width=4)
        d.text((x0 + w_ / 2, y0 + 55), name, font=font(MONT, 34 * max(0.6, min(1.15, s)) if on else 34),
               fill=INK if on else (120, 130, 150), anchor="mm")
    if st >= 0:
        d.rounded_rectangle((70, y0 + 140, W - 70, y0 + 230), 30, fill=(8, 12, 18, 210))
        d.text((W / 2, y0 + 185), info[st], font=font(BOLD, 46), fill=WHT, anchor="mm")


# ================================================================== overlay
TAGS = {   # shot-1 anchors (top-down wide), measured on the render
    "esp": ((250, 980), (260, 1500), "ESP32", "DevKit V1"),
    "oled": ((780, 980), (800, 1500), "1.3\" OLED", "SH1106 · I2C"),
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
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Sirf 2 wire se...", 76 * s, WHT, stroke=8)
        s2 = pop_s(f - HELLO, 6)
        if s2 > 0:
            txt(d, (W / 2, 380), "OLED ON!", 124 * s2, YEL, stroke=11)
            if s2 > 0.9:
                tw = d.textlength("OLED ON!", font=font(MONT, 124))
                lay.alpha_composite(e5.emoji("🤯", 110), (int(W / 2 + tw / 2 + 10), 320))
        v = ease((local - 34) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 330, 1620, W / 2 + 330, 1720), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1670), "ESP32 + OLED (I2C)", font=font(MONT, 46), fill=INK, anchor="mm")
    elif i == 1:
        label(lay, d, "4 wire ka setup", None, local, y=300, em="🔌")
        for j, key in enumerate(("esp", "oled")):
            a, b, tx, sub = TAGS[key]
            tag(lay, d, a, b, tx, sub, ease((local - 6 - j * 8) / 10))
    elif i == 2:
        txt(d, (W / 2, 250), "SDA = Data", 80 * pop_s(local - 2), SDA_C, stroke=8)
        txt(d, (W / 2, 360), "SCL = Clock", 80 * pop_s(local - 10), SCL_C, stroke=8)
        wave_panel(d, f)
    elif i == 3:
        if f < FOUND:
            label(lay, d, "Address scan...", None, local, y=300, em="🔍")
        else:
            s = pop_s(f - FOUND, 7)
            txt(d, (W / 2, 300), "MIL GAYA! 0x3C", 104 * s, GRN, stroke=10)
            if s > 0.9:
                lay.alpha_composite(e5.emoji("✅", 96), (W // 2 - 48, 370))
        wave_panel(d, f)
    elif i == 4:
        label(lay, d, "Ek I2C message", "5 hisson mein", local, y=300, em="📨")
        packet_chips(d, f)
    elif i == 5:
        label(lay, d, "2 wire, poora display!", "Ek hi bus pe kai devices", local, y=300, em="⚡")
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y_ / 700)) for y_ in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + Wiring FREE", 80 * s, WHT, stroke=8)
        corner_frame(d, (70, 130, W - 70, 310), local / 8, w=9, L=130)
        v = ease((local - 10) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"OLED\" — bhej dunga", font=font(MONT, 48), fill=INK, anchor="mm")
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
            fr[0:10, :] = CYAN
            enc.stdin.write(np.ascontiguousarray(fr).tobytes())
            continue
        fr = load3d(f)
        z = 1.0
        for ev, amt in ((HELLO, 0.05), (FOUND, 0.05), (BOOT, 0.03)):
            a = f - ev
            if 0 <= a < 8:
                z += amt * (1 - a / 8) ** 2
        for i_ in range(len(PACKET)):
            a = f - PKT0 - i_ * PKT_STEP
            if 0 <= a < 5:
                z += 0.02 * (1 - a / 5)
        if z > 1.0:
            fr = zoom(fr, z)
        x = fr.astype(np.float32) * (1 - 0.25 * vig)
        for ev, col in ((HELLO, CYAN), (FOUND, GRN)):
            a = f - ev
            if 0 <= a < 6:
                x += (np.array(col, np.float32) * 0.6 + 100 - x) * 0.28 * (1 - a / 6)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:
            dd = f - s
            if -3 <= dd < 4:
                k_ = 1 - abs(dd + 0.5) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / TOTAL)
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        fr[0:10, :p // 2] = SDA_C
        fr[0:10, p // 2:p] = SCL_C
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
