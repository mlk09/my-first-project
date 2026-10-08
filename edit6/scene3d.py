#!/usr/bin/env python3
"""Photoreal Smart Plant IoT scene (Blender, procedural): white desk, potted plant with an LDR
module in the soil, Arduino UNO R4 WiFi with an animated 12x8 LED matrix, SG90 servo whose horn
follows the phone slider, red grow LED, rainbow jumpers, phone on a stand with a live dashboard,
a hand-shadow sweep over the plant and a dusk light change. 24 fps, 384 frames.
Run: python3 edit6/scene3d.py [--preview] [--start N --end M --step S]
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit2_scene3d", os.path.join(HERE, "..", "edit2", "scene3d.py"))
k = importlib.util.module_from_spec(_spec)  # edit2 modelling helpers
_spec.loader.exec_module(k)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from timeline import FPS, N, SHOTS, SHADOW, LED_ON, night, servo_deg  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
DASH = os.path.join(HERE, "work", "dash")
P = Vector((1.2, 0.9, 0))      # plant pot
U = Vector((-0.9, -0.5, 0))    # UNO R4
S = Vector((0.9, -1.4, 0))     # servo
F = Vector((-1.6, 1.3, 0))     # phone stand


def wire(name, pts, col, r=0.022):
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
    o.data.materials.append(k.pbr(name + "m", col, rough=0.35))
    return o


def leaf_mat():
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.03, 0.16, 0.025, 1)
        p.inputs["Roughness"].default_value = 0.32
        p.inputs["Subsurface Weight"].default_value = 0.15
        p.inputs["Subsurface Radius"].default_value = (0.2, 0.6, 0.1)
        return p
    return k.node_mat("leaf", b)


def build_plant():
    pot = k.pbr("pot", (0.92, 0.92, 0.9), rough=0.3)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.55, radius2=0.72, depth=1.1, location=P + Vector((0, 0, 0.55)))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(pot)
    k.cyl("soil", 0.66, 0.04, P + Vector((0, 0, 1.06)), k.pbr("soil_m", (0.09, 0.06, 0.04), rough=0.95), verts=64)
    rnd = random.Random(3)
    lm = leaf_mat()
    stem_m = k.pbr("stem", (0.12, 0.28, 0.08), rough=0.6)
    for i in range(9):
        a = i / 9 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        top = P + Vector((math.cos(a) * rnd.uniform(0.3, 0.75), math.sin(a) * rnd.uniform(0.3, 0.75), rnd.uniform(1.7, 2.6)))
        base = P + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 1.05))
        wire(f"stem{i}", [base, (base + top) / 2 + Vector((0, 0, 0.2)), top], (0.12, 0.28, 0.08), r=0.018).data.materials[0] = stem_m
        for j in range(7):
            t = 0.3 + j * 0.11
            pos = base.lerp(top, t) + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=pos)
            lf = bpy.context.object
            lf.scale = (0.3, 0.085, 0.012)
            lf.rotation_euler = (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.5, 0.2), a + rnd.uniform(-0.8, 0.8))
            bpy.ops.object.shade_smooth()
            lf.data.materials.append(lm)
    # LDR module on a stick in the soil
    pcb = k.pbr("ldr_pcb", (0.02, 0.02, 0.025), rough=0.4)
    L = P + Vector((-0.25, -0.35, 0))
    k.box("ldr_stick", (0.08, 0.04, 1.4), L + Vector((0, 0, 1.6)), k.pbr("stick", (0.55, 0.4, 0.25), rough=0.8))
    k.box("ldr_pcb", (0.32, 0.05, 0.5), L + Vector((0, -0.04, 2.35)), pcb)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=L + Vector((0, -0.08, 2.52)))
    ldr = bpy.context.object
    ldr.scale = (1, 0.6, 1)
    ldr.data.materials.append(k.pbr("ldr_cell", (0.75, 0.35, 0.15), rough=0.2))
    k.cyl("ldr_pot", 0.05, 0.04, L + Vector((0, -0.07, 2.3)), k.pbr("trim", (0.1, 0.25, 0.75), 0.4), rot=(math.radians(90), 0, 0))
    return L + Vector((0, -0.1, 2.5))


def build_uno():
    pcb = k.pbr("r4_pcb", (0.02, 0.1, 0.22), rough=0.35)
    blk = k.pbr("hdr", (0.02, 0.02, 0.02), rough=0.45)
    steel = k.pbr("steel", (0.78, 0.79, 0.81), rough=0.2, metal=1.0)
    k.box("r4_board", (2.7, 2.1, 0.06), U + Vector((0, 0, 0.18)), pcb)
    for i in range(4):
        k.cyl("r4_standoff", 0.06, 0.15, U + Vector((-1.2 + (i % 2) * 2.4, -0.9 + (i // 2) * 1.8, 0.075)), steel, verts=12)
    k.box("hdr_top", (2.2, 0.12, 0.3), U + Vector((0.1, 0.95, 0.36)), blk)
    k.box("hdr_bot", (1.8, 0.12, 0.3), U + Vector((0.3, -0.95, 0.36)), blk)
    k.box("usb_c", (0.4, 0.3, 0.14), U + Vector((-1.3, 0.45, 0.28)), steel)
    k.box("jack", (0.5, 0.42, 0.35), U + Vector((-1.25, -0.55, 0.38)), blk)
    k.box("esp_s3", (0.5, 0.42, 0.06), U + Vector((-0.55, 0.3, 0.24)), steel)
    k.box("ra4m1", (0.36, 0.36, 0.05), U + Vector((0.55, -0.45, 0.235)), blk)
    k.text("r4_lbl", "UNO R4 WiFi", 0.12, U + Vector((0.55, -0.15, 0.215)), [k.emit("r4_t", (0.9, 0.9, 0.95), 1.0)], extrude=0.0, rot=(0, 0, 0))
    # 12 x 8 LED matrix, animated per frame
    on = k.emit("mx_on", (1.0, 0.06, 0.03), 1.4)
    off = k.pbr("mx_off", (0.05, 0.02, 0.02), rough=0.3)
    px = {}
    M0 = U + Vector((-0.05, 0.25, 0.22))
    for x in range(12):
        for y in range(8):
            o = k.box(f"mx_{x}_{y}", (0.055, 0.035, 0.025), M0 + Vector((x * 0.075, -y * 0.075, 0)), off)
            px[(x, y)] = o
    return px, on, off


HEART = ["..XX...XX...", ".XXXX.XXXX..", ".XXXXXXXXX..", ".XXXXXXXXX..", "..XXXXXXX...", "...XXXXX....", "....XXX.....", ".....X......"]
WIFI = ["............", "...XXXXXX...", "..X......X..", ".X..XXXX..X.", "...X....X...", ".....XX.....", ".....XX.....", "............"]


def matrix_pattern(f):
    if night(f) > 0.6:
        return {(x, y) for y, row in enumerate(WIFI) for x, c in enumerate(row) if c == "X"} if (f // 6) % 2 else set()
    if (f // 24) % 2 == 0:
        beat = 1 if (f % 12) < 6 else 0
        cells = {(x, y) for y, row in enumerate(HEART) for x, c in enumerate(row) if c == "X"}
        return cells if beat else {(x, y) for (x, y) in cells if 2 < x < 9 and 1 < y < 6}
    off = (f // 2) % 20
    return {(x, y) for y, row in enumerate(WIFI) for x, c in enumerate(row) if c == "X" and 0 <= x - off + 8 < 12} | \
        {(x, y) for y, row in enumerate(WIFI) for x, c in enumerate(row) if c == "X"}


def build_servo():
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.0, 0.07, 0.55, 1)
        p.inputs["Transmission Weight"].default_value = 0.12
        p.inputs["Roughness"].default_value = 0.2
        return p
    body = k.node_mat("servo_body", b)
    white = k.pbr("horn", (0.95, 0.95, 0.93), rough=0.35)
    k.box("sv_body", (0.9, 0.45, 0.85), S + Vector((0, 0, 0.43)), body)
    k.box("sv_tabs", (1.25, 0.45, 0.06), S + Vector((0, 0, 0.7)), body)
    k.cyl("sv_top", 0.17, 0.18, S + Vector((0.22, 0, 0.94)), body, verts=32)
    k.text("sv_lbl", "SG90", 0.12, S + Vector((0, -0.235, 0.43)), [k.emit("sv_t", (0.9, 0.9, 0.95), 1.0)], extrude=0.0)
    pivot = bpy.data.objects.new("sv_pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = S + Vector((0.22, 0, 1.06))
    horn = k.box("sv_horn", (0.62, 0.11, 0.05), S + Vector((0.42, 0, 1.06)), white)
    hub = k.cyl("sv_hub", 0.08, 0.08, S + Vector((0.22, 0, 1.06)), white, verts=24)
    bpy.context.view_layer.update()
    for o in (horn, hub):
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
    k.interp("LINEAR")
    for f in range(0, N + 1, 2):
        pivot.rotation_euler = (0, 0, math.radians(servo_deg(f) - 90))
        pivot.keyframe_insert("rotation_euler", frame=f)
    k.interp("BEZIER")
    for i, col in enumerate(((0.35, 0.18, 0.08), (0.85, 0.1, 0.05), (0.98, 0.55, 0.05))):
        wire(f"sv_w{i}", [S + Vector((-0.45, -0.05 + i * 0.05, 0.2)), S + Vector((-1.0, 0.2, 0.15)),
                          U + Vector((0.2 + i * 0.1, -0.95, 0.5))], col, r=0.018)


def build_phone():
    blk = k.pbr("phone_body", (0.03, 0.03, 0.035), rough=0.25, metal=0.4)
    k.box("stand", (0.9, 0.7, 0.08), F + Vector((0, 0.2, 0.04)), k.pbr("stand_m", (0.85, 0.85, 0.86), rough=0.3))
    root = bpy.data.objects.new("phone_root", None)
    bpy.context.collection.objects.link(root)
    root.location = F + Vector((0, 0, 0.1))
    parts = [k.box("phone", (1.0, 0.09, 2.15), F + Vector((0, 0, 1.18)), blk)]

    def b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "dash_tex"
        tex.image = bpy.data.images.load(os.path.join(DASH, "0000.png"))
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 1.15
        nt.links.new(tex.outputs["Color"], e.inputs["Color"])
        return e
    bpy.ops.mesh.primitive_plane_add(size=1, location=F + Vector((0, -0.05, 1.18)), rotation=(math.radians(90), 0, 0))
    scr = bpy.context.object
    scr.scale = (0.92, 2.0, 1)
    scr.data.materials.append(k.node_mat("dash", b))
    parts.append(scr)
    bpy.context.view_layer.update()
    for o in parts:
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    root.rotation_euler = (math.radians(-10), 0, math.radians(18))
    return F + Vector((0, -0.05, 1.18))


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.92, 0.93, 0.95, 1)
    bpy.ops.mesh.primitive_plane_add(size=80)
    bpy.context.object.data.materials.append(k.pbr("desk", (0.86, 0.86, 0.85), rough=0.38))
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 12, 0), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(k.pbr("wall", (0.6, 0.62, 0.65), rough=0.9))
    key = k.area("key", (-3, -4, 8), (0, 0, 1), 1500, 3)
    fill = k.area("fill", (6, -3, 4), (0, 0, 1), 500, 8)
    # dusk: lights + world dim down
    k.interp("BEZIER")
    for f in range(0, N + 1, 4):
        n = night(f)
        bg.inputs["Strength"].default_value = 0.75 * (1 - 0.9 * n)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
        key.data.energy = 1500 * (1 - 0.92 * n)
        key.data.keyframe_insert("energy", frame=f)
        fill.data.energy = 500 * (1 - 0.95 * n)
        fill.data.keyframe_insert("energy", frame=f)

    ldr_pt = build_plant()
    px, on_m, off_m = build_uno()
    build_servo()
    phone_c = build_phone()
    # red grow LED plugged into the R4 header, aimed at the plant
    led_m = k.pbr("led_m", (0.8, 0.05, 0.03), rough=0.15, em=(1.0, 0.08, 0.03), ems=0.0)
    Lp = U + Vector((1.1, 0.95, 0.5))
    for dx in (-0.04, 0.04):
        k.box("led_leg", (0.016, 0.016, 0.35), Lp + Vector((dx, 0, 0.15)), k.pbr("leg", (0.8, 0.8, 0.82), 0.2, 1.0))
    k.cyl("led_body", 0.09, 0.18, Lp + Vector((0, 0, 0.42)), led_m, verts=24)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=Lp + Vector((0, 0, 0.51)))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(led_m)
    bpy.ops.object.light_add(type="POINT", location=Lp + Vector((0.1, -0.1, 0.7)))
    glow = bpy.context.object
    glow.data.color = (1.0, 0.15, 0.08)
    em = led_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    k.interp("CONSTANT")
    for f, v in ((0, 0.0), (LED_ON, 8.0), (356, 0.0)):
        em.default_value = v
        em.keyframe_insert("default_value", frame=f)
        glow.data.energy = v * 6
        glow.data.keyframe_insert("energy", frame=f)
    k.interp("BEZIER")
    # rainbow jumpers: R4 -> LDR, R4 -> LED area
    rainbow = [(0.95, 0.45, 0.05), (0.98, 0.82, 0.05), (0.1, 0.6, 0.2), (0.1, 0.35, 0.9), (0.5, 0.2, 0.75)]
    for i, col in enumerate(rainbow[:3]):
        wire(f"ldr_w{i}", [U + Vector((0.5 + i * 0.1, 0.95, 0.5)), U + Vector((1.2, 1.4, 1.8 + i * 0.1)),
                           ldr_pt + Vector((-0.08 + i * 0.08, 0.06, -0.25))], col)
    # hand shadow: an occluder sweeping under the key light (never on camera)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    hand = bpy.context.object
    hand.scale = (0.45, 0.3, 0.08)
    hand.visible_camera = False
    hand.visible_glossy = False
    hand.data.materials.append(k.pbr("hand_m", (0.6, 0.45, 0.35), rough=0.6))
    k.interp("BEZIER")
    for f, x in ((SHADOW[0] - 4, -1.5), ((SHADOW[0] + SHADOW[1]) / 2, 0.0), (SHADOW[1] + 4, 1.5)):
        hand.location = ldr_pt + Vector((x - 0.9, -0.9, 2.6))
        hand.keyframe_insert("location", frame=f)
    k.show(hand, [(SHADOW[0] - 4, SHADOW[1] + 5)])

    # ---- cameras with DOF
    mx_c = U + Vector((0.35, 0.0, 0.25))
    sv_c = S + Vector((0.15, 0, 0.8))
    Sh = SHOTS

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        fo = bpy.data.objects.new(name + "_f", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    cams = [
        cam("s1", [(Sh[0], Vector((-0.5, -7.6, 4.6)), Vector((0.0, 0.0, 1.0))),
                   (Sh[1], Vector((0.3, -7.0, 4.2)), Vector((0.0, 0.0, 1.0)))], 30, Vector((0, -0.3, 1.0)), 2.8),
        cam("s2", [(Sh[1], ldr_pt + Vector((-0.6, -2.4, 0.3)), ldr_pt + Vector((0.2, 0.3, -0.2))),
                   (Sh[2], ldr_pt + Vector((-0.3, -2.1, 0.2)), ldr_pt + Vector((0.2, 0.3, -0.2)))], 40, ldr_pt, 1.8),
        cam("s3", [(Sh[2], phone_c + Vector((0.6, -2.6, 0.3)), phone_c),
                   (Sh[3], phone_c + Vector((0.4, -2.2, 0.2)), phone_c)], 45, phone_c, 2.0),
        cam("s4", [(Sh[3], mx_c + Vector((-0.6, -1.9, 1.4)), mx_c),
                   (Sh[4], mx_c + Vector((0.4, -1.7, 1.2)), mx_c)], 45, mx_c, 1.8),
        cam("s5", [(Sh[4], phone_c + Vector((-0.3, -2.3, 0.2)), phone_c + Vector((0, 0, -0.3))),
                   (Sh[5], phone_c + Vector((-0.2, -2.0, 0.1)), phone_c + Vector((0, 0, -0.3)))], 45, phone_c, 2.0),
        cam("s6", [(Sh[5], sv_c + Vector((-1.0, -2.0, 1.0)), sv_c),
                   (Sh[6], sv_c + Vector((0.6, -1.9, 0.9)), sv_c)], 42, sv_c, 1.8),
        cam("s7", [(Sh[6], Vector((2.6, -5.4, 3.0)), Vector((0.2, 0.3, 1.2))),
                   (Sh[7], Vector((1.8, -5.0, 3.2)), Vector((0.2, 0.3, 1.2)))], 32, Vector((0.6, 0.3, 1.2)), 2.4),
        cam("s8", [(Sh[7], Vector((-2.4, -6.8, 4.0)), Vector((0.0, 0.0, 1.0))),
                   (N, Vector((-1.4, -6.2, 3.6)), Vector((0.0, 0.0, 1.0)))], 30, Vector((0, -0.3, 1.0)), 2.8),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]

    imgs = {}

    def upd(scene, *_):
        f = scene.frame_current
        if f not in imgs:
            imgs[f] = bpy.data.images.load(os.path.join(DASH, f"{min(f, N - 1):04d}.png"), check_existing=True)
        bpy.data.materials["dash"].node_tree.nodes["dash_tex"].image = imgs[f]
        lit = matrix_pattern(f)
        for key_, o in px.items():
            o.data.materials[0] = on_m if key_ in lit else off_m
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
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces = 8, 6, 3
    cy.samples = 8 if args.preview else 14
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
