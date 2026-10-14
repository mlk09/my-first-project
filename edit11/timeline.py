"""Shared timeline for the ESP32 + OLED ultrasonic radar short (24 fps, 384 frames = 16 s).
sweep(f): servo/sensor heading in degrees (15..165, 90 = straight towards the camera side)."""

FPS, N = 24, 384
#        hook  setup  sensor  clear  alarm  normal  end
SHOTS = [0, 48, 96, 150, 210, 270, 324]
BOOT = 3
PERIOD = 56                         # frames for one full left-right-left sweep
OBJ_ANGLE, OBJ_DIST = 110.0, 13.0   # where the intruder cube stops (deg, cm from the sensor)
PRESENT = [(4, 44), (218, 286)]     # cube slides in at the first frame, out at the second
SLIDE = 9                           # frames to slide in / out


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def sweep(f):
    u = ((f + 22) % PERIOD) / PERIOD          # phase picked so the beam crosses the cube right after it arrives
    tri = 1 - abs(2 * u - 1)
    return 15 + 150 * tri


def presence(f):
    """0..1: how far the cube has slid into its spot."""
    v = 0.0
    for a, b in PRESENT:
        v = max(v, ease((f - a) / SLIDE) * (1 - ease((f - b) / SLIDE)))
    return v


def detected(f):
    return presence(f) > 0.95 and abs(sweep(f) - OBJ_ANGLE) < 9


def last_hit(f):
    for k in range(0, 40):
        if f - k >= 0 and detected(f - k):
            return f - k
    return None


def alarm(f):
    """Alarm stays on while the cube is there and was seen in the last ~1.6 s."""
    return presence(f) > 0.5 and last_hit(f) is not None


def first_alarm(a, b):
    for f in range(a, b):
        if alarm(f):
            return f
    return None


def ping(f):
    """True on frames where the sensor fires a burst (every 4 frames)."""
    return f >= BOOT and f % 4 == 0


if __name__ == "__main__":
    print([f for f in range(N) if detected(f)])
    print("alarm starts", first_alarm(0, 48), first_alarm(210, 270))


def busy(f):
    """ESP32 onboard LED activity (used by the shared edit10 board builder)."""
    return alarm(f)
