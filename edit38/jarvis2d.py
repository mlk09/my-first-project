#!/usr/bin/env python3
"""'Maine apna JARVIS bana liya!' - 22 s 2D neon motion-graphics short (ESP32-S3 + mic + speaker + round display
voice assistant). Everything is drawn with PIL: dark HUD room, glowing AI orb on the round display (idle pulse,
listening rings, thinking spinner, speaking waveform), zoom-out device reveal with part labels, WhatsApp-style
dialogue bubbles with typing, a room light that switches ON, a weather card, a funny refusal, CTA + Part 2 tease.
Sound: ambient pad, listen / done chimes, typing ticks, robot bleeps, light switch. All text in the safe zone.
Usage: python3 edit38/jarvis2d.py [preview FRAMES OUT]"""
import importlib.util
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
_spec = importlib.util.spec_from_file_location("b30", os.path.join(ROOT, "edit30", "build_short.py"))
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)
fx, e5, font, txt, pop_s, ease, head = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head
MONT, BOLD, INK, WHT, YEL, CYAN, GRN = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN
PINK, ORG = (255, 90, 200), (255, 150, 40)
W, H, FPS, SR = 1080, 1920, 24, 48000
N = 528
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "esp32-jarvis-ai-assistant-SHORT.mp4")
SCENES = [0, 48, 120, 252, 360, 456]
LIGHT_AT = 198
# dialogue: (scene start, user text, user emoji, jarvis text, jarvis emoji, user_at, think_at, reply_at)
DIALOG = [
    (120, "Jarvis, light on karo", "💡", "Ji Boss! Light ON", "✅", 126, 168, 182),
    (252, "Jarvis, aaj mausam kaisa hai?", "🌤️", "Boss, 24°C hai, halki thand", "🧥", 258, 296, 308),
    (360, "Jarvis, mera homework kar do", "📚", "Sorry Boss, ye main nahi karunga", "😏", 366, 400, 412),
]


def scene_of(f):
    i = max(j for j, s in enumerate(SCENES) if s <= f)
    return i, f - SCENES[i]


def t(f):
    return f / FPS


# ------------------------------------------------------------------ background
_BG = None


def background(f):
    global _BG
    if _BG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        base = np.zeros((H, W, 3), np.float32)
        base[..., 0] = 6 + 10 * (yy / H)
        base[..., 1] = 10 + 16 * (yy / H)
        base[..., 2] = 24 + 30 * (yy / H)
        for gx in range(0, W, 60):                                     # HUD grid
            base[:, gx:gx + 1] += (12, 30, 40)
        for gy in range(0, H, 60):
            base[gy:gy + 1, :] += (12, 30, 40)
        _BG = base
    x = _BG.copy()
    light = ease((f - LIGHT_AT) / 8)
    if light > 0:                                                    # warm room light after 'light on'
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        x = x + light * np.array((120, 90, 45), np.float32) * np.exp(-((yy - 300) / 900) ** 2) + light * 18
    return x


# ------------------------------------------------------------------ orb + device
def orb_state(f):
    for (s0, _, _, _, _, ua, ta, ra) in DIALOG:
        if ua <= f < ta:
            return "listen", f - ua
        if ta <= f < ra:
            return "think", f - ta
        if ra <= f < ra + 34:
            return "speak", f - ra
    return "idle", f


def draw_orb(lay, cx, cy, R, f):
    st, a = orb_state(f)
    col = {"idle": (60, 210, 255), "listen": (80, 255, 170), "think": (255, 200, 60), "speak": (60, 210, 255)}[st]
    glow = Image.new("RGBA", lay.size)
    gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - R * 1.08, cy - R * 1.08, cx + R * 1.08, cy + R * 1.08), fill=(14, 16, 22, 255), outline=(70, 76, 90, 255), width=int(R * 0.06))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(2, 6, 12, 255))
    pulse = 1 + 0.05 * math.sin(f * 0.25)
    rc = R * 0.42 * pulse
    for k in range(6, 0, -1):                                        # core
        rr = rc * k / 6
        c = tuple(int(v * (0.35 + 0.65 * (1 - k / 6))) for v in col)
        gd.ellipse((cx - rr * 1.5, cy - rr * 1.5, cx + rr * 1.5, cy + rr * 1.5), fill=c + (120,))
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=tuple(min(255, int(v * 0.6 + 100 * (1 - k / 6))) for v in col) + (255,))
    d.ellipse((cx - rc * 0.35, cy - rc * 0.35, cx + rc * 0.35, cy + rc * 0.35), fill=(255, 255, 255, 255))
    for j, (rf, sp, ext) in enumerate(((0.62, 2.2, 250), (0.74, -1.6, 200), (0.86, 1.1, 290))):   # HUD arcs
        r = R * rf
        a0 = f * sp + j * 70
        gd.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + ext, fill=col + (255,), width=int(R * 0.05))
        d.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + ext, fill=col + (255,), width=int(R * 0.018))
    if st == "listen":                                               # rings flowing inwards
        for k in range(3):
            r = R * (0.95 - ((a * 0.03 + k / 3) % 1) * 0.45)
            gd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col + (200,), width=int(R * 0.03))
    if st == "think":
        for k in range(8):
            ang = a * 0.35 + k * math.pi / 4
            r = R * 0.55
            s = R * 0.04 * (0.4 + 0.6 * ((k + a * 0.3) % 8) / 8)
            d.ellipse((cx + r * math.cos(ang) - s, cy + r * math.sin(ang) - s, cx + r * math.cos(ang) + s, cy + r * math.sin(ang) + s), fill=col + (255,))
    if st == "speak":                                                # radial waveform
        rng = np.random.default_rng(f)
        for k in range(48):
            ang = k * 2 * math.pi / 48
            amp = (0.08 + 0.18 * abs(math.sin(a * 0.6 + k * 0.7)) * rng.uniform(0.6, 1.0)) * R
            r0 = R * 0.66
            d.line((cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + (r0 + amp) * math.cos(ang), cy + (r0 + amp) * math.sin(ang)),
                   fill=col + (255,), width=int(R * 0.025))
    lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(R * 0.08)))
    lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(R * 0.025)))


def draw_device(lay, f, cx, cy, s):
    """Board under the round display: ESP32-S3, mic, speaker (s = scale)."""
    d = ImageDraw.Draw(lay)
    bw, bh = 760 * s, 330 * s
    x0, y0 = cx - bw / 2, cy + 230 * s
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 24 * s, fill=(18, 60, 40, 255), outline=(60, 140, 90, 255), width=max(2, int(6 * s)))
    for i in range(18):                                              # pins
        d.rectangle((x0 + 30 * s + i * 39 * s, y0 + 8 * s, x0 + 46 * s + i * 39 * s, y0 + 26 * s), fill=(220, 180, 60, 255))
        d.rectangle((x0 + 30 * s + i * 39 * s, y0 + bh - 26 * s, x0 + 46 * s + i * 39 * s, y0 + bh - 8 * s), fill=(220, 180, 60, 255))
    mx0 = cx - 150 * s
    d.rounded_rectangle((mx0, y0 + 70 * s, mx0 + 300 * s, y0 + 250 * s), 10 * s, fill=(200, 205, 215, 255))
    d.text((mx0 + 150 * s, y0 + 130 * s), "ESP32-S3", font=font(MONT, max(10, int(40 * s))), fill=(30, 34, 44, 255), anchor="mm")
    d.text((mx0 + 150 * s, y0 + 185 * s), "WiFi + AI", font=font(BOLD, max(8, int(26 * s))), fill=(70, 74, 90, 255), anchor="mm")
    lx = x0 + 70 * s                                                 # mic module
    d.rounded_rectangle((lx, y0 + 90 * s, lx + 120 * s, y0 + 230 * s), 10 * s, fill=(30, 40, 120, 255))
    d.ellipse((lx + 35 * s, y0 + 125 * s, lx + 85 * s, y0 + 175 * s), fill=(210, 215, 225, 255), outline=(40, 40, 50, 255), width=max(1, int(4 * s)))
    sx = x0 + bw - 190 * s                                           # speaker
    st, a = orb_state(f)
    vib = 4 * s * math.sin(f * 2.1) if st == "speak" else 0
    d.ellipse((sx, y0 + 70 * s, sx + 150 * s, y0 + 220 * s), fill=(30, 32, 38, 255), outline=(90, 95, 110, 255), width=max(2, int(6 * s)))
    d.ellipse((sx + 40 * s - vib, y0 + 110 * s - vib, sx + 110 * s + vib, y0 + 180 * s + vib), fill=(60, 64, 76, 255))
    for j in range(4):                                               # wires display <-> board
        d.line((cx - 60 * s + j * 40 * s, cy + 200 * s, cx - 60 * s + j * 40 * s, y0), fill=[(220, 60, 60), (240, 200, 40), (60, 200, 90), (60, 130, 255)][j] + (255,), width=max(2, int(8 * s)))
    return {"mic": (lx + 60 * s, y0 + 150 * s), "esp": (cx, y0 + 160 * s), "spk": (sx + 75 * s, y0 + 145 * s), "disp": (cx, cy)}


def tag(lay, d, anchor, box, text, sub, u, col=CYAN):
    b.tag(lay, d, anchor, box, text, sub, u, col)


# ------------------------------------------------------------------ bubbles
def bubble(lay, text, em, side, y, prog, f):
    """Chat bubble; prog 0..1 = pop + typing."""
    if prog <= 0:
        return
    d = ImageDraw.Draw(lay)
    fs = 44
    while fs > 26 and ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=font(MONT, fs)) + (70 if em else 0) > 820:
        fs -= 2
    fnt = font(MONT, fs)
    shown = text[: max(1, int(len(text) * min(1, prog * 1.6)))]
    full_w = d.textlength(text, font=fnt) + (70 if em else 0)
    bw = min(930, full_w + 90)
    s = pop_s(prog * 12, 5)
    if s <= 0.05:
        return
    if side == "user":
        x1 = W - 40
        x0 = x1 - bw * s
        fill, tcol, av = (37, 211, 102), INK, "🧑"
    else:
        x0 = 40
        x1 = x0 + bw * s
        fill, tcol, av = (16, 24, 36), WHT, "🤖"
    h = 110 * s
    shadow = Image.new("RGBA", lay.size)
    ImageDraw.Draw(shadow).rounded_rectangle((x0, y + 10, x1, y + h + 10), 40, fill=(0, 0, 0, 140))
    lay.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y, x1, y + h), 40, fill=fill + (245,), outline=(CYAN if side != "user" else WHT) + (255,), width=4)
    if s > 0.9:
        tx = x0 + 45
        d.text((tx, y + h / 2), shown, font=fnt, fill=tcol, anchor="lm")
        if em and len(shown) == len(text):
            lay.alpha_composite(e5.emoji(em, int(fs * 1.2)), (int(tx + d.textlength(text, font=fnt) + 12), int(y + h / 2 - fs * 0.62)))
        ax = x1 + 8 if side == "user" else x0 - 8
        ax = min(ax, W - 70) if side == "user" else ax
        av_img = e5.emoji(av, 64)
        lay.alpha_composite(av_img, (int(x1 - 74) if side == "user" else int(x0 + 6), int(y - 70)))


def weather_card(lay, f, f0):
    u = pop_s(f - f0, 7)
    if u <= 0.05:
        return
    d = ImageDraw.Draw(lay)
    cx, cy = W / 2, 400
    w_, h_ = 620 * u, 230 * u
    d.rounded_rectangle((cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2), 40, fill=(20, 40, 70, 235), outline=CYAN + (255,), width=5)
    if u > 0.9:
        lay.alpha_composite(e5.emoji("🌤️", 150), (int(cx - 280), int(cy - 78)))
        txt(d, (cx + 110, cy - 30), "24°C", 110, WHT, stroke=6)
        d.text((cx + 110, cy + 70), "Delhi • Halki thand", font=font(BOLD, 40), fill=(200, 225, 255), anchor="mm")


def bulb(lay, f):
    on = ease((f - LIGHT_AT) / 6)
    d = ImageDraw.Draw(lay)
    cx, cy = 165, 470
    d.line((cx, 330, cx, cy - 80), fill=(120, 120, 130, 255), width=6)
    if on > 0:
        g = Image.new("RGBA", lay.size)
        ImageDraw.Draw(g).ellipse((cx - 230, cy - 230, cx + 230, cy + 230), fill=(255, 210, 120, int(200 * on)))
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(70)))
    c = tuple(int(70 + (255 - 70) * on) for _ in range(1))[0]
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - 85, cy - 95, cx + 85, cy + 75), fill=(c, int(70 + 160 * on), int(70 + 60 * on), 255), outline=(200, 200, 210, 255), width=4)
    d.rectangle((cx - 45, cy + 70, cx + 45, cy + 120), fill=(150, 150, 160, 255))
    if on > 0.5:
        txt(d, (cx, cy + 170), "LIGHT ON", 44, YEL, stroke=5)


# ------------------------------------------------------------------ compose
def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🤖", 46), (W - 388, 46))


def frame(f):
    i, local = scene_of(f)
    im = Image.fromarray(np.clip(background(f), 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    # camera: big orb in the hook, zoom out for the device reveal, medium for the dialogue
    if i == 0:
        s, cy = 1.25 - 0.08 * ease(local / 48), 820
    else:
        s, cy = 1.17 - 0.52 * ease(local / 20), 820 - 60 * ease(local / 20)
    if i <= 1:
        R = 300 * s
        pts = draw_device(lay, f, W / 2, cy, s)
        draw_orb(lay, W / 2, cy, R, f)
    else:                                                            # dialogue: big orb only, bubbles below it
        cy = 690
        draw_orb(lay, W / 2, cy, 240, f)
    d = ImageDraw.Draw(lay)
    if i == 1:
        for j, (key, box, tx, sub) in enumerate((("disp", (W / 2 - 300, cy - 320), "Round Display", "= Chehra 😎"),
                                                   ("esp", (W / 2 + 230, cy + 560), "ESP32-S3", "= Dimaag"),
                                                   ("mic", (W / 2 - 300, cy + 560), "Mic", "= Kaan"),
                                                   ("spk", (W / 2 + 300, cy - 320), "Speaker", "= Awaaz"))):
            tag(lay, d, pts[key], box, tx, sub.replace(" 😎", ""), ease((local - 18 - j * 9) / 10))
    for (s0, ut, ue, jt, je, ua, ta, ra) in DIALOG:                 # dialogue bubbles
        if s0 <= f < s0 + (SCENES[SCENES.index(s0) + 1] - s0 if SCENES.index(s0) + 1 < len(SCENES) else 999):
            bubble(lay, ut, ue, "user", 1010, (f - ua) / 30, f)
            if f >= ta and f < ra:
                dd = ImageDraw.Draw(lay)
                for k in range(3):
                    yy = 1150 + 45 - 10 * abs(math.sin(f * 0.4 + k))
                    dd.ellipse((90 + k * 40, yy, 116 + k * 40, yy + 26), fill=CYAN + (255,))
            bubble(lay, jt, je, "jarvis", 1150, (f - ra) / 30, f)
    if i == 3:
        weather_card(lay, f, DIALOG[1][7])
    if i == 2:
        bulb(lay, f)
    # top shade + captions
    sh = Image.new("L", (1, H))
    sh.putdata([int(150 * max(0, 1 - y_ / 360)) for y_ in range(H)])
    top = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    top.putalpha(sh.resize((W, H)))
    im.alpha_composite(top)
    d = ImageDraw.Draw(lay)
    badge(lay, d)
    d = ImageDraw.Draw(lay)
    if i == 0:
        head(lay, d, "Maine apna JARVIS bana liya!", 175, 76, YEL, "🤖", 1 + 0.03 * math.sin(f * 0.6))
        head(lay, d, "ESP32 + ChatGPT AI", 275, 66, CYAN, "🧠")
    elif i == 1:
        head(lay, d, "Sirf ₹800 ka setup!".replace("₹", "Rs "), 200, 84, GRN, "😱", pop_s(local, 5))
    elif i == 2:
        head(lay, d, "Awaaz se light ON!", 200, 90, YEL, "💡", pop_s(local, 5))
    elif i == 3:
        head(lay, d, "ChatGPT wala smart jawab", 200, 78, CYAN, "🧠", pop_s(local, 5))
    elif i == 4:
        head(lay, d, "Jarvis bhi smart hai", 200, 88, PINK, "😂", pop_s(local, 5))
    else:
        head(lay, d, "Comment \"JARVIS\" = Code FREE", 190, 70, YEL, "👇", pop_s(local, 5))
        v = ease((local - 8) / 8)
        if v > 0:
            bw = int(860 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 300, W / 2 + bw / 2, 400), 50, fill=(130, 60, 255, 255))
            if v > 0.9:
                d.text((W / 2, 350), "Part 2: Jarvis se Robot chalayenge", font=font(MONT, 42), fill=WHT, anchor="mm")
        u = pop_s(local - 22, 6)
        if u > 0.05:
            pw = 1 + 0.06 * math.sin(f * 0.5)
            bw2, bh2 = 520 * u * pw, 120 * u * pw
            d.rounded_rectangle((W / 2 - bw2 / 2, 1180 - bh2 / 2, W / 2 + bw2 / 2, 1180 + bh2 / 2), 60, fill=(230, 30, 40, 255))
            if u > 0.9:
                d.text((W / 2 + 30, 1180), "SUBSCRIBE", font=font(MONT, 56), fill=WHT, anchor="mm")
                lay.alpha_composite(e5.emoji("🔔", 64).rotate(20 * math.sin(f * 0.8), resample=Image.BICUBIC), (int(W / 2 - 230), 1148))
    im.alpha_composite(lay)
    out = np.array(im.convert("RGB"))
    for s_ in SCENES[1:]:                                              # quick zoom punch on cuts
        a = f - s_
        if 0 <= a < 5:
            out = b.zoom(out, 1 + 0.05 * (1 - a / 5) ** 2)
    b.rainbow_bar(out, int(W * (f + 1) / N))
    return out


# ------------------------------------------------------------------ audio
def beep(freq, dur, vol=0.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * tt) * np.minimum(1, tt / 0.004) * np.minimum(1, (dur - tt) / 0.02) * vol


def pad(total):
    n = int(total * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    chords = [(110, 164.8, 220, 277.2), (98, 146.8, 196, 246.9), (87.3, 130.8, 174.6, 220), (98, 146.8, 196, 293.7)]
    for ci, ch in enumerate(chords * 3):
        t0 = ci * 2.0
        if t0 > total:
            break
        m = int(min(2.6, total - t0) * SR)
        u = np.arange(m) / SR
        env = np.minimum(1, u / 0.6) * np.minimum(1, (u[-1] - u) / 0.6)
        seg = sum(np.sin(2 * np.pi * fr * u) + 0.3 * np.sin(2 * np.pi * fr * 2.003 * u) for fr in ch) * env * 0.08
        i0 = int(t0 * SR)
        out[i0:i0 + m] += seg[: n - i0]
    k = int(60 / 100 * SR)                                              # soft pulse
    for i0 in range(0, n, k):
        m = min(int(0.12 * SR), n - i0)
        out[i0:i0 + m] += np.sin(2 * np.pi * 55 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 20) * 0.5
    return fx.filt(out, "lowpass", 3000)


def bleeps(n_notes, seed):
    rng = np.random.default_rng(seed)
    return np.concatenate([beep(rng.choice([880, 988, 1175, 1319, 1568, 1760]), 0.06, 0.25) for _ in range(n_notes)])


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), pad(total + 0.05))
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.7 * SR)], 0.0, 0.5)
    P(buf, fx.riser(0.6), 0.0, 0.25)
    for s_ in SCENES[1:]:
        P(buf, fx.whoosh(0.3, s_) * 0.6, max(0, t(s_) - 0.15), 0.4)
    for (s0, ut, ue, jt, je, ua, ta, ra) in DIALOG:
        P(buf, fx.pop(), t(ua), 0.35)
        for k in range(len(ut) // 2):
            P(buf, b.detent_click() * 0.5, t(ua) + k * 0.035, 0.25)
        P(buf, np.concatenate([beep(1320, 0.07, 0.4), beep(1760, 0.1, 0.4)]), t(ua + 6), 0.45)      # listening chime
        P(buf, np.concatenate([beep(1760, 0.07, 0.4), beep(2349, 0.12, 0.4)]), t(ra), 0.5)          # answer chime
        P(buf, bleeps(10, s0), t(ra) + 0.15, 0.35)
        P(buf, fx.pop(), t(ra), 0.35)
    P(buf, b.detent_click(), t(LIGHT_AT), 0.9)
    P(buf, fx.boom()[: int(0.4 * SR)] * 0.6, t(LIGHT_AT), 0.4)
    P(buf, b.fanfare8()[: int(0.9 * SR)] * 0.5, t(SCENES[5]), 0.4)
    P(buf, fx.ding(), t(SCENES[5] + 22), 0.5)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf)
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    for f in range(N):
        enc.stdin.write(np.ascontiguousarray(frame(f)).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        fs = [int(v) for v in sys.argv[2].split(",")]
        ims = [Image.fromarray(frame(f)).resize((360, 640)) for f in fs]
        c = Image.new("RGB", (360 * len(ims), 640))
        for k_, im_ in enumerate(ims):
            c.paste(im_, (k_ * 360, 0))
        c.save(sys.argv[3])
    else:
        build_audio()
        build_video()
