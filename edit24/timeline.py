"""Shared timeline for the ESP32 + OLED Snake (Nokia style) short (24 fps, 468 frames = 19.5 s story,
+ 2.5 s outro = 22 s). The KY-040 knob picks the speed in the menu (turn), starts the game (press) and
steers the snake while playing (1 click left / right = turn). 32 x 14 grid of 4 px cells under an 8 px
score bar. A deterministic auto-pilot eats apples, the snake grows, then bites its own tail ->
GAME OVER -> NEW HIGH SCORE.
game(f) -> dict(body[(x, y) head first], dir, apple, eaten, state, turn, t)"""
import math

FPS, N = 24, 468
#        hook  setup  menu  play  crash  best  end
SHOTS = [0, 60, 120, 180, 320, 352, 408]
DETENT = 18.0
LEVELS = ["SLOW", "NORMAL", "FAST"]
LEVEL_CLICKS = [(128, 1), (140, 2)]
START = 156
PLAY0 = 180
GW, GH, CELL, TOP = 32, 14, 4, 8
STEP = 2                                       # frames per move
APPLES = [(14, 6), (20, 10), (25, 5), (18, 2), (10, 4), (6, 10), (13, 12), (21, 8), (27, 11), (16, 4), (8, 7)]
HOOK_APPLES = [(16, 7), (21, 4), (10, 9)]
GOAL = 7                                       # apples eaten before it bites its tail
HIGH_OLD = 50
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]      # R, D, L, U  (index + 1 = turn right)


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _space(start, blocked):
    seen, stack = {start}, [start]
    while stack and len(seen) < 120:
        x, y = stack.pop()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if 0 <= n[0] < GW and 0 <= n[1] < GH and n not in blocked and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen)


def _sim(n_frames, apples, goal=None):
    body = [(6, 7), (5, 7), (4, 7), (3, 7)]
    d, ai, grow, out, state, turn, eaten = 0, 0, 0, [], "RUN", 0, 0
    for k in range(n_frames):
        turn = 0
        if state == "RUN" and k % STEP == 0 and k > 0:
            hx, hy = body[0]
            apple = apples[ai % len(apples)]
            best = None
            crash_mode = goal is not None and eaten >= goal
            for t in (0, -1, 1):
                nd = (d + t) % 4
                nx, ny = hx + DIRS[nd][0], hy + DIRS[nd][1]
                hit = not (0 <= nx < GW and 0 <= ny < GH) or (nx, ny) in body[:-1]
                if crash_mode:                                       # steer into its own body
                    tx, ty = body[len(body) // 2]
                    if (nx, ny) in body[:-1]:
                        score = -1
                    elif hit:
                        score = 999
                    else:
                        score = abs(nx - tx) + abs(ny - ty)
                else:
                    if hit:
                        continue
                    space = _space((nx, ny), set(body[:-1]))
                    score = abs(nx - apple[0]) + abs(ny - apple[1]) + (100 if space < len(body) + 2 else 0) + 0.1 * t * t
                if best is None or score < best[0]:
                    best = (score, t, nd, nx, ny, hit)
            if best is None:
                state = "DEAD"
            else:
                _, turn, d, nx, ny, hit = best
                if hit:
                    state = "DEAD"
                else:
                    body.insert(0, (nx, ny))
                    if (nx, ny) == apple:
                        eaten += 1
                        ai += 1
                        grow += 3
                    if grow:
                        grow -= 1
                    else:
                        body.pop()
        out.append(dict(body=list(body), dir=d, apple=apples[ai % len(apples)], eaten=eaten, state=state, turn=turn, k=k))
    return out


_M = _H = None


def _main():
    global _M, _H
    if _M is None:
        _M = _sim(SHOTS[6] - PLAY0, APPLES, GOAL)
        _H = _sim(SHOTS[1], HOOK_APPLES)
    return _M, _H


def game(f):
    m, h = _main()
    if f < SHOTS[1]:
        return h[max(0, f)]
    if PLAY0 <= f < SHOTS[6]:
        return m[f - PLAY0]
    return None


def crash_frame():
    m, _ = _main()
    return PLAY0 + next(k for k, s in enumerate(m) if s["state"] == "DEAD")


def final_score():
    m, _ = _main()
    return m[crash_frame() - PLAY0]["eaten"] * 10


def phase(f):
    if f < SHOTS[1]:
        return "hook"
    if f < SHOTS[2]:
        return "title"
    if f < START:
        return "menu"
    if f < PLAY0:
        return "count"
    if f < SHOTS[6]:
        cf = crash_frame()
        return "play" if f < cf else ("over" if f < cf + 26 else "best")
    return "title"


def level(f):
    lv = 0
    for c, i in LEVEL_CLICKS:
        if f >= c + 4:
            lv = i
    return min(lv, 1) if f >= START else lv


def countdown(f):
    return 3 - (f - START) // 8 if START <= f < PLAY0 else 0


def turning(f):
    g = game(f)
    return g["turn"] if g else 0


def flapping(f):
    """Knob clicks while playing (shared name with the other game timelines)."""
    return turning(f) != 0


def pressed(f):
    return START <= f < START + 4


def knob(f):
    a = 0.0
    for c, i in LEVEL_CLICKS:
        a -= DETENT * ease((f - c) / 6)
    a += DETENT * ease((f - START + 10) / 6)
    for k in range(0, min(f, N) + 1):                      # every steering click
        tr = turning(k)
        if tr:
            a -= tr * DETENT * ease((f - k) / 3)
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def busy(f):
    return flapping(f) or pressed(f)
