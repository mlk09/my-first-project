"""Shared timeline for the ESP32 + OLED Rock-Paper-Scissors robot short (24 fps, 468 frames = 19.5 s
story, + 2.5 s outro = 22 s). The player picks with the rotary knob (1 detent = next choice) and
presses it; OLED counts 3-2-1 while the robot's servo spins a 3-face box (ROCK / PAPER / SCISSORS)
and stops on its pick. First to 3 wins."""
import math

FPS, N = 24, 468
#        hook  setup  r1   r2   r3   r4   end
SHOTS = [0, 60, 120, 200, 272, 344, 408]
CHOICES = ["ROCK", "PAPER", "SCISSORS"]
EMO = {"ROCK": "✊", "PAPER": "✋", "SCISSORS": "✌️"}
DETENT = 18.0
# (round start frame, player choice, robot choice)
ROUNDS = [(124, 2, 1), (204, 0, 1), (276, 1, 0), (348, 0, 2)]
SEL, PRESS, CD, REVEAL = 18, 20, 20, 44          # offsets inside a round
HOOK_SPIN = (4, 26)                              # hook: robot spins and shows ROCK
SERVO_FACE = [0.0, -90.0, 90.0]                  # servo angle that turns each face towards the camera


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def beats(p, b):
    return (p - b) % 3 == 1                      # paper(1) beats rock(0), scissors(2) beats paper(1), rock beats scissors


def winner(r):
    _, p, b = ROUNDS[r]
    return "TIE" if p == b else "YOU" if beats(p, b) else "BOT"


def round_at(f):
    """(round index, local frame) of the round running at f, or (None, None)."""
    for i, (s, _, _) in enumerate(ROUNDS):
        end = ROUNDS[i + 1][0] if i + 1 < len(ROUNDS) else N
        if s <= f < end:
            return i, f - s
    return None, None


def score(f):
    """(robot, you) after every revealed result up to frame f."""
    bot = you = 0
    for i, (s, _, _) in enumerate(ROUNDS):
        if f >= s + REVEAL:
            w = winner(i)
            bot += w == "BOT"
            you += w == "YOU"
    return bot, you


def knob(f):
    a = 0.0
    cur = 0
    for s, p, _ in ROUNDS:
        d = (p - cur) % 3
        a += d * DETENT * ease((f - s) / SEL)
        cur = p
    return a + 8 * math.sin(f * 0.5) * (SHOTS[1] <= f < SHOTS[2])


def knob_choice(f):
    return int(math.floor(knob(f) / DETENT + 1e-6)) % 3


def pressed(f):
    i, l = round_at(f)
    return i is not None and PRESS <= l < PRESS + 5


def servo(f):
    """Box angle in degrees."""
    def spin(t0, t1, target):
        if f < t0:
            return None
        if f >= t1:
            return SERVO_FACE[target]
        u = (f - t0) / (t1 - t0)
        wob = 90 * math.sin(u * math.pi * 5) * (1 - u) ** 0.6
        return SERVO_FACE[target] * ease(u) + wob
    v = SERVO_FACE[0]
    h = spin(*HOOK_SPIN, 0)
    if h is not None:
        v = h
    for s, _, b in ROUNDS:
        r = spin(s + CD + 4, s + REVEAL, b)
        if r is not None:
            v = r
    return v


def phase(f):
    """'idle' | 'select' | 'count' | 'result' | 'champ' (+ countdown number)."""
    i, l = round_at(f)
    if i is None:
        return ("hook", 0) if f < SHOTS[1] else ("idle", 0)
    if i == len(ROUNDS) - 1 and l >= REVEAL + 14:
        return "champ", 0
    if l < PRESS:
        return "select", 0
    if l < REVEAL:
        return "count", 3 - min(2, (l - CD) // 8)
    return "result", 0


def led(f):
    """'green' | 'red' | None"""
    i, l = round_at(f)
    if i is None or l < REVEAL:
        return None
    if phase(f)[0] == "champ":
        return "green" if (f // 4) % 2 == 0 else None
    w = winner(i)
    return "green" if w == "YOU" else "red" if w == "BOT" else None


def busy(f):
    return phase(f)[0] == "count"
