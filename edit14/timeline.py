"""Shared timeline for the ESP32 + OLED rotary-encoder LED flow short (24 fps, 468 frames = 19.5 s
story, + 2.5 s outro = 22 s). knob(f): encoder shaft angle in degrees (+ = clockwise);
1 detent = 18 deg (20 per turn), and every detent moves the LED 'flow' by one LED."""
import math

FPS, N = 24, 468
#        hook  setup  encoder  cw  ccw  press  end
SHOTS = [0, 60, 120, 180, 270, 348, 408]
NLED = 8
DETENT = 18.0
PRESS = 360                         # knob pushed in -> BREATHE mode


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def knob(f):
    a = 0.0
    a += 360 * ease((f - 4) / 40)                         # hook: one fast turn
    a += 2 * 360 * ease((f - SHOTS[3] - 4) / 80)          # clockwise: two slow turns
    a -= 2 * 360 * ease((f - SHOTS[4] - 4) / 70)          # counter-clockwise: two turns back
    a += 10 * math.sin(f * 0.6) * (SHOTS[1] <= f < SHOTS[3])  # setup / encoder: gentle wiggle
    return a


def step(f):
    return int(math.floor(knob(f) / DETENT + 1e-6))


def direction(f):
    d = knob(f + 1) - knob(f - 1)
    return 1 if d > 0.8 else -1 if d < -0.8 else 0


def pressed(f):
    return PRESS <= f < PRESS + 6


def mode(f):
    return "BREATHE" if f >= PRESS + 2 else "FLOW"


def leds(f):
    """Brightness 0..1 for each of the 8 LEDs."""
    if mode(f) == "BREATHE":
        b = 0.15 + 0.85 * (0.5 - 0.5 * math.cos((f - PRESS) * 0.22))
        return [b] * NLED
    head = step(f) % NLED
    d = direction(f) or 1
    out = [0.0] * NLED
    for k_ in range(3):                                  # head + 2-LED fading tail behind it
        out[(head - d * k_) % NLED] = max(out[(head - d * k_) % NLED], (1.0, 0.45, 0.15)[k_])
    return out


def busy(f):
    """ESP32 onboard LED blinks on every detent (shared edit10 board builder)."""
    return step(f) != step(f - 1)
