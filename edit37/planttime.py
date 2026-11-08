"""Timeline for the ESP32 Smart Plant Watering short (13 s loop, 24 fps, 312 frames). A capacitive soil
moisture probe reads the pot; below 30 % the relay starts a mini pump, water runs through a clear tube onto
the soil until ~70 %, then the pump stops. The plant perks up and gets its colour back. In the last shot
'3 days later' the soil dries back to 12 % so the last frame loops into the first."""
import math

FPS, N = 24, 312
#        hook  oled  water  happy  data  loop
SHOTS = [0, 30, 60, 150, 222, 270]
DRY, WET, LOW = 12.0, 72.0, 30.0
PUMP_ON, PUMP_OFF = 52, 124             # relay frames
FLOW_DELAY = 6                           # water reaches the tube end this many frames after the pump starts
DRYING = 274                             # '3 din baad' - moisture falls back


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def pump(f):
    return PUMP_ON <= f < PUMP_OFF


def flow(f):
    """Water stream amount 0..1 at the tube end."""
    a = ease((f - PUMP_ON - FLOW_DELAY) / 5)
    b = 1 - ease((f - PUMP_OFF - 2) / 6)
    return max(0.0, min(a, b))


def moisture(f):
    if f < PUMP_ON + FLOW_DELAY + 4:
        return DRY + 0.4 * math.sin(f * 0.2)
    if f < DRYING:
        u = (f - PUMP_ON - FLOW_DELAY - 4) / (PUMP_OFF - PUMP_ON - FLOW_DELAY)
        return DRY + (WET - DRY) * ease(u)
    return WET - (WET - DRY) * ease((f - DRYING) / (N - DRYING - 6))


def wet(f):
    """0 = dry soil / drooping B&W plant, 1 = wet soil / fresh green plant (lags the moisture)."""
    return ease((moisture(f) - DRY - 6) / (WET - DRY - 14))


def state(f):
    if pump(f):
        return "WATERING"
    return "WET" if moisture(f) >= LOW + 10 else "DRY"


def history(f, n=60):
    """Last n moisture samples (one per 3 frames) for the panel graph."""
    return [moisture(max(0, f - 3 * (n - 1 - i))) for i in range(n)]


if __name__ == "__main__":
    print([(f, round(moisture(f)), state(f), round(wet(f), 2), round(flow(f), 2)) for f in range(0, N, 12)])
