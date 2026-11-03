"""Timeline for the ESP32 + MAX30102 Heart Rate Monitor short (13 s loop format, 24 fps, 312 frames).
A finger rests on the MAX30102 the whole time; the heart rate follows a little story: calm 74 BPM ->
'Crush ka message aaya' notification -> rises to ~128 BPM (HIGH alarm) -> calms back to 74 so the
last frame loops into the first. beat_frames() = frames where a heart beat (R peak) happens."""
import math

FPS, N = 24, 312
#        hook  finger  normal  high  calm  loop
SHOTS = [0, 30, 60, 150, 222, 270]
NOTIF = 108                     # phone notification pops
HIGH_TH = 110                   # BPM above this = HIGH alarm
SPO2 = 98


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def bpm(t):
    """Continuous heart rate at time t (frames, float)."""
    if t < NOTIF + 4:
        return 74 + 1.5 * math.sin(t * 0.21)
    if t < 172:
        return 74 + 54 * ease((t - NOTIF - 4) / (172 - NOTIF - 4))
    if t < 222:
        return 128 + 2.5 * math.sin(t * 0.3)
    if t < 296:
        return 128 - 52 * ease((t - 222) / 74)
    return 76 - 2 * ease((t - 296) / 16)


# beat phase = integral of bpm / 60 / FPS
_PH = [0.62]
for _i in range(N + 60):
    _PH.append(_PH[-1] + bpm(_i) / 60 / FPS)


def phase(t):
    """Beat phase (float, integer part = beat count) at frame t (float, may be < 0 for ECG history)."""
    if t < 0:
        return _PH[0] + t * 74 / 60 / FPS
    i = int(t)
    i = min(i, len(_PH) - 2)
    return _PH[i] + (_PH[i + 1] - _PH[i]) * (t - i)


R_AT = 0.28                    # R peak position inside one beat


def beat_frames():
    out = []
    for f in range(N):
        a, b = phase(f - 1) - R_AT, phase(f) - R_AT
        if math.floor(b) > math.floor(a):
            out.append(f)
    return out


BEATS = beat_frames()


def since_beat(f):
    prev = [b for b in BEATS if b <= f]
    return f - prev[-1] if prev else 99


def shown_bpm(f):
    """Value on the display: updates on each beat (like a real monitor)."""
    prev = [b for b in BEATS if b <= f]
    return int(round(bpm(prev[-1] if prev else 0)))


def ecg(p):
    """Normalised ECG (PQRST) at beat phase p (any real); returns -0.35..1.0."""
    u = p % 1.0
    g = lambda c, w, a: a * math.exp(-((u - c) / w) ** 2)  # noqa: E731
    return g(0.12, 0.035, 0.12) + g(0.25, 0.012, -0.15) + g(0.28, 0.011, 1.0) + g(0.31, 0.013, -0.3) + g(0.52, 0.06, 0.25)


def high(f):
    return shown_bpm(f) >= HIGH_TH


def state(f):
    return "HIGH" if high(f) else "NORMAL"


def sensor_glow(f):
    """MAX30102 red LED shining through the finger, brighter on each beat."""
    return 0.6 + 0.4 * math.exp(-since_beat(f) / 3.0)


if __name__ == "__main__":
    print("beats", len(BEATS), BEATS[:8], "...")
    print([(f, shown_bpm(f), state(f)) for f in range(0, N, 24)])
    print("high from", next(f for f in range(N) if high(f)), "to", max(f for f in range(N) if high(f)))
