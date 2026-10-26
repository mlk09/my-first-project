"""Shared timeline for the ESP32 + OLED Chrome Dino short (24 fps, 468 frames = 19.5 s story, + 2.5 s
outro = 22 s). 'No internet' -> the T-rex runs. The KY-040 knob picks the speed (turn) and jumps
(press). Runs in 128x64 OLED coordinates with a deterministic auto-pilot that clears cacti and low
pterodactyls, day turns to night, then it misses one -> GAME OVER -> NEW HIGH SCORE.
game(f) -> dict(dino_y, vel, obs[(x, kind)], jumped, dist, hi, state, jump, night)"""
import math

FPS, N = 24, 468
#        hook  setup  menu  play  crash  best  end
SHOTS = [0, 60, 120, 180, 334, 366, 408]
DETENT = 18.0
LEVELS = ["SLOW", "NORMAL", "FAST"]
LEVEL_CLICKS = [(128, 1), (140, 2)]
START = 156
PLAY0 = 180
GROUND = 54                                   # OLED y of the ground line (dino feet)
DINO_X, DINO_W, DINO_H = 16, 14, 16
GRAV, JUMP_V = 0.40, -4.6
SPEED0, ACCEL = 2.6, 0.006
HIGH_OLD = 150
# obstacle course: (spawn distance, kind)  kind: c1 small cactus, c2 tall cactus, c3 double, bird
COURSE = [(140, "c1"), (210, "c2"), (285, "bird"), (360, "c3"), (430, "c1"), (500, "c2"), (570, "bird"),
          (640, "c3"), (720, "c1"), (800, "bird"), (880, "c2")]
SIZES = {"c1": (7, 12), "c2": (8, 16), "c3": (15, 13), "bird": (14, 10)}
BIRD_Y = GROUND - 24                          # pterodactyl skims just over the T-rex head


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _sim(n, crash_at=None, offset=0.0):
    y, v, dist, out, state, passed = 0.0, 0.0, offset, [], "RUN", 0
    for k in range(n):
        jump = False
        sp = SPEED0 + ACCEL * k
        obs = [(DINO_X + d - dist, kind, i) for i, (d, kind) in enumerate(COURSE)]
        if state == "RUN":
            nxt = [o for o in obs if o[0] + SIZES[o[1]][0] > DINO_X - 2]
            if nxt and y == 0.0:
                x, kind, i = nxt[0]
                lead = 8 + sp * 7
                if x - (DINO_X + DINO_W) < lead and i != crash_at and kind != "bird":
                    v, jump = JUMP_V, True
            if y < 0 or v < 0:
                v += GRAV
                y = min(0.0, y + v)
                if y == 0.0:
                    v = 0.0
            dist += sp
            for x, kind, i in obs:
                w, h = SIZES[kind]
                bx = x - sp
                top = (BIRD_Y - h / 2) if kind == "bird" else GROUND - h
                bot = (BIRD_Y + h / 2) if kind == "bird" else GROUND
                dl, dr, dt, db = DINO_X + 2, DINO_X + DINO_W - 3, GROUND - DINO_H + y + 2, GROUND + y
                if bx < dr and bx + w > dl and dt < bot and db > top:
                    state = "DEAD"
                if x + w >= DINO_X and bx + w < DINO_X:
                    passed += 1
        obs = [(DINO_X + d - dist, kind) for d, kind in COURSE if -16 < DINO_X + d - dist < 140]
        out.append(dict(dino_y=y, vel=v, obs=obs, passed=passed, dist=int(dist / 2.4), state=state, jump=jump, k=k))
    return out


_M = _H = None


def _main():
    global _M, _H
    if _M is None:
        _M = _sim(SHOTS[6] - PLAY0, crash_at=5)
        _H = _sim(SHOTS[1], offset=60)
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
    return m[crash_frame() - PLAY0]["dist"]


def night(f):
    """0 = day .. 1 = night (fades in during play, like the real game)."""
    if PLAY0 <= f < SHOTS[6]:
        return ease((f - PLAY0 - 70) / 24)
    return 0.0


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


def flapping(f):
    """Jump presses (named like the Flappy Bird timeline so the edit code stays shared)."""
    g = game(f)
    return bool(g and g["jump"])


def pressed(f):
    return any(flapping(k) for k in range(f - 2, f + 1)) or START <= f < START + 4


def knob(f):
    a = 0.0
    for c, i in LEVEL_CLICKS:
        a -= DETENT * ease((f - c) / 6)
    a += DETENT * ease((f - START + 10) / 6)
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def busy(f):
    return pressed(f)
