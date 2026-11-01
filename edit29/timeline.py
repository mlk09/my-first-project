"""Shared timeline for the ESP32 + OLED Space Invaders short (24 fps, 468 frames = 19.5 s story, + 2.5 s
outro = 22 s). The KY-040 knob moves the laser ship (turn) and fires (press). 128x64 OLED coordinates:
a 3 x 6 alien formation marches left/right and steps down under an 8 px score bar; the ship sits at the
bottom. A deterministic auto-pilot leads its shots onto the marching aliens; after a few kills it gets
the TRIPLE LASER power-up, wipes the wave -> WAVE CLEAR -> NEW HIGH SCORE.
game(f) -> dict(px, bullets, bombs, aliens(set of (r, c)), ox, oy, score, hit_brick=(r, c) alien hit,
hit_xy, hit_pad=shot fired, state, fire=triple laser on)"""
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
ROWS, COLS = 3, 6
AW, AH, DX, DY = 10, 7, 16, 10           # alien size and grid pitch
SHIP_Y, SHIP_W, SHIP_H = 56, 11, 6
BUL_V, BOMB_V = 5.0, 1.8
FIRE_AFTER = 6                           # kills before the TRIPLE LASER power-up
HIGH_OLD = 150
ROW_PTS = [30, 20, 10]
BALL = 2                                  # bullet width (kept for API symmetry)


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def alien_rect(r, c, ox, oy):
    x = ox + c * DX
    y = oy + r * DY
    return x, y, x + AW, y + AH


def _sim(n, launch_at=6, power_after=FIRE_AFTER, ox0=14.0):
    aliens = {(r, c) for r in range(ROWS) for c in range(COLS)}
    ox, oy, dirx = ox0, TOP + 3.0, 1
    px, bullets, bombs = 64.0, [], []
    score, out, state, cd = 0, [], "READY", 0
    for k in range(n):
        hb, hxy, shot = None, None, False
        fire = (ROWS * COLS - len(aliens)) >= power_after
        if state == "READY" and k >= launch_at:
            state = "PLAY"
        if state == "PLAY":
            # formation march (speeds up as aliens die)
            spd = 0.7 + 0.07 * (ROWS * COLS - len(aliens))
            cols = [c for (_, c) in aliens]
            lo, hi = min(cols), max(cols)
            ox += dirx * spd
            if ox + hi * DX + AW > 126 or ox + lo * DX < 2:
                dirx = -dirx
                ox += dirx * spd
                oy = min(oy + 2, 30)
            # bullets
            nb = []
            for (bx, by, vx) in bullets:
                bx, by = bx + vx, by - BUL_V
                hit = None
                for (r, c) in sorted(aliens, key=lambda rc: -rc[0]):
                    x0, y0, x1, y1 = alien_rect(r, c, ox, oy)
                    if x0 - 1 <= bx <= x1 + 1 and y0 <= by <= y1 + BUL_V:
                        hit = (r, c)
                        break
                if hit:
                    aliens.discard(hit)
                    score += ROW_PTS[hit[0]]
                    hb = hit
                    x0, y0, x1, y1 = alien_rect(*hit, ox, oy)
                    hxy = ((x0 + x1) / 2, (y0 + y1) / 2)
                elif by > TOP:
                    nb.append((bx, by, vx))
            bullets = nb
            # alien bombs (visual threat, the ship dodges them)
            if aliens and k % 17 == 9:
                r, c = max(aliens, key=lambda rc: (rc[0], (rc[1] * 7 + k) % 5))
                x0, y0, x1, y1 = alien_rect(r, c, ox, oy)
                bombs.append(((x0 + x1) / 2, y1))
            bombs = [(x, y + BOMB_V) for (x, y) in bombs if y + BOMB_V < SHIP_Y + SHIP_H]
            # aim: lead the shot onto the nearest low alien
            if aliens:
                t = (SHIP_Y - (oy + 2 * DY)) / BUL_V
                lead = dirx * spd * t
                tgt = min(aliens, key=lambda rc: (-rc[0], abs(rc[1] * DX + ox + AW / 2 + lead - px)))
                target = ox + tgt[1] * DX + AW / 2 + lead
                for (x, y) in bombs:
                    if y > 34 and abs(x - target) < 7:
                        target = x + (9 if target >= x else -9)
            else:
                target = px
            target = max(SHIP_W / 2, min(128 - SHIP_W / 2, target))
            px += max(-2.2, min(2.2, target - px))
            cd = max(0, cd - 1)
            if aliens and cd == 0 and abs(px - target) < 3:
                shot = True
                bullets.append((px, SHIP_Y - 1, 0.0))
                if fire:
                    bullets += [(px - 3, SHIP_Y, -0.9), (px + 3, SHIP_Y, 0.9)]
                cd = 5 if fire else 10
            if not aliens:
                state = "CLEAR"
        elif state == "READY":
            px = 64 + 10 * math.sin(k * 0.2)
        out.append(dict(px=px, bullets=tuple(bullets), bombs=tuple(bombs), aliens=frozenset(aliens), ox=ox, oy=oy,
                        score=score, hit_brick=hb, hit_xy=hxy, hit_pad=shot, state=state, k=k,
                        fire=fire and state == "PLAY"))
    return out


_M = _H = None


def _main():
    global _M, _H
    if _M is None:
        _M = _sim(SHOTS[6] - PLAY0)
        _H = _sim(SHOTS[1], launch_at=0, power_after=0, ox0=20.0)
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
    """Menu: level clicks; in play the knob angle follows the ship (pot-style control)."""
    g = game(f)
    if g and g["state"] in ("READY", "PLAY", "CLEAR"):
        return (g["px"] - 64) * 4.0
    a = 0.0
    for c, i in LEVEL_CLICKS:
        a -= DETENT * ease((f - c) / 6)
    a += DETENT * ease((f - START + 10) / 6)
    return a + 6 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def pressed(f):
    g = game(f)
    return START <= f < START + 4 or 0 <= f < 2 or bool(g and g["hit_pad"]) or bool(game(f - 1) and game(f - 1)["hit_pad"])


def flapping(f):
    g = game(f)
    return bool(g and g["hit_pad"])


def busy(f):
    g = game(f)
    return bool(g and (g["hit_pad"] or g["hit_brick"])) or pressed(f)
