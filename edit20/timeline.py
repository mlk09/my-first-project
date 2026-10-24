"""Shared timeline for the ESP32 + OLED + PIR (HC-SR501) motion alarm short (24 fps, 468 frames =
19.5 s story, + 2.5 s outro = 22 s). A little toy 'chor' sneaks into the PIR detection zone; the knob
arms the system (DISARMED -> 3-2-1 -> ARMED); motion in the zone while ARMED fires the red LED +
buzzer + flashing OLED; when he runs away the green LED = ALL CLEAR."""
import math

FPS, N = 24, 468
#        hook  setup  sensor  knob  sneak  away  end
SHOTS = [0, 60, 120, 180, 240, 336, 408]
DETENT = 18.0
ARM_CLICK = SHOTS[3] + 10                       # knob click -> countdown
ARM_AT = ARM_CLICK + 36                         # 3-2-1 then ARMED
ZONE = 9.0                                      # detection range (cm, along the sensor axis)
HALF = math.radians(32)                         # half opening angle of the zone
HOLD = 30                                       # alarm keeps ringing this long after the last motion


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def thief(f):
    """(u, v, walking) of the toy in sensor coordinates: u = distance along the sensor axis,
    v = sideways offset; walking = legs moving."""
    if f < SHOTS[1]:                                   # hook: walks straight in from the right
        p = ease((f + 4) / 30)
        return 6.5, 11 - 11 * p, 0 < p < 1
    if f < SHOTS[4] + 8:                               # off stage
        return 6.5, 16.0, False
    if f < SHOTS[5] + 4:                               # sneak: tiptoes in from the right, stops, looks
        p = ease((f - SHOTS[4] - 8) / 56)
        return 6.0, 14 - 14 * p, 0 < p < 1
    p = min(max((f - SHOTS[5] - 8) / 40, 0.0), 1.0) ** 1.4     # runs back out the way he came
    return 6.0, 45 * p, 0 < p < 1


def in_zone(f):
    u, v, _ = thief(f)
    return 0.5 < u < ZONE and abs(math.atan2(v, u)) < HALF


def armed(f):
    """Hook: already armed; then DISARMED until the knob arms it (after the 3-2-1)."""
    return f < SHOTS[1] or f >= ARM_AT


def countdown(f):
    if ARM_CLICK + 4 <= f < ARM_AT:
        return 3 - (f - ARM_CLICK - 4) // 11
    return 0


def knob(f):
    return -DETENT * ease((f - ARM_CLICK) / 8) + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


_A = None


def _table():
    global _A
    if _A is None:
        out, last = [], -999
        for k in range(N + 2):
            if armed(k) and in_zone(k):
                last = k
            out.append(k - last < HOLD and armed(k))
        _A = out
    return _A


def alarm(f):
    return _table()[min(max(int(f), 0), N + 1)]


def detecting(f):
    return armed(f) and in_zone(f)


def busy(f):
    return detecting(f) and f % 6 < 3
