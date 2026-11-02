#!/usr/bin/env python3
"""13 s Car Racing short from the user's black-and-white Gemini AI clip (10 s, 720x1280, kept as is):
only the game screens (GAME CAM panel, OLED / inset screens, full-screen game shots) are re-coloured with a
neon gradient map and the two LEDs get red / green colour + glow; everything else stays B&W. A 3 s
Like / Share / Subscribe end page is appended. Upscaled to 1080x1920, chiptune + SFX from edit30.
Usage: python3 edit31/build.py"""
import importlib.util
import os
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
_spec = importlib.util.spec_from_file_location("b30", os.path.join(ROOT, "edit30", "build_short.py"))
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)
fx, e5, font, txt, pop_s, ease = b.fx, b.e5, b.font, b.txt, b.pop_s, b.ease
MONT, INK, WHT, YEL = b.MONT, b.INK, b.WHT, b.YEL

SRC = os.path.join(HERE, "work", "src")
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "output", "esp32-car-racing-color-SHORT.mp4")
FPS, SR = 24, 48000
CLIP = 240
OUTRO = 72
TOTAL = CLIP + OUTRO                       # 312 frames = 13 s
W, H = 1080, 1920
w0, h0 = 720, 1280

# ------------------------------------------------------------------ screen / LED regions (clip pixels)
PANEL = [(30, 232), (692, 232), (692, 570), (30, 570)]
# (first frame, last frame, polygon at first, polygon at last) - polygons interpolate inside the range
SCREENS = [
    (1, 30, [(262, 690), (445, 662), (470, 758), (290, 792)], [(272, 700), (455, 670), (482, 770), (298, 806)]),
    (31, 62, [(190, 712), (390, 680), (418, 790), (222, 822)], [(185, 705), (392, 675), (418, 785), (215, 816)]),
    (97, 127, PANEL, PANEL),
    (97, 127, [(36, 634), (418, 634), (418, 842), (36, 842)], [(130, 655), (562, 655), (562, 878), (130, 878)]),
    (128, 157, PANEL, PANEL),
    (158, 191, [(18, 250), (702, 250), (702, 1225), (18, 1225)], [(18, 250), (702, 250), (702, 1225), (18, 1225)]),
    (192, 240, PANEL, PANEL),
    (192, 240, [(225, 670), (430, 635), (452, 735), (250, 778)], [(185, 650), (525, 632), (533, 790), (195, 806)]),
]
# (first, last, centre red LED, centre green LED, radius x, radius y)
LEDS = [
    (1, 30, (385, 595), (462, 595), 16, 30),
    (31, 62, (325, 560), (418, 560), 20, 36),
    (128, 157, (360, 922), (439, 922), 38, 52),
]
STOPS = [(0.0, (6, 6, 28)), (0.22, (40, 26, 96)), (0.42, (60, 70, 170)), (0.6, (30, 200, 255)),
         (0.78, (255, 70, 180)), (0.92, (255, 220, 60)), (1.0, (255, 250, 220))]
LUT = np.zeros((256, 3), np.float32)
for i in range(256):
    u = i / 255
    for (a, ca), (b_, cb) in zip(STOPS, STOPS[1:]):
        if a <= u <= b_:
            k = (u - a) / (b_ - a)
            LUT[i] = np.array(ca) * (1 - k) + np.array(cb) * k
            break


def lerp_poly(p0, p1, k):
    return np.array([[x0 + (x1 - x0) * k, y0 + (y1 - y0) * k] for (x0, y0), (x1, y1) in zip(p0, p1)], np.int32)


def colorize(im, f):
    """im: RGB uint8 720x1280 B&W frame -> screens neon, LEDs red / green, rest untouched."""
    x = im.astype(np.float32)
    lum = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    mask = np.zeros((h0, w0), np.float32)
    for (a, z, p0, p1) in SCREENS:
        if a <= f <= z:
            k = (f - a) / max(1, z - a)
            cv2.fillPoly(mask, [lerp_poly(p0, p1, k)], 1.0)
    if mask.any():
        mask = cv2.GaussianBlur(mask, (0, 0), 3)[..., None]
        neon = LUT[lum]
        x = x * (1 - 0.92 * mask) + neon * 0.92 * mask
    glow = np.zeros_like(x)
    for (a, z, cr, cg, rx, ry) in LEDS:
        if a <= f <= z:
            for c, col in ((cr, (255, 40, 40)), (cg, (40, 255, 90))):
                m = np.zeros((h0, w0), np.float32)
                cv2.ellipse(m, c, (rx, ry), 0, 0, 360, 1.0, -1)
                m = cv2.GaussianBlur(m, (0, 0), 3)[..., None]
                l3 = (lum.astype(np.float32) / 255)[..., None]
                tint = np.array(col, np.float32) * (0.35 + 0.9 * l3) + 255 * np.clip(l3 - 0.8, 0, 1) * 2.5
                x = x * (1 - m) + np.clip(tint, 0, 255) * m
                lit = float(lum[max(0, c[1] - 5):c[1] + 5, max(0, c[0] - 5):c[0] + 5].mean()) / 255
                if lit > 0.55:                                            # coloured bloom around a lit LED
                    g = np.zeros((h0, w0), np.float32)
                    cv2.ellipse(g, c, (int(rx * 2.2), int(ry * 1.8)), 0, 0, 360, (lit - 0.5) * 1.6, -1)
                    glow += cv2.GaussianBlur(g, (0, 0), rx)[..., None] * np.array(col, np.float32)
    return np.clip(x + glow * 0.8, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ end page
BTN_POP = (4, 10, 16)
BTN_PRESS = (26, 38, 50)
_BG = None


def outro(a, last):
    global _BG
    if _BG is None:
        bg = cv2.GaussianBlur(last, (0, 0), 28).astype(np.float32) * 0.38
        _BG = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
    im = _BG.copy()
    d = ImageDraw.Draw(im)
    s = pop_s(a, 6)
    txt(d, (W / 2, 330), "Game pasand aaya?", 80 * s, WHT, stroke=8)
    if s > 0.9:
        im.alpha_composite(e5.emoji("😍", 110), (W // 2 - 55, 400))
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
        cy = 640 + i * 210
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
            d.text((ix + 45, cy), "↗", font=font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80), fill=tcol, anchor="mm")
        else:
            ang = 18 * np.sin((a - BTN_PRESS[2]) * 1.3) * max(0, 1 - (a - BTN_PRESS[2]) / 14) if (i == 2 and pressed) else 0
            im.alpha_composite(e5.emoji(ic, 86).rotate(ang, expand=False, resample=Image.BICUBIC), (ix, int(cy - 43)))
    if a >= BTN_POP[2] + 4:                                            # finger presses each button in turn
        tgt = [(W / 2 + 200, 640 + i * 210 + 40) for i in range(3)]
        seg = 0 if a < BTN_PRESS[0] else 1 if a < BTN_PRESS[1] else 2
        prev = (W / 2 + 330, 1400) if seg == 0 else tgt[seg - 1]
        start = BTN_POP[2] + 4 if seg == 0 else BTN_PRESS[seg - 1] + 2
        u = ease((a - start) / max(1, BTN_PRESS[seg] - 2 - start))
        x = prev[0] + (tgt[seg][0] - prev[0]) * u
        y = prev[1] + (tgt[seg][1] - prev[1]) * u
        press = max(0, 1 - abs(a - BTN_PRESS[seg]) / 3)
        sz = int(130 * (1 - 0.15 * press))
        im.alpha_composite(e5.emoji("👆", sz), (int(x - sz * 0.35), int(y)))
    v = ease((a - BTN_PRESS[2] - 4) / 6)
    if v > 0:                                                          # stays above the Shorts title / buttons
        txt(d, (W / 2 - 60, 1290), "@The IOT Engineer", 60 * (0.8 + 0.2 * v), YEL, stroke=6)
    b.badge(im, d)
    return np.array(im.convert("RGB"))


# ------------------------------------------------------------------ audio
def build_audio():
    os.makedirs(WORK, exist_ok=True)
    total = TOTAL / FPS
    mus = b.music(total + 0.05)
    t = lambda f: f / FPS  # noqa: E731
    i0 = int(t(CLIP) * SR)
    mus[i0:] = fx.filt(mus[i0:], "lowpass", 1400) * 0.7                # softer under the end page
    fx.write_wav(os.path.join(WORK, "music.wav"), mus)
    buf = np.zeros(int((total + 0.05) * SR))
    P = fx.place
    P(buf, fx.boom()[: int(0.6 * SR)], 0.0, 0.45)
    for c in (31, 63, 97, 128, 158, 192):                               # whooshes on the clip's cuts
        P(buf, fx.whoosh(0.25, c) * 0.6, max(0, t(c) - 0.12), 0.35)
    P(buf, fx.riser(0.5), t(145) - 0.45, 0.3)                           # LEDs light up = NITRO
    P(buf, fx.boom()[: int(0.5 * SR)], t(145), 0.45)
    P(buf, b.fanfare8(), t(226), 0.6)                                   # FINISH
    P(buf, fx.whoosh(0.4, 5) * 0.6, t(CLIP) - 0.2, 0.45)
    for a in BTN_POP:
        P(buf, fx.pop(), t(CLIP + a), 0.35)
    for a in BTN_PRESS:
        P(buf, b.ok_beep()[: int(0.09 * SR)] * 0.6, t(CLIP + a), 0.4)
    P(buf, fx.ding(), t(CLIP + BTN_PRESS[2] + 1), 0.5)
    fx.write_wav(os.path.join(WORK, "sfx.wav"), buf)
    fc = ("[0:a]loudnorm=I=-20:TP=-3,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[m][s]amix=inputs=2:normalize=0,"
          f"loudnorm=I=-14:TP=-1:LRA=9,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={total:.3f}[out]")
    fx.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "music.wav"), "-i", os.path.join(WORK, "sfx.wav"),
            "-filter_complex", fc, "-map", "[out]", "-t", f"{total:.3f}", os.path.join(WORK, "mix.wav")])


def frame(f):
    im = cv2.cvtColor(cv2.imread(os.path.join(SRC, f"{f:04d}.png")), cv2.COLOR_BGR2RGB)
    return cv2.resize(colorize(im, f), (W, H), interpolation=cv2.INTER_LANCZOS4)


def build_video():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "pipe:", "-i", os.path.join(WORK, "mix.wav"),
                            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-maxrate", "16M", "-bufsize", "32M",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                            "-shortest", OUT], stdin=subprocess.PIPE)
    last = None
    for f in range(TOTAL):
        if f < CLIP:
            fr = frame(f + 1)
            last = fr
        else:
            fr = outro(f - CLIP, last)
            if f - CLIP < 4:
                k = 1 - (f - CLIP) / 4
                fr = b.zoom(cv2.GaussianBlur(fr, (0, 0), 1 + 18 * k), 1 + 0.05 * k)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        fs = [int(v) for v in sys.argv[2].split(",")]
        ims = [Image.fromarray(frame(f) if f <= CLIP else outro(f - CLIP, frame(CLIP))).resize((360, 640)) for f in fs]
        c = Image.new("RGB", (360 * len(ims), 640))
        for i, im in enumerate(ims):
            c.paste(im, (i * 360, 0))
        c.save(sys.argv[3])
    else:
        build_audio()
        build_video()
