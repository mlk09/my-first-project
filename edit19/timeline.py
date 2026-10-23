"""Shared timeline for the ESP32 + OLED + TTP223 touch-sensor '3 modes' short (24 fps, 468 frames =
19.5 s story, + 2.5 s outro = 22 s). A finger taps the touch pad; the knob picks the mode:
LAMP (tap toggles the LED), BELL (tap = ding-dong + blinking LED), COUNT (taps count up, a long
press resets)."""
import math

FPS, N = 24, 468
#        hook  setup  sensor  lamp  bell  count  end
SHOTS = [0, 60, 120, 180, 252, 330, 408]
DETENT = 18.0
MODES = ["LAMP", "BELL", "COUNT"]
# (start frame, length) of every touch
TOUCHES = [(12, 6), (140, 30), (206, 6), (232, 6), (278, 6),
           (350, 4), (358, 4), (366, 4), (374, 4), (382, 4), (388, 18)]
HOLD = TOUCHES[-1]
KNOB_CLICKS = [(186, 0), (256, 1), (334, 2)]      # (frame, mode index after the click)
BELL_AT = TOUCHES[4][0]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def touching(f):
    return any(s <= f < s + n for s, n in TOUCHES)


def touch_amt(f):
    """0..1 finger press depth (for the pointer animation)."""
    best = 0.0
    for s, n in TOUCHES:
        a = f - s
        best = max(best, ease((a + 5) / 5) * (1 - ease((a - n) / 5)))
    return best


def mode_idx(f):
    m = 0
    for c, i in KNOB_CLICKS:
        if f >= c + 5:
            m = i
    return m


def mode(f):
    if f < SHOTS[3]:
        return "INTRO"
    return MODES[mode_idx(f)] if f < SHOTS[6] else "LAMP"


def knob(f):
    a = 0.0
    for c, _ in KNOB_CLICKS:
        a -= DETENT * ease((f - c) / 8)
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def taps_before(f, lo, hi):
    return sum(1 for s, n in TOUCHES if lo <= s <= f and s < hi)


def count(f):
    if f < SHOTS[5]:
        return 0
    if f >= HOLD[0] + HOLD[1] - 2:
        return 0
    return sum(1 for s, n in TOUCHES[5:10] if s <= f)


def hold_prog(f):
    s, n = HOLD
    return min(max((f - s) / (n - 2), 0.0), 1.0) if s <= f < s + n + 8 else 0.0


def reset_at(f):
    return HOLD[0] + HOLD[1] - 2 <= f < HOLD[0] + HOLD[1] + 22


def led(f):
    """Blue LED state."""
    if f < SHOTS[1]:
        return f >= TOUCHES[0][0]
    if f < SHOTS[2]:
        return False
    if f < SHOTS[3]:
        return touching(f)                                      # sensor demo: LED follows the finger
    if f < SHOTS[4]:
        return TOUCHES[2][0] <= f < TOUCHES[3][0]
    if f < SHOTS[5]:
        a = f - BELL_AT
        return 0 <= a < 36 and (a // 4) % 2 == 0
    if f < SHOTS[6]:
        return touching(f) and f < HOLD[0] or reset_at(f) and (f // 3) % 2 == 0
    return True


def busy(f):
    return touching(f)
