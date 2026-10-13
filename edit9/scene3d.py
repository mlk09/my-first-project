#!/usr/bin/env python3
"""Photoreal ESP32 self-balancing robot (Blender, procedural, units = cm). Clear acrylic
three-deck chassis on brass standoffs, two yellow TT gear motors with white-hub wheels, ESP32-S3
DevKit, MPU6050 on the bottom deck (near the axle), DRV8833 driver, 3.3 V buck converter, 2x18650
pack on top. The body pitches about the axle by timeline.theta(), wheels roll with timeline.y().
PID OFF: it falls over; PID ON: it settles, survives a ball push and drives. 24 fps, 384 frames.
Run: python3 edit9/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit2_scene3d", os.path.join(HERE, "..", "edit2", "scene3d.py"))
k = importlib.util.module_from_spec(_spec)  # edit2 modelling helpers
_spec.loader.exec_module(k)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from timeline import FPS, N, SHOTS, PUSH, WHEEL_R, BALL_R, theta, y, wheel_deg, ball_y, pid_on  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
TEX = os.path.join(HERE, "work", "tex")
R90 = (math.radians(90), 0, 0)
RY90 = (0, math.radians(90), 0)


def wire(name, pts, col, r=0.06, mat=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat or k.pbr(name + "m", col, rough=0.35))
    return o


def tex_mat(name, path, rough=0.5, scale=1.0, bump=0.0):
    def b(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, 1)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path)
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Roughness"].default_value = rough
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
        if bump:
            bm = nt.nodes.new("ShaderNodeBump")
            bm.inputs["Strength"].default_value = bump
            nt.links.new(t.outputs["Color"], bm.inputs["Height"])
            nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
        return p
    return k.node_mat(name, b)


def plane(name, size, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    o.data.materials.append(mat)
    return o


def acrylic():
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.92, 0.97, 1.0, 1)
        p.inputs["Roughness"].default_value = 0.04
        p.inputs["Transmission Weight"].default_value = 0.92
        p.inputs["IOR"].default_value = 1.49
        return p
    return k.node_mat("acrylic", b)


def build_body():
    """Everything that pitches with the chassis, built around the axle at the origin."""
    before = set(bpy.data.objects)
    acr = acrylic()
    brass = k.pbr("brass", (0.85, 0.62, 0.25), rough=0.25, metal=1.0)
    yel = k.pbr("tt_yel", (0.95, 0.72, 0.05), rough=0.45)
    blk = k.pbr("blk", (0.02, 0.02, 0.022), rough=0.4)
    pcb = k.pbr("pcb", (0.015, 0.015, 0.018), rough=0.35)
    steel = k.pbr("steel", (0.8, 0.81, 0.83), rough=0.18, metal=1.0)
    gold = k.pbr("gold", (0.95, 0.72, 0.3), rough=0.25, metal=1.0)
    for sx in (-1, 1):                                       # TT gear motors under the bottom deck
        k.box("tt_motor", (4.6, 2.2, 1.9), Vector((sx * 2.55, 0, 0)), yel)
        k.cyl("tt_can", 1.0, 1.6, Vector((sx * 1.0, 0, -0.1)), k.pbr("can", (0.75, 0.76, 0.78), 0.3, 1.0), rot=RY90)
        k.cyl("tt_shaft", 0.28, 1.4, Vector((sx * 5.2, 0, 0)), k.pbr("shaft", (0.95, 0.95, 0.95), 0.4), rot=RY90, verts=16)
    decks = (1.35, 7.5, 13.6)
    for z in decks:
        k.box("deck", (11.0, 6.2, 0.3), Vector((0, 0, z)), acr)
    for z0, z1 in ((decks[0], decks[1]), (decks[1], decks[2])):
        for sx in (-4.9, 4.9):
            for sy in (-2.6, 2.6):
                k.cyl("standoff", 0.17, z1 - z0, Vector((sx, sy, (z0 + z1) / 2)), brass, verts=6)
    # bottom deck: MPU6050 (close to the axle) + DRV8833
    plane("mpu", (2.1, 1.6), Vector((0, -0.4, decks[0] + 0.32)), tex_mat("mpu_m", os.path.join(TEX, "mpu6050.png"), 0.35))
    k.box("mpu_pcb", (2.1, 1.6, 0.14), Vector((0, -0.4, decks[0] + 0.23)), k.pbr("mpu_edge", (0.08, 0.27, 0.62), 0.4))
    plane("drv", (1.8, 1.4), Vector((-3.3, 0.6, decks[0] + 0.32)), tex_mat("drv_m", os.path.join(TEX, "drv8833.png"), 0.35))
    k.box("drv_pcb", (1.8, 1.4, 0.14), Vector((-3.3, 0.6, decks[0] + 0.23)), k.pbr("drv_edge", (0.4, 0.1, 0.45), 0.4))
    # middle deck: ESP32-S3 DevKitC + buck converter
    ez = decks[1] + 0.35
    k.box("s3_pcb", (6.3, 2.6, 0.16), Vector((-0.6, -0.6, ez)), pcb)
    k.box("s3_mod", (1.8, 2.5, 0.08), Vector((1.4, -0.6, ez + 0.12)), blk)
    k.box("s3_shield", (1.55, 1.8, 0.28), Vector((1.3, -0.6, ez + 0.28)), steel)
    k.text("s3_lbl", "ESP32-S3", 0.32, Vector((1.3, -0.6, ez + 0.43)), [k.pbr("etch", (0.4, 0.41, 0.43), 0.5, 1.0)],
           extrude=0.0, rot=(0, 0, math.radians(90)))
    for sx in (-3.55, -3.55):
        k.box("s3_usbc", (0.75, 0.9, 0.32), Vector((sx, -1.1, ez + 0.2)), steel)
    k.box("s3_usbc2", (0.75, 0.9, 0.32), Vector((-3.55, -0.1, ez + 0.2)), steel)
    for i in range(20):
        for sy in (-1.82, 0.62):
            k.box("s3_pin", (0.07, 0.07, 0.45), Vector((-3.4 + i * 0.254, sy, ez - 0.25)), gold)
    rgb = k.pbr("rgb_led", (0.2, 0.3, 1.0), rough=0.2, em=(0.15, 0.4, 1.0), ems=0.0)
    k.box("s3_rgb", (0.3, 0.3, 0.12), Vector((-2.3, -1.2, ez + 0.14)), rgb)
    rgb_s = rgb.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    k.interp("CONSTANT")
    for f in range(-1, N + 1):
        rgb_s.default_value = (12.0 if (f // 6) % 2 == 0 else 3.0) if pid_on(max(f, 0)) else 0.0
        rgb_s.keyframe_insert("default_value", frame=f)
    k.interp("BEZIER")
    pwr = k.pbr("pwr_led", (0.5, 0.02, 0.02), rough=0.2, em=(1.0, 0.04, 0.02), ems=20.0)
    k.box("s3_pwr", (0.2, 0.15, 0.1), Vector((-2.8, -1.25, ez + 0.13)), pwr)
    plane("buck", (2.2, 1.7), Vector((-2.4, 2.0, decks[1] + 0.32)), tex_mat("buck_m", os.path.join(TEX, "buck.png"), 0.35))
    k.box("buck_pcb", (2.2, 1.7, 0.14), Vector((-2.4, 2.0, decks[1] + 0.23)), k.pbr("buck_edge", (0.1, 0.35, 0.75), 0.4))
    k.box("buck_coil", (0.7, 0.7, 0.45), Vector((-2.9, 2.0, decks[1] + 0.55)), blk)
    # top deck: 2x18650 holder + cells + switch
    tz = decks[2] + 0.15
    k.box("bat_holder", (7.6, 4.2, 1.1), Vector((0, 0, tz + 0.55)), blk)
    for sy in (-1.0, 1.0):
        k.cyl("cell", 0.9, 6.6, Vector((0, sy, tz + 1.15)), k.pbr(f"cell{sy}", (0.1, 0.45, 0.85) if sy < 0 else (0.85, 0.15, 0.1), 0.3),
              rot=RY90, verts=32)
    k.box("switch", (1.0, 0.6, 0.6), Vector((4.6, -1.8, tz + 0.3)), blk)
    k.box("switch_rk", (0.4, 0.3, 0.3), Vector((4.6, -1.8, tz + 0.7)), k.pbr("rk", (0.85, 0.1, 0.08), 0.4))
    # wiring
    wire("w_bat_r", [Vector((-3.8, 1.8, tz + 0.6)), Vector((-5.2, 2.4, 11)), Vector((-3.3, 2.4, decks[1] + 0.5))], (0.85, 0.1, 0.05))
    wire("w_bat_k", [Vector((-3.8, 1.2, tz + 0.6)), Vector((-5.4, 1.6, 11)), Vector((-2.0, 2.2, decks[1] + 0.5))], (0.04, 0.04, 0.04))
    cols = [(0.95, 0.15, 0.1), (0.04, 0.04, 0.04), (1.0, 0.85, 0.05), (0.15, 0.35, 0.95)]
    for i, c in enumerate(cols):                              # MPU6050 I2C up to the S3
        wire(f"w_i2c{i}", [Vector((-0.6 + i * 0.4, -1.1, decks[0] + 0.4)), Vector((-1.5 + i * 0.4, -3.0, 4.5)),
                           Vector((-2.5 + i * 0.5, -1.9, ez - 0.4))], c, r=0.05)
    for i, c in enumerate([(1.0, 0.5, 0.05), (0.1, 0.7, 0.2), (0.6, 0.2, 0.75), (0.95, 0.95, 0.95)]):   # driver inputs
        wire(f"w_drv{i}", [Vector((-3.9 + i * 0.35, 1.3, decks[0] + 0.4)), Vector((-4.6 + i * 0.3, 3.1, 4.5)),
                           Vector((-0.4 + i * 0.5, 0.7, ez - 0.4))], c, r=0.05)
    for sx in (-1, 1):                                        # motor leads
        wire(f"w_mot{sx}", [Vector((sx * 0.3, 0.9, 0.6)), Vector((sx * 1.5, 1.6, 1.0)), Vector((-3.0 + sx * 0.4, 1.2, decks[0] + 0.4))],
             (0.85, 0.1, 0.05), r=0.05)
    return [o for o in bpy.data.objects if o not in before and o.parent is None]


def build_wheel(sx):
    before = set(bpy.data.objects)
    tire = k.pbr("tire", (0.02, 0.02, 0.022), rough=0.8)
    hub = k.pbr("hub", (0.93, 0.93, 0.9), rough=0.35)
    bpy.ops.mesh.primitive_torus_add(major_radius=WHEEL_R - 0.55, minor_radius=0.6, location=(0, 0, 0), rotation=RY90,
                                     major_segments=64, minor_segments=16)
    t = bpy.context.object
    t.scale = (1.0, 1.0, 1.0)
    bpy.ops.object.shade_smooth()
    t.data.materials.append(tire)
    k.cyl("tire_core", WHEEL_R - 0.3, 2.4, Vector((0, 0, 0)), tire, rot=RY90, verts=64)
    k.cyl("hub", WHEEL_R - 0.9, 2.5, Vector((0, 0, 0)), hub, rot=RY90, verts=48)
    for i in range(6):                                        # spoke holes
        a = i * math.pi / 3
        k.cyl("hole", 0.38, 2.6, Vector((0, 1.3 * math.cos(a), 1.3 * math.sin(a))), k.pbr("holeb", (0.05, 0.05, 0.05), 0.6), rot=RY90, verts=16)
    k.cyl("cap", 0.45, 2.7, Vector((0, 0, 0)), k.pbr("capm", (0.15, 0.15, 0.16), 0.4), rot=RY90, verts=24)
    parts = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(f"wheel{sx}", None)
    bpy.context.collection.objects.link(root)
    for o in parts:
        o.parent = root
    return root


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    plane("mat", (300, 300), Vector((0, 0, 0)), tex_mat("mat_m", os.path.join(TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    plane("wall", (600, 300), Vector((0, 120, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.text("sign", "ROBO LAB", 16, Vector((-10, 115, 70)), [k.emit("neon", (1.0, 0.25, 0.8), 1.4)], extrude=0.5)
    k.text("sign2", "PID", 10, Vector((55, 115, 45)), [k.emit("neon2", (0.2, 0.9, 1.0), 1.4)], extrude=0.5)
    k.area("key", (-40, -50, 90), (0, 0, 8), 110000, 45)
    k.area("fill", (60, -40, 50), (0, 0, 8), 35000, 50, col=(0.85, 0.9, 1.0))
    k.area("rim", (-50, 60, 40), (0, 0, 10), 45000, 30, col=(0.7, 0.4, 1.0))
    plane("wall_l", (600, 300), Vector((-150, 0, 60)), bpy.data.materials["wall_m"], rot=(math.radians(90), 0, math.radians(90)))

    body_parts = build_body()
    body = bpy.data.objects.new("body_root", None)
    bpy.context.collection.objects.link(body)
    for o in body_parts:
        o.parent = body
    wheels = []
    for sx in (-1, 1):
        wr = build_wheel(sx)
        wheels.append((sx, wr))
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        ff = max(f, 0)
        yy = y(ff)
        body.location = (0, yy, WHEEL_R)
        body.rotation_euler = (math.radians(-theta(ff)), 0, 0)
        body.keyframe_insert("location", frame=f)
        body.keyframe_insert("rotation_euler", frame=f)
        for sx, wr in wheels:
            wr.location = (sx * 6.45, yy, WHEEL_R)
            wr.rotation_euler = (math.radians(-wheel_deg(ff)), 0, 0)
            wr.keyframe_insert("location", frame=f)
            wr.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    # rubber ball for the push test
    bpy.ops.mesh.primitive_uv_sphere_add(radius=BALL_R, location=(0, 0, BALL_R), segments=48, ring_count=24)
    ball = bpy.context.object
    bpy.ops.object.shade_smooth()
    ball.data.materials.append(k.pbr("ball_m", (1.0, 0.3, 0.05), rough=0.5))
    k.interp("LINEAR")
    for f in range(SHOTS[3] - 2, SHOTS[4] + 2):
        by = ball_y(f)
        ball.location = (0.4, by, BALL_R)
        ball.rotation_euler = (by / BALL_R, 0, 0)
        ball.keyframe_insert("location", frame=f)
        ball.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    k.show(ball, [(SHOTS[3], SHOTS[4])])

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        c.data.clip_start = 0.5
        c.data.clip_end = 2000
        fo = bpy.data.objects.new(name + "_f", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    Sh = SHOTS
    tgt = Vector((0, 1.5, 8.0))
    cams = [
        cam("s0", [(Sh[0], Vector((-31, -25, 17)), Vector((0, 3, 6))), (Sh[1], Vector((-27, -23, 15)), Vector((0, 3, 6)))], 40, Vector((0, 2, 6)), 4.0),
        cam("s1", [(Sh[1], Vector((26, -40, 17)), tgt), (Sh[2], Vector((20, -35, 15)), tgt)], 40, Vector((0, 0, 8)), 4.0),
        cam("s2", [(Sh[2], Vector((-15, -24, 17)), Vector((0, 0, 7.0))), (Sh[3], Vector((-5, -26, 14)), Vector((0, 0, 7.0)))], 40, Vector((0, -0.6, 8)), 2.8),
        cam("s3", [(Sh[3], Vector((58, -8, 12)), Vector((0, -5, 7))), (Sh[4], Vector((54, -5, 12)), Vector((0, -3, 7)))], 36, Vector((0, -2, 7)), 5.6),
        cam("s4", [(Sh[4], Vector((-24, -34, 24)), tgt), (Sh[5], Vector((-6, -40, 22)), tgt)], 36, Vector((0, 0, 8)), 4.0),
        cam("s5", [(Sh[5], Vector((7, -42, 6)), Vector((0, 6, 8))), (Sh[6], Vector((4, -40, 6.5)), Vector((0, 6, 8)))], 32, Vector((0, 4, 8)), 4.0),
        cam("s6", [(Sh[6], Vector((-18, -36, 16)), tgt), (N, Vector((-22, -44, 18)), tgt)], 36, Vector((0, 0, 8)), 4.0),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]


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
    sc.render.use_persistent_data = False   # persistent data intermittently mis-rendered materials in edit6/edit8
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces = 8, 6, 3
    cy.samples = 8 if args.preview else 14
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
