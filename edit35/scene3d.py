#!/usr/bin/env python3
"""Photoreal ESP32 Smart Dustbin (Blender, procedural, units = cm). Re-uses the ESP32 + 1.3" OLED breadboard
from edit10; a small white bin stands beside it with an HC-SR04 on its front, a blue SG90 servo at the back
hinge and a lid that swings open (bintime.lid()); a hand brings a crumpled paper ball, then a can, and drops
them in. A mini breadboard carries a red (closed) / green (open) LED and a buzzer. The OLED shows
bingfx.oled_png(). Writes projected OLED / LED positions per frame (work/proj) for the B&W + colour grade.
13 s loop: the last shot ends on the first shot's pose. Run: python3 edit35/scene3d.py [--preview] [...]"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from bintime import FPS, N, SHOTS, D, BIN_W, BIN_DEP, BIN_H, FRONT_Y, HINGE, THROWS, hand, item, lid, lid_open, detected  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
PROJ = os.path.join(HERE, "work", "proj")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
b10.OLED = OLED
MB = Vector((1.0, -6.4, 0))
LED_R = MB + Vector((0.6, 0.3, 0.9))
LED_G = MB + Vector((1.6, 0.3, 0.9))
DV = Vector(D)
R90 = (math.radians(90), 0, 0)


def build_bin():
    plastic = k.pbr("bin_m", (0.86, 0.87, 0.88), 0.35)
    inner = k.pbr("bin_in", (0.25, 0.26, 0.28), 0.6)
    t = 0.25
    k.box("bin_bottom", (BIN_W, BIN_DEP, t), DV + Vector((0, 0, t / 2)), plastic)
    k.box("bin_floor_in", (BIN_W - 2 * t, BIN_DEP - 2 * t, 0.02), DV + Vector((0, 0, t + 0.01)), inner)
    for sx in (-1, 1):
        k.box("bin_side", (t, BIN_DEP, BIN_H), DV + Vector((sx * (BIN_W - t) / 2, 0, BIN_H / 2)), plastic)
    for sy in (-1, 1):
        k.box("bin_fb", (BIN_W, t, BIN_H), DV + Vector((0, sy * (BIN_DEP - t) / 2, BIN_H / 2)), plastic)
    for sx in (-1, 1):                                                   # rim = four thin strips (open top)
        k.box("bin_rim", (0.45, BIN_DEP + 0.2, 0.18), DV + Vector((sx * (BIN_W / 2 - 0.12), 0, BIN_H - 0.09)), plastic)
    for sy in (-1, 1):
        k.box("bin_rim", (BIN_W + 0.2, 0.45, 0.18), DV + Vector((0, sy * (BIN_DEP / 2 - 0.12), BIN_H - 0.09)), plastic)
    liner = k.pbr("liner", (0.03, 0.03, 0.035), 0.35)                  # black bin-bag liner inside
    hi = BIN_H - 0.6
    for sx in (-1, 1):
        k.box("liner_s", (0.03, BIN_DEP - 2 * t - 0.04, hi), DV + Vector((sx * (BIN_W / 2 - t - 0.03), 0, t + hi / 2)), liner)
    for sy in (-1, 1):
        k.box("liner_fb", (BIN_W - 2 * t - 0.04, 0.03, hi), DV + Vector((0, sy * (BIN_DEP / 2 - t - 0.03), t + hi / 2)), liner)
    k.box("liner_b", (BIN_W - 2 * t - 0.04, BIN_DEP - 2 * t - 0.04, 0.03), DV + Vector((0, 0, t + 0.04)), liner)
    # lid on a hinge at the back top edge
    hinge = bpy.data.objects.new("lid_hinge", None)
    bpy.context.collection.objects.link(hinge)
    hinge.location = Vector(HINGE) + Vector((0, 0.1, 0.1))
    before = set(bpy.data.objects)
    k.box("lid", (BIN_W + 0.3, BIN_DEP + 0.3, 0.3), Vector((0, -(BIN_DEP + 0.3) / 2, 0.15)), plastic)
    k.box("lid_grip", (1.6, 0.4, 0.25), Vector((0, -BIN_DEP + 0.2, 0.42)), inner)
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = hinge
    # HC-SR04 on the front face
    steel = bpy.data.materials["steel"]
    sp = Vector((DV.x, FRONT_Y - 0.12, 4.3))
    k.box("hc_pcb", (4.5, 0.15, 2.0), sp, k.pbr("hc_m", (0.05, 0.25, 0.65), 0.4))
    for sx in (-1.3, 1.3):
        k.cyl("hc_can", 0.8, 1.0, sp + Vector((sx, -0.55, -0.1)), steel, rot=R90, verts=40)
        k.cyl("hc_mesh", 0.68, 0.05, sp + Vector((sx, -1.06, -0.1)), k.pbr("mesh", (0.03, 0.03, 0.03), 0.8), rot=R90, verts=40)
    k.text("hc_lbl", "HC-SR04", 0.3, sp + Vector((0, -0.09, 0.72)), [k.emit("hc_t", (0.9, 0.92, 0.95), 1.0)], extrude=0.0, rot=R90)
    # SG90 servo at the back, horn pushing the lid
    blue = k.pbr("servo_blue", (0.0, 0.07, 0.55), 0.3)
    k.box("servo", (2.3, 1.2, 2.2), Vector((DV.x + 1.6, HINGE[1] + 0.75, BIN_H - 1.5)), blue)
    k.text("sg_lbl", "SG90", 0.28, Vector((DV.x + 1.6, HINGE[1] + 1.36, BIN_H - 1.5)), [k.emit("sg_t", (0.9, 0.9, 0.95), 0.9)],
           extrude=0.0, rot=(math.radians(90), 0, math.radians(180)))
    return hinge


def build_side():
    k.box("mini_bb", (8.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (8.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    steel = bpy.data.materials["steel"]
    blk = bpy.data.materials["esp_blk"]
    for name, c, col in (("led_r", LED_R, (1.0, 0.06, 0.03)), ("led_g", LED_G, (0.1, 1.0, 0.2))):
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.name = "P"
            p.inputs["Base Color"].default_value = (*[0.02 + 0.2 * v for v in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.35
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(name, b)
        k.cyl(name + "_rim", 0.33, 0.08, c + Vector((0, 0, 0.62)), m, verts=32)
        k.cyl(name + "_body", 0.29, 0.5, c + Vector((0, 0, 0.88)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.29, location=c + Vector((0, 0, 1.13)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        for dx in (-0.127, 0.127):
            k.box("led_leg", (0.04, 0.04, 0.6), c + Vector((dx, 0, 0.3)), steel)
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.3, 1.7)))
        gl = bpy.context.object
        gl.name = name + "_glow"
        gl.data.color = col
        gl.data.shadow_soft_size = 0.2
        gl.data.energy = 0.0
    k.cyl("buzzer", 0.62, 0.95, MB + Vector((3.0, 0.2, 1.38)), blk, verts=40)
    k.cyl("buzzer_hole", 0.12, 0.03, MB + Vector((3.0, 0.2, 1.86)), k.pbr("hole", (0, 0, 0), 0.9), verts=16)
    ends = [(LED_R + Vector((0, 1.0, 0)), (0.85, 0.1, 0.05)), (LED_G + Vector((0, 1.0, 0)), (0.1, 0.7, 0.2)),
            (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
    for i, (a, col) in enumerate(ends):
        e = Vector((b10.E.x - 1.4 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.6, 1.6)), e + Vector((0, -1.2, 1.6)), e), col, r=0.05)
    # bin wires (sensor + servo) back to the ESP32 header
    for i, col in enumerate(((0.85, 0.1, 0.05), (1.0, 0.8, 0.05), (0.1, 0.6, 0.2), (0.04, 0.04, 0.04), (0.95, 0.5, 0.05))):
        a = Vector((DV.x - BIN_W / 2 - 0.1, FRONT_Y + 0.6 + i * 0.25, 5.0 - 0.3 * i))
        e = Vector((b10.E.x + 0.3 + i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_bin{i}", b10.bez(a, a + Vector((-2.5, 0, 1.0)), e + Vector((1.5, 1.0, 2.5)), e), col, r=0.05)


def build_hand():
    """Hand grabbing from above: flat palm, four fingers and a thumb curling down round the item, forearm
    rising back to the right (the hand enters from the right side)."""
    skin = k.pbr("skin", (0.78, 0.52, 0.4), rough=0.5)
    root = bpy.data.objects.new("hand_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)

    def rounded(name, size, loc, rot=(0, 0, 0), bevel=0.3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
        o = bpy.context.object
        o.name = name
        o.scale = size
        bv = o.modifiers.new("bev", "BEVEL")
        bv.width, bv.segments = bevel, 4
        o.data.materials.append(skin)
        bpy.ops.object.shade_smooth()
        return o

    def limb(name, r, a, b_):
        a, b_ = Vector(a), Vector(b_)
        d = b_ - a
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
        k.cyl(name, r, d.length, (a + b_) / 2, skin, rot=tuple(rot), verts=20)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=b_, segments=20, ring_count=10)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(skin)

    rounded("palm", (2.5, 2.4, 0.95), (0, 0, 0.4), rot=(0, math.radians(-8), 0))
    for i in range(4):                                         # fingers: forward then down round the item
        y = -0.85 + i * 0.57
        L1 = 1.1 - abs(i - 1.5) * 0.12
        a = Vector((-1.15, y, 0.35))
        m = a + Vector((-L1, 0, -0.35))
        limb("fing1", 0.27, a, m)
        limb("fing2", 0.25, m, m + Vector((-0.25, 0, -1.25 + abs(i - 1.5) * 0.15)))
    limb("thumb1", 0.32, (0.2, -1.25, 0.1), (-0.35, -1.55, -0.8))
    limb("thumb2", 0.29, (-0.35, -1.55, -0.8), (-0.9, -1.2, -1.5))
    limb("wrist", 1.0, (1.1, 0, 0.5), (2.2, 0.1, 0.9))
    limb("forearm", 1.1, (2.2, 0.1, 0.9), (12.0, 1.0, 6.0))
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    return root


def build_items():
    paper = k.pbr("paper", (0.92, 0.92, 0.9), 0.85)
    objs = []
    for i, (t0, kind) in enumerate(THROWS):
        if kind == "ball":
            bpy.ops.mesh.primitive_ico_sphere_add(radius=0.9, subdivisions=3, location=(0, 0, 0))
            o = bpy.context.object
            tex = bpy.data.textures.new(f"crumple{i}", "VORONOI")
            tex.noise_scale = 0.35
            dm = o.modifiers.new("disp", "DISPLACE")
            dm.texture = tex
            dm.strength = 0.25
            o.data.materials.append(paper)
        else:
            o = k.cyl(f"can{i}", 0.7, 2.2, Vector((0, 0, 0)), k.pbr("can_m", (0.75, 0.05, 0.08), 0.25, 0.8), verts=32)
            o.rotation_euler = (0, math.radians(75), 0)
        o.name = f"item{i}"
        objs.append(o)
    return objs


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.25
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-20, -45, 70), (6, -3, 3), 70000, 32)
    k.area("fill", (55, -35, 40), (6, -3, 3), 14000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (6, 0, 3), 25000, 25, col=(0.8, 0.8, 1.0))
    b10.build_board()
    bpy.data.materials["blue_led"].node_tree.animation_data_clear()
    hinge = build_bin()
    build_side()
    hand_root = build_hand()
    objs = build_items()

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
    binc = DV + Vector((0, 0, 4.5))
    top = DV + Vector((0, 0, BIN_H))
    p0 = binc + Vector((-6.5, -20.0, 7.5))
    p1 = binc + Vector((-5.5, -18.0, 6.8))
    look0 = binc + Vector((0.5, -2.5, 1.5))
    mid = (scr + binc) / 2
    cams = [
        cam("s0", [(Sh[0], p0, look0), (Sh[1], p1, look0)], 36, binc + Vector((0, -2, 0)), 4.0),
        cam("s1", [(Sh[1], top + Vector((-5.0, -10.0, 14.0)), top + Vector((0, 0.3, -2.5))),
                   (Sh[2], top + Vector((-4.2, -9.0, 12.5)), top + Vector((0, 0.3, -2.5)))], 34, top, 5.6),
        cam("s2", [(Sh[2], scr + Vector((0.6, -9.6, 8.6)), scr + Vector((0, 0.9, 0.6))), (Sh[3], scr + Vector((0.1, -8.8, 7.9)), scr + Vector((0, 0.9, 0.6)))], 42, scr, 4.0),
        cam("s3", [(Sh[3], Vector((DV.x - 8, FRONT_Y - 20, 3.6)), Vector((DV.x + 1.5, FRONT_Y, 5.5))),
                   (Sh[4], Vector((DV.x - 7, FRONT_Y - 17.5, 4.2)), Vector((DV.x + 1.5, FRONT_Y, 5.5)))], 34, Vector((DV.x, FRONT_Y - 3, 5)), 4.0),
        cam("s4", [(Sh[4], top + Vector((5.0, -10.0, 14.0)), top + Vector((0, 0.3, -2.5))),
                   (Sh[5], top + Vector((4.2, -9.0, 12.5)), top + Vector((0, 0.3, -2.5)))], 34, top, 5.6),
        cam("s5", [(Sh[5], mid + Vector((0, -30, 22)), mid + Vector((0, -1, 0))), (Sh[6], mid + Vector((0, -27, 20)), mid + Vector((0, -1, 0)))], 34, mid, 8.0),
        cam("s6", [(Sh[6], p1, look0), (N, p0, look0)], 36, binc + Vector((0, -2, 0)), 4.0),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]
    imgs = {}
    os.makedirs(PROJ, exist_ok=True)
    scr_obj = bpy.data.objects["oled_screen"]

    def upd(scene, *_):
        f = scene.frame_current
        ff = min(max(f, 0), N - 1)
        if f not in imgs:
            imgs[f] = bpy.data.images.load(os.path.join(OLED, f"{ff:04d}.png"), check_existing=True)
        bpy.data.materials["oled_scr"].node_tree.nodes["oled_tex"].image = imgs[f]
        hinge.rotation_euler = (math.radians(-100 * lid(ff)), 0, 0)
        hand_root.location = Vector(hand(ff))
        for (t0, kind), o in zip(THROWS, objs):
            p = item(ff, t0, kind)
            o.hide_render = p is None
            if p is not None:
                o.location = Vector(p)
                if kind == "can":
                    o.rotation_euler = (0, math.radians(75 if ff - t0 < 60 else 90), 0)
        op = lid_open(ff)
        for name, on in (("led_r", not op), ("led_g", op)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 9.0 if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = 5.0 if on else 0.0
        bl = bpy.data.materials["blue_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        bl.default_value = 22.0 if detected(ff) else 0.0
        ci = max(i for i, s in enumerate(Sh) if s <= ff)
        cm = cams[ci]
        scene.camera = cm
        bpy.context.view_layer.update()
        mw = scr_obj.matrix_world
        pts = {"screen": [list(world_to_camera_view(scene, cm, mw @ v.co)[:2]) for v in scr_obj.data.vertices]}
        for key, p in (("led_r", LED_R + Vector((0, 0, 1.0))), ("led_g", LED_G + Vector((0, 0, 1.0)))):
            pts[key] = list(world_to_camera_view(scene, cm, p)[:2])
        a = world_to_camera_view(scene, cm, LED_R + Vector((0, 0, 1.0)))
        b_ = world_to_camera_view(scene, cm, LED_R + Vector((1.0, 0, 1.0)))
        pts["cm_px"] = abs(b_[0] - a[0]) * 1080
        pts["screen"] = [[x * 1080, (1 - y) * 1920] for x, y in pts["screen"]]
        for key in ("led_r", "led_g"):
            x, y = pts[key]
            pts[key] = [x * 1080, (1 - y) * 1920]
        with open(os.path.join(PROJ, f"{ff:04d}.json"), "w") as fh:
            json.dump(pts, fh)
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
    cy.samples = 8 if args.preview else 12
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = 33 if args.preview else 100
    sc.render.use_motion_blur = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(args.out, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
