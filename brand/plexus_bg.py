#!/usr/bin/env python3
"""Animated PLEXUS background (from the user's reference still): deep navy/black space with soft
drifting nebula fog, glowing star-like nodes connected by thin pale-blue lines that fade with
distance. Nodes drift slowly in 3-D (depth changes brightness/size), so the network keeps moving.

background(t) -> RGBA 1080x1920
"""
import math
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image

W, H = 1080, 1920
SC = 2                      # draw at half resolution, upscale (soft look like the reference)
w, h = W // SC, H // SC
N = 52
LINK = 330 / SC             # max link distance (half-res px)


@lru_cache(None)
def _nodes():
    rng = np.random.default_rng(23)
    p = rng.uniform(0, 1, (N, 3)) * np.array([w * 1.2, h * 1.1, 1.0]) - np.array([w * 0.1, h * 0.05, 0])
    v = rng.normal(0, 1, (N, 3)) * np.array([6.0, 6.0, 0.05])
    ph = rng.uniform(0, 2 * math.pi, N)
    return p, v, ph


@lru_cache(None)
def _fog():
    """large soft nebula clouds (two layers that drift at different speeds)"""
    out = []
    for seed, scale in ((1, 22), (2, 34)):
        rng = np.random.default_rng(seed)
        small = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
        f = cv2.resize(small, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        f = cv2.GaussianBlur(f, (0, 0), 45)
        f = (f - f.min()) / (f.max() - f.min())
        out.append(np.clip((f - 0.45) * 2.2, 0, 1) ** 1.5)
    return out


@lru_cache(None)
def _base():
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w * .5) / w) ** 2 + ((yy - h * .4) / h) ** 2)
    g = np.clip(1 - r * 1.25, 0, 1)[..., None]
    return np.array([1, 2, 7], np.float32) + g * np.array([8, 12, 28], np.float32)


def background(t):
    img = _base().copy()
    f1, f2 = _fog()
    o1x, o1y = int(t * 6) % w, int(t * 3) % h
    o2x, o2y = int(-t * 4) % w, int(t * 5) % h
    fog = f1[o1y:o1y + h, o1x:o1x + w] * 0.6 + f2[o2y:o2y + h, o2x:o2x + w] * 0.45
    img += fog[..., None] * np.array([16, 24, 46], np.float32)
    p0, v, ph = _nodes()
    p = p0 + v * t
    p[:, 0] = (p[:, 0] + w * 0.1) % (w * 1.2) - w * 0.1
    p[:, 1] = (p[:, 1] + h * 0.05) % (h * 1.1) - h * 0.05
    z = 0.55 + 0.45 * np.sin(t * 0.35 + ph)                  # pseudo depth 0.1..1
    lines = np.zeros((h, w), np.float32)
    dots = np.zeros((h, w), np.float32)
    for i in range(N):
        for j in range(i + 1, N):
            d = math.hypot(p[i, 0] - p[j, 0], p[i, 1] - p[j, 1])
            if d < LINK:
                a = (1 - d / LINK) ** 0.9 * (0.35 + 0.65 * min(z[i], z[j]))
                cv2.line(lines, (int(p[i, 0]), int(p[i, 1])), (int(p[j, 0]), int(p[j, 1])), float(a), 1, cv2.LINE_AA)
    for i in range(N):
        tw = 0.75 + 0.25 * math.sin(t * 2.3 + ph[i] * 3)
        cv2.circle(dots, (int(p[i, 0]), int(p[i, 1])), max(1, int(1 + 2 * z[i])), float(z[i] * tw), -1, cv2.LINE_AA)
    halo = cv2.GaussianBlur(dots, (0, 0), 5) * 2.2 + cv2.GaussianBlur(lines, (0, 0), 2) * 0.8
    img += lines[..., None] * np.array([95, 120, 175], np.float32)
    img += halo[..., None] * np.array([90, 120, 190], np.float32)
    img += dots[..., None] * np.array([220, 230, 255], np.float32)
    full = cv2.resize(np.clip(img, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
    return Image.fromarray(full).convert("RGBA")


if __name__ == "__main__":
    import sys
    background(float(sys.argv[1]) if len(sys.argv) > 1 else 0.0).save("/tmp/plexus.png")
