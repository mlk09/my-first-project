#!/usr/bin/env python3
"""3D for "Bolt's Spooky Tales Part 2: The Mystery of the Midnight Candy" (180 s, 2.39:1).

Reuses Part 1's world and characters from edit3/scene3d.py, then adds Part 2's
own original assets: glowing three-toed footprints, the candy basket, a claw
branch, a swinging front door, the haunted-house interior, Granny Gloom, five
Wisplings, her giant wall shadow and the mystery eyes.

Run: python3 part2/scene_p2.py --frames 0 4320 [--samples 5]
     python3 part2/scene_p2.py --at 20,75,140 --pct 50 --samples 2   (stills)
"""
import argparse
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit3"))
sys.path.insert(0, HERE)
_argv, sys.argv = sys.argv, [sys.argv[0]]
import scene3d as S  # noqa: E402
sys.argv = _argv

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from timeline_p2 import CARDS, FPS, NFRAMES, SHOTS  # noqa: E402

T, V, smooth, window, wob, lerp = S.Track, S.V, S.smooth, S.window, S.wob, S.lerp
TAU = math.tau
SYNC = json.load(open(os.path.join(HERE, "work", "sync.json")))
ENVL = SYNC["env"]
R = V(150.0, 0.0, 0.0)                       # interior set origin (far from the forest)
END = V(20.0, S.path_y(20.0), 0)             # where Part 1 ended
CLEAR = V(-1.0, 0.55, 0)                     # Bolt's spot by the stump
PARTY = V(-5.6, -0.3, 0)                     # party spot at the pumpkin patch
DOOR_YAW = S.yaw_to(-0.75, -1)
DOOR_W = S.HOUSE_POS + Matrix.Rotation(DOOR_YAW, 3, "Z") @ V(0, 2.53, 0)
PORCH = DOOR_W + V(-0.6, -0.8, 0) * 1.3
EYES_AT = V(-5.4, 16.5, 0)


def gz(p):
    return S.ground_h(p.x, p.y)


def mouth(who, t):
    e = ENVL[who]
    f = int(t * FPS)
    return e[f] if 0 <= f < len(e) else 0.0


def P(x):
    return ("P", x)


# ================================================================ new assets
NEW = {}


def mat(name, color, rough=0.6, emit_obj=0.0, glow=0.0, obj_base=False, bump=0.0, fog=True):
    return S.mat_pbr(name, color, rough=rough, emit_obj=emit_obj, fresnel_glow=glow, obj_base=obj_base,
                     bump=bump, bump_scale=60, fog=fog)


def lathe(profile, seg=28, wave=0.0):
    """Revolves (r, z) points around Z; optional wavy hem on the first ring."""
    bm = bmesh.new()
    rings = []
    for k, (r, z) in enumerate(profile):
        ring = []
        for i in range(seg):
            a = TAU * i / seg
            zz = z + (wave * math.sin(a * 7) if k == 0 else 0.0)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), zz)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    top = bm.verts.new((0, 0, profile[-1][1] + 0.01))
    for i in range(seg):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % seg], top))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def ghost_profile(h, rb):
    """Sheet-ghost silhouette: flared hem, soft body, round head."""
    pts = [(rb, 0.0), (rb * 0.86, h * 0.12), (rb * 0.72, h * 0.32), (rb * 0.66, h * 0.52)]
    for k in range(1, 9):
        a = k / 9 * math.pi / 2
        pts.append((rb * 0.66 * math.cos(a), h * 0.52 + rb * 0.7 * math.sin(a)))
    return pts


def build_granny():
    M = S.MATS
    sheet = mat("granny_sheet", (0.86, 0.84, 0.96), rough=0.7, glow=2.0)
    root = S.empty("granny")
    body = S.empty("granny_body", parent=root)
    g = S.mesh_obj("granny_sheet", lathe(ghost_profile(0.55, 0.3), wave=0.03), sheet, parent=body)
    g.color = (0.6, 0.7, 1.0, 0.5)
    face_y = 0.19
    for sx in (-1, 1):
        S.mesh_obj("g_eye", S.bm_sphere(1, 12, 6), M["engrave"], parent=body,
                   loc=(sx * 0.065, face_y + 0.005, 0.52), scale=(0.022, 0.012, 0.03))
        S.mesh_obj("g_lens", S.bm_tube(S.arc_points(0, 0, 0.05, 0, TAU, 21)[:-1], 0.008, seg=6, closed=True),
                   mat("gold", (0.9, 0.7, 0.25), rough=0.25), parent=body, loc=(sx * 0.065, face_y + 0.03, 0.52))
        cheek = S.mesh_obj("g_cheek", S.bm_sphere(1, 10, 5), mat("cheek", (1.0, 0.45, 0.55), rough=0.8),
                           parent=body, loc=(sx * 0.11, face_y - 0.005, 0.45), scale=(0.03, 0.01, 0.02))
    S.mesh_obj("g_bridge", S.bm_tube([(-0.016, 0, 0.53), (0, 0, 0.54), (0.016, 0, 0.53)], 0.006, seg=5),
               S.MATS["gold"], parent=body, loc=(0, face_y + 0.035, 0))
    smile = S.mesh_obj("g_smile", S.bm_tube(S.arc_points(0, 0.03, 0.035, math.pi + 0.5, TAU - 0.5, 9, 0),
                                            0.007, seg=5), M["engrave"], parent=body, loc=(0, face_y + 0.01, 0.4))
    shawl = S.mesh_obj("g_shawl", S.bm_tube(S.arc_points(0, 0, 0.21, 0, TAU, 29)[:-1], 0.05, seg=8, closed=True),
                       mat("shawl", (0.55, 0.3, 0.75), rough=0.95, bump=0.6), parent=body, loc=(0, 0, 0.36),
                       rot=(math.pi / 2, 0, 0))
    cap = S.mesh_obj("g_cap", S.bm_tube([(0, 0, 0), (0.03, 0, 0.12), (0.12, 0, 0.2), (0.2, 0, 0.16)], 0.09, seg=10,
                                       taper=lambda u: 1 - 0.85 * u), S.MATS["shawl"], parent=body, loc=(0, 0, 0.66))
    S.mesh_obj("g_pom", S.bm_sphere(0.04, 10, 5), mat("pom", (1.0, 0.85, 0.35), rough=0.9), parent=body,
               loc=(0.2, 0, 0.82))
    needles = S.empty("g_needles", parent=body, loc=(0, 0.26, 0.3))
    for sx in (-1, 1):
        S.mesh_obj("g_needle", S.bm_cyl(0.008, 0.004, 0.36, seg=6, m=Matrix.Rotation(sx * 0.6, 4, "Y")),
                   mat("needle", (0.75, 0.75, 0.8), rough=0.2), parent=needles, loc=(sx * 0.04, 0, 0.08))
    S.mesh_obj("g_yarn", S.bm_sphere(0.06, 12, 6), mat("yarn", (0.9, 0.2, 0.3), rough=0.95, bump=0.8),
               parent=body, loc=(0.18, 0.2, 0.1))
    gl = bpy.data.lights.new("granny_glow", "POINT")
    gl.color, gl.energy, gl.use_shadow = (0.7, 0.75, 1.0), 4.0, False
    S.link(bpy.data.objects.new("granny_glow", gl), parent=body, loc=(0, 0.6, 0.5))
    NEW["granny"] = dict(root=root, body=body, needles=needles, smile=smile)


def build_wisplings():
    cols = [(0.6, 1.0, 0.8), (1.0, 0.75, 0.55), (0.6, 0.8, 1.0), (1.0, 0.95, 0.5), (1.0, 0.65, 0.85)]
    me_bm = lathe(ghost_profile(0.24, 0.13), seg=20, wave=0.015)
    me = bpy.data.meshes.new("wisp")
    me_bm.to_mesh(me)
    me_bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat("wisp", (1, 1, 1), rough=0.6, emit_obj=1.2, obj_base=True))
    NEW["wisps"] = []
    for i, c in enumerate(cols):
        r = S.empty(f"wisp_{i}")
        b = S.shared(f"wisp_body_{i}", me, parent=r)
        b.color = (*c, 1)
        eyes = []
        for sx in (-1, 1):
            e = S.mesh_obj("w_eye", S.bm_sphere(1, 10, 5), S.MATS["engrave"], parent=r,
                           loc=(sx * 0.035, 0.085, 0.2), scale=(0.018, 0.01, 0.026))
            eyes.append(e)
        NEW["wisps"].append(dict(root=r, eyes=eyes))


def footprint_mesh():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=1,
                              matrix=Matrix.Diagonal((0.075, 0.1, 0.012, 1)))
    for a in (-0.5, 0.0, 0.5):  # three toes
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=1,
                                  matrix=Matrix.Translation((0.11 * math.sin(a), 0.11 * math.cos(a) + 0.03, 0))
                                  @ Matrix.Diagonal((0.028, 0.04, 0.01, 1)))
    me = bpy.data.meshes.new("print")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(S.mat_emit("print", (1, 1, 1), 6.0, obj_color=True, fog=True))
    return me


def trail(points, step=0.55):
    out = []
    for a, b in zip(points, points[1:]):
        d = (b - a)
        n = max(1, int(d.length / step))
        for k in range(n):
            out.append((a + d * (k / n), math.atan2(d.y, d.x)))
    return out


def build_footprints():
    me = footprint_mesh()
    pts = [V(0.6, 1.0, 0)] + [V(x, S.path_y(x) + 0.05, 0) for x in range(2, 21, 2)] + \
          [V(23.0, 9.0, 0), V(25.5, 14.0, 0), PORCH]
    pts2 = [PARTY + V(0.4, 0.9, 0), V(-5.2, 6, 0), V(-5.3, 11, 0), EYES_AT + V(0, -1.5, 0)]
    NEW["prints"], NEW["prints2"] = [], []
    for lst, ps in ((NEW["prints"], pts), (NEW["prints2"], pts2)):
        for i, (p, ang) in enumerate(trail(ps)):
            side = 0.13 * (1 if i % 2 else -1)
            q = p + V(-math.sin(ang) * side, math.cos(ang) * side, 0)
            o = S.shared("print", me, loc=(q.x, q.y, gz(q) + 0.03), rot=(0, 0, ang - math.pi / 2), scale=1.3)
            o.color = (0, 0, 0, 1)
            lst.append(o)


def build_props():
    M = S.MATS
    # candy basket on the stump
    bm = S.bm_cyl(0.3, 0.24, 0.22, seg=20, m=Matrix.Translation((0, 0, 0.11)))
    basket = S.mesh_obj("basket", bm, mat("wicker", (0.55, 0.38, 0.18), rough=0.9, bump=0.9),
                        loc=(S.STUMP.x, S.STUMP.y, 0.61))
    S.mesh_obj("basket_handle", S.bm_tube(S.arc_points(0, 0.22, 0.27, 0, math.pi, 14, 0), 0.02, seg=6),
               M["wicker"], parent=basket)
    cme = S.PROPS["candy"][0].data
    rnd = random.Random(4)
    cols = [(1, 0.15, 0.2), (0.2, 0.6, 1), (1, 0.85, 0.1), (0.3, 1, 0.35), (0.9, 0.3, 1), (1, 0.5, 0.1)]
    NEW["basket_candy"] = []
    for i in range(24):
        a, r = rnd.uniform(0, TAU), rnd.uniform(0, 0.2)
        h = 0.2 + 0.07 * (i // 8) + rnd.uniform(0, 0.04)
        o = S.shared(f"bcandy_{i}", cme, loc=(S.STUMP.x + r * math.cos(a), S.STUMP.y + r * math.sin(a), 0.61 + h),
                     rot=(rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), scale=1.2)
        o.color = (*cols[i % 6], 1)
        NEW["basket_candy"].append(o)
    # extra gravestones along the east path, and the claw branch
    for i, (x, y) in enumerate(((7.5, -2.4), (9.6, -3.1), (11.8, -2.2), (13.6, -3.0), (9.0, 2.6))):
        b = S.bm_rbox(0.55, 0.13, 0.6, bev=0.03, m=Matrix.Translation((0, 0, 0.3)))
        S.bm_cyl(0.275, 0.275, 0.13, seg=16, bm=b, m=Matrix.Translation((0, 0, 0.6)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        S.mesh_obj(f"p2grave_{i}", b, M["stone"], loc=(x, y, S.ground_h(x, y) - 0.04),
                   rot=(0.05 * i, -0.06, S.yaw_to(0, 1 if y < 0 else -1) + 0.2 * i), sharp_angle=0.6)
    cx = 12.0
    trunk_p = V(cx + 0.8, S.path_y(cx) + 2.6, 0)
    br = S.bm_cyl(0.3, 0.22, 3.4, seg=8, m=Matrix.Translation((0, 0, 1.7)))
    S.bm_tube([(0, 0, 2.6), (-0.4, -0.9, 2.3), (-0.6, -1.9, 1.75), (-0.7, -2.4, 1.35)], 0.1, seg=7, bm=br,
              taper=lambda u: 1 - 0.7 * u)
    for a in (-0.5, 0.0, 0.5):  # bony "fingers"
        S.bm_tube([(-0.7, -2.4, 1.35), (-0.7 + 0.25 * math.sin(a), -2.6 - 0.15 * math.cos(a), 1.2)], 0.03, seg=5,
                  bm=br, taper=lambda u: 1 - 0.8 * u)
    S.mesh_obj("claw_tree", br, M["bark"], loc=(trunk_p.x, trunk_p.y, gz(trunk_p) - 0.1))
    # the front door that swings open
    S.ENV["door"].hide_render = True
    hinge = S.empty("door_hinge", parent=bpy.data.objects["house"], loc=(-0.5, 2.56, 0))
    S.mesh_obj("door_new", S.bm_rbox(1.0, 0.08, 1.8, bev=0.02, m=Matrix.Translation((0.5, 0, 0.9))),
               mat("doorwood", (0.12, 0.07, 0.05), rough=0.8, bump=0.5), parent=hinge)
    glow = S.mesh_obj("door_glow", S.bm_rbox(0.96, 0.02, 1.76, bev=0.01, m=Matrix.Translation((0, 0, 0.88))),
                      S.MATS["window"], parent=bpy.data.objects["house"], loc=(0, 2.5, 0))
    glow.color = (0.0, 0.0, 0.0, 1)
    NEW.update(hinge=hinge, door_glow=glow)
    # the mystery eyes in the dark forest
    eyes = []
    for sx in (-1, 1):
        e = S.mesh_obj("big_eye", S.bm_sphere(1, 16, 8), S.MATS["owl_eye"],
                       loc=(EYES_AT.x + sx * 0.45, EYES_AT.y, gz(EYES_AT) + 2.4), scale=(0.22, 0.1, 0.3))
        e.color = (1.0, 0.85, 0.2, 1)
        eyes.append(e)
    NEW["big_eyes"] = eyes
    # a second candy basket for the montage, and the party candy carried by wisplings
    NEW["basket2"] = S.mesh_obj("basket2", S.bm_cyl(0.3, 0.24, 0.22, seg=20, m=Matrix.Translation((0, 0, 0.11))),
                                M["wicker"], loc=R + V(-1.3, -0.5, 0))


def build_room():
    M = S.MATS
    W, D, Hh = 8.0, 6.0, 3.3
    wall = S.mat_pbr("wallpaper", (0.2, 0.09, 0.18), rough=0.85, var=0.4, var_scale=40)
    floor = S.mat_pbr("planks", (0.22, 0.13, 0.07), rough=0.6, var=0.45, var_scale=8, bump=0.3)

    def box(name, size, loc, m, rot=(0, 0, 0)):
        return S.mesh_obj(name, S.bm_rbox(*size, bev=0.02), m, loc=R + V(*loc), rot=rot, sharp_angle=0.6)

    box("floor", (W, D, 0.1), (0, 0, -0.05), floor)
    box("ceiling", (W, D, 0.1), (0, 0, Hh), M["house_roof"])
    box("wall_n", (W, 0.1, Hh), (0, D / 2, Hh / 2), wall)
    box("wall_e", (0.1, D, Hh), (W / 2, 0, Hh / 2), wall)
    box("wall_w", (0.1, D, Hh), (-W / 2, 0, Hh / 2), wall)
    for x0, x1 in ((-W / 2, -0.6), (0.6, W / 2)):
        box("wall_s", (x1 - x0, 0.1, Hh), ((x0 + x1) / 2, -D / 2, Hh / 2), wall)
    box("wall_s_top", (1.2, 0.1, Hh - 2.0), (0, -D / 2, 2.0 + (Hh - 2.0) / 2), wall)
    box("skirting", (W, 0.12, 0.2), (0, D / 2 - 0.08, 0.1), M["doorwood"])
    # window with the moon, curtains
    box("window_frame", (1.4, 0.12, 1.6), (-2.2, D / 2 - 0.05, 1.8), M["doorwood"])
    sky = S.mesh_obj("window_sky", S.bm_rbox(1.2, 0.05, 1.4, bev=0.01), S.mat_emit("winsky", (0.08, 0.12, 0.3), 1.5),
                     loc=R + V(-2.2, D / 2 - 0.1, 1.8))
    S.mesh_obj("window_moon", S.bm_sphere(0.22, 16, 8), S.MATS["moon"], loc=R + V(-2.0, D / 2 - 0.13, 2.1),
               scale=(1, 0.2, 1))
    for sx in (-1, 1):
        box("curtain", (0.45, 0.06, 1.9), (-2.2 + sx * 0.82, D / 2 - 0.2, 1.75),
            S.mat_pbr("curtain", (0.4, 0.06, 0.12), rough=0.9, var=0.3, var_scale=20))
    # fireplace on the east wall
    box("fireplace", (0.6, 1.8, 1.4), (W / 2 - 0.35, 0.6, 0.7), M["stone"])
    box("hearth_hole", (0.3, 1.0, 0.8), (W / 2 - 0.62, 0.6, 0.45), M["engrave"])
    fire = S.mesh_obj("fire", S.bm_cyl(0.3, 0.02, 0.5, seg=10, m=Matrix.Translation((0, 0, 0.25))),
                      S.mat_emit("fire", (1, 1, 1), 8.0, obj_color=True), loc=R + V(W / 2 - 0.62, 0.6, 0.1))
    # table with the candy mountain
    box("table", (1.4, 0.9, 0.08), (-2.3, 1.5, 0.8), M["doorwood"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("leg", (0.07, 0.07, 0.8), (-2.3 + sx * 0.6, 1.5 + sy * 0.37, 0.4), M["doorwood"])
    cme = S.PROPS["candy"][0].data
    cols = [(1, 0.15, 0.2), (0.2, 0.6, 1), (1, 0.85, 0.1), (0.3, 1, 0.35), (0.9, 0.3, 1), (1, 0.5, 0.1)]
    rnd = random.Random(9)
    for i in range(170):
        h = rnd.random() ** 1.6 * 0.8
        r = (0.55 - h * 0.62) * math.sqrt(rnd.random())
        a = rnd.uniform(0, TAU)
        o = S.shared(f"mcandy_{i}", cme, loc=R + V(-2.3 + r * math.cos(a), 1.5 + r * math.sin(a) * 0.75, 0.88 + h),
                     rot=(rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), scale=1.25)
        o.color = (*cols[i % 6], 1)
    # Granny's little side table, candles, rocking chair, portraits, wrappers on the floor
    box("side_table", (0.6, 0.6, 0.06), (2.55, 1.6, 0.6), M["doorwood"])
    box("side_leg", (0.08, 0.08, 0.6), (2.55, 1.6, 0.3), M["doorwood"])
    cand = S.mat_pbr("wax", (0.95, 0.9, 0.75), rough=0.5)
    flame = S.mat_emit("flame", (1.0, 0.7, 0.3), 12.0, obj_color=True)
    NEW["flames"], NEW["candle_lights"] = [], []
    for i, (x, y, z, h) in enumerate(((2.55, 1.55, 0.63, 0.3), (-2.0, 1.3, 0.84, 0.22), (-1.4, 2.6, 0.0, 0.5))):
        S.mesh_obj("candle", S.bm_cyl(0.04, 0.04, h, seg=10, m=Matrix.Translation((0, 0, h / 2))), cand,
                   loc=R + V(x, y, z))
        f = S.mesh_obj("flame", S.bm_sphere(1, 10, 6), flame, loc=R + V(x, y, z + h + 0.04), scale=(0.02, 0.02, 0.045))
        f.color = (1, 0.7, 0.3, 1)
        NEW["flames"].append(f)
        L = bpy.data.lights.new(f"candle_{i}", "POINT")
        L.color, L.energy, L.use_shadow, L.shadow_soft_size = (1.0, 0.6, 0.25), 25, False, 0.1
        NEW["candle_lights"].append(S.link(bpy.data.objects.new(L.name, L), loc=R + V(x, y, z + h + 0.1)))
    fl = bpy.data.lights.new("fire_light", "POINT")
    fl.color, fl.energy, fl.use_shadow = (1.0, 0.45, 0.15), 90, False
    NEW["fire_light"] = S.link(bpy.data.objects.new("fire_light", fl), loc=R + V(W / 2 - 1.0, 0.6, 0.6))
    NEW["fire"] = fire
    wl = bpy.data.lights.new("window_light", "POINT")
    wl.color, wl.energy, wl.use_shadow = (0.5, 0.6, 1.0), 40, False
    S.link(bpy.data.objects.new("window_light", wl), loc=R + V(-2.2, D / 2 - 0.8, 2.0))
    box("chair_seat", (0.5, 0.5, 0.06), (1.9, 2.0, 0.45), M["doorwood"])
    box("chair_back", (0.5, 0.06, 0.6), (1.9, 2.25, 0.75), M["doorwood"])
    for sx in (-1, 1):
        S.mesh_obj("runner", S.bm_tube(S.arc_points(0, 0.9, 0.95, 4.4, 5.0, 10, 0), 0.025, seg=5), M["doorwood"],
                   loc=R + V(1.9 + sx * 0.22, 2.0, 0), rot=(0, 0, math.pi / 2))
    for i, (x, z) in enumerate(((0.2, 2.1), (1.2, 2.3), (-0.9, 2.2))):
        box("frame", (0.5 if i != 1 else 0.4, 0.05, 0.6), (x, D / 2 - 0.08, z), S.MATS["gold"])
        box("canvas", (0.4 if i != 1 else 0.3, 0.06, 0.5), (x, D / 2 - 0.1, z),
            S.mat_pbr(f"canvas{i}", [(0.15, 0.2, 0.1), (0.2, 0.12, 0.25), (0.25, 0.18, 0.1)][i], rough=0.9, var=0.6))
    rnd = random.Random(2)
    for i in range(14):  # wrappers trail from the door to the table
        u = i / 13
        p = lerp((0.0, -2.6), (-1.9, 1.0), u)
        o = S.shared(f"wrapper_{i}", cme, loc=R + V(p[0] + rnd.uniform(-.2, .2), p[1] + rnd.uniform(-.2, .2), 0.03),
                     rot=(math.pi / 2, 0, rnd.uniform(0, 3)), scale=(1.4, 1.4, 0.35))
        o.color = (*cols[i % 6], 1)
    # Wisplings' basket by the fireplace
    S.mesh_obj("wisp_basket", S.bm_cyl(0.42, 0.34, 0.25, seg=20, m=Matrix.Translation((0, 0, 0.125))), S.MATS["wicker"],
               loc=R + V(3.0, -0.7, 0))
    # the giant shadow on the north wall: Granny's outline, huge, with claw-like needles
    outline = []
    for r, z in ghost_profile(1.0, 0.55):
        outline.append((r, z))
    pts = [(x, z) for x, z in outline] + [(-x, z) for x, z in reversed(outline)]
    pts = pts[::-1]
    sbm = S.bm_prism(pts, 0.01)
    for sx in (-1, 1):  # needle "claws"
        S.bm_prism([(sx * 0.25, 0.35), (sx * 0.95, 1.25), (sx * 0.9, 1.3), (sx * 0.2, 0.42)], 0.01, bm=sbm)
        S.bm_prism([(sx * 0.38, 0.45), (sx * 1.15, 0.95), (sx * 1.1, 1.02), (sx * 0.33, 0.5)], 0.01, bm=sbm)
    S.bm_prism([(-0.1, 1.15), (0.05, 1.7), (0.35, 1.85), (0.15, 1.15)], 0.01, bm=sbm)  # nightcap "horn"
    sm, N_, L_ = S.new_mat("shadow")
    sm.surface_render_method = "BLENDED"
    oi = N_.new("ShaderNodeObjectInfo")
    tr, dk = N_.new("ShaderNodeBsdfTransparent"), N_.new("ShaderNodeEmission")
    dk.inputs["Color"].default_value = (0.0, 0.0, 0.01, 1)
    mx = N_.new("ShaderNodeMixShader")
    L_.new(oi.outputs["Alpha"], mx.inputs[0])
    L_.new(tr.outputs[0], mx.inputs[1])
    L_.new(dk.outputs[0], mx.inputs[2])
    S.finish(sm, N_, L_, mx.outputs[0], fog=False)
    sh = S.mesh_obj("wall_shadow", sbm, sm, loc=R + V(2.0, D / 2 - 0.07, 0.3), rot=(0, 0, math.pi), smooth_shade=False)
    sh.color = (0, 0, 0, 0)
    NEW["shadow"] = sh


# ================================================================ animation
def path_xy(x):
    return V(x, S.path_y(x), 0)


BOLT_PATH = S.PTrack(
    (0, (END.x, END.y)), (15.0, (END.x, END.y)), (15.01, (CLEAR.x, CLEAR.y)), (46.0, (CLEAR.x, CLEAR.y)),
    (48.0, P(3.0)), (57.0, P(12.5), "l"), (57.01, (25.4, 15.6)), (60.8, (PORCH.x - 0.4, PORCH.y - 0.5), "o"),
    (67.0, (PORCH.x - 0.4, PORCH.y - 0.5)), (67.01, (R.x + 0.0, R.y - 2.7)), (71.5, (R.x - 0.3, R.y - 0.9), "o"),
    (113.0, (R.x - 0.3, R.y - 0.9)), (115.0, (R.x - 0.5, R.y - 0.6)), (119.0, (R.x - 0.5, R.y - 0.6)),
    (119.01, (PORCH.x - 0.3, PORCH.y - 0.6)), (123.0, (24.6, 12.8), "l"),
    (127.0, (PARTY.x, PARTY.y)), (180.0, (PARTY.x, PARTY.y)),
)


def bolt_pos(t):
    if 123.0 <= t < 127.0:  # flying over the pumpkin patch, held by Boo
        a = math.pi + TAU * 0.8 * smooth((t - 123.0) / 4.0)
        return V(-9.0 + 5.0 * math.cos(a), 0.5 + 5.0 * math.sin(a), 1.7 + 0.25 * math.sin(t * 2.2))
    x, y = BOLT_PATH(t)
    p = V(x, y, 0)
    z = 0.0 if R.x - 10 < x < R.x + 10 else gz(p)
    z += BOLT_HOP(t)
    if 137.0 <= t < 149.0:
        z += abs(math.sin(t * 5)) * 0.1
    return V(x, y, z)


BOLT_HOP = T((0, 0.0), (35.6, 0.0), (35.75, 0.12, "o"), (35.95, 0.0, "i"), (53.7, 0.0), (53.85, 0.25, "o"),
             (54.2, 0.0, "i"), (72.4, 0.0), (72.55, 0.15, "o"), (72.8, 0.0, "i"), (176.3, 0.0), (176.45, 0.2, "o"),
             (176.7, 0.0, "i"))


def face_point(t):
    """Where Bolt looks (x, y) in each part of the story; None = walking direction."""
    if t < 15:
        return (16.0, 0.0)
    if t < 25:
        return (S.STUMP.x, S.STUMP.y)
    if t < 33:
        return (CLEAR.x - 4, CLEAR.y + 1.5)       # looks away at the owl
    if t < 42:
        return (S.STUMP.x, S.STUMP.y)
    if t < 46:
        return (CLEAR.x + 3, CLEAR.y - 1.5)
    if 61 <= t < 67:
        return (DOOR_W.x, DOOR_W.y)
    if 71.5 <= t < 81:
        return (R.x + 2.0, R.y + 2.9)            # the shadow
    if 81 <= t < 86 or 91 <= t < 97:
        return (R.x + 1.4, R.y + 1.2)            # Granny
    if 86 <= t < 91:
        return (R.x - 2.3, R.y + 1.5)            # candy table
    if 97 <= t < 108:
        return (R.x + 3.0, R.y - 0.7)            # Wisplings
    if 108 <= t < 119:
        return (R.x + 0.5, R.y - 0.2)
    if 127 <= t < 137:
        return (PARTY.x - 0.5, PARTY.y + 2.6)     # pumpkins
    if 137 <= t < 155:
        return (PARTY.x + 0.3, PARTY.y - 3.0)     # camera-ish
    if 155 <= t < 160:
        return (PARTY.x + 0.4, PARTY.y + 2.5)     # footprints
    if t >= 160:
        return (PARTY.x + 0.2, PARTY.y - 3.0)
    return None


YAW = []


def precompute():
    cur = None
    for f in range(NFRAMES + 1):
        t = f / FPS
        p0, p1 = bolt_pos(t - 0.08), bolt_pos(t + 0.08)
        v = V(p1.x - p0.x, p1.y - p0.y, 0)
        fp = face_point(t)
        if v.length / 0.16 > 0.4 and not (123 <= t < 127):
            want = S.yaw_to(v.x, v.y)
        elif fp is not None:
            p = bolt_pos(t)
            want = S.yaw_to(fp[0] - p.x, fp[1] - p.y)
        elif 123 <= t < 127:
            want = S.yaw_to(v.x, v.y)
        else:
            want = cur if cur is not None else 0.0
        jump = cur is None or (f > 0 and (bolt_pos(t) - bolt_pos(t - 1 / FPS)).length > 2.0)
        cur = want if jump else S.ang_lerp(cur, want, 0.18)
        if 142.0 <= t < 144.5:
            cur_out = cur + TAU * smooth((t - 142.0) / 2.0)
        else:
            cur_out = cur
        YAW.append(cur_out)


def byaw(t):
    return YAW[max(0, min(len(YAW) - 1, int(round(t * FPS))))]


def fwd(t):
    y = byaw(t)
    return V(-math.sin(y), math.cos(y), 0)


def boo_pos(t):
    b = bolt_pos(t)
    f = fwd(t)
    side = V(f.y, -f.x, 0)
    if t < 15:
        p = b + Matrix.Rotation(byaw(t), 3, "Z") @ V(0, -0.3, 1.37)
        return p + V(0, 0, 0.05 * math.sin(t * 3))
    if t < 46:
        p = V(S.STUMP.x + 0.85, S.STUMP.y - 0.8, 0.95)
        if 35.6 <= t < 36.0:
            p.z += 0.12 * math.sin((t - 35.6) / 0.4 * math.pi)
        return p + V(0, 0, 0.05 * math.sin(t * 2.6))
    if t < 67:
        if 53.7 <= t < 55.6:  # leaps into Bolt's arms
            return b + f * 0.42 + V(0, 0, 0.88)
        return b - f * 0.55 + side * 0.25 + V(0, 0, 0.85 + 0.04 * math.sin(t * 3))
    if t < 113:
        if 72.4 <= t < 81.0:  # hugging Bolt, trembling
            return b + side * -0.38 + f * 0.05 + V(0.01 * math.sin(t * 40), 0, 0.82)
        return b + side * -0.75 + V(0, 0, 0.9 + 0.05 * math.sin(t * 2.6))
    if t < 119:
        return R + V(-1.3, -0.5, 0.75 + 0.04 * math.sin(t * 6))
    if t < 123:
        return b + side * -0.8 + V(0, 0, 0.95 + 0.06 * math.sin(t * 3))
    if t < 127:
        return b + V(0, 0, 1.33)
    p = PARTY + V(0.85, 0.15, 0.92 + 0.06 * math.sin(t * 2.6))
    if 137.0 <= t < 149.0:
        p.z += abs(math.sin(t * 5 + 1)) * 0.12
    return p


def granny_pos(t):
    if t < 113:
        k = smooth((t - 86.0) / 2.5)
        a, b = R + V(1.9, 1.4, 0.12), R + V(0.9, 0.5, 0.12)
        p = a.lerp(b, k)
        if t > 108:
            p = b
        return p + V(0, 0, 0.04 * math.sin(t * 2))
    if t < 119:
        return R + V(0.6, -0.2, 0.2 + 0.05 * math.sin(t * 2))
    if t < 123:
        u = (t - 119.0) / 4.0
        return V(*lerp(tuple(PORCH + V(0.5, 0.4, 0)), (25.4, 13.6, 0), u)) + V(0, 0, gz(PORCH) * (1 - u) + 0.3)
    if t < 127:
        return bolt_pos(t - 0.7) + V(0, 0, 0.4)
    return PARTY + V(0.35, 1.05, 0.22 + 0.04 * math.sin(t * 2))


def wisp_pos(i, t):
    if t < 113:
        base = R + V(3.0 + 0.16 * math.cos(i * 1.3), -0.7 + 0.16 * math.sin(i * 1.3), 0.28)
        if t > 100:  # peek up shyly
            base.z += 0.12 * smooth((t - 100 - i * 0.3) / 1.0)
        return base + V(0, 0, 0.02 * math.sin(t * 3 + i))
    if t < 119:
        a = t * 2 + i * TAU / 5
        return R + V(-0.6 + 0.6 * math.cos(a), -0.5 + 0.6 * math.sin(a), 0.6 + 0.15 * math.sin(a * 2))
    if t < 123:
        return granny_pos(t - 0.35 * (i + 1)) + V(0, 0, 0.1)
    if t < 127:
        return bolt_pos(t - 0.45 * (i + 2)) + V(0, 0, 0.1)
    if t < 132:  # hiding behind Granny
        g = granny_pos(t)
        return g + V(-0.35 + 0.18 * i, 0.3, 0.05 + 0.04 * math.sin(t * 9 + i))
    if i == 0 and t < 137:  # the brave one offers a candy to the big pumpkin
        u = smooth((t - 132.0) / 2.2)
        g = granny_pos(t) + V(-0.35, 0.3, 0.05)
        return g.lerp(BIG_PUMPKIN + V(0, -0.5, 0.35), u)
    if t < 137:
        g = granny_pos(t)
        return g + V(-0.35 + 0.18 * i, 0.3, 0.05)
    a = (t - 137) * 1.8 + i * TAU / 5
    c = PARTY + V(0.4, 0.4, 0)
    return c + V(1.35 * math.cos(a), 1.35 * math.sin(a), 0.5 + 0.2 * abs(math.sin(t * 6 + i)))


BIG_PUMPKIN = V(0, 0, 0)


# ================================================================ shots
def lin(t0, t1, a, b):
    tr = T((t0, tuple(a)), (t1, tuple(b)))
    return lambda t: V(*tr(t))


def const(v):
    v = V(*v)
    return lambda t: v


def fol(fn, off):
    off = V(*off)
    return lambda t: fn(t) + off


Rx, Ry = R.x, R.y
CAM = {
    "episode card": (const((-36, -20, 9)), const((-36, 30, 22)), 26, 8),
    "the wink": (lambda t: bolt_pos(t) + V(-1.6, -2.6, 1.35) + V(0, -1.5, 0.2) * smooth((t - 6.5) / 2.5),
                 lambda t: boo_pos(t) + V(0, 0, -0.15) - V(0, 0, 0.6) * smooth((t - 6.5) / 2.5), 40, 2.8),
    "title": (lin(9, 15, (-40, -3.5, 2.0), (-40, -1.4, 2.15)), const((-40, 6.5, 2.2)), 32, 5.6),
    "candy pile": (lin(15, 21, (-2.7, -1.7, 1.5), (-2.3, -1.4, 1.35)), const((-0.3, 1.0, 0.75)), 30, 4),
    "midnight": (lin(21, 25, (-2.0, -1.0, 0.4), (-2.0, -1.0, 0.5)), lin(21, 25, (-24, 150, 40), (-30, 150, 52)), 30, 8),
    "yawn": (lin(25, 29, (0.6, -2.2, 1.0), (0.5, -2.0, 1.0)), const((0.0, 0.8, 0.9)), 32, 4),
    "candy vanishes": (lin(29, 33, (-0.9, 0.1, 1.4), (-0.75, 0.3, 1.3)), const((S.STUMP.x, S.STUMP.y, 0.75)), 35, 2.8),
    "it's gone": (lin(33, 37, (0.6, -1.6, 1.0), (0.5, -1.4, 1.0)), const((0.0, 0.7, 0.95)), 32, 2.8),
    "footprints": (lin(37, 42, (1.0, 1.4, 0.18), (1.4, 1.2, 0.22)), lin(37, 42, (6, 0.2, 0.0), (10, 0.5, 0.2)), 26, 4),
    "let's follow": (fol(bolt_pos, (0.7, -1.2, 1.0)), fol(bolt_pos, (0, 0, 0.95)), 40, 2.8),
    "card WHO TOOK": (const((8, -1.0, 0.4)), const((14, 0.5, 0.2)), 30, 8),
    "graveyard": (fol(bolt_pos, (1.2, -4.0, 1.0)), fol(bolt_pos, (0.6, 0, 0.6)), 32, 4),
    "the claw": (lambda t: bolt_pos(t) + V(-1.6, -1.8, 1.2), lambda t: bolt_pos(t) + V(0.2, 0.1, 0.9), 30, 4),
    "the house": (lin(57, 61, (21.5, 9.0, 1.2), (21.8, 9.4, 1.0)), const((S.HOUSE_POS.x, S.HOUSE_POS.y, 6.5)), 26, 8),
    "the door": (lambda t: PORCH + V(-2.6, -0.9, 1.3 + gz(PORCH)), lambda t: DOOR_W + V(0, 0, gz(DOOR_W) - 0.4), 28, 4),
    "card THE CANDY": (const((Rx, Ry - 2.7, 1.2)), const((Rx, Ry + 3, 1.2)), 30, 8),
    "inside": (lin(67, 72, (Rx + 0.5, Ry - 2.85, 0.9), (Rx + 0.3, Ry - 2.6, 0.95)), fol(bolt_pos, (0, 0, 0.7)), 26, 4),
    "the shadow": (lin(72, 77, (Rx - 2.3, Ry - 2.1, 0.35), (Rx - 2.2, Ry - 1.9, 0.38)), const((Rx + 1.6, Ry + 2.9, 1.55)), 22, 5.6),
    "who are you": (lambda t: bolt_pos(t) + V(0.9, 1.0, 1.0), lambda t: bolt_pos(t) + V(0.15, 0, 0.9), 35, 2.8),
    "granny reveal": (lambda t: R + V(0.6, -0.3, 0.75) + V(0.15, 0.25, 0) * smooth((t - 81) / 5),
                      lambda t: granny_pos(t) + V(0, 0, 0.4), 38, 2.8),
    "our candy": (lin(86, 91, (Rx + 0.9, Ry - 2.0, 1.3), (Rx + 0.8, Ry - 1.8, 1.25)), const((Rx - 1.4, Ry + 0.8, 0.9)), 26, 5.6),
    "granny sorry": (lambda t: granny_pos(t) + V(-0.35, -1.0, 0.45), lambda t: granny_pos(t) + V(0, 0, 0.45), 45, 2.8),
    "wisplings": (lin(97, 103, (Rx + 2.2, Ry - 2.0, 0.7), (Rx + 2.4, Ry - 1.8, 0.65)), const((Rx + 3.0, Ry - 0.7, 0.35)), 40, 2.8),
    "boo remembers": (lambda t: boo_pos(t) + V(0.35, 1.15, 0.12), lambda t: boo_pos(t) + V(0, 0, 0.02), 45, 2.8),
    "bolt's idea": (lambda t: bolt_pos(t) + fwd(t) * 1.2 + V(fwd(t).y, -fwd(t).x, 0) * 0.35 + V(0, 0, 1.05), lambda t: bolt_pos(t) + V(0, 0, 1.0), 40, 2.8),
    "card TOGETHER": (const((Rx, Ry - 2.7, 1.2)), const((Rx, Ry + 3, 1.2)), 30, 8),
    "montage hic": (lin(115, 119, (Rx - 1.6, Ry - 2.4, 1.1), (Rx - 1.4, Ry - 2.2, 1.0)), const((Rx - 1.0, Ry - 0.4, 0.6)), 28, 4),
    "montage parade": (lambda t: bolt_pos(t) + V(-1.6, -2.4, 1.0), lambda t: bolt_pos(t) + V(0.6, 0.9, 0.7), 28, 8),
    "montage flight": (lambda t: V(-9, 0.5, 0) + (bolt_pos(t) - V(-9, 0.5, 0)) * 1.0 + V(0, 0, 0) +
                       (V(bolt_pos(t).x + 9, bolt_pos(t).y - 0.5, 0).normalized() * 3.0) + V(0, 0, 0.3),
                       lambda t: bolt_pos(t) + V(0, 0, 0.7), 26, 8),
    "pumpkins scared": (lin(127, 132, (PARTY.x + 0.6, PARTY.y - 3.4, 1.4), (PARTY.x + 0.5, PARTY.y - 3.1, 1.3)),
                        const((PARTY.x + 0.2, PARTY.y + 1.2, 0.6)), 26, 5.6),
    "the offer": (lambda t: BIG_PUMPKIN + V(1.5, -1.6, 0.6), lambda t: BIG_PUMPKIN + V(0.0, -0.3, 0.35), 32, 2.8),
    "fast: candy ring": (S.orbit(lambda t: PARTY + V(0.4, 0.3, 0), 3.0, 1.2, -1.2, -0.7, 137, 139.5),
                         const(tuple(PARTY + V(0.4, 0.3, 1.0))), 28, 4),
    "fast: wisplings dance": (const(tuple(PARTY + V(0.5, -2.7, 0.7))), const(tuple(PARTY + V(0.4, 0.4, 0.6))), 24, 4),
    "fast: spin": (const(tuple(PARTY + V(0.3, -2.0, 1.0))), const(tuple(PARTY + V(0.4, 0.0, 0.9))), 30, 4),
    "group hug": (lin(144.5, 149, (PARTY.x + 0.5, PARTY.y - 2.6, 1.1), (PARTY.x + 0.45, PARTY.y - 2.2, 1.05)),
                  const(tuple(PARTY + V(0.45, 0.35, 0.8))), 32, 4),
    "the lesson": (lambda t: granny_pos(t) + V(-0.5, -1.05, 0.5), lambda t: granny_pos(t) + V(0, 0, 0.42), 40, 2.8),
    "no feet": (lambda t: bolt_pos(t) + fwd(t) * 1.25 + V(fwd(t).y, -fwd(t).x, 0) * 0.4 + V(0, 0, 1.05), lambda t: bolt_pos(t) + V(0, 0, 0.98), 38, 2.8),
    "freeze": (lin(160, 164, (PARTY.x + 0.45, PARTY.y - 2.7, 1.0), (PARTY.x + 0.45, PARTY.y - 2.0, 1.0)),
               const(tuple(PARTY + V(0.45, 0.4, 0.75))), 30, 4),
    "the eyes": (lin(164, 170, tuple(PARTY + V(0.4, 1.6, 0.35)), tuple(PARTY + V(0.3, 5.5, 0.6))),
                 lin(164, 170, tuple(PARTY + V(0.3, 7.0, 0.1)), tuple(EYES_AT + V(0, 0, 2.3))), 30, 8),
    "part 3 card": (lin(170, 175, (-36, -16, 4), (-36, -14, 3)), const((-36, 30, 18)), 26, 8),
    "final gag": (lin(175, 180, (PARTY.x + 0.4, PARTY.y - 2.5, 1.05), (PARTY.x + 0.4, PARTY.y - 2.2, 1.05)),
                  const(tuple(PARTY + V(0.4, 0.2, 0.9))), 32, 4),
}


def shot_at(t):
    for s in SHOTS:
        if s[0] <= t < s[1]:
            return s
    return SHOTS[-1]


def cam_state(t):
    s = shot_at(t)
    pos, tgt, lens, fstop = CAM[s[2]]
    p, g = V(*pos(t)), V(*tgt(t))
    k = 0.004 + 0.02 * window(t, 53.7, 54.6, 0.1) + 0.03 * window(t, 57.0, 57.5, 0.05) + \
        0.015 * window(t, 72.4, 74.0, 0.2) + 0.03 * window(t, 168.4, 169.0, 0.05)
    for i in range(3):
        p[i] += wob(t, 0.9, i) * k * 6
        g[i] += wob(t, 0.8, i + 4) * k * 9
    return p, g, lens, fstop


# ================================================================ per frame
EYE_T = T((0, (1, 1)), (33.0, (1, 1)), (33.15, (1.5, 1.5), "o"), (36.5, (1.5, 1.5)), (37, (1, 1)),
          (42.3, (1, 1)), (42.5, (1.05, 0.75)), (46, (1.05, 0.75)), (46.5, (1, 1)), (53.7, (1, 1)),
          (53.8, (1.4, 1.4), "o"), (55.4, (1.4, 1.4)), (55.6, (1, 1)), (61.5, (1, 1)), (61.7, (1.3, 1.3)),
          (66, (1.3, 1.3)), (72.4, (1.3, 1.3)), (72.5, (1.6, 1.6), "o"), (80.8, (1.6, 1.6)), (81.3, (1.2, 1.2)),
          (86.5, (1.2, 1.2)), (86.7, (1.4, 1.4)), (90, (1, 1)), (91.5, (1, 0.85)), (108, (1, 0.85)), (108.3, (1.3, 1.3), "b"),
          (110.5, (1.1, 1.1)), (113, (1, 1)), (155.3, (1, 1)), (157.6, (1, 1)), (157.75, (1.5, 1.5), "o"),
          (164, (1.5, 1.5)), (164.2, (1, 1)), (175.9, (1, 1)), (176.0, (1.4, 1.4), "o"), (176.4, (1.2, 0.4)),
          (178.5, (1.2, 0.4)), (178.8, (1, 1)))
HAPPY = T((0, 1.0), (15.0, 1.0), (15.01, 1.0), (24.9, 1.0), (25.0, 0.0), (115.0, 0.0), (115.1, 1.0), (155.2, 1.0),
          (155.3, 0.0), (180, 0.0))
SYMQ = T((0, 0.0), (157.4, 0.0), (157.6, 0.0), (88.4, 0.0))
ARMS = {  # (raise, inward) right / left
    "r": T((0, (0.15, 0.0)), (15.0, (0.15, 0.0)), (15.6, (1.4, 0.2)), (16.4, (0.4, 0.0)), (17.0, (1.4, 0.2)),
           (17.8, (0.4, 0.0)), (25.0, (0.15, 0.0)), (25.3, (2.8, -0.3)), (27.0, (2.8, -0.3)), (27.4, (0.15, 0.0)),
           (33.2, (0.15, 0.0)), (33.4, (2.6, 0.6), "o"), (36.5, (2.6, 0.6)), (37.0, (0.15, 0.0)), (42.4, (0.15, 0.0)),
           (42.8, (2.4, -0.2), "o"), (45.5, (2.4, -0.2)), (46.0, (0.15, 0.0)), (53.7, (0.15, 0.0)), (53.9, (1.3, 0.8), "o"),
           (55.6, (1.3, 0.8)), (56.0, (0.15, 0.0)), (72.4, (0.15, 0.0)), (72.6, (1.3, 0.8)), (80.8, (1.3, 0.8)),
           (81.2, (0.15, 0.0)), (108.3, (0.15, 0.0)), (108.6, (2.8, -0.1), "b"), (110.4, (2.8, -0.1)), (110.8, (1.4, 0.3)),
           (113.0, (0.15, 0.0)), (127.8, (0.15, 0.0)), (128.1, (1.4, -0.6)), (130.2, (1.4, -0.6)), (130.6, (0.15, 0.0)),
           (137.0, (0.15, 0.0)), (137.3, (2.7, -0.3)), (144.5, (2.7, -0.3)), (145.0, (1.4, 0.6)), (149.0, (1.4, 0.6)),
           (149.4, (0.15, 0.0)), (157.6, (0.15, 0.0)), (157.8, (1.5, -0.7), "o"), (160.0, (1.5, -0.7)), (160.3, (0.15, 0.0)),
           (176.3, (0.15, 0.0)), (176.5, (2.6, 0.3), "o"), (178.0, (2.6, 0.3)), (178.4, (0.15, 0.0))),
    "l": T((0, (0.15, 0.0)), (25.0, (0.15, 0.0)), (25.3, (2.8, -0.3)), (27.0, (2.8, -0.3)), (27.4, (0.15, 0.0)),
           (33.2, (0.15, 0.0)), (33.4, (2.6, 0.6), "o"), (36.5, (2.6, 0.6)), (37.0, (0.15, 0.0)), (53.7, (0.15, 0.0)),
           (53.9, (1.3, 0.8), "o"), (55.6, (1.3, 0.8)), (56.0, (0.15, 0.0)), (72.4, (0.15, 0.0)), (72.6, (1.3, 0.8)),
           (80.8, (1.3, 0.8)), (81.2, (0.15, 0.0)), (88.4, (0.15, 0.0)), (88.7, (1.5, -0.5)), (90.5, (1.5, -0.5)),
           (90.9, (0.15, 0.0)), (137.0, (0.15, 0.0)), (137.3, (2.7, -0.3)), (144.5, (2.7, -0.3)), (145.0, (1.4, 0.6)),
           (149.0, (1.4, 0.6)), (149.4, (0.15, 0.0)), (176.3, (0.15, 0.0)), (176.5, (2.6, 0.3), "o"), (178.0, (2.6, 0.3)),
           (178.4, (0.15, 0.0))),
}
BOO_EYES = T((0, 1.0), (4.6, 1.0), (4.7, 1.0), (33.0, 1.0), (33.1, 1.4, "o"), (37, 1.0), (53.7, 1.0), (53.75, 1.5),
             (55.5, 1.5), (55.8, 1.0), (72.4, 1.0), (72.5, 1.45), (81, 1.45), (81.3, 1.0), (103.0, 1.0), (103.5, 0.6),
             (108.0, 0.6), (108.4, 1.0), (115, 1.0), (115.1, 0.35), (155.2, 0.35), (155.3, 1.0), (157.7, 1.0),
             (157.8, 1.45), (164, 1.45), (164.2, 0.35), (180, 0.35))
BOO_FROWN = T((0, 0.0), (103.0, 0.0), (103.6, 1.0), (108.0, 1.0), (108.4, 0.0))
BOO_SQ = T((0, 0.0), (35.55, 0.0), (35.6, -0.3, "o"), (35.85, 0.25), (36.1, 0.0), (53.7, 0.0), (53.8, 0.3, "o"),
           (54.1, -0.15), (54.4, 0.0), (175.0, 0.0))


def candy_head(t):
    b = bolt_pos(t)
    return b + Matrix.Rotation(byaw(t), 3, "Z") @ V(-0.05, 0, 1.25)


def apply(t):
    cam = S.SC.camera
    p, g, lens, fstop = cam_state(t)
    cam.location = p
    cam.rotation_euler = (g - p).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = max(0.2, (g - p).length)
    cam.data.dof.aperture_fstop = fstop
    inside = 67.0 <= t < 119.0 and not (113 <= t < 115 and False)
    if 115.0 <= t < 119.0:
        inside = True
    S.setv(S.FOG.nodes["density"].inputs[1], -(0.012 if inside else 0.022 + 0.015 * window(t, 9, 15, 0.5)))
    flash = window(t, 57.0, 57.3, 0.03) + 0.6 * window(t, 57.45, 57.55, 0.03)
    S.setv(S.ENV["sun"].data, (0.05 if inside else 1.6) + 9 * flash, "energy")
    S.setv(S.ENV["rim"].data, 0.0 if inside else 0.45, "energy")

    # ---- Bolt
    B = S.BOLT
    bp = bolt_pos(t)
    B["root"].location = bp
    B["root"].rotation_euler = (0, 0, byaw(t))
    B["wheel"].rotation_euler = (-(bp.x + bp.y) * 3.0, 0, 0)
    tremble = 0.05 * window(t, 72.5, 80.8, 0.2) + 0.03 * window(t, 157.8, 164, 0.2)
    lean = 0.12 if (46 <= t < 57 or 119 <= t < 123) else 0.0
    side = 0.35 if 123 <= t < 127 else 0.0
    B["tilt"].rotation_euler = (-lean + tremble * wob(t, 25, 1), -side + tremble * wob(t, 27, 2), 0)
    talk = mouth("bolt", t)
    yawn = window(t, 25.2, 27.2, 0.3)
    B["head"].rotation_euler = (0.06 * talk * math.sin(t * 20) + 0.15 * yawn, 0, 0.25 * math.sin(t * 0.8) * window(t, 48, 57, 1))
    ew, eh = EYE_T(t)
    blink = max(window(t, b, b + 0.13, 0.04) for b in (17.6, 40.5, 50.4, 69.4, 94.6, 101.0, 130.8, 152.0, 162.5))
    eh *= (1 - 0.92 * blink) * (1 - 0.7 * yawn)
    happy = HAPPY(t)
    for i, e in enumerate(B["eyes"]):
        sx = -1 if i == 0 else 1
        e.scale = (0.045 * ew * (1 - happy), 0.02, max(0.0005, 0.075 * eh * (1 - happy)))
        e.hide_render = happy > 0.5
        e.location = (sx * 0.12, 0.24, 0.24)
        e.rotation_euler = (0, sx * 0.3 * window(t, 91.5, 108, 0.3), 0)
    for h in B["happy"]:
        S.set_vis(h, happy)
    om = max(min(1.0, talk * 1.8), yawn, window(t, 33.0, 36.5, 0.1), window(t, 72.5, 80.8, 0.2),
             window(t, 157.7, 164, 0.1))
    S.set_vis(B["omouth"], (0.55 + 0.6 * min(1.0, talk * 1.8 + yawn)) if om > 0.08 else 0)
    S.set_vis(B["smile"], (1 + 0.4 * happy) if om <= 0.08 else 0)
    for arm, key, sx in ((B["arms"][1], "r", 1), (B["arms"][0], "l", -1)):
        r, inward = ARMS[key](t)
        if 46 <= t < 57 or 119 <= t < 123:
            r += 0.35 * math.sin(t * 9 + (0 if sx > 0 else math.pi))
        if 123 <= t < 127:
            r, inward = 2.9, 0.1
        arm.rotation_euler = (r, 0, sx * inward)
    lamp = 1.0 + 0.8 * window(t, 42.4, 45.5, 0.3) + 0.6 * window(t, 108.3, 110.5, 0.2)
    flick = 1 - 0.5 * window(t, 72.5, 80.8, 0.2) * (0.5 + 0.5 * math.sin(t * 37) * math.sin(t * 13))
    B["bulb"].color = (1.0 * flick * min(lamp, 1.6), 0.65 * flick, 0.25 * flick, 1)
    S.setv(B["lamp"].data, round(22 * flick * lamp * (1.8 if inside else 1.0), 1), "energy")
    sym = bp + V(0.32, 0, 1.55)
    S.billboard(B["sym"]["?"], cam, sym, window(t, 88.4, 90.6, 0.15) + window(t, 157.7, 159.5, 0.15) * 1.2)
    S.billboard(B["sym"]["!"], cam, sym, 1.2 * (window(t, 33.1, 35.2, 0.12) + window(t, 72.5, 74.4, 0.12) +
                                                window(t, 176.4, 177.6, 0.1)))
    S.place_blob(S.PROPS["blob_bolt"], bp if not inside else bp + V(0, 0, 0), 0.42, 0.85)

    # ---- Boo
    G = S.BAG
    gp = boo_pos(t)
    G["root"].location = gp
    if t < 15:
        G["root"].rotation_euler = (0, 0, S.yaw_to(cam.location.x - gp.x, cam.location.y - gp.y))
    elif 115 <= t < 119:
        G["root"].rotation_euler = (0, 0, S.yaw_to(-0.2, -1))
    else:
        tgt = bp if not (127 <= t < 180 or 103 <= t < 108) else V(cam.location.x, cam.location.y, 0)
        if 25 <= t < 33:
            tgt = V(CLEAR.x - 4, CLEAR.y + 1.5, 0)
        G["root"].rotation_euler = (0, 0, S.yaw_to(tgt.x - gp.x, tgt.y - gp.y) + 0.3 * math.sin(t * 6) * window(t, 137, 149, 0.3))
    sq = BOO_SQ(t)
    if 115 <= t < 119:
        sq = 0.3 * max(0.0, math.sin((t - 115.3) / 0.42 * math.pi * 2))
    G["body"].scale = (1 + sq * 0.5, 1 + sq * 0.5, 1 - sq)
    G["body"].rotation_euler = (0.07 * math.sin(t * 1.7), 0.09 * math.sin(t * 1.3), 0)
    eo = BOO_EYES(t)
    bl = max(window(t, b, b + 0.13, 0.04) for b in (12.0, 23.0, 44.0, 62.0, 99.0, 121.0, 152.5))
    for i, e in enumerate(G["eyes"]):
        sx = -1 if i == 0 else 1
        wink = (window(t, 4.6, 5.3, 0.08) + window(t, 178.0, 178.8, 0.08)) if i == 0 else 0.0
        h = eo * (1 - bl) * (1 - 0.95 * min(1, wink))
        e.scale = (0.05 * (1.15 if eo > 1.1 else 1), 0.02, max(0.0005, 0.06 * h))
        e.hide_render = h < 0.02
        e.rotation_euler = (0, -sx * 0.5 * BOO_FROWN(t), 0)
        e.color = (0.85, 0.5, 1.0, 1)
    fr = BOO_FROWN(t)
    mo = max(0.25 + 1.1 * mouth("boo", t), 0.9 * window(t, 33.1, 36.4, 0.1), 1.2 * window(t, 53.7, 55.5, 0.1),
             0.9 * window(t, 72.5, 80.8, 0.2), (0.6 if 115 <= t < 119 else 0), 0.9 * window(t, 157.8, 164, 0.1))
    G["mouth"].scale = (1 - 0.3 * fr, 1, mo * (1 - 0.7 * fr))
    G["mouth"].rotation_euler = (0, math.pi * fr, 0)
    G["mouth"].hide_render = False
    G["tear"].location = (0.11, 0.268, 0.03 - 0.17 * S.clamp((t - 104.5) / 3))
    S.set_vis(G["tear"], 1.0 if 104.5 < t < 107.6 else 0.0)
    G["glow"].data.energy = 6
    G["glow"].data.color = (0.85, 0.5, 1.0)
    for o in G["body"].children:
        if o.name.startswith(("bag_sack", "bag_tuft")):
            o.color = (0.85, 0.5, 1.0, 0.5)
    S.place_blob(S.PROPS["blob_bag"], gp - V(0, 0, 0.28), 0.36, 0.8)

    # ---- Granny Gloom & the Wisplings
    gr = NEW["granny"]
    grp = granny_pos(t)
    gr["root"].location = grp
    gr["root"].hide_render = False
    look = bp if t < 127 or 149 <= t else V(cam.location.x, cam.location.y, 0)
    gr["root"].rotation_euler = (0, 0, S.yaw_to(look.x - grp.x, look.y - grp.y))
    gt = mouth("granny", t)
    gr["body"].scale = (1 + 0.04 * gt, 1 + 0.04 * gt, 1 - 0.04 * gt + 0.02 * math.sin(t * 2))
    gr["body"].rotation_euler = (0.05 * math.sin(t * 1.5) - 0.12 * window(t, 91.5, 97, 0.4), 0.06 * math.sin(t * 1.1), 0)
    knit = window(t, 0, 86.2, 0.3) + window(t, 91.4, 97.0, 0.3) * 0.5
    gr["needles"].rotation_euler = (0.3 * math.sin(t * 9) * knit, 0, 0.2 * math.sin(t * 9 + 1) * knit)
    gr["smile"].scale = (1, 1, -1.0 if 91.4 <= t < 103 else 1.0 + 0.6 * gt)
    vis = 67.0 <= t
    for o in [gr["root"]] + list(gr["root"].children_recursive):
        o.hide_render = not vis
    for i, w in enumerate(NEW["wisps"]):
        wp = wisp_pos(i, t)
        w["root"].location = wp
        lookw = V(cam.location.x, cam.location.y, 0)
        w["root"].rotation_euler = (0, 0, S.yaw_to(lookw.x - wp.x, lookw.y - wp.y) + 0.2 * math.sin(t * 3 + i))
        shiver = 0.03 * math.sin(t * 40 + i) if 97 <= t < 103 or 127 <= t < 132 else 0.0
        w["root"].scale = (1 + shiver, 1 + shiver, 1 - shiver)
        bl = window(t, 99.5 + i * 0.4, 99.65 + i * 0.4, 0.04)
        for e in w["eyes"]:
            e.scale = (0.018, 0.01, max(0.001, 0.026 * (1 - bl)))
        for o in [w["root"]] + list(w["root"].children_recursive):
            o.hide_render = not (97.0 <= t)

    # ---- the giant shadow
    sh = NEW["shadow"]
    rise = smooth((t - 72.2) / 1.6) * (1 - smooth((t - 80.9) / 0.4))
    sh.scale = (0.9 + 0.45 * rise, 1, 0.6 + 0.75 * rise)
    sh.color = (0, 0, 0, 0.82 * rise)
    sh.hide_render = rise < 0.01
    sh.rotation_euler = (0, 0.04 * math.sin(t * 9), math.pi)

    # ---- props
    for i, o in enumerate(NEW["basket_candy"]):  # vanishing at midnight, two per pop
        S.set_vis(o, 1.2 if t < 29.4 + (i // 2) * 0.28 else 0.0)
    prints_on = smooth((t - 37.2) / 0.3)
    for i, o in enumerate(NEW["prints"]):
        on = S.clamp((t - (37.3 + i * 0.1)) / 0.2) * prints_on
        pulse = 0.75 + 0.25 * math.sin(t * 3 + i * 0.7)
        o.color = (0.25 * on * pulse, 1.0 * on * pulse, 0.7 * on * pulse, 1)
        o.hide_render = on < 0.01
    for i, o in enumerate(NEW["prints2"]):
        on = S.clamp((t - (155.5 + i * 0.12)) / 0.2)
        o.color = (0.25 * on, 1.0 * on, 0.7 * on, 1)
        o.hide_render = on < 0.01
    NEW["hinge"].rotation_euler = (0, 0, -1.6 * smooth((t - 61.6) / 2.2) if t < 119 else -1.6)
    NEW["door_glow"].color = (0.0, 0.0, 0.0, 1) if t < 61.6 else ((0.35, 0.22, 0.1, 1) if t < 119 else (0.9, 0.6, 0.25, 1))
    o = smooth((t - 166.6) / 0.25) * (1 - window(t, 167.9, 168.05, 0.03))
    for e in NEW["big_eyes"]:
        e.scale = (0.22, 0.1, max(0.003, 0.3 * o))
        e.hide_render = o < 0.02
    fire_f = 0.8 + 0.2 * math.sin(t * 13) * math.sin(t * 7.1)
    NEW["fire"].color = (1.0 * fire_f, 0.45 * fire_f, 0.1, 1)
    S.setv(NEW["fire_light"].data, round(90 * fire_f, 0), "energy")
    for k, f in enumerate(NEW["flames"]):
        f.scale = (0.02, 0.02, 0.045 * (0.9 + 0.1 * math.sin(t * 17 + k)))
    for k, L in enumerate(NEW["candle_lights"]):
        S.setv(L.data, round(25 * (0.9 + 0.1 * math.sin(t * 17 + k)), 0), "energy")

    # the running gag: the candy on Bolt's head (gone at 175.9)
    candies = S.PROPS["candy"]
    for i, c in enumerate(candies):
        if i == 0:
            if t < 175.9:
                c.location = candy_head(t)
                c.rotation_euler = (0, 0, 0.3)
                S.set_vis(c, 1.25)
            else:
                S.set_vis(c, 0)
            continue
        if 137.0 <= t < 149.0 or 115.0 <= t < 119.0:
            if 115 <= t < 119:  # hiccuped candies arcing into the basket
                k = (t - 115.3 - (i % 9) * 0.42)
                if 0 <= k < 0.5:
                    a = R + V(-1.3, -0.68, 0.8)
                    c.location = a.lerp(R + V(-1.3, -0.5, 0.25), k / 0.5) + V(0, 0, 0.3 * math.sin(k / 0.5 * math.pi))
                    S.set_vis(c, 1.2)
                else:
                    S.set_vis(c, 0)
                continue
            a = TAU * i / (len(candies) - 1) + (t - 137) * 1.6
            center = PARTY + V(0.4, 0.3, 0)
            c.location = center + V(1.7 * math.cos(a), 1.7 * math.sin(a), 1.2 + 0.15 * math.sin(a * 3 + t * 2))
            c.rotation_euler = (t * 3 + i, t * 2 + i, 0)
            S.set_vis(c, 1.1)
        else:
            S.set_vis(c, 0)
    for i, h in enumerate(S.PROPS["hearts"]):
        t0 = 145.0 + i * 0.5
        u = (t - t0) / 3.0
        if 0 <= u <= 1:
            h.location = PARTY + V(0.4 + 0.6 * math.sin(i * 2.4 + u * 4), 0.2, 1.3 + u * 1.5)
            h.rotation_euler = (math.pi / 2, 0, cam.rotation_euler.z)
            S.set_vis(h, math.sin(min(u * 4, 1) * math.pi / 2) * (1 - smooth((u - 0.7) / 0.3)) * 1.3)
        else:
            S.set_vis(h, 0)

    # pumpkins: lit, scared (dim) at 127, relit happy in a wave from 133.5; bounce at the party
    party = window(t, 137, 155, 0.3)
    for root, face, i in S.ENV["pumpkins"]:
        scared = window(t, 127.2, 133.3 + i * 0.2, 0.15)
        fl = (0.85 + 0.15 * math.sin(t * 9 + i * 2.1)) * (1 - 0.85 * scared) + 0.4 * party * abs(math.sin(t * 8 + i))
        face.color = (min(1, fl), min(1, 0.42 * fl), 0.08 * fl, 1)
        b = 0.06 * party * abs(math.sin(t * 8 + i * 1.7))
        root.scale = (1 + b, 1 + b, 1 - b)
    for L in S.ENV["pumpkin_lights"]:
        S.setv(L.data, 70.0, "energy")
    fw = 0.4 + 0.6 * smooth((t - 132) / 6)
    for o, base, ph in S.PROPS["flies"]:
        o.location = base + V(wob(t, 0.15, ph) * 1.5, wob(t, 0.15, ph + 3) * 1.5, wob(t, 0.2, ph + 6) * 0.5)
        tw = (0.6 + 0.4 * fw) * (0.55 + 0.45 * math.sin(t * 3 + ph))
        hue = (ph * 0.137) % 1.0
        r_, g_, b_ = __import__("colorsys").hsv_to_rgb(hue, 0.75, 1.0)
        o.color = (r_ * tw, g_ * tw, b_ * tw, 1)
    for k, w in enumerate(S.ENV["windows"]):
        w.color = (0.9, 0.6, 0.25, 1)
    for c, base in S.ENV["fogcards"]:
        c.location = base + Vector((0.12 * t % 8 - 4, 0.05 * math.sin(t * 0.1), 0))
    for o, wings in S.PROPS["bats"]:
        o.hide_render = True
        for c in o.children_recursive:
            c.hide_render = True
    for e in S.ENV["owl_eyes"]:
        e.hide_render = True
    title = S.PROPS["title"]
    title.hide_render = True
    fl = smooth((t - 9.3) / 0.6)
    title.color = (1.0 * fl, 0.62 * fl, 0.1 * fl, 1)
    title.scale = (1 + 0.025 * (t - 9),) * 3
    S.PROPS["theend"].hide_render = True


def on_frame(scene, depsgraph=None):
    apply(scene.frame_current / FPS)


def _set_mix_colors(mat_or_tree, a=None, b=None):
    nt = mat_or_tree.node_tree if hasattr(mat_or_tree, "node_tree") else mat_or_tree
    for n in nt.nodes:
        if n.bl_idname == "ShaderNodeMix" and getattr(n, "data_type", "") == "RGBA":
            if a is not None:
                n.inputs[6].default_value = (*a, 1)
            if b is not None:
                n.inputs[7].default_value = (*b, 1)
            return n


def _base(mat, col):
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (*col, 1)


ACCENTS = []


def colorize():
    """Colour pass: purple-magenta night, teal rims, coloured accent lights, rainbow fireflies."""
    M = S.MATS
    S.FOG.nodes["fogcol"].inputs["Color"].default_value = (0.065, 0.04, 0.1, 1)
    wn = S.SC.world.node_tree.nodes
    for n in wn:
        if n.bl_idname == "ShaderNodeMix" and n.data_type == "RGBA":
            if n.blend_type == "MIX":      # sky gradient: magenta-purple horizon, deep indigo zenith
                n.inputs[6].default_value = (0.13, 0.045, 0.17, 1)
                n.inputs[7].default_value = (0.03, 0.015, 0.09, 1)
            elif tuple(round(v, 2) for v in n.inputs[7].default_value[:3]) == (0.32, 0.36, 0.5):
                n.inputs[7].default_value = (0.75, 0.38, 0.55, 1)   # pink moon halo
    S.ENV["sun"].data.color = (0.78, 0.68, 1.0)
    S.ENV["rim"].data.color = (0.15, 1.0, 0.9)
    S.ENV["rim"].data.energy = 1.1
    _set_mix_colors(M["bark"], (0.07, 0.03, 0.07), (0.16, 0.08, 0.14))
    g = M["ground"].node_tree.nodes
    mixes = [n for n in g if n.bl_idname == "ShaderNodeMix"]
    mixes[0].inputs[6].default_value = (0.02, 0.09, 0.07, 1)   # teal moss
    mixes[0].inputs[7].default_value = (0.09, 0.12, 0.03, 1)
    mixes[1].inputs[7].default_value = (0.2, 0.1, 0.06, 1)     # warm path
    _set_mix_colors(M["grass"], (0.06, 0.2, 0.12), (0.3, 0.18, 0.05))
    _set_mix_colors(M["stone"], (0.16, 0.15, 0.26), (0.3, 0.27, 0.42))
    _set_mix_colors(M["moss_stone"], (0.05, 0.16, 0.13), (0.12, 0.3, 0.22))
    _set_mix_colors(M["pumpkin"], (0.95, 0.35, 0.02), (1.0, 0.55, 0.08))
    for n in M["fogcard"].node_tree.nodes:
        if n.bl_idname == "ShaderNodeEmission":
            n.inputs["Color"].default_value = (0.18, 0.1, 0.24, 1)
    M["jack_face"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 11.0
    for name, loc, col, en in (("acc_magenta", (-3.0, 4.5, 2.6), (1.0, 0.15, 0.7), 260),
                               ("acc_cyan", (4.0, -3.5, 2.2), (0.1, 0.9, 1.0), 220),
                               ("acc_orange", (-11.5, 3.5, 1.4), (1.0, 0.45, 0.1), 200),
                               ("acc_violet", (13.0, 5.0, 2.8), (0.6, 0.25, 1.0), 260),
                               ("acc_green", (-19.0, -4.5, 1.6), (0.3, 1.0, 0.4), 200),
                               ("acc_pink", (-7.0, -3.0, 2.0), (1.0, 0.4, 0.6), 180),
                               ("acc_house", (24.0, 14.0, 4.5), (0.85, 0.3, 1.0), 450),
                               ("acc_eyes", (-5.5, 13.0, 2.5), (0.2, 0.8, 0.6), 160)):
        L = bpy.data.lights.new(name, "POINT")
        L.color, L.energy, L.use_shadow, L.shadow_soft_size = col, en * 2.6, False, 1.0
        ACCENTS.append(S.link(bpy.data.objects.new(name, L), loc=loc))
    S.PROPS["title"].hide_render = True       # the title is now a colourful 2D card in post


def setup(samples, pct):
    global BIG_PUMPKIN
    S.build_all(samples, pct)
    bpy.app.handlers.frame_change_pre.clear()
    build_granny()
    build_wisplings()
    build_footprints()
    build_props()
    build_room()
    S.PROPS["title"].data.body = "THE MYSTERY OF THE\nMIDNIGHT CANDY"
    S.PROPS["title"].data.size = 1.0
    best = min(S.ENV["pumpkins"], key=lambda r: (r[0].location - V(PARTY.x - 0.4, PARTY.y + 2.4, 0)).length)
    BIG_PUMPKIN = best[0].location.copy()
    best[0].scale = (1.6, 1.6, 1.6)
    for root, face, i in S.ENV["pumpkins"]:  # clear the party floor
        if (root.location - PARTY).length < 1.6 and root is not best[0]:
            root.hide_render = True
            for c in root.children:
                c.hide_render = True
    colorize()
    precompute()
    bpy.app.handlers.frame_change_pre.append(on_frame)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--at", default="")
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--out", default=os.path.join(HERE, "work", "frames"))
    a = ap.parse_args()
    setup(a.samples, a.pct)
    sc = S.SC
    if a.at:
        out = os.path.join(HERE, "work", "stills")
        os.makedirs(out, exist_ok=True)
        sc.render.use_overwrite, sc.render.use_placeholder = True, False
        for x in a.at.split(","):
            sc.frame_set(int(round(float(x) * FPS)))
            sc.render.filepath = os.path.join(out, f"t{float(x):06.2f}.png")
            bpy.ops.render.render(write_still=True)
        return
    os.makedirs(a.out, exist_ok=True)
    # text-card frames are drawn in post: pre-fill them so the renderer skips them
    from PIL import Image
    blank = Image.new("RGB", (8, 8))
    for t0, t1 in [(0.0, 4.0)] + [(c[0] - 0.15, c[1] + 0.1) for c in CARDS]:
        for f in range(int(t0 * FPS), int(t1 * FPS)):
            p = os.path.join(a.out, f"f_{f:05d}.png")
            if not os.path.exists(p):
                blank.save(p)
    sc.frame_start, sc.frame_end = a.frames[0], a.frames[1] - 1
    sc.render.filepath = os.path.join(a.out, "f_#####")
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
