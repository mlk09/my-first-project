"""Shared timeline for the ESP32 + OLED Flappy Bird short (24 fps, 468 frames = 19.5 s story, + 2.5 s
outro = 22 s). The KY-040 knob picks the level (turn) and flaps the bird (press). The game runs in
128x64 OLED coordinates with a deterministic auto-pilot: it flaps through every gap, passes 7 pipes,
then misses the 8th -> GAME OVER -> NEW HIGH SCORE.
game(f) -> dict(bird_y, vel, pipes[(x, gap_y)], score, state, flap)"""
import math

FPS, N = 24, 468
#        hook  setup  menu  play  crash  best  end
SHOTS = [0, 60, 120, 180, 326, 362, 408]
DETENT = 18.0
LEVELS = ["EASY", "NORMAL", "HARD"]
LEVEL_CLICKS = [(128, 1), (140, 2)]            # knob turns in the menu shot (frame, level after)
START = 156                                    # knob press = START, then 3-2-1
PLAY0 = 180                                    # first gameplay frame
HOOK_PLAY = (0, 56)                            # the hook shows a short burst of play
GRAV, FLAP_V, SPEED = 0.30, -2.6, 2.2          # px / frame^2, px / frame, px / frame
PIPE_GAP, PIPE_W, PIPE_DX = 24, 12, 52
BIRD_X = 30
HIGH_OLD = 3


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _gap(i):
    return 24 + int(16 * (0.5 + 0.5 * math.sin(i * 1.9 + 0.7)))


def _sim(n_frames, crash_pipe=None, seed_x=130):
    """Run the auto-pilot for n_frames; returns per-frame states."""
    y, v = 26.0, 0.0
    pipes = [(seed_x + i * PIPE_DX, _gap(i), i) for i in range(12)]
    out, score, state, dead_at = [], 0, "PLAY", None
    for k in range(n_frames):
        flap = False
        if state == "PLAY":
            nxt = min((p for p in pipes if p[0] + PIPE_W >= BIRD_X - 4), key=lambda p: p[0])
            target = nxt[1] + 2
            give_up = crash_pipe is not None and nxt[2] == crash_pipe and nxt[0] < BIRD_X + 40
            if not give_up and y > target + 4 and v > 0:
                v, flap = FLAP_V, True
            v += GRAV
            y += v
            pipes = [(x - SPEED, g, i) for x, g, i in pipes]
            for x, g, i in pipes:
                if x + PIPE_W < BIRD_X and x + PIPE_W + SPEED >= BIRD_X:
                    score += 1
            for x, g, i in pipes:                                  # collision
                if x - 3 < BIRD_X + 3 and x + PIPE_W > BIRD_X - 3 and not (g - PIPE_GAP / 2 < y - 3 and y + 3 < g + PIPE_GAP / 2):
                    state, dead_at = "DEAD", k
            if y > 58:
                state, dead_at = "DEAD", k
        else:                                                      # tumble to the ground
            v = min(v + GRAV * 1.4, 5)
            y = min(58.0, y + v)
        out.append(dict(bird_y=y, vel=v, pipes=[(x, g) for x, g, _ in pipes if -PIPE_W < x < 140],
                        score=score, state=state, flap=flap, dead_at=dead_at))
    return out


_MAIN = None
_HOOK = None


def _main():
    global _MAIN, _HOOK
    if _MAIN is None:
        _MAIN = _sim(SHOTS[5] - PLAY0 + 40, crash_pipe=5)
        _HOOK = _sim(HOOK_PLAY[1] + 2, seed_x=70)
    return _MAIN, _HOOK


def phase(f):
    if f < SHOTS[1]:
        return "hook"
    if f < SHOTS[2]:
        return "title"
    if f < START:
        return "menu"
    if f < PLAY0:
        return "count"
    g = game(f)
    if g and g["state"] == "DEAD":
        return "best" if f >= crash_frame() + 26 and f < SHOTS[6] else ("over" if f < SHOTS[6] else "title")
    return "play" if f < SHOTS[6] else "title"


def game(f):
    m, h = _main()
    if f < SHOTS[1]:
        return h[max(0, min(len(h) - 1, f))]
    if PLAY0 <= f < SHOTS[6]:
        return m[min(len(m) - 1, f - PLAY0)]
    return None


def crash_frame():
    m, _ = _main()
    return PLAY0 + next(k for k, s in enumerate(m) if s["state"] == "DEAD")


def final_score():
    m, _ = _main()
    return m[crash_frame() - PLAY0]["score"]


def level(f):
    lv = 0
    for c, i in LEVEL_CLICKS:
        if f >= c + 4:
            lv = i
    return min(lv, 1) if f >= START else lv          # plays on NORMAL after the HARD tease


def countdown(f):
    return 3 - (f - START) // 8 if START <= f < PLAY0 else 0


def flapping(f):
    g = game(f)
    return bool(g and g["flap"])


def pressed(f):
    return any(flapping(k) for k in range(f - 2, f + 1)) or START <= f < START + 4


def knob(f):
    a = 0.0
    for c, i in LEVEL_CLICKS:
        a -= DETENT * ease((f - c) / 6)
    a += DETENT * ease((f - START + 10) / 6)                      # back to NORMAL before START
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def busy(f):
    return pressed(f)
