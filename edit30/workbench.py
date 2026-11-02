#!/usr/bin/env python3
"""Animated workbench backdrop (1080x1920) from the user's wooden-table electronics photo: depth-of-field
blur, slow seamless-loop pan + breathing zoom across the wide photo, a warm lamp light that drifts over the
table, floating dust / bokeh specks and a soft vignette. workbench(f) -> RGB uint8 (frame N == frame 0)."""
import math
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, N = 1080, 1920, 312
_SRC = None


def _src():
    global _SRC
    if _SRC is None:
        im = cv2.cvtColor(cv2.imread(os.path.join(HERE, "assets", "workbench.webp")), cv2.COLOR_BGR2RGB)
        hh = int(H * 1.12)
        ww = int(im.shape[1] * hh / im.shape[0])
        im = cv2.resize(im, (ww, hh), interpolation=cv2.INTER_CUBIC)
        im = cv2.GaussianBlur(im, (0, 0), 5)                      # depth of field (the console is in focus)
        x = im.astype(np.float32)
        x = (x - 128) * 1.08 + 128                                # a touch more contrast
        _SRC = np.clip(x * 0.82, 0, 255)
    return _SRC


rng = np.random.default_rng(30)
ND = 70
DX, DY = rng.uniform(0, W, ND), rng.uniform(0, H, ND)
DR = rng.uniform(2, 9, ND)
DP = rng.uniform(0, 2 * math.pi, ND)
DA = rng.uniform(0.15, 0.55, ND)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = 1 - 0.5 * np.clip(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H * 0.48) / (H * 0.62)) ** 2, 0, 1)


def workbench(f):
    src = _src()
    ph = 2 * math.pi * (f % N) / N
    z = 1.0 + 0.03 * (1 - math.cos(ph)) / 2                     # breathing zoom, loops
    cw, chh = int(W / z), int(H / z)
    span = src.shape[1] - cw
    cx = span * (0.45 + 0.2 * math.sin(ph))                      # slow pan across the table, loops
    cy = (src.shape[0] - chh) / 2
    crop = src[int(cy):int(cy) + chh, int(cx):int(cx) + cw]
    x = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LINEAR)
    lx = W * (0.5 + 0.35 * math.sin(ph + 1.0))                    # warm lamp light drifting over the wood
    ly = H * (0.38 + 0.08 * math.cos(ph))
    light = np.exp(-(((xx - lx) / 520) ** 2 + ((yy - ly) / 700) ** 2))[..., None]
    x = x * (0.78 + 0.45 * light) + np.array((255, 190, 110), np.float32) * 0.10 * light
    x *= VIG[..., None]
    out = np.clip(x, 0, 255).astype(np.uint8)
    lay = np.zeros_like(out)
    for i in range(ND):                                           # dust / bokeh specks floating up, loops
        px = int((DX[i] + 18 * math.sin(ph * 2 + DP[i])) % W)
        py = int((DY[i] - H * (f % N) / N * 0.35) % H)
        a = DA[i] * (0.6 + 0.4 * math.sin(ph * 3 + DP[i]))
        cv2.circle(lay, (px, py), int(DR[i]), (int(255 * a), int(225 * a), int(170 * a)), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 2.5)
    return np.clip(out.astype(np.int16) + lay, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    import sys
    from PIL import Image
    ims = [Image.fromarray(workbench(f)).resize((360, 640)) for f in (0, 80, 160, 240)]
    c = Image.new("RGB", (1440, 640))
    for i, im in enumerate(ims):
        c.paste(im, (i * 360, 0))
    c.save(sys.argv[1])
