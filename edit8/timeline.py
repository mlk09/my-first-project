"""Shared timeline for the ESP32 RFID smart door lock short (24 fps, 384 frames = 16 s)."""
FPS, N = 24, 384
#        hook  door  circuit denied granted servo  open/end
SHOTS = [0, 48, 96, 144, 204, 264, 324]
# (frame, result) RFID reads: the hook flash-forward, a wrong card, the right key fob
READS = [(12, "OK"), (162, "NO"), (224, "OK")]
UID_OK, UID_BAD = "4A 2F 9C 11", "E3 07 5B A2"
DOOR_OPEN = (332, 362)


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def unlocked(f):
    """Bolt/servo open amount 0..1."""
    hook = ease((f - 15) / 6) * (1 - ease((f - 40) / 6))
    main = ease((f - 270) / 10)
    return max(hook, main) if f < SHOTS[1] or f >= 264 else 0.0


def servo_deg(f):
    return 10 + 160 * unlocked(f)


def green(f):
    return any(r == "OK" and t + 1 <= f < t + 50 for t, r in READS)


def red(f):
    return any(r == "NO" and t + 1 <= f < t + 32 and ((f - t) // 4) % 2 == 0 for t, r in READS)


def door_angle(f):
    return 72 * ease((f - DOOR_OPEN[0]) / (DOOR_OPEN[1] - DOOR_OPEN[0]))


def fob(f):
    """0 = away, 1 = touching the reader (hook + granted shot)."""
    return max(ease((f - 2) / 9) * (1 - ease((f - 30) / 10)),
               ease((f - 208) / 15) * (1 - ease((f - 250) / 12)))


def card(f):
    return ease((f - 146) / 15) * (1 - ease((f - 186) / 12))
