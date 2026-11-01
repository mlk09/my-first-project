#!/usr/bin/env python3
"""Animated cinematic 'digital tunnel' backdrop (1080x1920): glowing blue / cyan / green digits flying
out of a vanishing point along the walls of a triangular tunnel, light-speed streaks, faint triangle
wireframes rushing at the camera, dust motes, vignette. Deterministic per frame: tunnel(f) -> RGB uint8."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
CX, CY = W / 2, H * 0.47
FOCAL = 520.0
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COLS = [(40, 90, 255), (60, 140, 255), (90, 220, 255), (110, 255, 150), (30, 60, 220)]
_F = {}
rng = np.random.default_rng(29)
ND = 700
D_ANG = rng.uniform(0, 2 * math.pi, ND)
D_R = rng.uniform(1.0, 2.6, ND)            # distance from tunnel axis (wall-ish)
D_Z0 = rng.uniform(0.3, 12.0, ND)
D_CH = rng.integers(0, 10, ND)
D_COL = rng.integers(0, len(COLS), ND)
D_SPD = rng.uniform(0.07, 0.14, ND)
NS = 60
S_ANG = rng.uniform(0, 2 * math.pi, NS)
S_Z0 = rng.uniform(0.5, 14.0, NS)
S_R = rng.uniform(1.2, 2.4, NS)
S_COL = rng.integers(0, 3, NS)
ZMAX = 12.0


def font(sz):
    sz = int(max(8, min(140, sz)) // 4 * 4)
    if sz not in _F:
        _F[sz] = ImageFont.truetype(FONT, sz)
    return _F[sz]


def proj(ang, r, z):
    s = FOCAL / z
    # stretch vertically a little so the tunnel fills the tall frame
    return CX + math.cos(ang) * r * s, CY + math.sin(ang) * r * s * 1.45, s


def tunnel(f):
    base = Image.new("RGB", (W, H), (1, 2, 8))
    bd = ImageDraw.Draw(base)
    for i in range(14, 0, -1):                                   # deep blue core glow
        rr = i * 70
        c = int(3 + (14 - i) * 1.6)
        bd.ellipse((CX - rr, CY - rr * 1.4, CX + rr, CY + rr * 1.4), fill=(c // 3, c // 2, c + 6))
    lay = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(lay)
    # triangle wireframes rushing at the camera
    for k in range(8):
        z = ZMAX - ((f * 0.12 + k * 1.5) % ZMAX)
        if z < 0.4:
            continue
        a = int(110 * min(1, (ZMAX - z) / 3) * min(1, z / 1.5))
        pts = [proj(-math.pi / 2 + j * 2 * math.pi / 3, 3.0, z)[:2] for j in range(3)]
        d.line(pts + [pts[0]], fill=(70, 120, 255, a), width=2)
    # light-speed streaks
    for i in range(NS):
        z = S_Z0[i] - (f * 0.35) % 14.0
        z = z if z > 0.25 else z + 14.0
        x0, y0, _ = proj(S_ANG[i], S_R[i], z + 2.2)
        x1, y1, _ = proj(S_ANG[i], S_R[i], z)
        a = int(230 * min(1, (14 - z) / 4))
        col = [(60, 110, 255), (120, 230, 255), (150, 255, 190)][S_COL[i]]
        d.line((x0, y0, x1, y1), fill=col + (a,), width=max(2, int(9 / z)))
    # digits (far first)
    zs = (D_Z0 - f * D_SPD) % ZMAX + 0.25
    for i in np.argsort(-zs):
        z = zs[i]
        x, y, s = proj(D_ANG[i], D_R[i], z)
        if not (-80 < x < W + 80 and -80 < y < H + 80):
            continue
        sz = 0.22 * s
        a = int(255 * min(1, (ZMAX - z) / 4) * min(1, z / 0.6))
        col = COLS[D_COL[i]]
        ch = str((D_CH[i] + (f // 9 if i % 7 == 0 else 0)) % 10)
        fo = font(sz)
        if sz > 26:                                             # motion trail toward the vanishing point
            for t in (3, 2, 1):
                xt, yt, _ = proj(D_ANG[i], D_R[i], z + t * 0.12)
                d.text((xt, yt), ch, font=fo, fill=col + (a // (t + 2),), anchor="mm")
        d.text((x, y), ch, font=fo, fill=col + (a,), anchor="mm")
    glow = lay.filter(ImageFilter.GaussianBlur(10))
    out = base.convert("RGBA")
    out.alpha_composite(glow)
    out.alpha_composite(glow)
    out.alpha_composite(lay)
    x = np.asarray(out.convert("RGB")).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.55 * np.clip(((xx - CX) / (W * 0.75)) ** 2 + ((yy - CY) / (H * 0.65)) ** 2, 0, 1)
    return np.clip(x * v[..., None], 0, 255).astype(np.uint8)


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    ims = [Image.fromarray(tunnel(f)).resize((360, 640)) for f in (0, 60, 200)]
    c = Image.new("RGB", (1080, 640))
    for i, im in enumerate(ims):
        c.paste(im, (i * 360, 0))
    c.save(out)
