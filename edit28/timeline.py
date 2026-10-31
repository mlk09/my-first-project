"""Shared timeline for the ESP32 + OLED Brick Breaker short (24 fps, 468 frames = 19.5 s story, + 2.5 s
outro = 22 s). The KY-040 knob moves the paddle (turn) and launches the ball (press). 128x64 OLED
coordinates: 3 rows x 8 bricks under an 8 px score bar, paddle at the bottom. A deterministic
auto-pilot aims the ball at the remaining bricks; it clears the wall -> LEVEL CLEAR -> NEW HIGH SCORE.
game(f) -> dict(bx, by, px, bricks(set of (r, c)), score, hit_brick, hit_pad, state)"""
import math

FPS, N = 24, 468
#        hook  setup  menu  play  final  best  end
SHOTS = [0, 60, 120, 180, 276, 366, 408]
DETENT = 18.0
LEVELS = ["EASY", "NORMAL", "HARD"]
LEVEL_CLICKS = [(128, 1), (140, 2)]
START = 156
PLAY0 = 180
TOP = 9
ROWS, COLS = 3, 8
BW, BH, BGAP, BY0 = 15, 5, 1, 13
PAD_Y, PAD_W, PAD_H = 58, 22, 3
BALL = 3
SPEED = 4.6
FIRE_AFTER = 4                                 # bricks broken before the FIREBALL power-up
HIGH_OLD = 150
ROW_PTS = [30, 20, 10]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def brick_rect(r, c):
    x = 1 + c * (BW + BGAP)
    y = BY0 + r * (BH + BGAP)
    return x, y, x + BW, y + BH


def _sim(n, launch_at=6, seed_bricks=None):
    bricks = set(seed_bricks) if seed_bricks is not None else {(r, c) for r in range(ROWS) for c in range(COLS)}
    px, bx, by = 64.0, 64.0, PAD_Y - BALL - 0.5
    vx, vy = 0.0, 0.0
    score, out, state = 0, [], "READY"
    for k in range(n):
        hb, hp = None, False
        if state == "READY":
            bx = px - BALL / 2
            if k >= launch_at:
                state = "PLAY"
                vx, vy = 1.2, -SPEED
        elif state == "PLAY":
            nx, ny = bx + vx, by + vy
            if nx < 0 or nx > 128 - BALL:
                vx = -vx
                nx = bx + vx
            if ny < TOP + 1:
                vy = -vy
                ny = by + vy
            fire = (ROWS * COLS - len(bricks)) >= FIRE_AFTER
            for (r, c) in sorted(bricks):
                x0, y0, x1, y1 = brick_rect(r, c)
                if nx + BALL > x0 and nx < x1 and ny + BALL > y0 and ny < y1:
                    bricks.discard((r, c))
                    score += ROW_PTS[r]
                    hb = (r, c)
                    if fire:                                      # fireball smashes straight through
                        continue
                    if bx + BALL <= x0 or bx >= x1:
                        vx = -vx
                    else:
                        vy = -vy
                    nx, ny = bx + vx, by + vy
                    break
            if fire and ny < BY0 + ROWS * (BH + BGAP) and ny > BY0 - BALL:
                for (r, c) in sorted(bricks):
                    x0, y0, x1, y1 = brick_rect(r, c)
                    if nx + BALL > x0 and nx < x1 and ny + BALL > y0 and ny < y1:
                        bricks.discard((r, c))
                        score += ROW_PTS[r]
                        hb = (r, c)
            if vy > 0 and ny + BALL >= PAD_Y and by + BALL <= PAD_Y + 1 and px - PAD_W / 2 - 2 <= nx + BALL / 2 <= px + PAD_W / 2 + 2:
                off = (nx + BALL / 2 - px) / (PAD_W / 2)
                vx = max(-3.2, min(3.2, off * 3.0))
                vy = -math.sqrt(max(1.0, SPEED ** 2 + 1.5 - vx * vx))
                ny = PAD_Y - BALL
                hp = True
            bx, by = nx, ny
            if not bricks:
                state = "CLEAR"
            elif by > 66:
                state = "LOST"
        # paddle: go under the ball, offset so the bounce aims at the nearest remaining brick column
        if state in ("READY", "PLAY"):
            target = bx + BALL / 2
            if vy > 0 and bricks:
                t = max(1.0, (PAD_Y - BALL - by) / max(vy, 0.1))
                land = bx + vx * t
                while land < 0 or land > 128 - BALL:
                    land = -land if land < 0 else 2 * (128 - BALL) - land
                tc = min(bricks, key=lambda rc: (-rc[0], abs(brick_rect(*rc)[0] + BW / 2 - land)))
                want_vx = max(-3.0, min(3.0, (brick_rect(*tc)[0] + BW / 2 - land) / 14))
                target = land + BALL / 2 - want_vx / 3.0 * PAD_W / 2
            elif state == "READY":
                target = 64 + 10 * math.sin(k * 0.2)
            px += max(-4.0, min(4.0, target - px))
            px = max(PAD_W / 2, min(128 - PAD_W / 2, px))
        out.append(dict(bx=bx, by=by, px=px, bricks=frozenset(bricks), score=score, hit_brick=hb, hit_pad=hp, state=state, k=k,
                        fire=(ROWS * COLS - len(bricks)) >= FIRE_AFTER and state == "PLAY"))
    return out


_M = _H = None


def _main():
    global _M, _H
    if _M is None:
        _M = _sim(SHOTS[6] - PLAY0)
        _H = _sim(SHOTS[1], launch_at=2)
    return _M, _H


def game(f):
    m, h = _main()
    if f < SHOTS[1]:
        return h[max(0, f)]
    if PLAY0 <= f < SHOTS[6]:
        return m[f - PLAY0]
    return None


def clear_frame():
    m, _ = _main()
    return PLAY0 + next(k for k, s in enumerate(m) if s["state"] == "CLEAR")


def fire_frame():
    m, _ = _main()
    return PLAY0 + next(k for k, s in enumerate(m) if s["fire"])


def final_score():
    m, _ = _main()
    return m[clear_frame() - PLAY0]["score"]


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
        cf = clear_frame()
        return "play" if f < cf else ("clear" if f < cf + 3 else "best")
    return "title"


def level(f):
    lv = 0
    for c, i in LEVEL_CLICKS:
        if f >= c + 4:
            lv = i
    return min(lv, 1) if f >= START else lv


def countdown(f):
    return 3 - (f - START) // 8 if START <= f < PLAY0 else 0


def knob(f):
    """Menu: level clicks; in play the knob angle follows the paddle (pot-style control)."""
    g = game(f)
    if g and g["state"] in ("READY", "PLAY", "CLEAR"):
        return (g["px"] - 64) * 4.0
    a = 0.0
    for c, i in LEVEL_CLICKS:
        a -= DETENT * ease((f - c) / 6)
    a += DETENT * ease((f - START + 10) / 6)
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def pressed(f):
    return START <= f < START + 4 or PLAY0 + 4 <= f < PLAY0 + 8 or 0 <= f < 4


def flapping(f):
    g = game(f)
    return bool(g and g["hit_pad"])


def busy(f):
    g = game(f)
    return bool(g and (g["hit_pad"] or g["hit_brick"])) or pressed(f)
