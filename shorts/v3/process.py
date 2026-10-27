"""Recolour the joined edit: golden scene, green tram, orange robot with red eyes.
Usage: process.py <in.mkv> <out.mkv> [debug_dir]"""
import sys, subprocess, numpy as np, cv2
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from recolor import recolor, rgb2hsv
from robot import lerp_box, paint_orange

W, H, FPS = 1080, 1920, 30
# segment: (start, end, tram_x, tram_bottom, robot box keyframes or None, eyes visible)
SEGS = [
    (0.0, 2.4, 480, 1220, [(0.0, (90, 590, 560, 1575)), (2.4, (80, 620, 570, 1660))], True),
    (2.4, 4.4, 0, 1250, None, False),
    (4.4, 6.9, 560, 1250, [(4.4, (220, 650, 640, 1540)), (5.5, (260, 680, 700, 1585)), (6.9, (280, 680, 770, 1650))], True),
    (6.9, 8.4, 500, 1300, None, False),
    (8.4, 10.4, 620, 1400, None, False),
    (10.4, 13.4, 420, 1500, [(10.4, (200, 620, 900, 1660)), (11.0, (280, 540, 940, 1640)), (11.5, (280, 540, 1020, 1660)),
                             (12.0, (360, 430, 940, 1620)), (12.5, (410, 400, 890, 1620)), (13.0, (470, 400, 830, 1620)), (13.4, (480, 400, 820, 1620))], False),
    (13.4, 17.0, 380, 1550, [(13.4, (250, 650, 650, 1640)), (15.0, (330, 650, 950, 1640)), (17.0, (380, 560, 1000, 1640))], False),
]

_SESSION = None

def mask_step(rgb, box, prev=None, pad=40):
    """Robot matte from an AI cut-out model run on a crop around the robot (robot = main subject there)."""
    global _SESSION
    from rembg import new_session, remove
    from PIL import Image
    if _SESSION is None:
        _SESSION = new_session("isnet-general-use")
    Hh, Ww = rgb.shape[:2]
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(Ww, x1 + pad), min(Hh, y1 + pad)
    m = np.zeros((Hh, Ww), np.float32)
    m[Y0:Y1, X0:X1] = np.asarray(remove(Image.fromarray(rgb[Y0:Y1, X0:X1]), session=_SESSION, only_mask=True), np.float32) / 255
    return m

def find_eyes(rgb, mask):
    """Two dark round lenses in the top of the robot's head."""
    ys, xs = np.where(mask > 0.5)
    if len(ys) < 500: return [], None
    top, bot = ys.min(), ys.max(); hh = int((bot - top) * 0.20)
    rows = (ys < top + hh); hx0, hx1 = xs[rows].min(), xs[rows].max()
    g = cv2.cvtColor(rgb[top:top + hh, hx0:hx1 + 1], cv2.COLOR_RGB2GRAY).astype(np.float32)
    mm = mask[top:top + hh, hx0:hx1 + 1] > 0.5
    if mm.sum() < 200: return [], (hx0, top, max(hx1 - hx0, 1))
    thr = np.percentile(g[mm], 14)
    dark = ((g < thr) & cv2.erode(mm.astype(np.uint8), np.ones((5, 5))).astype(bool)).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3)))
    n, lab, st, cen = cv2.connectedComponentsWithStats(dark)
    head_w = hx1 - hx0
    cands = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 40 or w > head_w * 0.45 or h > hh * 0.6: continue
        if min(w, h) / max(w, h) < 0.5: continue
        cands.append((a, cen[i][0] + hx0, cen[i][1] + top, max(w, h) / 2))
    cands.sort(reverse=True); cands = cands[:4]
    best = None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            a, b = cands[i], cands[j]
            dy, dx = abs(a[2] - b[2]), abs(a[1] - b[1])
            if dy < hh * 0.18 and head_w * 0.15 < dx < head_w * 0.8:
                score = a[0] + b[0]
                if best is None or score > best[0]: best = (score, a, b)
    head = (hx0, top, max(head_w, 1))
    if best is None: return [], head
    eyes = [best[1][1:], best[2][1:]]
    if max(e[2] for e in eyes) > head_w * 0.2: return [], head
    return eyes, head

def draw_eyes(rgb, eyes, strength=1.0):
    if not eyes: return rgb
    f = rgb.astype(np.float32) / 255
    glow = np.zeros(f.shape[:2], np.float32); core = np.zeros_like(glow); pupil = np.zeros_like(glow)
    rm = max(6, float(np.mean([e[2] for e in eyes])))      # both lenses the same size
    for x, y, _ in eyes:
        r = rm
        cv2.circle(glow, (int(x), int(y)), int(r * 2.2), 1, -1)
        cv2.circle(core, (int(x), int(y)), int(r * 0.95), 1, -1)
        cv2.circle(pupil, (int(x - r * 0.15), int(y - r * 0.1)), int(r * 0.38), 1, -1)
    glow = cv2.GaussianBlur(glow, (0, 0), 9) * 0.55 * strength
    core = cv2.GaussianBlur(core, (0, 0), 1.5) * strength; pupil = cv2.GaussianBlur(pupil, (0, 0), 1.2) * strength
    red = np.array([1.0, 0.08, 0.03], np.float32)
    f = f + glow[..., None] * red * 0.9
    f = f * (1 - core[..., None]) + red * core[..., None]
    f = f * (1 - pupil[..., None]) + np.array([0.05, 0.0, 0.0]) * pupil[..., None]
    hl = np.zeros_like(glow)
    for x, y, _ in eyes:
        cv2.circle(hl, (int(x + rm * 0.25), int(y - rm * 0.3)), max(2, int(rm * 0.16)), 1, -1)
    f = f * (1 - hl[..., None] * strength) + hl[..., None] * strength
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)

def main(src, dst, dbg=None):
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "fast", "-crf", "10",
                           "-pix_fmt", "yuv420p", "-c:a", "copy", dst], stdin=subprocess.PIPE)
    prev = None; seg_prev = None; eye_hist = []; i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        t = i / FPS
        seg = next(sg for sg in SEGS if sg[0] <= t < sg[1] + 1e-6) if t < SEGS[-1][1] else SEGS[-1]
        if seg is not seg_prev: prev = None; eye_hist = []; seg_prev = seg
        out = recolor(rgb, seg[2], seg[3])
        if seg[4]:
            box = lerp_box(seg[4], t)
            m = mask_step(rgb, box, prev)
            m = m if prev is None else 0.65 * m + 0.35 * prev
            prev = m
            out = paint_orange(out, m)
            if seg[5]:
                e, head = find_eyes(rgb, m)
                pred = None
                if eye_hist and head:   # last good eyes, carried along with the head box
                    hx, hy, hw = head
                    pred = [(hx + rx * hw, hy + ry * hw, rr * hw) for rx, ry, rr in eye_hist[-1]]
                if e:
                    e = sorted(e)
                    if pred and max(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(e, pred)) > head[2] * 0.18:
                        e = pred
                    elif pred:
                        e = [tuple(0.5 * np.array(a) + 0.5 * np.array(b)) for a, b in zip(e, pred)]
                else:
                    e = pred or []
                if e and head:
                    hx, hy, hw = head
                    eye_hist.append([((x - hx) / hw, (y - hy) / hw, r / hw) for x, y, r in e])
                out = draw_eyes(out, e)
            if dbg and i % 15 == 0:
                v = out.copy(); cv2.rectangle(v, box[:2], box[2:], (255, 0, 0), 3)
                cv2.imwrite(f"{dbg}/d_{i:03d}.jpg", cv2.cvtColor(cv2.resize(v, (360, 640)), cv2.COLOR_RGB2BGR))
        wr.stdin.write(out.tobytes()); i += 1
    wr.stdin.close(); wr.wait(); rd.wait()
    print("frames", i)

if __name__ == "__main__":
    main(*sys.argv[1:])
