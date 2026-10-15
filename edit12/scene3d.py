#!/usr/bin/env python3
"""Photoreal ESP32 + OLED parking sensor (Blender, procedural, units = cm). Re-uses the ESP32 + 1.3"
OLED breadboard from edit10 (same channel look); adds an HC-SR04 on a small stand at the head of a
painted parking bay, a green / yellow / red LED 'traffic light' + buzzer board, and a red toy car that
reverses into the bay (reverse lights on) following timeline.dist(), then drives away.
The OLED shows the parking display from edit12/make_screens.py. 24 fps, 468 frames.
Run: python3 edit12/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, BOOT, dist, zone, reversing  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
SENSOR = Vector((0, -4.6, 2.4))                # HC-SR04 board centre (faces -y, down the bay)
FACE_Y = SENSOR.y - 1.35                       # front of the transducer cans
CAR_L, CAR_W = 10.0, 4.6
LEDB = Vector((-9.0, -8.0, 0))                 # LED + buzzer mini breadboard
R90 = (math.radians(90), 0, 0)


def car_y(f):
    """Car centre y: rear bumper sits dist(f) cm in front of the sensor."""
    return FACE_Y - dist(f) - CAR_L / 2


def emit_mat(name, col, strength):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = 0.15
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = strength
        return p
    return k.node_mat(name, b)


def build_sensor():
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    gold = bpy.data.materials["gold"]
    k.box("hc_stand", (3.2, 1.6, 0.4), Vector((SENSOR.x, SENSOR.y + 0.6, 0.2)), blk)
    k.box("hc_stand_up", (0.5, 0.5, 1.4), Vector((SENSOR.x, SENSOR.y + 0.45, 1.0)), blk)
    k.box("hc_pcb", (4.5, 0.15, 2.0), SENSOR, k.pbr("hc_m", (0.05, 0.25, 0.65), 0.4))
    k.text("hc_lbl", "HC-SR04", 0.32, SENSOR + Vector((0, -0.09, -0.75)), [k.emit("hc_t", (0.9, 0.92, 0.95), 1.0)], extrude=0.0)
    for sx in (-1.3, 1.3):
        k.cyl("hc_can", 0.8, 1.2, SENSOR + Vector((sx, -0.65, 0.15)), steel, rot=R90, verts=40)
        k.cyl("hc_mesh", 0.68, 0.05, SENSOR + Vector((sx, -1.27, 0.15)), k.pbr("mesh", (0.03, 0.03, 0.03), 0.8), rot=R90, verts=40)
    k.box("hc_xtal", (0.6, 0.25, 0.3), SENSOR + Vector((0, -0.15, 0.55)), steel)
    for i, col in enumerate(((0.85, 0.1, 0.05), (1.0, 0.8, 0.05), (0.1, 0.6, 0.2), (0.04, 0.04, 0.04))):
        x = -0.38 + i * 0.254
        k.box("hc_pin", (0.064, 0.064, 0.6), SENSOR + Vector((x, 0, 1.25)), gold)
        a = SENSOR + Vector((x, 0.05, 1.5))
        e = Vector((b10.E.x + 1.0 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_hc{i}", b10.bez(a, a + Vector((0, 0.4, 1.4)), e + Vector((0, -0.8, 1.4)), e), col, r=0.05)


def build_bay():
    paint = k.pbr("paint", (0.95, 0.95, 0.9), rough=0.6)
    yel = k.pbr("paint_y", (1.0, 0.78, 0.05), rough=0.6)
    for sx in (-1, 1):
        b10.plane("bay_line", (0.5, 36.0), Vector((sx * 4.1, FACE_Y - 18.5, 0.012)), paint)
    b10.plane("bay_stop", (8.7, 0.5), Vector((0, FACE_Y - 1.0, 0.012)), yel)
    for i in range(6):                                          # hatch at the wall end
        b10.plane("hatch", (0.35, 2.2), Vector((-3.2 + i * 1.3, FACE_Y - 2.6, 0.013)), yel, rot=(0, 0, math.radians(35)))
    k.text("bay_txt", "P", 2.4, Vector((0, FACE_Y - 26, 0.02)), [k.pbr("ptxt", (0.95, 0.95, 0.9), 0.6)], extrude=0.0, rot=(0, 0, 0))


def build_leds():
    k.box("mini_bb", (5.6, 3.4, 0.9), LEDB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (5.6, 3.4), LEDB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    specs = (("led_g", -2.0, (0.1, 1.0, 0.2), lambda f: f >= BOOT and zone(f) == "SAFE"),
             ("led_y", -1.0, (1.0, 0.7, 0.03), lambda f: zone(f) == "SLOW"),
             ("led_r", 0.0, (1.0, 0.06, 0.03), lambda f: zone(f) == "STOP" and (f // 3) % 2 == 0))
    tops = []
    for name, x, col, states in specs:
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.inputs["Base Color"].default_value = (*[0.08 + 0.8 * c for c in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.6
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(name, b)
        c = LEDB + Vector((x, 0.3, 0.9))
        k.cyl(name + "_body", 0.25, 0.45, c + Vector((0, 0, 0.85)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=c + Vector((0, 0, 1.08)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        k.cyl(name + "_rim", 0.29, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), bpy.data.materials["steel"])
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.6)))
        g = bpy.context.object
        g.data.color = col
        g.data.shadow_soft_size = 0.2
        b10.key_bool(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value", states, 4.0)
        b10.key_bool(g.data, "energy", states, 3.0)
        tops.append(c)
    k.cyl("buzzer", 0.62, 0.95, LEDB + Vector((1.6, 0.2, 1.38)), bpy.data.materials["esp_blk"], verts=40)
    k.cyl("buzzer_hole", 0.12, 0.03, LEDB + Vector((1.6, 0.2, 1.86)), k.pbr("hole", (0, 0, 0), 0.9), verts=16)
    tops.append(LEDB + Vector((1.6, 0.9, 0.9)))
    cols = ((0.1, 0.7, 0.2), (1.0, 0.75, 0.05), (0.85, 0.1, 0.05), (0.95, 0.95, 0.95))
    for i, (c, col) in enumerate(zip(tops, cols)):
        a = c + Vector((0, 1.0, 0))
        e = Vector((b10.E.x - 1.6 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_al{i}", b10.bez(a, a + Vector((0, 0.6, 1.6)), e + Vector((0, -1.2, 1.6)), e), col, r=0.05)


def build_car():
    before = set(bpy.data.objects)

    def paint(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.75, 0.04, 0.03, 1)
        p.inputs["Metallic"].default_value = 0.35
        p.inputs["Roughness"].default_value = 0.28
        p.inputs["Coat Weight"].default_value = 1.0
        p.inputs["Coat Roughness"].default_value = 0.05
        return p
    body = k.node_mat("car_paint", paint)
    glass = k.pbr("car_glass", (0.02, 0.025, 0.035), rough=0.05, metal=0.2)
    tyre = k.pbr("tyre", (0.02, 0.02, 0.022), rough=0.8)
    rim = k.pbr("rim", (0.8, 0.8, 0.82), rough=0.2, metal=1.0)
    c = Vector((0, 0, 0))
    k.box("car_body", (CAR_W, CAR_L, 1.7), c + Vector((0, 0, 1.45)), body)
    k.box("car_cabin", (CAR_W - 0.7, CAR_L * 0.5, 1.4), c + Vector((0, 0.3, 2.85)), body)
    k.box("car_win_f", (CAR_W - 0.9, 0.08, 1.05), c + Vector((0, -CAR_L * 0.25 + 0.27, 2.85)), glass)
    k.box("car_win_r", (CAR_W - 0.9, 0.08, 1.05), c + Vector((0, CAR_L * 0.25 + 0.33, 2.85)), glass)
    for sx in (-1, 1):
        k.box("car_win_s", (0.08, CAR_L * 0.42, 1.0), c + Vector((sx * (CAR_W / 2 - 0.33), 0.3, 2.85)), glass)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = c + Vector((sx * (CAR_W / 2 - 0.15), sy * 3.1, 0.95))
            k.cyl("tyre", 0.95, 0.7, p, tyre, rot=(0, math.radians(90), 0), verts=40)
            k.cyl("rim", 0.55, 0.74, p, rim, rot=(0, math.radians(90), 0), verts=24)
    head = emit_mat("headlight", (1.0, 0.95, 0.8), 6.0)
    tail = emit_mat("taillight", (1.0, 0.05, 0.03), 4.0)
    for sx in (-1, 1):
        k.box("car_head", (0.9, 0.12, 0.4), c + Vector((sx * 1.5, -CAR_L / 2 - 0.02, 1.7)), head)
        k.box("car_tail", (0.9, 0.12, 0.4), c + Vector((sx * 1.5, CAR_L / 2 + 0.02, 1.7)), tail)
    rev = emit_mat("reverse_light", (1.0, 1.0, 1.0), 0.0)
    for sx in (-1, 1):
        k.box("car_rev", (0.35, 0.12, 0.3), c + Vector((sx * 0.75, CAR_L / 2 + 0.02, 1.7)), rev)
    k.box("plate", (1.8, 0.06, 0.5), c + Vector((0, CAR_L / 2 + 0.04, 1.15)), k.pbr("plate_m", (0.95, 0.95, 0.9), 0.4))
    k.text("plate_t", "ESP 32", 0.32, c + Vector((0, CAR_L / 2 + 0.08, 1.15)), [k.pbr("plate_t_m", (0.05, 0.05, 0.05), 0.5)],
           extrude=0.0, rot=(math.radians(90), 0, math.radians(180)))
    k.box("bumper_r", (CAR_W, 0.35, 0.45), c + Vector((0, CAR_L / 2 + 0.05, 0.75)), k.pbr("bumper", (0.05, 0.05, 0.06), 0.5))
    k.box("bumper_f", (CAR_W, 0.35, 0.45), c + Vector((0, -CAR_L / 2 - 0.05, 0.75)), bpy.data.materials["bumper"])
    parts = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("car_root", None)
    bpy.context.collection.objects.link(root)
    for o in parts:
        o.parent = root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        root.location = (0, car_y(max(f, 0)), 0)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    b10.key_bool(rev.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value", reversing, 8.0)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -55, 70), (0, -12, 1), 75000, 35)
    k.area("fill", (45, -45, 40), (0, -12, 1), 24000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (0, 0, 2), 25000, 25, col=(0.7, 0.4, 1.0))
    b10.build_board()
    build_sensor()
    build_bay()
    build_leds()
    build_car()

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        c.data.clip_start = 0.1
        c.data.clip_end = 2000
        fo = bpy.data.objects.new(name + "_f", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    Sh = SHOTS
    scr = b10.M + Vector((0, -0.25, 0.23))
    mid = Vector((0, -20, 1.0))
    cams = [
        cam("s0", [(Sh[0], Vector((-13, -36, 8)), Vector((0, -11, 2))), (Sh[1], Vector((-11, -33, 7.5)), Vector((0, -10, 2)))], 35, Vector((0, -10, 2)), 5.6),
        cam("s1", [(Sh[1], Vector((0, -38, 50)), Vector((0, -21, 0))), (Sh[2], Vector((0, -36, 46)), Vector((0, -21, 0)))], 30, mid, 8.0),
        cam("s2", [(Sh[2], SENSOR + Vector((7, -13, 4)), SENSOR), (Sh[3], SENSOR + Vector((-5, -14, 4)), SENSOR)], 40, SENSOR, 2.8),
        cam("s3", [(Sh[3], Vector((12, -50, 30)), Vector((0, -21, 1.0))), (Sh[4], Vector((9, -44, 26)), Vector((0, -15, 1.0)))], 32, Vector((0, -14, 1.5)), 8.0),
        cam("s4", [(Sh[4], scr + Vector((0.0, -5.6, 5.8)), scr), (Sh[5], scr + Vector((0.4, -5.0, 5.2)), scr)], 50, scr, 2.8),
        cam("s5", [(Sh[5], Vector((-13, -52, 28)), mid), (Sh[6], Vector((-9, -54, 30)), mid)], 32, mid, 8.0),
        cam("s6", [(Sh[6], Vector((0, -50, 32)), mid), (N, Vector((0, -54, 34)), mid)], 32, mid, 8.0),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]

    imgs = {}

    def upd(scene, *_):
        f = scene.frame_current
        if f not in imgs:
            imgs[f] = bpy.data.images.load(os.path.join(OLED, f"{min(max(f, 0), N - 1):04d}.png"), check_existing=True)
        bpy.data.materials["oled_scr"].node_tree.nodes["oled_tex"].image = imgs[f]
    bpy.app.handlers.frame_change_pre.append(upd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=N - 1)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=FRAMES)
    args = ap.parse_args(sys.argv[1:])
    os.makedirs(args.out, exist_ok=True)
    sc = k.reset()
    sc.render.fps = FPS
    build(sc)
    k.setup_render(sc, args.preview)
    sc.render.use_persistent_data = False
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces = 8, 6, 3
    cy.samples = 8 if args.preview else 14
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
