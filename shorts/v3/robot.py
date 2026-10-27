"""Robot cut-out (GrabCut inside a keyframed box) and WALL-E orange repaint."""
import numpy as np, cv2

def lerp_box(keys, t):
    ts = [k[0] for k in keys]
    if t <= ts[0]: return keys[0][1]
    if t >= ts[-1]: return keys[-1][1]
    i = np.searchsorted(ts, t) - 1; a = (t - ts[i]) / (ts[i+1] - ts[i])
    return tuple(int(p + (q - p) * a) for p, q in zip(keys[i][1], keys[i+1][1]))

def robot_mask(rgb, box, prev=None, scale=0.5):
    H, W = rgb.shape[:2]
    small = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    bgr = cv2.cvtColor(small, cv2.COLOR_RGB2BGR)
    x0, y0, x1, y1 = [int(v * scale) for v in box]
    x0, y0 = max(x0, 1), max(y0, 1); x1, y1 = min(x1, small.shape[1]-2), min(y1, small.shape[0]-2)
    m = np.zeros(small.shape[:2], np.uint8); bgd = np.zeros((1, 65)); fgd = np.zeros((1, 65))
    if prev is not None:
        p = cv2.resize(prev, (small.shape[1], small.shape[0])) > 0.5
        m[:] = cv2.GC_BGD
        m[y0:y1, x0:x1] = cv2.GC_PR_BGD
        m[(cv2.dilate(p.astype(np.uint8), np.ones((9, 9))) > 0) & (m == cv2.GC_PR_BGD)] = cv2.GC_PR_FGD
        core = cv2.erode(p.astype(np.uint8), np.ones((7, 7))) > 0
        m[core & (m != cv2.GC_BGD)] = cv2.GC_FGD
        cv2.grabCut(bgr, m, None, bgd, fgd, 3, cv2.GC_INIT_WITH_MASK)
    else:
        cv2.grabCut(bgr, m, (x0, y0, x1 - x0, y1 - y0), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
    # keep the largest blob, close small holes
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        fg = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5)))
    return cv2.resize(fg.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)

def paint_orange(rgb, mask):
    """Repaint masked pixels WALL-E orange, keeping the original shading."""
    a = cv2.GaussianBlur(mask, (0, 0), 2.5)[..., None]
    f = rgb.astype(np.float32) / 255
    lum = (0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2])[..., None]
    orange = np.array([1.0, 0.42, 0.05], np.float32)
    shade = np.clip(lum * 2.1, 0, 1.25) ** 0.9
    dark = np.clip((lum - 0.05) / 0.12, 0, 1)            # deep shadows/joints stay dark grey
    col = orange * shade * dark + lum * 1.1 * (1 - dark)
    col = np.clip(col + 0.25 * np.clip(lum - 0.55, 0, 1), 0, 1)  # keep specular highlights
    out = f * (1 - a) + col * a
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
