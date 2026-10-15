"""Shared timeline for the ESP32 + OLED robot-eyes short (24 fps, 468 frames = 19.5 s story,
+ 2.5 s outro = 22 s). mood(f) drives the OLED eyes; touches(f) the finger on the TTP223 pad."""
import math

FPS, N = 24, 468
#        hook  setup  look  happy  angry  sleepy  end
SHOTS = [0, 60, 120, 192, 264, 336, 408]
WAKE = 8                                   # eyes open in the hook
TAPS = [214, 286, 296, 306, 316]           # finger presses: 1 gentle tap (happy), 4 quick pokes (angry)
TAP_LEN = 6


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def pressed(f):
    return any(t <= f < t + TAP_LEN for t in TAPS)


def finger(f):
    """0 = finger away, 1 = touching the pad. Only around the tap shots."""
    v = 0.0
    for t in TAPS:
        v = max(v, ease((f - t + 5) / 5) * (1 - ease((f - t - TAP_LEN) / 5)))
    near = SHOTS[3] - 4 <= f < SHOTS[5]
    return v if near else 0.0


def mood(f):
    if f < WAKE:
        return "off"
    if f < SHOTS[3]:
        return "idle"
    if f < TAPS[1]:
        return "happy" if f >= TAPS[0] + 2 else "idle"
    if f < SHOTS[5]:
        return "angry" if f >= TAPS[2] + 2 else "happy" if f < TAPS[1] + 2 else "annoyed"
    if f < SHOTS[6]:
        return "sleepy"
    return "love"


def blink(f):
    """0 = open, 1 = closed. Short blinks at fixed beats, plus the wake-up open."""
    if f < WAKE:
        return 1.0
    v = 1 - ease((f - WAKE) / 6)
    for b in (40, 100, 150, 176, 236, 380):
        a = f - b
        if 0 <= a < 6:
            v = max(v, 1 - abs(a - 2.5) / 3)
    return v


def look(f):
    """Eye gaze offset in OLED pixels (x, y)."""
    if SHOTS[2] <= f < SHOTS[3]:
        a = f - SHOTS[2]
        x = -14 * ease(a / 8) * (1 - ease((a - 22) / 8)) + 14 * ease((a - 30) / 8) * (1 - ease((a - 52) / 8))
        y = -6 * ease((a - 56) / 6) * (1 - ease((a - 66) / 6))
        return x, y
    if SHOTS[1] <= f < SHOTS[2]:
        return 3 * math.sin(f * 0.15), 0
    if f < SHOTS[1]:
        return 0, 0
    if mood(f) == "sleepy":
        return 0, 6 * ease((f - SHOTS[5]) / 30)
    return 0, 0


def led(f):
    """RGB LED colour (r, g, b, strength)."""
    m = mood(f)
    if m in ("happy", "love"):
        return (0.1, 1.0, 0.2, 4.0) if m == "happy" else (1.0, 0.1, 0.5, 4.0)
    if m in ("angry", "annoyed"):
        return (1.0, 0.04, 0.02, 4.0 if (f // 3) % 2 == 0 or m == "annoyed" else 1.0)
    if m == "sleepy":
        return (0.1, 0.25, 1.0, 1.0 + 0.8 * math.sin(f * 0.12))
    if m == "idle":
        return (0.2, 0.8, 1.0, 2.0)
    return (0, 0, 0, 0.0)


def busy(f):
    """ESP32 onboard LED (used by the shared edit10 board builder)."""
    return pressed(f)
