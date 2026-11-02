"""Shared timeline for the ESP32 + OLED Car Racing short, NEW retention format: 13 s (24 fps, 312 frames),
no menu / countdown / outro, gameplay from frame 0, hard cuts, and the last shot ends in the same camera
pose, lane and speed as frame 0 so the Short loops seamlessly.
Original top-down side-scrolling racer on the 128x64 OLED: 4 lanes, the KY-040 knob steers the car (turn)
and fires NITRO (press). Traffic is overtaken, coins fill the nitro meter, the run ends at a FINISH line.
game(f) -> dict(py, cars[(x, y, col)], coins[(x, y)], dist, speed, score, coins_got, coin(bool),
close(bool), nitro(bool), finish_x, state)"""
import math

FPS, N = 24, 312
#        hook  knob  play  nitro  finish  loop
SHOTS = [0, 30, 54, 150, 222, 270]
TOP = 9
LANES, ROAD_Y0, LANE_H = 4, 11, 13
PX, CAR_W, CAR_H = 18, 16, 8
TRAFFIC_V = 1.2
STEER = 1.9
BASE_V, NITRO_V = 2.6, 4.6
HIGH_OLD = 600
# (frame the car starts to steer, target lane); the run starts and ends in lane 1 (loop)
PLAN = [(2, 0), (44, 1), (78, 3), (126, 2), (150, 0), (176, 1), (196, 3), (214, 2), (276, 1)]
NITRO_AT = 112                     # knob press when the nitro meter is full (3rd coin)
FINISH = 236                       # finish line crosses the car


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lane_y(l):
    return ROAD_Y0 + LANE_H * l + LANE_H / 2


def speed(f):
    if f < NITRO_AT:
        return BASE_V
    if f < FINISH:
        return BASE_V + (NITRO_V - BASE_V) * ease((f - NITRO_AT) / 6)
    return NITRO_V + (BASE_V - NITRO_V) * ease((f - FINISH) / 30)


_D = [0.0]
for _f in range(N + 40):
    _D.append(_D[-1] + speed(_f))


def dist(f):
    return _D[max(0, min(f, len(_D) - 1))]


def _player():
    ys, y, li = [], lane_y(1), 0
    tgt = lane_y(1)
    for f in range(N):
        while li < len(PLAN) and PLAN[li][0] <= f:
            tgt = lane_y(PLAN[li][1])
            li += 1
        y += max(-STEER, min(STEER, tgt - y))
        ys.append(y)
    return ys


PY = _player()


def overlap_frames(fp):
    return int(math.ceil((CAR_W + 1) / max(0.5, speed(fp) - TRAFFIC_V))) + 1


def _events():
    dodge, coins, extra = [], [], []
    for (fc, ln), (fp_prev, ln_prev) in zip(PLAN, [(0, 1)] + PLAN[:-1]):
        if fc > FINISH - 20:
            continue
        clear_at = fc + int(math.ceil((CAR_H + 1) / STEER)) + 1
        fp = clear_at + overlap_frames(clear_at)
        dodge.append((fp, ln_prev))                                    # the car you just swerved around
        coins.append((fp + 6, ln))
    rnd = [(i * 7919 + 13) % 101 for i in range(400)]
    for i, fp in enumerate(range(4, N + 30, 4)):                      # background traffic in free lanes
        ln = rnd[i] % LANES
        if FINISH - 12 < fp < FINISH + 20 or rnd[i + 50] % 3 == 0:
            continue
        ok = all(abs(PY[min(N - 1, max(0, ff))] - lane_y(ln)) > CAR_H + 2
                 for ff in range(fp - overlap_frames(fp) - 2, fp + overlap_frames(fp) + 3))
        gap = 2 * overlap_frames(fp) + 3
        if ok and all(abs(fp - a) > gap or l != ln for a, l in dodge + extra):
            extra.append((fp, ln))
    return dodge, coins[:-1] if len(coins) > 6 else coins, extra


DODGE, COINS, EXTRA = _events()
COIN_COL = 3


def car_x(fp, f, v=TRAFFIC_V):
    return PX + (dist(fp) - dist(f)) - v * (fp - f)


def game(f):
    if not (0 <= f < N):
        return None
    py = PY[f]
    cars = []
    for j, (fp, ln) in enumerate(DODGE + EXTRA):
        x = car_x(fp, f)
        if -20 < x < 140:
            cars.append((x, lane_y(ln), (j * 3 + ln * 2) % 5))
    coins, got = [], 0
    for (fp, ln) in COINS:
        x = car_x(fp, f, 0.0)
        if fp <= f:
            got += 1
        elif x < 140:
            coins.append((x, lane_y(ln)))
    coin = any(fp == f for fp, _ in COINS)
    close = any(fp == f for fp, _ in DODGE)
    fx = PX + CAR_W / 2 + (dist(FINISH) - dist(f))
    score = int(dist(f) / 4) + 50 * got + 20 * sum(1 for fp, _ in DODGE if fp <= f)
    return dict(py=py, cars=cars, coins=coins, dist=dist(f), speed=speed(f), score=score, coins_got=got,
                coin=coin, close=close, nitro=NITRO_AT <= f < FINISH + 10, finish_x=fx,
                state="FINISH" if f >= FINISH else "PLAY", meter=min(got, COIN_COL))


def clear_frame():
    return FINISH


def final_score():
    return game(FINISH)["score"]


def knob(f):
    """Pot-style steering: the knob angle follows the car's vertical position."""
    return (PY[min(max(f, 0), N - 1)] - lane_y(1.5)) * 6.0


def pressed(f):
    return NITRO_AT - 2 <= f < NITRO_AT + 3


def busy(f):
    g = game(f)
    return bool(g and (g["coin"] or g["close"])) or pressed(f)


def check():
    bad = []
    for f in range(N):
        g = game(f)
        for (x, y, _) in g["cars"]:
            if abs(x - PX) < CAR_W and abs(y - g["py"]) < CAR_H:
                bad.append((f, round(x, 1), y))
    return bad


if __name__ == "__main__":
    print("crashes:", check()[:10])
    print("dodge", DODGE)
    print("coins", COINS)
    print("extra", len(EXTRA), "final", final_score(), "got", game(FINISH)["coins_got"], "nitro coin3", COINS[2][0] if len(COINS) > 2 else None)
