"""Shared timeline for the ESP32 + OLED + MQ-2 gas-leak alarm short (24 fps, 468 frames = 19.5 s story,
+ 2.5 s outro = 22 s). A small LPG cylinder's valve opens, a gas cloud drifts to the MQ-2, ppm(f)
climbs; the knob sets the alarm limit (400 -> 300 ppm); above the limit the red LED + buzzer fire and
the exhaust fan spins up; the fan clears the gas -> SAFE (green LED)."""
import math

FPS, N = 24, 468
#        hook  setup  sensor  knob  leak  clear  end
SHOTS = [0, 60, 120, 180, 240, 336, 408]
DETENT = 18.0
STEP = 50                                     # ppm per knob click
LIMIT0 = 400
CLEAN = 80                                    # clean-air reading
HYST = 20


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def leak(f):
    """0..1 how much gas the cylinder is releasing."""
    return max(ease((f - 2) / 8) * (1 - ease((f - 40) / 10)), ease((f - SHOTS[4] - 6) / 10) * (1 - ease((f - SHOTS[5] + 10) / 10)))


def knob(f):
    return 2 * DETENT * ease((f - SHOTS[3] - 10) / 30) + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def limit(f):
    return LIMIT0 - STEP * round(knob(f) / DETENT)


_T = None


def _table():
    global _T
    if _T is None:
        out, gas, fan_on, al = [], 0.0, 0.0, False
        rows = []
        for k in range(N + 2):
            gas += 0.11 * leak(k) * (1.0 - gas) - gas * (0.012 + 0.10 * fan_on)
            gas = max(0.0, gas)
            p = CLEAN + 820 * gas + 6 * math.sin(k * 0.9)
            lim = limit(k)
            if not al and p > lim + HYST:
                al = True
            elif al and p < lim - HYST:
                al = False
            fan_on = min(1.0, fan_on + 0.08) if al or (fan_on > 0 and p > lim - 120) else max(0.0, fan_on - 0.04)
            rows.append((p, al, fan_on, gas))
        _T = rows
    return _T


def _row(f):
    return _table()[min(max(int(f), 0), N + 1)]


def ppm(f):
    return _row(f)[0]


def alarm(f):
    return _row(f)[1]


def fan(f):
    """0..1 fan speed."""
    return _row(f)[2]


def gas(f):
    """0..1 gas concentration near the sensor (drives the cloud size / opacity)."""
    return _row(f)[3]


def fan_angle(f):
    return sum(fan(k) * 55.0 for k in range(0, int(f) + 1))


def busy(f):
    return f % 12 < 2
