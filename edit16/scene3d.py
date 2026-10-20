#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + DHT11 temperature-controlled LED (Blender, procedural, units = cm).
Re-uses the ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds a DHT11 module on a
stand, a hot coffee mug that slides in beside it (timeline.mug()), a KY-040 knob that sets the limit
(timeline.knob()) and a red HOT / blue OK LED pair + buzzer driven by timeline.hot(). The OLED shows
edit16/make_screens.py. 24 fps, 468 frames.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, knob, mug, hot, busy  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
TEX16 = os.path.join(HERE, "work", "tex")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
D = Vector((1.6, 5.4, 0))                      # DHT11 stand centre
DHTC = D + Vector((0, -0.2, 3.2))              # sensor housing (camera target)
MUG_R, MUG_H = 1.75, 4.0
MUG_IN = D + Vector((3.4, -0.2, 0))            # mug right beside the DHT11
MUG_OUT = D + Vector((30.0, 6.0, 0))
MB = Vector((1.0, -6.4, 0))                    # mini breadboard (knob + LEDs)
ENC = MB + Vector((-2.2, 0, 0.9))
KNOB = ENC + Vector((0, 0, 2.3))
R90 = (math.radians(90), 0, 0)


def dht_tex():
    from PIL import Image, ImageDraw
    os.makedirs(TEX16, exist_ok=True)
    path = os.path.join(TEX16, "dht.png")
    im = Image.new("RGB", (310, 400), (40, 115, 220))
    d = ImageDraw.Draw(im)
    for r in range(6):
        for c in range(4):
            x, y = 30 + c * 66, 110 + r * 46
            d.rounded_rectangle((x, y, x + 52, y + 30), 6, fill=(8, 30, 75))
    d.rectangle((0, 0, 309, 399), outline=(25, 85, 180), width=8)
    im.save(path)
    return path


def build_dht():
    blk = bpy.data.materials["esp_blk"]
    gold = bpy.data.materials["gold"]
    k.box("dht_stand", (3.2, 2.6, 0.9), D + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("dht_stand_top", (3.2, 2.6), D + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    pcb = D + Vector((0, 0.2, 0.9 + 0.5 + 1.5))
    k.box("dht_pcb", (2.1, 0.16, 3.0), pcb, k.pbr("dht_pcb_m", (0.02, 0.12, 0.45), 0.35))
    k.box("dht_body", (1.6, 0.62, 2.05), pcb + Vector((0, -0.39, 0.32)), k.pbr("dht_blue", (0.06, 0.22, 0.75), 0.45))
    b10.plane("dht_face", (1.6, 2.05), pcb + Vector((0, -0.705, 0.32)), b10.tex_mat("dht_face_m", dht_tex(), rough=0.5), rot=R90)
    k.text("dht_lbl", "DHT11", 0.3, pcb + Vector((0, -0.09, -1.12)), [k.emit("dht_silk", (0.95, 0.95, 0.95), 1.0)], extrude=0.0)
    for i in range(3):
        x = pcb.x + (i - 1) * 0.254
        k.box("dht_pin", (0.064, 0.064, 0.9), Vector((x, pcb.y, 0.9 + 0.45)), gold)
        k.box("dht_hdr", (0.25, 0.25, 0.25), Vector((x, pcb.y, 0.9 + 0.13)), blk)
    for i, col in enumerate(((0.85, 0.08, 0.05), (1.0, 0.8, 0.05), (0.04, 0.04, 0.04))):
        a = Vector((D.x - 1.3, pcb.y + (i - 1) * 0.254, 0.9))
        e = Vector((b10.E.x - 0.7 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_dht{i}", b10.bez(a, a + Vector((-0.6, 0, 1.4)), e + Vector((0, 0.8, 1.6)), e), col, r=0.05)


def build_mug():
    import bmesh
    root = bpy.data.objects.new("mug_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)
    cer = k.pbr("mug_m", (0.55, 0.03, 0.03), 0.18)
    bpy.ops.mesh.primitive_cylinder_add(radius=MUG_R, depth=MUG_H, location=(0, 0, MUG_H / 2), vertices=64)
    m = bpy.context.object
    m.name = "mug"
    bm = bmesh.new()
    bm.from_mesh(m.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context="FACES")
    bm.to_mesh(m.data)
    bm.free()
    sol = m.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.2
    bev = m.modifiers.new("bev", "BEVEL")
    bev.width, bev.segments = 0.06, 3
    bpy.ops.object.shade_smooth()
    m.data.materials.append(cer)
    k.cyl("coffee", MUG_R - 0.18, 0.05, Vector((0, 0, MUG_H - 0.55)), k.pbr("coffee_m", (0.09, 0.035, 0.01), 0.08), verts=64)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.24, location=(MUG_R + 0.55, 0, MUG_H * 0.52),
                                     rotation=(math.radians(90), 0, 0), major_segments=48, minor_segments=16)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(cer)
    bpy.ops.object.light_add(type="POINT", location=(-MUG_R - 0.3, -0.6, MUG_H * 0.75))
    g = bpy.context.object
    g.name = "mug_heat"
    g.data.color = (1.0, 0.45, 0.15)
    g.data.shadow_soft_size = 1.2
    g.data.energy = 0.0
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        u = mug(max(f, 0))
        root.location = MUG_IN * u + MUG_OUT * (1 - u)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")


def build_controls():
    k.box("mini_bb", (8.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (8.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    k.box("ky_pcb", (2.0, 2.6, 0.12), ENC + Vector((0, 0, 0.5)), k.pbr("ky_pcb_m", (0.02, 0.02, 0.025), 0.4))
    k.box("ky_body", (1.25, 1.25, 0.65), ENC + Vector((0, -0.2, 0.9)), steel)
    k.cyl("ky_bush", 0.45, 0.35, ENC + Vector((0, -0.2, 1.4)), steel, verts=32)
    root = bpy.data.objects.new("knob_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)
    k.cyl("knob", 0.85, 1.3, Vector((0, 0, 0)), k.pbr("knob_m", (0.04, 0.04, 0.045), 0.45), verts=48)
    for j in range(24):
        a = j * 2 * math.pi / 24
        k.box("rib", (0.08, 0.12, 1.2), Vector((0.86 * math.cos(a), 0.86 * math.sin(a), 0)), blk, rot=(0, 0, a))
    k.cyl("knob_cap", 0.72, 0.04, Vector((0, 0, 0.66)), k.pbr("cap_m", (0.75, 0.76, 0.78), 0.25, 1.0), verts=48)
    k.box("knob_mark", (0.14, 0.55, 0.02), Vector((0, 0.42, 0.69)), k.emit("mark_m", (1.0, 1.0, 1.0), 1.2))
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    k.interp("LINEAR")
    for f in range(-1, N + 1):
        ff = max(f, 0)
        root.rotation_euler = (0, 0, math.radians(-knob(ff)))
        root.location = KNOB + Vector((0, -0.2, 0))
        root.keyframe_insert("rotation_euler", frame=f)
        root.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    for name, x, col in (("led_r", 0.6, (1.0, 0.06, 0.03)), ("led_b", 1.6, (0.1, 0.35, 1.0))):
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
            (MB + Vector((1.6, 1.3, 0.9)), (0.1, 0.35, 0.95)), (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
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
    build_dht()
    build_controls()
    build_mug()

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
    game = Vector((1.6, -0.3, 1.4))                   # OLED + DHT11 + mug + LEDs
    kn = Vector((0.6, -3.6, 1.6))                     # knob + OLED
    cams = [
        cam("s0", [(Sh[0], Vector((2.6, -15, 19)), game), (Sh[1], Vector((2.0, -13.5, 17.5)), game)], 35, game, 5.6),
        cam("s1", [(Sh[1], Vector((0.8, -12, 25)), mid1), (Sh[2], Vector((0.8, -11, 23)), mid1)], 32, mid1, 8.0),
        cam("s2", [(Sh[2], DHTC + Vector((3.2, -7.5, 6.4)), DHTC), (Sh[3], DHTC + Vector((2.2, -6.6, 5.6)), DHTC)], 50, DHTC, 2.8),
        cam("s3", [(Sh[3], kn + Vector((-2.0, -11, 11)), kn), (Sh[4], kn + Vector((-1.0, -10, 10)), kn)], 40, kn, 4.0),
        cam("s4", [(Sh[4], Vector((0.8, -15, 19)), game), (Sh[5], Vector((1.8, -13.5, 17)), game)], 35, game, 5.6),
        cam("s5", [(Sh[5], scr + Vector((-0.3, -11.5, 9.5)), scr + Vector((0, -3.4, -0.6))),
                   (Sh[6], scr + Vector((0.2, -10.5, 8.7)), scr + Vector((0, -3.4, -0.6)))], 40, scr, 4.0),
        cam("s6", [(Sh[6], Vector((-3, -21, 15)), mid), (N, Vector((-4, -23, 16)), mid)], 34, mid, 5.6),
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
        h = hot(ff)
        for name, on in (("led_r", h), ("led_b", not h)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
        bpy.data.objects["mug_heat"].data.energy = 6.0 * mug(ff)
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
