#!/usr/bin/env python3
"""Post-production for "Robot and the Haunted Bag": grade, transitions, captions, mux.

Reads the Blender frames (work/frames, 1280x536), and for every output frame:
  * upscales to 1920x804 and letterboxes into 1920x1080 (2.39:1, like the reference)
  * cinematic grade: bloom, teal/orange split-tone, soft S-curve, vignette, grain
  * transitions from timeline.TRANSITIONS: dip to black, motion-blurred whip,
    white flash, and the glitch-in of the raw clip (your original Short) before
    the title
  * story-book captions in the lower letterbox bar, channel handle in the top bar,
    subscribe end card
then encodes H.264 + AAC with the soundtrack normalised to -14 LUFS (YouTube).

Run: python3 edit3/build_final.py [--src work/frames] [--out output/...mp4]
"""
import argparse
import glob
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import CAPTIONS, CUTS, DURATION, FPS, NFRAMES, TRANSITIONS  # noqa: E402

W, H = 1920, 1080
PW, PH = 1920, 804          # picture area inside the letterbox
TOP = (H - PH) // 2         # 138 px bars
FONT_ROUND = os.path.join(HERE, "assets", "fonts", "Fredoka-Bold.ttf")
FONT_SPOOKY = os.path.join(HERE, "assets", "fonts", "Creepster.ttf")
RAW = os.path.join(HERE, "..", "Screenrecorder-2026-10-08-17-57-24-640.mp4")
HANDLE = "@Cadd123-q2t"
rng = np.random.default_rng(3)


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def window(t, t0, t1, fade):
    return float(smooth((t - t0) / fade) * smooth((t1 - t) / fade))


# ------------------------------------------------------------------ static assets

yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
_r2 = ((xx - PW / 2) / (PW / 2)) ** 2 + ((yy - PH / 2) / (PH / 2)) ** 2
VIGNETTE = (1.0 - 0.32 * np.clip(_r2, 0, 2) ** 1.2)[..., None].astype(np.float32)
GRAIN = [rng.normal(0, 1, (PH // 2, PW // 2)).astype(np.float32) for _ in range(6)]


def make_lut():
    x = np.linspace(0, 1, 256)
    s = x * x * (3 - 2 * x)
    y = 0.62 * x + 0.38 * s          # gentle S-curve
    y = 0.018 + y * 0.982            # lifted blacks (filmic)
    return y.astype(np.float32)


LUT = make_lut()


def grade(img):
    """img: float32 HxWx3 in 0..1 (picture area)."""
    # bloom from a quarter-res copy
    small = Image.fromarray((img * 255).astype(np.uint8)).resize((PW // 4, PH // 4), Image.BILINEAR)
    s = np.asarray(small).astype(np.float32) / 255
    bright = np.clip((s - 0.5) * 2.0, 0, 1)
    b8 = Image.fromarray((bright * 255).astype(np.uint8))
    g1 = np.asarray(b8.filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    g2 = np.asarray(b8.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
    glow = np.asarray(Image.fromarray(((g1 * 0.6 + g2 * 0.7).clip(0, 1) * 255).astype(np.uint8))
                      .resize((PW, PH), Image.BILINEAR)).astype(np.float32) / 255
    img = 1 - (1 - img) * (1 - glow * 0.55)
    # tone curve
    img = LUT[(img * 255).clip(0, 255).astype(np.uint8)]
    lum = (img @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    # split toning: teal shadows, warm highlights
    img = img + (1 - lum) ** 2 * np.array([-0.012, 0.012, 0.03], np.float32) \
        + lum ** 2 * np.array([0.035, 0.012, -0.02], np.float32)
    img = lum + (img - lum) * 1.18   # saturation
    img = img * VIGNETTE
    return img


def add_grain(img, f):
    g = GRAIN[f % len(GRAIN)]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    return img + g * 0.012


# ------------------------------------------------------------------ captions


def caption_image(text, spooky=False):
    font = ImageFont.truetype(FONT_SPOOKY if spooky else FONT_ROUND, 56 if spooky else 46)
    dialogue = text.startswith('"') or text.startswith("*")
    col = (255, 207, 84) if dialogue else (255, 255, 255)
    if spooky:
        col = (255, 120, 30)
    tmp = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    y = (140 - (bb[3] - bb[1])) // 2 - bb[1]
    glow = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, y), text, font=font, fill=(col[0], col[1] // 2, 0, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    d.text((x, y), text, font=font, fill=col + (255,), stroke_width=2, stroke_fill=(10, 8, 14, 255))
    out = Image.alpha_composite(glow, tmp)
    return np.asarray(out).astype(np.float32) / 255


CAPS = [(t0, t1, caption_image(txt)) for t0, t1, txt in CAPTIONS]
CAPS.append((7.2, 11.6, caption_image("A spooky story for kids", spooky=True)))
CAPS.append((176.0, 180.0, caption_image("Subscribe for more spooky stories!   " + HANDLE)))


def handle_image():
    font = ImageFont.truetype(FONT_ROUND, 28)
    im = Image.new("RGBA", (420, 60), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 12), HANDLE, font=font, fill=(255, 255, 255, 120))
    return np.asarray(im).astype(np.float32) / 255


HANDLE_IMG = handle_image()


def over(canvas, rgba, x, y, alpha=1.0):
    rgba = rgba[: canvas.shape[0] - y, : canvas.shape[1] - x]  # clip at the frame edge
    h, w = rgba.shape[:2]
    a = rgba[..., 3:4] * alpha
    region = canvas[y:y + h, x:x + w]
    canvas[y:y + h, x:x + w] = region * (1 - a) + rgba[..., :3] * a


# ------------------------------------------------------------------ raw clip glitch


def load_raw():
    """Frames of the original Short (screen recording), cropped to its title card."""
    if not os.path.exists(RAW):
        return []
    cmd = ["ffmpeg", "-v", "error", "-i", RAW, "-vf", "crop=780:800:0:310,scale=585:600",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    data = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(data) // (585 * 600 * 3)
    return [np.frombuffer(data, np.uint8, 585 * 600 * 3, i * 585 * 600 * 3).reshape(600, 585, 3)
            .astype(np.float32) / 255 for i in range(n)]


RAW_FRAMES = load_raw()
GLITCH_T0, GLITCH_T1 = 6.0, 6.7


def glitch(canvas, t, f):
    if not RAW_FRAMES:
        return canvas
    k = int((t - GLITCH_T0) * 24) % len(RAW_FRAMES)
    src = RAW_FRAMES[k]
    r = np.random.default_rng(f)
    h, w = src.shape[:2]
    x0, y0 = (W - w) // 2, (H - h) // 2
    card = np.zeros((h, w, 3), np.float32)
    shift = int(14 * (1 - (t - GLITCH_T0) / (GLITCH_T1 - GLITCH_T0)) + 4)
    card[..., 0] = np.roll(src[..., 0], shift, 1)   # RGB split
    card[..., 1] = src[..., 1]
    card[..., 2] = np.roll(src[..., 2], -shift, 1)
    for _ in range(7):                                # displaced slices
        a = r.integers(0, h - 20)
        b = a + r.integers(6, 40)
        card[a:b] = np.roll(card[a:b], r.integers(-60, 60), 1)
    card[::3] *= 0.75                                 # scanlines
    card += r.normal(0, 0.05, card.shape).astype(np.float32)
    flick = 0.75 + 0.25 * r.random()
    canvas *= 0.25
    canvas[y0:y0 + h, x0:x0 + w] = card.clip(0, 1) * flick
    return canvas


# ------------------------------------------------------------------ frames


class Frames:
    def __init__(self, src):
        self.files = {}
        for p in glob.glob(os.path.join(src, "f_*.png")):
            if os.path.getsize(p) > 0:
                self.files[int(os.path.basename(p)[2:7])] = p
        self.keys = sorted(self.files)
        if not self.keys:
            sys.exit(f"no frames in {src}")
        self.cache = {}

    def get(self, f):
        """Rendered frame f (or the nearest earlier one), upscaled to the picture area."""
        i = np.searchsorted(self.keys, f, side="right") - 1
        k = self.keys[max(i, 0)]
        if k not in self.cache:
            if len(self.cache) > 24:
                self.cache.pop(next(iter(self.cache)))
            im = Image.open(self.files[k]).convert("RGB").resize((PW, PH), Image.LANCZOS)
            self.cache[k] = np.asarray(im).astype(np.float32) / 255
        return self.cache[k]


def whip_blur(img, amount, direction):
    if amount < 0.02:
        return img
    n = 8
    dx = int(amount * 70)
    acc = np.zeros_like(img)
    for k in range(n):
        acc += np.roll(img, direction * dx * k // n, axis=1)
    return acc / n


_bx = np.arange(PW, dtype=np.float32)
_bark = (0.5 + 0.5 * np.sin(_bx * 0.031) * np.sin(_bx * 0.0071 + 1.3)).astype(np.float32)
BARK = (np.array([0.028, 0.03, 0.042], np.float32) * (0.6 + 0.8 * _bark[:, None]))[None]


def trunk_wipe(img, d, span=0.4):
    """A dark tree trunk sweeps right-to-left past the lens; the cut hides behind it."""
    u = d / span                                   # -1 .. 1
    centre = PW / 2 - u * PW * 1.25
    half = PW * 0.62
    cover = smooth((half - np.abs(_bx - centre)) / 140.0)[None, :, None]
    return img * (1 - cover) + BARK * cover


def picture(fr, f):
    t = f / FPS
    img = fr.get(f).copy()
    for c, kind in TRANSITIONS.items():
        d = t - c
        if kind == "whip" and abs(d) < 0.25:
            img = whip_blur(img, 1 - abs(d) / 0.25, 1 if d < 0 else -1)
        elif kind == "dip" and abs(d) < 0.4:
            img *= smooth(abs(d) / 0.4)
        elif kind == "trunk" and abs(d) < 0.4:
            img = trunk_wipe(img, d)
    img = grade(img)
    # lightning + flash cut
    fl = window(t, 52.15, 52.42, 0.04) * 0.85 + window(t, 52.6, 52.7, 0.03) * 0.5
    for c, kind in TRANSITIONS.items():
        if kind == "flash" and 0 <= t - c < 0.35:
            fl = max(fl, 1 - (t - c) / 0.35)
    if fl > 0:
        img = img + (1 - img) * fl
    return img


def compose(fr, f):
    t = f / FPS
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[TOP:TOP + PH] = add_grain(picture(fr, f), f)
    # fades: open from black, close to black under the end card
    canvas[TOP:TOP + PH] *= smooth(t / 0.8) * (1 - smooth((t - 178.0) / 1.6))
    if GLITCH_T0 <= t < GLITCH_T1:
        canvas = glitch(canvas, t, f)
    for t0, t1, im in CAPS:
        if t0 - 0.05 <= t <= t1 + 0.05:
            a = window(t, t0, t1, 0.25)
            dy = int(10 * (1 - smooth((t - t0) / 0.3)))
            over(canvas, im, 0, H - 140 + dy, a)
    if 1.0 < t < 176.0:
        over(canvas, HANDLE_IMG, W - 430, 40, window(t, 1.0, 176.0, 1.0))
    return (canvas.clip(0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(HERE, "work", "frames"))
    ap.add_argument("--audio", default=os.path.join(HERE, "work", "audio", "mix.wav"))
    ap.add_argument("--out", default=os.path.join(HERE, "output", "Robot-and-the-Haunted-Bag-3D.mp4"))
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=DURATION)
    ap.add_argument("--fast", action="store_true", help="quick preview encode")
    ap.add_argument("--still", type=float, nargs="*", help="write PNG stills at these times")
    a = ap.parse_args()
    fr = Frames(a.src)
    if a.still:
        os.makedirs(os.path.join(HERE, "work", "post"), exist_ok=True)
        for t in a.still:
            p = os.path.join(HERE, "work", "post", f"post_{t:07.2f}.png")
            Image.fromarray(compose(fr, int(round(t * FPS)))).save(p)
            print(p)
        return
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    f0, f1 = int(a.start * FPS), min(NFRAMES, int(a.end * FPS))
    venc = (["-c:v", "libx264", "-preset", "veryfast", "-crf", "26"] if a.fast else
            ["-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "7M", "-bufsize", "14M",
             "-tune", "animation", "-x264-params", "aq-mode=3"])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", f"{a.start}", "-t", f"{(f1 - f0) / FPS}", "-i", a.audio,
           *venc, "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-colorspace", "bt709", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac",
           "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(compose(fr, f).tobytes())
        if f % 240 == 0:
            print(f"{f / FPS:6.1f}s", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", a.out)


if __name__ == "__main__":
    main()
