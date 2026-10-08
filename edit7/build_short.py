#!/usr/bin/env python3
"""14 s 'ESP32 + App = Tap to Light' short. Reference style (satisfying phone tap -> real LED,
clean product shots, crisp tap/ping ASMR sounds, corner logo) pushed further: hook payoff in
the first second, punch-in on every tap, LED bloom, colour-word pops, party-mode beat drop,
blur-zoom cuts, rainbow progress bar, end card CTA. Original music + SFX synced to TAPS.
Usage: python3 edit7/build_short.py [audio] [video]
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
from timeline import FPS, N, SHOTS, TAPS, PARTY, POWER_ON, CONNECT, COLORS, leds, ease  # noqa: E402

_spec = importlib.util.spec_from_file_location("e5b", os.path.join(ROOT, "edit5", "build_short.py"))
e5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5)

WORK = os.path.join(HERE, "work")
F3D = os.path.join(WORK, "frames3d")
OUT = os.path.join(HERE, "output", "esp32-tap-to-light-SHORT.mp4")
W, H, SR = 1080, 1920, 48000
MONT = os.path.join(ROOT, "edit", "assets", "fonts", "Montserrat-Black.ttf")
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
WHT, YEL, INK, CYAN = (255, 255, 255), (255, 214, 10), (15, 18, 26), (60, 220, 255)
LEDC = [(255, 70, 60), (255, 200, 40), (60, 235, 110), (70, 150, 255)]
NOTES = [523.3, 659.3, 784.0, 1046.5]           # C5 E5 G5 C6: one note per LED colour


def font(p, s):
    return ImageFont.truetype(p, max(8, int(s)))


def shot_of(f):
    i = max(j for j, s in enumerate(SHOTS) if s <= f)
    return i, f - SHOTS[i]


def t(f):
    return f / FPS


# ================================================================== audio
def tap():
    n = int(0.04 * SR)
    tt = np.arange(n) / SR
    x = fx.filt(fx.noise(n, 11), "bandpass", [2000, 9000]) * np.exp(-tt * 180)
    return x + np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 120) * 0.4


def pling(freq):
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * m * tt) * np.exp(-tt * d) for m, a, d in ((1, 1, 5), (2, 0.35, 9), (3, 0.15, 14)))
    return x * np.minimum(1, tt / 0.002) * 0.5


def thump():
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)
    hum = np.sin(2 * np.pi * 100 * tt) * 0.15 * np.exp(-tt * 6)
    return np.tanh(1.5 * x) + hum


def music(total):
    """120 BPM minor pluck groove; sparse until the party drop, full kit + saw stabs in party mode."""
    bpm, n = 120, int(total * SR)
    beat = 60 / bpm
    mel, drums, bass = np.zeros(n), np.zeros(n), np.zeros(n)
    chords = [[220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6],
              [196.0, 246.9, 293.7, 392.0], [164.8, 207.7, 246.9, 329.6]]
    roots = [55.0, 43.7, 49.0, 41.2]
    kick = fx.kick() * 0.55
    p0, p1 = t(PARTY[0]), t(PARTY[1])
    b = 0
    while b * beat < total:
        t0 = b * beat
        bar, pos = divmod(b, 4)
        ch = chords[bar % 4]
        party = p0 <= t0 < p1 + 0.2
        for s in range(2):
            fx.place(mel, fx.synth_note(ch[(pos * 2 + s) % 4] * 2, beat / 2 * 1.6, "tri", 8, 3500), t0 + s * beat / 2, 0.16)
        if party:
            fx.place(mel, fx.synth_note(ch[0] * 2, beat * 0.4, "saw", 9, 2600), t0 + beat / 2, 0.13)
        if t0 > 0.4:
            fx.place(bass, fx.synth_note(roots[bar % 4], beat * 0.9, "tri", 3, 240), t0, 0.7 if party else 0.5)
        if t0 > 0.4 and (party or pos in (0, 2)):
            fx.place(drums, kick, t0, 0.9 if party else 0.7)
        if party and pos in (1, 3):
            fx.place(drums, fx.clap(), t0, 0.35)
        for s in range(4 if party else 2):
            fx.place(drums, fx.hat(b * 4 + s), t0 + s * beat / (4 if party else 2), 0.06)
        b += 1
    mix = mel + bass + drums
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.9


def sfx_track(total):
    buf = np.zeros(int(total * SR))
    P = fx.place
    P(buf, fx.riser(0.5), 0.0, 0.5)                                  # shimmer into the first tap
    for s in SHOTS[1:]:
        P(buf, fx.whoosh(0.3, s) * 0.6, max(0, t(s) - 0.18), 0.4)
    for s in SHOTS[1:6]:
        P(buf, fx.pop(), t(s + 4), 0.25)                             # label pop
    for f, b in TAPS:
        P(buf, tap(), t(f), 0.9)
        on = leds(f + 3)
        if b == "ALL":
            for i in range(4):
                P(buf, pling(NOTES[i]), t(f + 2) + i * 0.035, 0.45)
            P(buf, fx.boom()[: int(0.6 * SR)], t(f + 2), 0.5 if f < 50 else 0.3)
        elif b == "OFF":
            P(buf, pling(330) * 0.6, t(f + 2), 0.35)
        elif b == "CONNECT":
            P(buf, e5.notify(), t(CONNECT[1]), 0.5)
        elif isinstance(b, int):
            P(buf, pling(NOTES[b] if on[b] else NOTES[b] / 2), t(f + 2), 0.55 if on[b] else 0.3)
    P(buf, thump(), t(POWER_ON), 0.7)                                # USB power on
    P(buf, fx.riser(t(PARTY[0]) - t(PARTY[0] - 14)), t(PARTY[0] - 14), 0.6)
    P(buf, fx.boom(), t(PARTY[0] + 2), 0.8)                          # party drop
    for f in range(PARTY[0] + 2, PARTY[1] + 2, 3):
        st = leds(f)
        if any(st) and st != leds(f - 1):
            P(buf, pling(NOTES[st.index(True)] * 2) * 0.5, t(f), 0.18)
    P(buf, fx.ding(), t(SHOTS[6] + 10), 0.4)
    return buf


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = N / FPS
    fx.write_wav(os.path.join(WORK, "music.wav"), music(total + 0.05))
    fx.write_wav(os.path.join(WORK, "sfx.wav"), sfx_track(total + 0.05))
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


# ================================================================== video
def load3d(f):
    im = cv2.imread(os.path.join(F3D, f"{f:04d}.png"))
    if im is None:
        im = cv2.imread(os.path.join(F3D, f"{max(0, f - 1):04d}.png"))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    im = cv2.addWeighted(im, 1.25, cv2.GaussianBlur(im, (0, 0), 1.6), -0.25, 0)
    x = im.astype(np.float32) / 255
    sat = x.max(2, keepdims=True) - x.min(2, keepdims=True)
    bright = x * np.clip((x.max(2, keepdims=True) - 0.6) / 0.3, 0, 1) * np.clip(sat / 0.3, 0, 1)
    sm = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    x += cv2.resize(cv2.GaussianBlur(sm, (0, 0), 6), (W, H)) * 0.6
    x += cv2.resize(cv2.GaussianBlur(sm, (0, 0), 22), (W, H)) * 0.45
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def txt(d, xy, s, size, fill, f=MONT, stroke=None, anchor="mm"):
    d.text(xy, s, font=font(f, size), fill=fill, anchor=anchor,
           stroke_width=stroke if stroke is not None else max(4, int(size) // 10), stroke_fill=(0, 0, 0))


def pop_s(age, dur=8):
    """0 -> overshoot -> 1 scale for text pops."""
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
    """Corner logo like the reference's, our own: channel pill top-right."""
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("💡", 46), (W - 388, 46))


def overlay(fr, f):
    i, local = shot_of(f)
    im = Image.fromarray(fr).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    if i < 6:
        g = Image.new("L", (1, H))
        g.putdata([int(150 * max(0, 1 - y / 560)) for y in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
    badge(lay, d)
    if i == 0:
        s = pop_s(local, 6)
        txt(d, (W / 2, 250), "Phone pe TAP karo...", 66 * s, WHT, stroke=7)
        s2 = pop_s(local - 15, 7)
        if s2 > 0:
            txt(d, (W / 2, 370), "LED ON!", 130 * s2, YEL, stroke=11)
            if s2 > 0.9:
                tw = d.textlength("LED ON!", font=font(MONT, 130))
                lay.alpha_composite(e5.emoji("💡", 110), (int(W / 2 + tw / 2 + 20), 310))
                lay.alpha_composite(e5.emoji("📱", 100), (int(W / 2 - tw / 2 - 120), 315))
        v = ease((local - 24) / 8)
        if v > 0:
            d.rounded_rectangle((W / 2 - 330, 1590, W / 2 + 330, 1690), 50, fill=(255, 255, 255, int(235 * v)))
            d.text((W / 2, 1640), "ESP32 + MIT App Inventor", font=font(MONT, 44), fill=INK, anchor="mm")
    elif i == 1:
        corner_frame(d, (140, 560, 940, 1240), (local - 2) / 8)
        label(lay, d, "ESP32", "WiFi + Bluetooth wala dimaag", local, em="🧠")
        if f >= POWER_ON:
            v = pop_s(f - POWER_ON, 6)
            txt(d, (W / 2, 420), "POWER ON", 70 * v, (255, 90, 80), stroke=7)
    elif i == 2:
        if f < CONNECT[1]:
            label(lay, d, "Apni App", "MIT App Inventor · drag & drop", local, y=1620, em="📱")
        else:
            s = pop_s(f - CONNECT[1], 7)
            d.rounded_rectangle((W / 2 - 380 * s, 1560, W / 2 + 380 * s, 1700), 70, fill=(30, 180, 90, 240))
            if s > 0.8:
                d.text((W / 2, 1630), "Bluetooth Connected", font=font(MONT, 50), fill=WHT, anchor="mm")
                lay.alpha_composite(e5.emoji("✅", 80), (int(W / 2 + 390), 1590))
    elif i == 3:
        label(lay, d, "1 TAP = 1 LED", None, local, y=230)
        for ft, b in TAPS:
            if isinstance(b, int) and SHOTS[3] <= ft <= f < ft + 13 + (14 if b == 3 else 0):
                s = pop_s(f - ft - 2, 5)
                txt(d, (W / 2, 1560), COLORS[b], 150 * s, LEDC[b], stroke=12)
    elif i == 4:
        label(lay, d, "Bluetooth Signal", "Phone → ESP32 → LED, wire nahi", local, y=300, em="⚡")
    elif i == 5:
        s = pop_s(f - PARTY[0] - 2, 6)
        if s > 0:
            c = LEDC[(f // 3) % 4]
            txt(d, (W / 2, 300), "PARTY MODE", 120 * s, c, stroke=11)
            if s > 0.9:
                lay.alpha_composite(e5.emoji("🎉", 110), (W // 2 - 55, 400))
    else:
        g = Image.new("L", (1, H))
        g.putdata([int(200 * max(0, 1 - y / 700)) for y in range(H)])
        lay.paste((0, 0, 0, 255), mask=g.resize((W, H)))
        badge(lay, d)
        s = pop_s(local, 7)
        txt(d, (W / 2, 220), "Code + App FREE", 92 * s, WHT, stroke=8)
        corner_frame(d, (90, 130, W - 90, 310), local / 8, w=9, L=130)
        v = ease((local - 8) / 8)
        if v > 0:
            bw = int(920 * v)
            d.rounded_rectangle((W / 2 - bw / 2, 1540, W / 2 + bw / 2, 1690), 75, fill=YEL)
            if v > 0.9:
                d.text((W / 2, 1615), "Comment \"LED\" — bhej dunga", font=font(MONT, 50), fill=INK, anchor="mm")
        w_ = ease((local - 16) / 8)
        if w_ > 0:
            txt(d, (W / 2, 1780), "Follow @The IOT Engineer", 54, WHT, stroke=5)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def zoom(fr, z, cx=W / 2, cy=H / 2):
    M = cv2.getRotationMatrix2D((cx, cy), 0, z)
    return cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2).clip(0, 1)[..., None].astype(np.float32)
    for f in range(N):
        fr = load3d(f)
        z = 1.0
        for ft, b in TAPS:                                         # punch-in on every tap
            a = f - ft - 2
            if 0 <= a < 8:
                z += 0.04 * (1 - a / 8) ** 2
        if PARTY[0] + 2 <= f < PARTY[1] + 2 and leds(f) != leds(f - 1):
            z += 0.02
        if z > 1.0:
            fr = zoom(fr, z)
        x = fr.astype(np.float32)
        if PARTY[0] + 2 <= f < PARTY[1] + 2:                       # coloured edge glow in party mode
            st = leds(f)
            c = np.array(LEDC[st.index(True)] if any(st) else (255, 255, 255), np.float32)
            x = x * (1 - 0.35 * vig) + c * 0.35 * vig
        else:
            x *= 1 - 0.25 * vig
        for ft, b in TAPS:                                         # flash on ALL ON / party drop
            a = f - ft - 2
            if b in ("ALL", "PARTY") and 0 <= a < 4:
                x += (255 - x) * 0.35 * (1 - a / 4)
        fr = overlay(np.clip(x, 0, 255).astype(np.uint8), f)
        for s in SHOTS[1:]:                                        # blur-zoom cut
            dd = f - s
            if -3 <= dd < 4:
                k_ = 1 - abs(dd + 0.5) / 4
                fr = zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 22 * k_), 1 + 0.06 * k_)
        p = int(W * (f + 1) / N)                                   # rainbow progress bar
        fr[0:10, :] = (fr[0:10, :] * 0.4).astype(np.uint8)
        for j in range(4):
            fr[0:10, j * W // 4: min(p, (j + 1) * W // 4)] = LEDC[j]
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
        if f % 48 == 0:
            print(f"  frame {f}/{N}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["audio", "video"]
    if "audio" in steps:
        build_audio()
    if "video" in steps:
        build_video()
