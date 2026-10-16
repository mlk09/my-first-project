"""Animated BLACK GRID background (inspired by the print(f"Hello {a}") reference frame).

Big soft-grey grid on near-black with faint speckle, plus motion so it never feels static:
  * the grid drifts slowly (diagonal)
  * light pulses (yellow / cyan / orange comets) run along the grid lines
  * intersection nodes breathe
  * a soft spotlight wanders and lifts the lines under it
  * a random cell flashes faintly every ~2.5 s
  * twinkling dust speckle

background(t) -> RGBA PIL image (1080x1920).
"""
import math
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920
CELL = 360                      # 3 big columns like the reference
MINOR = CELL // 4
DRIFT = (10.0, 22.0)            # px/s (x, y)
LINE = np.array([62, 62, 68], np.float32)
COMET_COLS = [(255, 205, 40), (40, 225, 235), (255, 140, 30), (255, 205, 40)]


@lru_cache(None)
def _tiles():
    tw, th = W + CELL, H + CELL
    major = Image.new("L", (tw, th), 0)
    minor = Image.new("L", (tw, th), 0)
    dM, dm = ImageDraw.Draw(major), ImageDraw.Draw(minor)
    for x in range(0, tw + 1, MINOR):
        (dM if x % CELL == 0 else dm).line((x, 0, x, th), fill=255, width=3 if x % CELL == 0 else 1)
    for y in range(0, th + 1, MINOR):
        (dM if y % CELL == 0 else dm).line((0, y, tw, y), fill=255, width=3 if y % CELL == 0 else 1)
    M = np.asarray(major).astype(np.float32) / 255
    halo = cv2.GaussianBlur(M, (0, 0), 6)
    m = np.asarray(minor).astype(np.float32) / 255
    return M, halo, m


@lru_cache(None)
def _base():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * .45) / H) ** 2)
    return (np.array([5, 5, 7], np.float32) + np.clip(1 - r * 1.3, 0, 1)[..., None] * np.array([9, 9, 12], np.float32))


@lru_cache(None)
def _spot():
    yy, xx = np.mgrid[0:2 * H, 0:2 * W].astype(np.float32)
    return np.exp(-(((xx - W) / 520.0) ** 2 + ((yy - H) / 620.0) ** 2))


@lru_cache(None)
def _speckle():
    out = []
    for s in range(3):
        rng = np.random.default_rng(40 + s)
        a = (rng.random((H // 2, W // 2)) < 0.0035) * rng.uniform(18, 55, (H // 2, W // 2))
        out.append(cv2.resize(a.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST))
    return out


def _comets(t, ox, oy):
    """Light pulses travelling along major grid lines (positions follow the drift)."""
    lay = np.zeros((H, W, 3), np.float32)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for k in range(4):
        period = 3.2 + 0.7 * k
        ph = (t + k * 1.3) / period
        cyc, f = int(ph), ph % 1.0
        rng = np.random.default_rng(1000 * k + cyc)
        vertical = (k + cyc) % 2 == 0
        col = COMET_COLS[(k + cyc) % 4]
        if vertical:
            xs = [g for g in range(-ox, W, CELL) if 60 < g < W - 60]
            x = xs[int(rng.integers(0, len(xs)))]
            head = f * (H + 600) - 300
            pts = [(x, head - j * 28) for j in range(14)]
        else:
            ys = [g for g in range(-oy, H, CELL) if 60 < g < H - 60]
            y = ys[int(rng.integers(0, len(ys)))]
            head = f * (W + 600) - 300
            if (k + cyc) % 4 == 1:
                head = W - head
                pts = [(head + j * 28, y) for j in range(14)]
            else:
                pts = [(head - j * 28, y) for j in range(14)]
        for j in range(13):
            a = (1 - j / 13) ** 1.6
            c = tuple(int(v * a) for v in col)
            d.line((pts[j], pts[j + 1]), fill=c, width=4)
        hx, hy = pts[0]
        d.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), fill=(255, 255, 240))
    sharp = np.asarray(img).astype(np.float32)
    small = cv2.resize(sharp, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (W, H), interpolation=cv2.INTER_LINEAR)
    lay += sharp * 0.9 + glow * 3.0
    return lay


def background(t):
    ox, oy = int(t * DRIFT[0]) % CELL, int(t * DRIFT[1]) % CELL
    M, halo, m = (a[oy:oy + H, ox:ox + W] for a in _tiles())
    # wandering spotlight
    sx = int(W / 2 + 300 * math.sin(t * 0.37))
    sy = int(H * .45 + 520 * math.sin(t * 0.23 + 1.0))
    spot = _spot()[H - sy:2 * H - sy, W - sx:2 * W - sx]
    lift = (0.55 + 1.1 * spot)[..., None]
    img = _base() + (M[..., None] * LINE * 1.0 + halo[..., None] * LINE * 0.5) * lift + m[..., None] * LINE * 0.28 * lift
    img += spot[..., None] * np.array([10, 10, 14], np.float32)
    # breathing intersection nodes
    for gy in range(-oy, H + CELL, CELL):
        for gx in range(-ox, W + CELL, CELL):
            if 0 <= gx < W and 0 <= gy < H:
                b = 0.5 + 0.5 * math.sin(t * 2.2 + gx * 0.013 + gy * 0.007)
                y0, y1, x0, x1 = max(gy - 5, 0), min(gy + 6, H), max(gx - 5, 0), min(gx + 6, W)
                img[y0:y1, x0:x1] += 70 * b
    # faint cell flash every 2.5 s
    ph = t / 2.5
    cyc, f = int(ph), ph % 1.0
    rng = np.random.default_rng(77 + cyc)
    cx, cy = rng.integers(0, W // CELL + 1), rng.integers(0, H // CELL + 1)
    a = math.sin(math.pi * min(f / 0.7, 1.0)) * 0.10
    if a > 0:
        x0, y0 = cx * CELL - ox + 3, cy * CELL - oy + 3
        xs, ys = slice(max(x0, 0), max(min(x0 + CELL - 5, W), 0)), slice(max(y0, 0), max(min(y0 + CELL - 5, H), 0))
        img[ys, xs] += np.array(COMET_COLS[cyc % 3], np.float32) * a
    # twinkling dust
    sp = _speckle()
    w = [0.5 + 0.5 * math.sin(t * 1.7 + k * 2.1) for k in range(3)]
    img += (sp[0] * w[0] + sp[1] * w[1] + sp[2] * w[2])[..., None] * 0.8
    img += _comets(t, ox, oy)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


if __name__ == "__main__":
    import sys
    for tt in (0.0, 1.3, 2.6):
        background(tt).save(sys.argv[1] + f"_{tt}.png" if len(sys.argv) > 1 else f"/tmp/dg_{tt}.png")
