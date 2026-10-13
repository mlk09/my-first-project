"""Shared timeline for the ESP32 self-balancing robot short (24 fps, 384 frames = 16 s).
theta(f): body pitch in degrees (+ = leaning back, away from camera); y(f): wheel travel in cm (+ = away)."""
import math

FPS, N = 24, 384
#        hook  pid-on  inside  push  pid-hud  drive  end
SHOTS = [0, 48, 96, 144, 204, 264, 324]
FALL = (6, 26)            # PID OFF: tips over and hits the mat
PID_ON = 52               # placed upright, PID switched on
PUSH = 160                # ball hits the robot
DRIVE = (270, 318)        # drives forward and back
WHEEL_R = 3.3             # cm
BALL_R = 2.6
BALL_HIT = WHEEL_R + BALL_R   # ball centre when it touches the wheels


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _jitter(f):
    return 0.6 * math.sin(f * 0.9) + 0.35 * math.sin(f * 2.3 + 1)


def _fall(f):
    if f < FALL[0]:
        return 1.5 * math.sin(f * 0.8)
    u = (f - FALL[0]) / (FALL[1] - FALL[0])
    if u <= 1:
        return 78 * u ** 2.2                       # gravity: slow start, fast finish
    a = f - FALL[1]
    return 78 - 7 * math.exp(-a / 3) * abs(math.sin(a * 0.9))   # small bounce, then rest


def theta(f):
    if f < SHOTS[1]:
        return _fall(f)
    if f < PUSH:
        a = f - PID_ON
        settle = 9 * math.exp(-max(a, 0) / 7) * math.cos(max(a, 0) * 0.55) if f >= PID_ON else 9
        return settle + _jitter(f)
    if f < DRIVE[0]:
        a = f - PUSH
        hit = 15 * math.exp(-a / 8) * math.sin(a * 0.42) if a >= 0 else 0
        return hit + _jitter(f)
    a = f - DRIVE[0]
    lean = 5 * math.sin(math.pi * min(max(a, 0), 24) / 24) - 5 * math.sin(math.pi * min(max(a - 24, 0), 24) / 24)
    return (lean if f < DRIVE[1] else 0) + _jitter(f)


def y(f):
    if f < SHOTS[1]:
        return -0.08 * _fall(f)                     # wheels slip back a little as it falls
    if f < PUSH:
        return 0.18 * theta(f)
    if f < DRIVE[0]:
        a = f - PUSH
        catch = 7 * (1 - math.exp(-a / 6)) * math.exp(-max(a - 10, 0) / 14) if a >= 0 else 0
        return catch + 0.18 * theta(f)
    drive = 14 * (ease((f - DRIVE[0]) / 22) - ease((f - DRIVE[0] - 26) / 22))
    return drive + 0.18 * theta(f)


def wheel_deg(f):
    return math.degrees(y(f) / WHEEL_R)


def ball_y(f):
    """Ball rolls in from the camera side, hits the robot front at PUSH, bounces back."""
    if f < PUSH:
        return -BALL_HIT - 1.4 * (PUSH - f)
    return -BALL_HIT - 0.5 * (f - PUSH)


def pid_on(f):
    return f >= PID_ON
