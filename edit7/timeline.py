"""Shared timeline for the ESP32 'Tap to Light' short (24 fps, 336 frames = 14 s)."""
FPS, N = 24, 336
#        hook  esp32  app   taps  macro party  end
SHOTS = [0, 54, 102, 150, 210, 258, 300]
POWER_ON = 66            # USB power: red PWR led + onboard blue blink (shot 1)
CONNECT = (112, 126)     # tap CONNECT -> 'Connected' (shot 2)
PARTY = (262, 300)       # chase mode, room lights dim
COLORS = ["RED", "YELLOW", "GREEN", "BLUE"]
# (frame, button) phone taps; button = colour index, "ALL", "OFF", "PARTY", "CONNECT"
TAPS = [(12, "ALL"), (40, "OFF"), (CONNECT[0], "CONNECT"), (156, 0), (169, 1), (182, 2), (195, 3),
        (226, 3), (238, 3), (PARTY[0], "PARTY"), (302, "ALL")]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def leds(f):
    """On/off state of the 4 breadboard LEDs at frame f."""
    if PARTY[0] + 2 <= f < PARTY[1] + 2:
        k = (f - PARTY[0]) // 3
        pat = k % 12
        if pat < 8:                                      # chase back and forth
            i = pat if pat < 4 else 7 - pat
            return [j == i for j in range(4)]
        return [pat % 2 == 0] * 4                         # strobe all
    st = [False] * 4
    for t, b in TAPS:
        if t + 2 > f:
            break
        if b == "ALL":
            st = [True] * 4
        elif b == "OFF":
            st = [False] * 4
        elif isinstance(b, int):
            st[b] = not st[b]
    if f < 150 and f >= 54:                              # esp32 + app shots: all off
        return [False] * 4
    return st


def connected(f):
    return not (SHOTS[1] <= f < CONNECT[1])


def power(f):
    return not (SHOTS[1] <= f < POWER_ON)


def dim(f):
    return ease((f - PARTY[0]) / 8) * (1 - 0.55 * ease((f - PARTY[1]) / 10))
