#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + joystick 4-servo robot arm (Blender, procedural, units = cm). Re-uses the
ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds a purple acrylic arm with blue
MG90S servos (base / shoulder / elbow / gripper driven by timeline.ik()), a red cube it picks up and a
yellow DROP cup, a KY-023 joystick that tilts with the motion (timeline.joystick()) and a red / green
LED pair + buzzer. 24 fps, 468 frames.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, L1, L2, HS, CUBE, CUP, CUP_TOP, ik, cube, joystick, holding, status, busy  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
TEX17 = os.path.join(HERE, "work", "tex")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
A = Vector((-1.0, 9.5, 0))                     # robot-arm base
RY = (0, math.radians(90), 0)
MB = Vector((1.0, -6.4, 0))                    # mini breadboard (knob + LEDs)
ENC = MB + Vector((-2.2, 0, 0.9))
KNOB = ENC + Vector((0, 0, 2.3))
R90 = (math.radians(90), 0, 0)


def arm_dir(yaw):
    y = math.radians(yaw)
    return Vector((math.sin(y), -math.cos(y), 0))


def at(yaw, r, z):
    return A + arm_dir(yaw) * r + Vector((0, 0, z))


def frames(f):
    """World (location, euler) of the turret, shoulder, elbow and wrist frames at frame f."""
    yaw, a1, a2, wr, grip = ik(f)
    y = math.radians(yaw)
    e1, e2, e3 = math.radians(a1), math.radians(a1 + a2), math.radians(a1 + a2 + wr)
    sh = A + Vector((0, 0, HS))
    el = sh + arm_dir(yaw) * (L1 * math.cos(e1)) + Vector((0, 0, L1 * math.sin(e1)))
    wr_ = el + arm_dir(yaw) * (L2 * math.cos(e2)) + Vector((0, 0, L2 * math.sin(e2)))
    return [(A, (0, 0, y)), (sh, (-e1, 0, y)), (el, (-e2, 0, y)), (wr_, (-e3, 0, y))], grip


def build_arm():
    purple = k.pbr("arm_acr", (0.22, 0.1, 0.85), 0.2)
    blue = k.pbr("servo_blue", (0.0, 0.07, 0.55), 0.3)
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    k.cyl("arm_foot", 2.0, 0.5, A + Vector((0, 0, 0.25)), blk, verts=48)
    k.box("arm_base_servo", (2.2, 1.2, 1.1), A + Vector((0, 0, 0.95)), blue)
    empties = []
    for name in ("turret", "shoulder", "elbow", "wrist"):
        e = bpy.data.objects.new(name, None)
        bpy.context.collection.objects.link(e)
        empties.append(e)

    def under(parent, build):
        before = set(bpy.data.objects)
        build()
        for o in [o for o in bpy.data.objects if o not in before]:
            o.parent = parent

    def turret():
        k.cyl("tur_disk", 1.5, 0.3, Vector((0, 0, 1.65)), purple, verts=48)
        for sx in (-0.75, 0.75):
            k.box("tur_cheek", (0.2, 1.4, 1.5), Vector((sx, 0, 2.45)), purple)
        k.box("sh_servo", (0.9, 1.2, 1.0), Vector((-0.3, 0, 2.55)), blue)
        k.text("sg_lbl", "MG90S", 0.2, Vector((-0.76, 0, 2.55)), [k.emit("sg_t", (0.9, 0.9, 0.95), 0.9)], extrude=0.0,
               rot=(math.radians(90), 0, math.radians(-90)))

    def link(L, w=0.75):
        def b():
            k.box("link_l", (0.12, L + 0.6, w), Vector((-0.45, -L / 2, 0)), purple)
            k.box("link_r", (0.12, L + 0.6, w), Vector((0.45, -L / 2, 0)), purple)
            k.cyl("hub", 0.35, 1.1, Vector((0, 0, 0)), steel, rot=RY, verts=24)
            k.box("el_servo", (0.7, 1.1, 0.9), Vector((0, -L, 0)), blue)
        return b

    def gripper():
        k.box("palm", (2.2, 0.35, 0.8), Vector((0, -0.65, 0)), purple)
        k.box("gr_servo", (0.8, 0.9, 0.7), Vector((0, -0.2, 0.55)), blue)
    under(empties[0], turret)
    under(empties[1], link(L1))
    under(empties[2], link(L2, 0.65))
    under(empties[3], gripper)
    fingers = []
    for side in (-1, 1):
        fe = bpy.data.objects.new("finger", None)
        bpy.context.collection.objects.link(fe)
        fe.parent = empties[3]
        b0 = set(bpy.data.objects)
        k.box("finger_m", (0.18, 1.1, 0.7), Vector((0, -1.35, 0)), purple)
        k.box("finger_pad", (0.06, 0.6, 0.55), Vector((-side * 0.1, -1.55, 0)), k.pbr("pad_m", (0.05, 0.05, 0.05), 0.9))
        for o in [o for o in bpy.data.objects if o not in b0]:
            o.parent = fe
        fingers.append((side, fe))
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        fr, grip = frames(max(f, 0))
        for e, (loc, rot) in zip(empties, fr):
            e.location = loc
            e.rotation_euler = rot
            e.keyframe_insert("location", frame=f)
            e.keyframe_insert("rotation_euler", frame=f)
        for side, fe in fingers:
            fe.location = (side * (1.0 - 0.38 * grip), 0, 0)
            fe.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    for i, col in enumerate(((0.95, 0.5, 0.05), (0.85, 0.1, 0.05), (0.45, 0.25, 0.1), (1.0, 0.8, 0.05))):
        a = A + Vector((-1.1 + 0.15 * i, -0.4, 0.6))
        e = Vector((b10.E.x - 0.7 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_arm{i}", b10.bez(a, a + Vector((-0.6, -1.0, 0.8)), e + Vector((0, 0.8, 1.8)), e), col, r=0.05)


def build_props():
    import bmesh
    o = k.box("cube", (1.0, 1.0, 1.0), Vector((0, 0, 0)), k.pbr("cube_m", (0.9, 0.08, 0.05), 0.35))
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        yaw, r, z = cube(max(f, 0))
        o.location = at(yaw, r, z)
        o.rotation_euler = (0, 0, math.radians(yaw))
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    cp = at(CUP[0], CUP[1], 0)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.25, depth=CUP_TOP, location=cp + Vector((0, 0, CUP_TOP / 2)), vertices=64)
    m = bpy.context.object
    m.name = "cup"
    bm = bmesh.new()
    bm.from_mesh(m.data)
    bmesh.ops.delete(bm, geom=[f_ for f_ in bm.faces if f_.normal.z > 0.9], context="FACES")
    bm.to_mesh(m.data)
    bm.free()
    m.modifiers.new("sol", "SOLIDIFY").thickness = 0.12
    bpy.ops.object.shade_smooth()
    m.data.materials.append(k.pbr("cup_m", (1.0, 0.75, 0.05), 0.3))
    k.text("cup_lbl", "DROP", 0.32, cp + Vector((0, -1.3, 0.75)), [k.emit("cup_t", (0.1, 0.1, 0.12), 1.0)], extrude=0.0)
    k.cyl("spot", 0.85, 0.02, at(CUBE[0], CUBE[1], 0.01), k.pbr("spot_m", (0.95, 0.95, 0.95), 0.6), verts=48)


def build_controls():
    k.box("mini_bb", (8.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (8.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    k.box("joy_pcb", (2.6, 3.4, 0.12), ENC + Vector((0, 0, 0.5)), k.pbr("joy_pcb_m", (0.02, 0.02, 0.025), 0.4))
    k.box("joy_gimbal", (1.7, 1.7, 0.9), ENC + Vector((0, -0.2, 1.0)), k.pbr("joy_gim", (0.12, 0.12, 0.13), 0.5))
    k.cyl("joy_dome", 0.75, 0.25, ENC + Vector((0, -0.2, 1.55)), k.pbr("joy_dome_m", (0.15, 0.15, 0.16), 0.4), verts=32)
    root = bpy.data.objects.new("knob_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)
    k.cyl("stick", 0.13, 1.1, Vector((0, 0, 0.55)), steel, verts=16)
    k.cyl("joy_cap", 0.85, 0.7, Vector((0, 0, 1.3)), k.pbr("knob_m", (0.04, 0.04, 0.045), 0.45), verts=48)
    for j in range(24):
        a_ = j * 2 * math.pi / 24
        k.box("rib", (0.08, 0.12, 0.6), Vector((0.86 * math.cos(a_), 0.86 * math.sin(a_), 1.3)), blk, rot=(0, 0, a_))
    k.cyl("joy_top", 0.7, 0.05, Vector((0, 0, 1.66)), k.pbr("cap_m", (0.75, 0.76, 0.78), 0.25, 1.0), verts=48)
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        jx, jy, pr = joystick(max(f, 0))
        root.rotation_euler = (math.radians(-20 * jy), math.radians(20 * jx), 0)
        root.location = ENC + Vector((0, -0.2, 1.55 - (0.15 if pr else 0.0)))
        root.keyframe_insert("rotation_euler", frame=f)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    for name, x, col in (("led_r", 0.6, (1.0, 0.06, 0.03)), ("led_g", 1.6, (0.1, 1.0, 0.2))):
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.name = "P"
            p.inputs["Base Color"].default_value = (*[0.02 + 0.2 * c for c in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.35
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(name, b)
        c = MB + Vector((x, 0.3, 0.9))
        k.cyl(name + "_rim", 0.33, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        k.cyl(name + "_body", 0.29, 0.5, c + Vector((0, 0, 0.88)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.29, location=c + Vector((0, 0, 1.13)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), steel)
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.7)))
        g = bpy.context.object
        g.name = name + "_glow"
        g.data.color = col
        g.data.shadow_soft_size = 0.2
        g.data.energy = 0.0
    k.cyl("buzzer", 0.62, 0.95, MB + Vector((3.0, 0.2, 1.38)), blk, verts=40)
    k.cyl("buzzer_hole", 0.12, 0.03, MB + Vector((3.0, 0.2, 1.86)), k.pbr("hole", (0, 0, 0), 0.9), verts=16)
    ends = [(ENC + Vector((-0.4, 1.4, 0)), (1.0, 0.8, 0.05)), (ENC + Vector((0, 1.4, 0)), (0.1, 0.35, 0.95)),
            (ENC + Vector((0.4, 1.4, 0)), (0.95, 0.95, 0.95)), (MB + Vector((0.6, 1.3, 0.9)), (0.85, 0.1, 0.05)),
            (MB + Vector((1.6, 1.3, 0.9)), (0.1, 0.7, 0.2)), (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
    for i, (a, col) in enumerate(ends):
        e = Vector((b10.E.x - 1.4 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.6, 1.6)), e + Vector((0, -1.2, 1.6)), e), col, r=0.05)


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -45, 70), (3, -2, 2), 60000, 35)
    k.area("fill", (45, -35, 40), (3, -2, 2), 20000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (3, 0, 3), 25000, 25, col=(0.7, 0.4, 1.0))
    b10.build_board()
    bpy.data.materials["blue_led"].node_tree.animation_data_clear()   # busy LED is set per frame in upd
    build_arm()
    build_controls()
    build_props()

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
    mid = Vector((3.0, -2.0, 1.8))
    mid1 = Vector((0.8, -1.4, 1.8))
    son = A + Vector((0.6, -2.5, 3.2))                # arm base + servos
    game = Vector((0.4, 2.6, 2.6))                    # arm + cube + cup + board
    grab = at(CUBE[0], CUBE[1], 1.6)
    cupc = at(CUP[0], CUP[1], 2.2)
    kn = Vector((0.6, -3.6, 1.6))                     # knob + OLED
    cams = [
        cam("s0", [(Sh[0], Vector((-1.0, -9, 15)), A + Vector((-1.5, -3.0, 3.0))),
                   (Sh[1], Vector((1.0, -8, 14)), A + Vector((0.5, -3.0, 3.5)))], 30, A + Vector((-1.0, -3.0, 3.0)), 5.6),
        cam("s1", [(Sh[1], Vector((0.4, -13, 27)), game + Vector((0, -1.5, 0))), (Sh[2], Vector((0.4, -12, 25)), game + Vector((0, -1.5, 0)))], 32, game, 8.0),
        cam("s2", [(Sh[2], son + Vector((4.0, -12.0, 9.5)), son), (Sh[3], son + Vector((2.5, -11.0, 9.0)), son)], 34, son, 4.0),
        cam("s3", [(Sh[3], grab + Vector((5.0, -12.0, 13.0)), grab + Vector((2.6, 1.0, 0.8))), (Sh[4], grab + Vector((4.0, -10.5, 12.0)), grab + Vector((2.6, 1.0, 0.8)))], 34, grab, 4.0),
        cam("s4", [(Sh[4], Vector((0.0, -15, 18)), game), (Sh[5], Vector((1.5, -13.5, 16.5)), game)], 32, game, 5.6),
        cam("s5", [(Sh[5], cupc + Vector((-4.0, -12.0, 10.0)), cupc), (Sh[6], cupc + Vector((-3.0, -11.0, 9.5)), cupc)], 34, cupc, 4.0),
        cam("s6", [(Sh[6], Vector((-3, -20, 25)), game), (N, Vector((-4, -22, 26)), game)], 34, game, 5.6),
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
        ff = min(max(f, 0), N - 1)                         # per frame (keyframes interpolate in Blender 5)
        st = status(ff)
        for name, on in (("led_r", st in ("GRAB!", "DROP!") and (ff // 3) % 2 == 0), ("led_g", holding(ff))):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
        bl = bpy.data.materials["blue_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        bl.default_value = 22.0 if busy(ff) else 0.0
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
