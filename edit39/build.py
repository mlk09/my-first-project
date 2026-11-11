#!/usr/bin/env python3
"""Re-cut of the user's final JARVIS video (VN edit, 16.6 s) into a clearer 18 s short: keeps the user's
thumbnail intro and footage, removes the style-glitch and the long wait before the weather answer, covers the
small / garbled burned-in captions with one clean step header ('Bolo: ...', 'Light ON ho gayi!'), adds big
speaker subtitles ('Tum: ...' / 'Jarvis: ...') inside the safe zone, and ends with the Like / Share / big
pulsing SUBSCRIBE page. Audio: the user's soundtrack, re-cut to match, over a soft pad, + end-page SFX.
Usage: python3 edit39/build.py [preview FRAMES OUT]"""
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
_spec = importlib.util.spec_from_file_location("b31", os.path.join(ROOT, "edit31", "build.py"))
b31 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b31)
b = b31.b
fx, e5, font, txt, pop_s, ease, head = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease, b.head
MONT, BOLD, INK, WHT, YEL, CYAN, GRN = b.MONT, b.BOLD, b.INK, b.WHT, b.YEL, b.CYAN, b.GRN
W, H, FPS, SR = 1080, 1920, 24, 48000
SRC = os.path.join(HERE, "work", "src")
WORK = os.path.join(HERE, "work")
SRC_MP4 = os.path.join(HERE, "assets", "user_final.mp4")
OUT = os.path.join(HERE, "output", "esp32-jarvis-final-SHORT.mp4")
# (src first frame, src last frame) kept in order; ("hold", n) freezes the previous frame
CUTS = [(1, 36), (47, 145), (146, 215), (216, 262), (330, 399), ("hold", 24)]
OUTRO = 86


def build_map():
    m = []
    for c in CUTS:
        if c[0] == "hold":
            m += [m[-1]] * c[1]
        else:
            m += list(range(c[0], c[1] + 1))
    return m


MAP = build_map()
CLIP = len(MAP)
TOTAL = CLIP + OUTRO                                  # 432 = 18 s


def seg_start(i):
    return sum((c[1] - c[0] + 1) if c[0] != "hold" else c[1] for c in CUTS[:i])


S_SETUP, S_LIGHT, S_WQ, S_WA = seg_start(1), seg_start(2), seg_start(3), seg_start(4)
REPLY_LIGHT = S_LIGHT + (181 - 146)                   # 'Ji Boss! Light ON' bubble in the source
REPLY_WEATHER = S_WA + (361 - 330)                    # weather card appears


def header(lay, d, f):
    """Clean step header over the burned-in captions."""
    if f < S_SETUP:
        return
    g = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(g)
    gd.rectangle((0, 0, W, 360), fill=(4, 8, 14, 235))
    lay.alpha_composite(g)
    for y in range(360, 410):
        ImageDraw.Draw(lay).line((0, y, W, y), fill=(4, 8, 14, int(235 * (1 - (y - 360) / 50))))
    d = ImageDraw.Draw(lay)
    if f < S_SETUP + 60:
        head(lay, d, "Maine apna JARVIS bana liya!", 190, 74, YEL, "🤖", pop_s(f - S_SETUP, 5))
        head(lay, d, "ESP32 + ChatGPT AI", 285, 60, CYAN, "🧠", pop_s(f - S_SETUP - 6, 5))
    elif f < S_LIGHT:
        head(lay, d, "Mic + Speaker + Display", 190, 70, WHT, "🎤", pop_s(f - S_SETUP - 60, 5))
        head(lay, d, "Sirf Rs 800 ka setup!", 285, 64, GRN, "😱", pop_s(f - S_SETUP - 66, 5))
    elif f < REPLY_LIGHT:
        head(lay, d, "Bolo: \"Jarvis, light on karo\"", 200, 66, YEL, "🗣️", pop_s(f - S_LIGHT, 5))
        d.text((W / 2, 290), "Test 1: Awaaz se light", font=font(BOLD, 44), fill=(200, 210, 230), anchor="mm")
    elif f < S_WQ:
        head(lay, d, "Light ON ho gayi!", 210, 96, YEL, "💡", pop_s(f - REPLY_LIGHT, 5))
    elif f < REPLY_WEATHER:
        head(lay, d, "Bolo: \"Aaj mausam kaisa hai?\"", 200, 64, YEL, "🗣️", pop_s(f - S_WQ, 5))
        d.text((W / 2, 290), "Test 2: ChatGPT se sawaal", font=font(BOLD, 44), fill=(200, 210, 230), anchor="mm")
    else:
        head(lay, d, "Jarvis ne bataya: 24°C", 210, 82, CYAN, "🌤️", pop_s(f - REPLY_WEATHER, 5))


def subtitle(lay, f):
    """Big speaker subtitle (who is talking) just above the Shorts title area."""
    if S_LIGHT <= f < REPLY_LIGHT:
        who, line, col, em, f0 = "Tum", "Jarvis, light on karo", (37, 211, 102), "🧑", S_LIGHT
    elif REPLY_LIGHT <= f < S_WQ:
        who, line, col, em, f0 = "Jarvis", "Ji Boss! Light ON", (60, 200, 255), "🤖", REPLY_LIGHT
    elif S_WQ <= f < REPLY_WEATHER:
        who, line, col, em, f0 = "Tum", "Aaj mausam kaisa hai?", (37, 211, 102), "🧑", S_WQ
    elif REPLY_WEATHER <= f < CLIP:
        who, line, col, em, f0 = "Jarvis", "Boss, 24°C, halki thand", (60, 200, 255), "🤖", REPLY_WEATHER
    else:
        return
    u = pop_s(f - f0, 5)
    if u <= 0.05:
        return
    d = ImageDraw.Draw(lay)
    fnt = font(MONT, 50)
    text = f"{who}: {line}"
    tw = d.textlength(text, font=fnt) + 150
    x0, y0 = W / 2 - tw / 2 * u, 1140
    sh = Image.new("RGBA", (W, H))
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 10, W - x0, y0 + 130), 50, fill=(0, 0, 0, 160))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, W - x0, y0 + 120), 50, fill=(10, 14, 22, 240), outline=col + (255,), width=6)
    if u > 0.9:
        lay.alpha_composite(e5.emoji(em, 70), (int(x0 + 30), int(y0 + 25)))
        d.text((x0 + 115, y0 + 60), who + ":", font=fnt, fill=col, anchor="lm")
        wl = d.textlength(who + ": ", font=fnt)
        d.text((x0 + 115 + wl, y0 + 60), line, font=fnt, fill=WHT, anchor="lm")


def badge(lay, d):
    d.rounded_rectangle((W - 400, 34, W - 30, 104), 35, fill=(255, 255, 255, 235))
    d.text((W - 190, 69), "The IOT Engineer", font=font(MONT, 30), fill=INK, anchor="mm")
    lay.alpha_composite(e5.emoji("🤖", 46), (W - 388, 46))


def src_frame(i):
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, f"{i:04d}.png")), cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]
    if (w, h) != (W, H):
        s = max(W / w, H / h)
        im = cv2.resize(im, (int(w * s + 0.5), int(h * s + 0.5)), interpolation=cv2.INTER_AREA)
        x0, y0 = (im.shape[1] - W) // 2, (im.shape[0] - H) // 2
        im = im[y0:y0 + H, x0:x0 + W]
    return im


_PM = None


def hide_left(arr):
    """Blur + darken the left column where the source shows a wrongly-timed bulb / 'LIGHT ON' / labels."""
    global _PM
    if _PM is None:
        m = np.zeros((H, W), np.float32)
        cv2.rectangle(m, (0, 330), (255, 1110), 1.0, -1)
        _PM = cv2.GaussianBlur(m, (0, 0), 25)[..., None]
    bl = cv2.GaussianBlur(arr, (0, 0), 28).astype(np.float32) * 0.55
    return (arr.astype(np.float32) * (1 - _PM) + bl * _PM).astype(np.uint8)


def light_chip(lay, f):
    on = f >= REPLY_LIGHT
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = 28, 440, 250, 560
    if on:
        g = Image.new("RGBA", (W, H))
        ImageDraw.Draw(g).ellipse((x0 - 40, y0 - 60, x1 + 40, y1 + 60), fill=(255, 210, 90, 150))
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
        d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x1, y1), 30, fill=((255, 205, 60) if on else (30, 34, 44)) + (240,), outline=WHT + (255,), width=4)
    bulb = e5.emoji("💡", 70)
    if not on:
        bulb = Image.fromarray(np.array(bulb.convert("LA").convert("RGBA")) // np.array([2, 2, 2, 1], np.uint8))
    lay.alpha_composite(bulb, (x0 + 14, y0 + 25))
    d.text((x0 + 155, y0 + 38), "LIGHT", font=font(MONT, 30), fill=INK if on else (190, 195, 210), anchor="mm")
    d.text((x0 + 155, y0 + 82), "ON" if on else "OFF", font=font(MONT, 42), fill=INK if on else (255, 90, 90), anchor="mm")


def frame(f):
    im = Image.fromarray(src_frame(MAP[f])).convert("RGBA")
    if f < S_SETUP:
        return np.array(im.convert("RGB"))                 # the user's thumbnail intro stays as is
    im = Image.fromarray(hide_left(np.array(im.convert("RGB")))).convert("RGBA")
    if f >= CLIP - 24:                                     # slow push-in on the held answer frame
        k = (f - (CLIP - 24)) / 24
        im = Image.fromarray(b.zoom(np.array(im.convert("RGB")), 1 + 0.06 * ease(k))).convert("RGBA")
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    header(lay, d, f)
    if f >= S_LIGHT:
        light_chip(lay, f)
    badge(lay, ImageDraw.Draw(lay))
    subtitle(lay, f)
    im.alpha_composite(lay)
    return np.array(im.convert("RGB"))


def build_audio():
    os.makedirs(WORK, exist_ok=True)
    raw = os.path.join(WORK, "user_audio.wav")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", SRC_MP4, "-vn", "-ac", "2", "-ar", str(SR), raw])
    import wave
    with wave.open(raw) as wf:
        a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32768
    spf = SR // FPS
    out = []
    for c in CUTS:
        if c[0] == "hold":
            seg = np.zeros((c[1] * spf, 2), np.float32)
        else:
            s0, s1 = (c[0] - 1) * spf, c[1] * spf
            seg = a[s0:s1].copy()
            if len(seg) < (c[1] - c[0] + 1) * spf:
                seg = np.pad(seg, ((0, (c[1] - c[0] + 1) * spf - len(seg)), (0, 0)))
        fade = min(len(seg) // 4, int(0.03 * SR))
        if fade:
            r = np.linspace(0, 1, fade)[:, None]
            seg[:fade] *= r
            seg[-fade:] *= r[::-1]
        out.append(seg)
    clip_a = np.concatenate(out)
    total = TOTAL / FPS
    n = int(total * SR)
    mix = np.zeros((n, 2), np.float32)
    mix[: len(clip_a)] += clip_a[:n]
    _spec2 = importlib.util.spec_from_file_location("j2d", os.path.join(ROOT, "edit38", "jarvis2d.py"))
    j2d = importlib.util.module_from_spec(_spec2)
    _spec2.loader.exec_module(j2d)
    pad = j2d.pad(total + 0.05)[:n] * 0.25                 # soft bed so the held frame / end page are not silent
    mix += pad[:, None]
    buf = np.zeros(n)
    t = lambda f: f / FPS  # noqa: E731
    for f0 in (S_SETUP, S_LIGHT, S_WQ, S_WA):
        fx.place(buf, fx.whoosh(0.25, f0) * 0.5, max(0, t(f0) - 0.12), 0.3)
    fx.place(buf, fx.whoosh(0.4, 5) * 0.6, t(CLIP) - 0.2, 0.45)
    for a_ in b31.BTN_POP:
        fx.place(buf, fx.pop(), t(CLIP + a_), 0.35)
    for a_ in b31.BTN_PRESS:
        fx.place(buf, b.ok_beep()[: int(0.09 * SR)] * 0.6, t(CLIP + a_), 0.4)
    fx.place(buf, fx.ding(), t(CLIP + b31.BTN_PRESS[2] + 1), 0.5)
    mix += buf[:n, None]
    tmp = os.path.join(WORK, "premix.wav")
    with wave.open(tmp, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-ar", str(SR), os.path.join(WORK, "mix.wav")])


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    last = None
    for f in range(TOTAL):
        if f < CLIP:
            fr = frame(f)
            last = fr
        else:
            fr = b31.outro(f - CLIP, last, "Jarvis pasand aaya?", badge=badge, dim=0.55, sub_big=True)
            if f - CLIP < 4:
                k = 1 - (f - CLIP) / 4
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 18 * k), 1 + 0.05 * k)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT, TOTAL, "frames")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        fs = [int(v) for v in sys.argv[2].split(",")]
        ims = [Image.fromarray(frame(f)).resize((360, 640)) for f in fs]
        c = Image.new("RGB", (360 * len(ims), 640))
        for k_, im_ in enumerate(ims):
            c.paste(im_, (k_ * 360, 0))
        c.save(sys.argv[3])
        print("CLIP", CLIP, "TOTAL", TOTAL, "S", S_SETUP, S_LIGHT, REPLY_LIGHT, S_WQ, S_WA, REPLY_WEATHER)
    else:
        build_audio()
        build_video()
