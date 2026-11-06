"""Timeline for the ESP32 Smart Dustbin short (13 s loop format, 24 fps, 312 frames). An HC-SR04 on the
front of a small bin measures the distance to the hand; under 20 cm the SG90 servo opens the lid, the
hand drops its rubbish in and the lid closes ~2.5 s after the last detection. Throw 1 (paper ball) is
already under way at frame 0, throw 2 (a can) follows, throw 3 starts so that the last frame matches the
first (seamless loop). All positions in cm (Blender units)."""
import math

FPS, N = 24, 312
#        hook  drop  oled  hand2  drop2  data  loop
SHOTS = [0, 30, 60, 110, 160, 230, 270]
D = (10.5, -3.5, 0.0)                    # bin centre on the table
BIN_W, BIN_DEP, BIN_H = 6.0, 5.0, 7.0
FRONT_Y = D[1] - BIN_DEP / 2             # -6.0
SENS_Y = FRONT_Y - 0.8                   # sensor cans' face
HINGE = (D[0], D[1] + BIN_DEP / 2, BIN_H)
DETECT = 20.0
HOLD = 60                                # frames the lid stays open after the last detection
THROWS = [(-20, "ball"), (116, "can"), (292, "ball")]
REL_U = 46                               # local frame the hand lets go
GRAV = 0.2                               # cm / frame^2


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


P_OFF = (D[0] + 24, -10.0, 15.0)
P0 = (D[0] + 5, -14.0, 7.5)
P1 = (D[0], SENS_Y - 8.0, 5.0)
P2 = (D[0], D[1], BIN_H + 6.0)
P3 = (D[0] + 13, -15.0, 17.0)


def hand_local(u):
    keys = [(0, P_OFF), (10, P0), (26, P1), (44, P2), (48, P2), (74, P3), (90, P_OFF)]
    if u <= 0:
        return P_OFF
    for (a, pa), (b, pb) in zip(keys, keys[1:]):
        if a <= u <= b:
            return lerp(pa, pb, ease((u - a) / (b - a)))
    return P_OFF


def active_throw(f):
    best = None
    for t0, kind in THROWS:
        if t0 <= f < t0 + 90:
            best = (t0, kind)
    return best


def hand(f):
    a = active_throw(f)
    return hand_local(f - a[0]) if a else P_OFF


def dist(f):
    x, y, z = hand(f)
    if y < SENS_Y and abs(x - D[0]) < 5 and z < 14:
        return max(2.0, SENS_Y - y)
    return None


def detected(f):
    d = dist(f)
    return d is not None and d < DETECT


_LID = None


def _lid_all():
    global _LID
    if _LID is None:
        out, ang, last = [], 0.0, -999
        for f in range(-120, N + 120):
            if detected(f):
                last = f
            tgt = 1.0 if f - last <= HOLD else 0.0
            ang += max(-1 / 14, min(1 / 10, tgt - ang))
            out.append(ang)
        _LID = out
    return _LID


def lid(f):
    """Lid opening 0..1 (eased)."""
    return ease(_lid_all()[f + 120])


def lid_open(f):
    return lid(f) > 0.5


def item(f, t0, kind):
    """World position of the throw's item at frame f, or None if not visible."""
    u = f - t0
    if u < 0:
        return None
    rest_z = 0.25 + (0.9 if kind == "ball" else 1.1)
    off = (-1.0, -0.1, -1.6)
    if u <= REL_U:
        h = hand_local(u)
        return (h[0] + off[0], h[1] + off[1], h[2] + off[2])
    h = hand_local(REL_U)
    z0 = h[2] + off[2]
    t = u - REL_U
    z = z0 - 0.5 * GRAV * t * t
    dx = 0.8 if kind == "ball" else -0.9
    if z <= rest_z:
        tl = math.sqrt(2 * (z0 - rest_z) / GRAV)
        b = max(0.0, 0.8 * math.sin(min(math.pi, (t - tl) * 0.5))) * math.exp(-(t - tl) * 0.15)
        z = rest_z + b
        return (h[0] + dx, h[1] + 0.3, z)
    k = t / math.sqrt(2 * (z0 - rest_z) / GRAV)
    return (h[0] + dx * k, h[1] + 0.3 * k, z)


def landed(f):
    """Frames where an item hits the bottom (for SFX)."""
    out = []
    for t0, kind in THROWS:
        z0 = hand_local(REL_U)[2] - 1.6
        rest = 0.25 + (0.9 if kind == "ball" else 1.1)
        out.append((t0 + REL_U + int(math.sqrt(2 * (z0 - rest) / GRAV)), kind))
    return out


def items(f):
    """Rubbish count shown on the display (resets for the loop)."""
    n = 0
    for (t0, kind), (lf, _) in zip(THROWS[:2], landed(0)[:2]):
        if f >= lf:
            n += 1
    return n


def open_frames():
    return [f for f in range(N) if lid_open(f) and not lid_open(f - 1)]


def close_frames():
    return [f for f in range(N) if not lid_open(f) and lid_open(f - 1)]


if __name__ == "__main__":
    print("open", open_frames(), "close", close_frames(), "land", landed(0))
    print([(f, None if dist(f) is None else round(dist(f)), round(lid(f), 2), items(f)) for f in range(0, N, 12)])
