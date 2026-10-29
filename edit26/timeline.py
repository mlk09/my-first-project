"""Shared timeline for the ESP32 + OLED 2-player Pong short (24 fps, 468 frames = 19.5 s story, + 2.5 s
outro = 22 s). Two KY-040 knobs = two paddles (TUM on the left, DOST on the right): knob angle sets the
paddle height, a press on knob 1 serves. Runs in 128x64 OLED coordinates with scripted rallies (who
hits how often, who misses), first to 2 points wins.
game(f) -> dict(bx, by, p1, p2, s1, s2, state, hit, point)"""
import math

FPS, N = 24, 468
#        hook  setup  menu  play  final  win  end
SHOTS = [0, 60, 120, 180, 268, 370, 408]
DETENT = 18.0
TOP, PH, PW, BALL = 10, 14, 3, 3
P1X, P2X = 4, 121
V = 6.0                                        # ball x-speed px / frame
PSPEED = 5.5
START = 160                                    # knob 1 press = START
PLAY0 = 180
# (server 1 / 2, paddle hits in the rally, loser 1 / 2, serve vy)
RALLIES = [(1, 1, 2, 1.6), (2, 0, 1, -1.9), (1, 3, 2, 2.2)]
HOOK_RALLY = [(1, 1, 2, 1.3)]
WIN = 2


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _bounce_y(y, vy):
    lo, hi = TOP + 1, 63 - BALL
    y += vy
    if y < lo:
        y, vy = 2 * lo - y, -vy
    if y > hi:
        y, vy = 2 * hi - y, -vy
    return y, vy


def _intercept(bx, by, vx, vy, px):
    x, y, v = bx, by, vy
    for _ in range(200):
        if (vx > 0 and x >= px) or (vx < 0 and x <= px):
            return y
        x += vx
        y, v = _bounce_y(y, v)
    return y


def _sim(n, rallies, pause0=8):
    p1 = p2 = 37.0 - PH / 2
    s1 = s2 = 0
    out, ri, pause = [], 0, pause0
    bx, by, vx, vy, hits_left, loser = 62.0, 36.0, 0.0, 0.0, 0, 0
    state = "SERVE"
    for k in range(n):
        hit, point = 0, 0
        if state == "SERVE":
            pause -= 1
            if pause <= 0 and ri < len(rallies):
                srv, hits_left, loser, svy = rallies[ri]
                bx, by = 62.0, 30.0 + 8 * (ri % 2)
                vx, vy = (V if srv == 1 else -V), svy
                state = "RALLY"
        elif state == "RALLY":
            bx += vx
            by, vy = _bounce_y(by, vy)
            for side, px, pad in ((1, P1X + PW, p1), (2, P2X - BALL, p2)):
                going = vx < 0 if side == 1 else vx > 0
                crossed = bx <= px if side == 1 else bx >= px
                if going and crossed:
                    if side == loser and hits_left <= 0:
                        continue
                    bx = 2 * px - bx
                    vx = -vx
                    off = (by + BALL / 2 - (pad + PH / 2)) / (PH / 2)
                    vy = max(-3.0, min(3.0, vy * 0.6 + off * 2.2))
                    hits_left -= 1
                    hit = side
            if bx < -6 or bx > 134:
                point = 2 if bx < 0 else 1
                if point == 1:
                    s1 += 1
                else:
                    s2 += 1
                ri += 1
                state = "OVER" if max(s1, s2) >= WIN else "SERVE"
                pause = 16
        # paddles: chase the predicted intercept (the loser lunges the wrong way)
        for side in (1, 2):
            pad = p1 if side == 1 else p2
            target = 37.0
            if state == "RALLY" and ((side == 1 and vx < 0) or (side == 2 and vx > 0)):
                target = _intercept(bx, by, vx, vy, P1X if side == 1 else P2X) + BALL / 2
                if side == loser and hits_left <= 0:
                    target += 22 if target < 37 else -22
            want = target - PH / 2
            step = max(-PSPEED, min(PSPEED, want - pad))
            pad = max(TOP + 1, min(63 - PH, pad + step))
            if side == 1:
                p1 = pad
            else:
                p2 = pad
        out.append(dict(bx=bx, by=by, p1=p1, p2=p2, s1=s1, s2=s2, state=state, hit=hit, point=point, k=k))
    return out


_M = _H = None


def _main():
    global _M, _H
    if _M is None:
        _M = _sim(SHOTS[6] - PLAY0, RALLIES)
        _H = _sim(SHOTS[1], HOOK_RALLY, pause0=2)
    return _M, _H


def game(f):
    m, h = _main()
    if f < SHOTS[1]:
        return h[max(0, f)]
    if PLAY0 <= f < SHOTS[6]:
        return m[f - PLAY0]
    return None


def end_frame():
    m, _ = _main()
    return PLAY0 + next(k for k, s in enumerate(m) if s["state"] == "OVER")


def points():
    """Frames where a point is scored (hook + match)."""
    out = []
    for f in range(N):
        g = game(f)
        if g and g["point"]:
            out.append((f, g["point"]))
    return out


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
        return "play" if f < end_frame() else "win"
    return "title"


def countdown(f):
    return 3 - (f - START) // 7 if START <= f < PLAY0 else 0


def mode(f):
    return "2 PLAYER" if f >= 140 else "1 PLAYER"


def _pad_angle(y):
    return (y - (37.0 - PH / 2)) * 6.0


def knob(f):
    g = game(f)
    a = _pad_angle(g["p1"]) if g else 0.0
    if SHOTS[2] <= f < START:
        a -= DETENT * ease((f - 136) / 6)                      # 1P -> 2P in the menu
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def knob2(f):
    g = game(f)
    return _pad_angle(g["p2"]) if g else 0.0


def pressed(f):
    return START <= f < START + 4


def flapping(f):
    g = game(f)
    return bool(g and g["hit"])


def busy(f):
    return flapping(f) or pressed(f)
