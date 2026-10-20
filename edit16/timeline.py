"""Shared timeline for the ESP32 + OLED + DHT11 temperature-controlled LED short (24 fps, 468 frames
= 19.5 s story, + 2.5 s outro = 22 s). A hot coffee mug is brought next to the DHT11; temp(f) rises,
the knob sets the limit, and the red LED switches ON above the limit (blue 'OK' LED otherwise)."""
import math

FPS, N = 24, 468
#        hook  setup  dht  knob  heat  cool  end
SHOTS = [0, 60, 120, 180, 240, 336, 408]
DETENT = 18.0
HYST = 0.4                                        # degC hysteresis on the switch


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def mug(f):
    """0 = mug away, 1 = right next to the DHT11."""
    return max(ease((f - 2) / 14) * (1 - ease((f - 46) / 12)),
               ease((f - SHOTS[4] - 2) / 16) * (1 - ease((f - SHOTS[5] - 4) / 14)))


_T = None


def _table():
    global _T
    if _T is None:
        room, t, out = 26.0, 26.0, []
        for k in range(N + 2):
            target = room + 9.0 * mug(k)
            t += (target - t) * (0.06 if target > t else 0.055)
            out.append(t)
        _T = out
    return _T


def temp(f):
    f = min(max(int(f), 0), N + 1)
    return _table()[f] + 0.08 * math.sin(f * 0.7)


def hum(f):
    return 58.0 - 0.9 * (temp(f) - 26.0) + 0.3 * math.sin(f * 0.31)


def knob(f):
    """Knob angle: 2 detents counter-clockwise in the knob shot = limit 30 -> 28 degC."""
    return -2 * DETENT * ease((f - SHOTS[3] - 10) / 30) + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def limit(f):
    return 30.0 + round(knob(f) / DETENT)


def _hot_table():
    out, on = [], False
    for k in range(N + 2):
        t, lim = temp(k), limit(k)
        if not on and t > lim + HYST:
            on = True
        elif on and t < lim - HYST:
            on = False
        out.append(on)
    return out


_H = None


def hot(f):
    global _H
    if _H is None:
        _H = _hot_table()
    return _H[min(max(int(f), 0), N + 1)]


def busy(f):
    """ESP32 onboard LED: blinks on every DHT read (every 12 frames ~ 2 Hz)."""
    return f % 12 < 2
