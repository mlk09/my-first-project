"""Hue remap for the golden-hour look: teal cast -> warm gold, sage tram -> rich green, rust robot -> orange."""
import numpy as np

def rgb2hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 1e-6, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx

def hsv2rgb(h, s, v):
    c = v * s; hp = (h % 360) / 60; x = c * (1 - np.abs(hp % 2 - 1)); m = v - c
    z = np.zeros_like(h); i = hp.astype(np.int32) % 6
    r = np.choose(i, [c, x, z, z, x, c]); g = np.choose(i, [x, c, c, x, z, z]); b = np.choose(i, [z, z, x, c, c, x])
    return np.stack([r + m, g + m, b + m], -1)

def bump(h, lo, hi, soft):
    return np.clip(np.minimum(h - (lo - soft), (hi + soft) - h) / soft, 0, 1)

def recolor(img, tram_x=0, tram_bottom=10**6):
    f = img.astype(np.float32) / 255
    h, s, v = rgb2hsv(f)
    H, W = h.shape
        # (the robot itself is repainted orange from its mask; here only warm the rust a little)
    wo = bump(h, 5, 45, 12) * np.clip((s - 0.10) / 0.12, 0, 1) * 0.35
    nh = h + (30 - h) * wo * 0.5
    ns = s + (np.clip(s * 1.6, 0, 0.7) - s) * wo
    nv = v
    # sage tram -> rich green, only right of tram_x (keeps the road/pavement out)
    region = np.clip((np.arange(W, dtype=np.float32) - tram_x) / 120 + 0.5, 0, 1)[None, :] \
             * np.clip((tram_bottom - np.arange(H, dtype=np.float32)) / 150 + 0.5, 0.15, 1)[:, None]
    wg = bump(h, 55, 135, 12) * np.clip((s - 0.10) / 0.10, 0, 1) * region
    nh = nh + (140 - nh) * wg * 0.85
    ns = ns + (np.clip(s * 2.3 + 0.18, 0, 0.72) - ns) * wg
    nv = nv * (1 - 0.08 * wg)
    # teal/grey cast -> warm gold (sky, buildings, mist)
    wt = bump(h, 150, 215, 15) * (1 - wg)
    nh = nh * (1 - wt) + 38 * wt
    ns = ns * (1 - wt) + np.clip(s * 1.3, 0, 0.45) * wt
    out = hsv2rgb(nh % 360, np.clip(ns, 0, 1), np.clip(nv, 0, 1))
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)

if __name__ == "__main__":
    import sys
    from PIL import Image
    for arg in sys.argv[1:]:
        p, tx = arg.split(":")
        im = np.asarray(Image.open(p).convert("RGB"))
        Image.fromarray(recolor(im, int(tx) * im.shape[1] // 1080)).save(p.replace(".png", "_rc.png"))
