"""Shared timeline for the ESP32 + OLED RGB colour mixer short (24 fps, 468 frames = 19.5 s story,
+ 2.5 s outro = 22 s). One RGB LED under a ping-pong-ball diffuser: the hook flashes R / G / B, the
mix shot adds the channels (R, R+G = yellow, R+G+B = white), the knob sweeps the hue, then sets the
brightness (PWM) and a press starts PARTY mode."""
import colorsys
import math

FPS, N = 24, 468
#        hook  setup  mix  hue  bright  party  end
SHOTS = [0, 60, 120, 180, 264, 348, 408]
DETENT = 18.0                    # knob degrees per click
HUE_STEP = 15.0                  # hue degrees per click
PRESS = SHOTS[5] + 4             # knob press -> party mode
NAMES = [(15, "RED"), (45, "ORANGE"), (70, "YELLOW"), (100, "LIME"), (150, "GREEN"), (195, "CYAN"),
         (250, "BLUE"), (290, "PURPLE"), (340, "PINK"), (361, "RED")]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def hue_clicks(f):
    """Knob clicks in the hue shot: 0 -> 18 clicks (= 270 deg, purple), then holds."""
    return round(18 * ease((f - SHOTS[3] - 8) / 70))


def bright(f):
    """Brightness 0..1: 100 % -> 20 % -> 100 % in the brightness shot."""
    if SHOTS[4] <= f < SHOTS[5]:
        l = f - SHOTS[4] - 6
        return 1 - 0.8 * ease(l / 30) * (1 - ease((l - 46) / 28))
    return 1.0


def bright_clicks(f):
    return round((1 - bright(f)) / 0.1)


def knob(f):
    a = -hue_clicks(f) * DETENT                                   # clockwise = negative z
    a += -bright_clicks(f) * DETENT * (SHOTS[4] <= f < SHOTS[5]) - 0 * f
    a += 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])
    return a


def pressed(f):
    return PRESS <= f < PRESS + 5


def mode(f):
    if f < SHOTS[1]:
        return "hook"
    if f < SHOTS[2]:
        return "idle"
    if f < SHOTS[3]:
        return "mix"
    if f < SHOTS[4]:
        return "hue"
    if f < PRESS:
        return "bright"
    if f < SHOTS[6]:
        return "party"
    return "idle"


def hsv(h, v=1.0):
    return colorsys.hsv_to_rgb((h % 360) / 360.0, 1.0, v)


def hue(f):
    m = mode(f)
    if m == "hue":
        return hue_clicks(f) * HUE_STEP
    if m == "bright":
        return 270.0
    if m == "party":
        return (f - PRESS) * 22.0
    return (f - SHOTS[1]) * 4.0


def rgb(f):
    """LED colour (r, g, b) in 0..1 at frame f."""
    m = mode(f)
    if m == "hook":
        seq = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        i = min(2, max(0, (f - 4) // 16))
        if f < 4:
            return (0, 0, 0)
        if f >= 52:
            return hsv((f - 52) * 45)
        return seq[i]
    if m == "mix":
        l = f - SHOTS[2]
        r = 1.0 if l >= 4 else 0.0
        g = 1.0 if l >= 22 else 0.0
        b = 1.0 if l >= 40 else 0.0
        return (r, g, b)
    return hsv(hue(f), bright(f))


def to255(c):
    return tuple(int(round(255 * x)) for x in c)


def name(f):
    r, g, b = rgb(f)
    if max(r, g, b) < 0.05:
        return "OFF"
    if min(r, g, b) > 0.9:
        return "WHITE"
    h = colorsys.rgb_to_hsv(r, g, b)[0] * 360
    for lim, n in NAMES:
        if h < lim:
            return n
    return "RED"


def busy(f):
    return f % 12 < 2
