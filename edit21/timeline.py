"""Shared timeline for the ESP32 + OLED + joystick 4-servo robot-arm short (24 fps, 468 frames =
19.5 s story, + 2.5 s outro = 22 s). The joystick drives the arm: X = base, Y = reach / up-down,
button = gripper. It picks a red cube off the mat and drops it into a cup.
pose(f) = (yaw deg, reach cm, fingertip height cm, grip 0..1); ik() turns it into servo angles."""
import math

FPS, N = 24, 468
#        hook  setup  servo  reach  carry  drop  end
SHOTS = [0, 60, 120, 180, 264, 348, 408]
L1, L2, HS, G = 4.6, 4.2, 2.6, 1.4          # link lengths, shoulder height, wrist -> grip centre
HOME = (0.0, 4.6, 4.2, 0.0)
CUBE = (-55.0, 6.0, 0.55)                   # cube spot (yaw, reach, centre height)
CUP = (55.0, 6.0)                           # cup position (yaw, reach)
CUP_TOP, CUP_IN = 1.5, 0.6                  # cup rim height, cube rest height inside
GRAB, RELEASE = SHOTS[3] + 58, SHOTS[5] + 4  # gripper fully closed / opens


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# key poses: (frame, yaw, reach, z, grip); linear blend with ease between consecutive keys
KEYS = [
    (0, CUBE[0], CUBE[1], CUBE[2], 1.0), (4, CUBE[0], CUBE[1], CUBE[2], 1.0),
    (22, CUBE[0], 5.0, 4.6, 1.0), (40, 25.0, 4.8, 5.4, 1.0), (52, 15.0, 4.8, 5.4, 1.0), (59, 15.0, 4.8, 5.4, 1.0),
    (60, *HOME), (120, *HOME),
    (134, -40.0, 4.6, 4.2, 0.0), (150, 40.0, 4.6, 4.2, 0.0), (166, 0.0, 4.6, 4.2, 0.0), (180, *HOME),
    (200, CUBE[0], 4.6, 4.2, 0.0), (216, CUBE[0], CUBE[1], 3.0, 0.0), (236, CUBE[0], CUBE[1], CUBE[2], 0.0),
    (GRAB, CUBE[0], CUBE[1], CUBE[2], 1.0), (264, CUBE[0], CUBE[1], CUBE[2], 1.0),
    (286, CUBE[0], 5.2, 4.4, 1.0), (322, CUP[0], 5.2, 4.4, 1.0), (338, CUP[0], CUP[1], 3.4, 1.0), (348, CUP[0], CUP[1], 3.4, 1.0),
    (RELEASE, CUP[0], CUP[1], 3.4, 1.0), (RELEASE + 6, CUP[0], CUP[1], 3.4, 0.0), (372, CUP[0], CUP[1], 3.4, 0.0),
    (400, *HOME), (N + 1, *HOME),
]


def pose(f):
    if f < 0:
        return KEYS[0][1:]
    for (f0, *a), (f1, *b) in zip(KEYS, KEYS[1:]):
        if f0 <= f < f1:
            u = ease((f - f0) / (f1 - f0))
            return tuple(x + (y - x) * u for x, y in zip(a, b))
    return KEYS[-1][1:]


def ik(f):
    """Servo angles in degrees: base yaw, shoulder elevation, elbow (relative, negative = bend down),
    wrist (relative, keeps the gripper pointing straight down), grip 0..1."""
    yaw, r, z, grip = pose(f)
    dx, dz = r, z + G - HS
    d = min(math.hypot(dx, dz), L1 + L2 - 1e-3)
    c2 = (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    a2 = -math.acos(max(-1.0, min(1.0, c2)))
    a1 = math.atan2(dz, dx) + math.atan2(L2 * math.sin(-a2), L1 + L2 * math.cos(a2))
    wr = -math.pi / 2 - (a1 + a2)
    return yaw, math.degrees(a1), math.degrees(a2), math.degrees(wr), grip


def holding(f):
    return pose(f)[3] > 0.85 and (f < SHOTS[1] or GRAB <= f < RELEASE + 2)


def cube(f):
    """(yaw, reach, centre height) of the cube."""
    if holding(f):
        y, r, z, _ = pose(f)
        return y, r, z
    if f < GRAB:
        return CUBE
    t = (f - RELEASE - 2) / 24.0                       # free fall into the cup
    z = max(CUP_IN, 3.4 - 0.5 * 980 / 100 * t * t * 1.6)
    return CUP[0], CUP[1], z


def landed(f):
    return f >= RELEASE + 2 and cube(f)[2] <= CUP_IN + 1e-6


def joystick(f):
    """(x, y, pressed): the stick that would produce this motion (x = base speed, y = reach / height)."""
    y0, r0, z0, g0 = pose(f - 1)
    y1, r1, z1, g1 = pose(f + 1)
    jx = max(-1.0, min(1.0, (y1 - y0) / 6.0))
    jy = max(-1.0, min(1.0, ((r1 - r0) - (z1 - z0)) / 0.5))
    return jx, jy, abs(g1 - g0) > 0.02


def status(f):
    if SHOTS[1] <= f < SHOTS[2] or f >= SHOTS[6]:
        return "READY"
    if RELEASE <= f < RELEASE + 22:
        return "DROP!"
    if GRAB - 20 <= f < GRAB + 8 or f < 4:
        return "GRAB!"
    if abs(pose(f + 1)[3] - pose(f - 1)[3]) > 0.02:
        return "GRAB!" if pose(f + 1)[3] > pose(f - 1)[3] else "DROP!"
    if holding(f):
        return "HOLDING"
    return "MOVING" if any(abs(a - b) > 0.01 for a, b in zip(pose(f + 1), pose(f - 1))) else "READY"


def busy(f):
    return status(f) != "READY" and f % 6 < 3
