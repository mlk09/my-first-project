"""Shared timeline for the ESP32 + OLED + HC-SR04 object-detection alarm short (24 fps, 468 frames
= 19.5 s story, + 2.5 s outro = 22 s). A red wooden block slides towards the ultrasonic sensor;
dist(f) is its distance in cm, the knob sets the alarm range (20 -> 10 cm) and alert(f) drives the
red LED + buzzer (green LED = area clear)."""
import math

FPS, N = 24, 468
#        hook  setup  sensor  knob  approach  away  end
SHOTS = [0, 60, 120, 180, 240, 336, 408]
DETENT = 18.0
STEP = 5.0                       # cm per knob detent
FAR = 40.0
PULSE = 12                       # one ultrasonic ping every 12 frames (~2 Hz)
HYST = 0.5


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 2.2


def dist(f):
    if f < SHOTS[1]:                                   # hook: block rushes in
        return FAR - (FAR - 5) * ease_out((f - 2) / 22)
    if f < SHOTS[2]:
        return FAR
    if f < SHOTS[4] + 6:                               # sensor + knob shots: parked at 22 cm
        return 22.0
    if f < SHOTS[5] + 4:                               # slow approach 22 -> 4 cm
        return 22 - 18 * ease((f - SHOTS[4] - 6) / 80)
    return 4 + (FAR - 4) * ease((f - SHOTS[5] - 4) / 44)


def knob(f):
    """Knob angle: 2 detents counter-clockwise in the knob shot = range 20 -> 10 cm."""
    return -2 * DETENT * ease((f - SHOTS[3] - 10) / 30) + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def rng(f):
    return 20.0 + STEP * round(knob(f) / DETENT)


_A = None


def alert(f):
    global _A
    if _A is None:
        out, on = [], False
        for k in range(N + 2):
            d, r = dist(k), rng(k)
            if not on and d < r - HYST:
                on = True
            elif on and d > r + HYST:
                on = False
            out.append(on)
        _A = out
    return _A[min(max(int(f), 0), N + 1)]


def busy(f):
    """ESP32 onboard LED blinks with every ping."""
    return f % PULSE < 2
