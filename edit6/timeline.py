"""Shared timeline for the Smart Plant IoT short (24 fps, 384 frames = 16 s)."""
import math

FPS, N = 24, 384
#        hook  LDR  graph  R4   slider servo night  end
SHOTS = [0, 48, 96, 144, 192, 240, 288, 336]
SHADOW = (58, 92)        # a hand-shadow sweeps across the LDR (shot 2)
SLIDE = (200, 236)       # phone slider 44 -> 160 deg (shot 5), servo follows (shot 6)
DUSK = (280, 300)        # lights dim; LED switches on at LED_ON
LED_ON = 300


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def night(f):
    return ease((f - DUSK[0]) / (DUSK[1] - DUSK[0])) * (1 - ease((f - 352) / 16))


def shadow(f):
    a, b = SHADOW
    if not a <= f <= b:
        return 0.0
    return math.sin(math.pi * (f - a) / (b - a))


def ldr(f):
    base = 78 + 4 * math.sin(f * 0.35) + 2 * math.sin(f * 1.3)
    return max(3.0, base - 62 * shadow(f) - 70 * night(f))


def servo_deg(f):
    """Slider dragged 44->160 on the phone (shot 5), then swept 160->40->170 while we watch the servo (shot 6)."""
    d = 44 + 116 * ease((f - SLIDE[0]) / (SLIDE[1] - SLIDE[0]))
    d += -120 * ease((f - 242) / 20) + 130 * ease((f - 264) / 20)
    return d - 126 * ease((f - 350) / 20)
