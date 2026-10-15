"""Shared timeline for the ESP32 + OLED parking sensor short (24 fps, 468 frames = 19.5 s story,
+ 2.5 s outro = 22 s). dist(f): gap between the car's rear bumper and the HC-SR04, in cm."""
FPS, N = 24, 468
#        hook  setup  sensor  reverse  oled  away  end
SHOTS = [0, 60, 120, 180, 282, 348, 408]
BOOT = 3
FAR = 32.0                       # parked start / end distance
SAFE, STOP = 25.0, 10.0          # > SAFE: green, (STOP, SAFE]: yellow, <= STOP: red + continuous tone


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 2.2


def dist(f):
    if f < SHOTS[1]:                                   # hook: already reversing, ends at the wall
        return 22 - 17 * ease_out((f - 2) / 44)
    if f < SHOTS[3] + 6:                               # setup / sensor shots: parked far out
        return FAR
    if f < SHOTS[5] + 8:                               # the long reverse, slowing down near the wall
        u = min(max((f - SHOTS[3] - 6) / 100, 0.0), 1.0)
        return FAR - (FAR - 4) * (1 - (1 - u) ** 1.2)
    return 4 + (FAR - 4) * ease((f - SHOTS[5] - 8) / 40)   # drives away


def zone(f):
    d = dist(f)
    return "SAFE" if d > SAFE else "SLOW" if d > STOP else "STOP"


def moving(f):
    return abs(dist(f + 1) - dist(f - 1)) > 0.05


def reversing(f):
    return dist(f + 1) < dist(f - 1) - 0.05


def beep_on(f):
    """Buzzer state per frame: silent when SAFE, faster beeps as it closes in, solid tone at STOP."""
    if f < BOOT:
        return False
    z = zone(f)
    if z == "SAFE":
        return False
    if z == "STOP":
        return True
    d = dist(f)
    period = int(4 + 12 * (d - STOP) / (SAFE - STOP))     # 16 frames at 25 cm -> 4 frames at 10 cm
    return (f % max(4, period)) < 2


def busy(f):
    """ESP32 onboard LED activity (used by the shared edit10 board builder)."""
    return moving(f) and f % 6 < 3


if __name__ == "__main__":
    for f in (0, 20, 46, 60, 186, 220, 250, 270, 282, 330, 356, 380, 408):
        print(f, round(dist(f), 1), zone(f))
