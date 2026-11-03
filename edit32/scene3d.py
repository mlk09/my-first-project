#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + MAX30102 heart-rate monitor (Blender, procedural, units = cm). Re-uses the
ESP32 + 1.3" OLED breadboard from edit10; a mini breadboard holds the purple MAX30102 module with a
finger resting on it (red sensor light pulsing through on every beat), a red LED that flashes on each
beat (fast blink while HIGH), a green 'normal' LED and a buzzer. The OLED shows hrgfx.oled_png().
For the B&W + colour-screen grade it also writes, per frame, the projected screen corners, LED and
sensor positions (work/proj/NNNN.json) so the edit can keep only those areas in colour.
13 s loop format: the last shot ends on the first shot's camera pose. 24 fps, 312 frames.
Run: python3 edit32/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from hrtime import FPS, N, SHOTS, BEATS, since_beat, sensor_glow, high  # noqa: E402
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
MB = Vector((1.0, -6.4, 0))
SENS = MB + Vector((-2.0, 0.1, 0.9))           # MAX30102 module centre (on the mini breadboard top)
SENS_TOP = SENS + Vector((0, 0, 0.55))
LED_R = MB + Vector((0.6, 0.3, 0.9))
LED_G = MB + Vector((1.6, 0.3, 0.9))
R90 = (math.radians(90), 0, 0)


def emit_mat(name, col, strength):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.name = "P"
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = strength
        return p
    return k.node_mat(name, b)


def build_side():
    k.box("mini_bb", (8.0, 3.6, 0.9), MB + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("mini_top", (8.0, 3.6), MB + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    blk = bpy.data.materials["esp_blk"]
    steel = bpy.data.materials["steel"]
    # MAX30102 module: purple pcb on a header, black sensor window with a red LED
    k.box("max_hdr", (1.3, 0.25, 0.32), SENS + Vector((0, 0.55, 0.16)), blk)
    k.box("max_pcb", (1.45, 1.45, 0.1), SENS + Vector((0, 0, 0.42)), k.pbr("max_pcb_m", (0.22, 0.05, 0.42), 0.35))
    k.box("max_win", (0.55, 0.32, 0.06), SENS + Vector((0, -0.1, 0.5)), k.pbr("max_win_m", (0.01, 0.01, 0.012), 0.08))
    k.box("max_led", (0.14, 0.12, 0.02), SENS + Vector((-0.12, -0.1, 0.535)), emit_mat("max_led_m", (1.0, 0.03, 0.02), 6.0))
    k.text("max_lbl", "MAX30102", 0.13, SENS + Vector((0, 0.42, 0.475)), [k.emit("max_t", (0.95, 0.95, 0.95), 0.8)], extrude=0.0)
    bpy.ops.object.light_add(type="POINT", location=SENS_TOP + Vector((0, -0.25, 0.1)))
    g = bpy.context.object
    g.name = "sens_glow"
    g.data.color = (1.0, 0.05, 0.04)
    g.data.shadow_soft_size = 0.3
    g.data.energy = 3.0
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
    ends = [(SENS + Vector((-0.4, 0.7, 0)), (1.0, 0.8, 0.05)), (SENS + Vector((-0.13, 0.7, 0)), (0.1, 0.35, 0.95)),
            (SENS + Vector((0.13, 0.7, 0)), (0.95, 0.95, 0.95)), (SENS + Vector((0.4, 0.7, 0)), (0.04, 0.04, 0.04)),
            (LED_R + Vector((0, 1.0, 0)), (0.85, 0.1, 0.05)), (LED_G + Vector((0, 1.0, 0)), (0.1, 0.7, 0.2)),
            (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
    for i, (a, col) in enumerate(ends):
        e = Vector((b10.E.x - 1.4 + i * 0.254, -1.27 - 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_side{i}", b10.bez(a, a + Vector((0, 0.6, 1.6)), e + Vector((0, -1.2, 1.6)), e), col, r=0.05)


def build_finger():
    skin = k.pbr("skin", (0.78, 0.52, 0.4), rough=0.5)
    nail = k.pbr("nail", (0.92, 0.75, 0.7), rough=0.25)
    root = bpy.data.objects.new("finger_root", None)
    bpy.context.collection.objects.link(root)
    parts = []
    tip = Vector((0, 0, 0.75))
    parts.append(k.cyl("finger", 0.75, 9.0, tip + Vector((0, -4.3, 2.2)), skin, rot=(math.radians(62), 0, 0), verts=32))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75, location=tip, segments=32, ring_count=16)
    bpy.ops.object.shade_smooth()
    s = bpy.context.object
    s.data.materials.append(skin)
    parts.append(s)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=tip + Vector((0, -0.25, 0.55)), segments=24, ring_count=12)
    nl = bpy.context.object
    nl.scale = (1, 1.3, 0.25)
    nl.rotation_euler = (math.radians(-28), 0, 0)
    nl.data.materials.append(nail)
    parts.append(nl)
    bpy.context.view_layer.update()
    for o in parts:
        o.parent = root
    root.location = SENS_TOP + Vector((0, -0.1, -0.68))
    return root


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.25
    b10.plane("mat", (300, 300), Vector((0, 0, 0)), b10.tex_mat("mat_m", os.path.join(b10.TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    b10.plane("wall", (600, 300), Vector((0, 70, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -45, 70), (0, -3, 1), 65000, 30)
    k.area("fill", (45, -35, 40), (0, -3, 1), 12000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (0, 0, 2), 25000, 25, col=(0.8, 0.8, 1.0))
    b10.build_board()
    bpy.data.materials["blue_led"].node_tree.animation_data_clear()
    build_side()
    finger = build_finger()

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
    look0 = scr + Vector((0, 0.9, 0.6))
    p0 = scr + Vector((1.2, -10.5, 9.0))
    p1 = scr + Vector((0.5, -9.6, 8.3))
    both = (scr + SENS) / 2
    cams = [
        cam("s0", [(Sh[0], p0, look0), (Sh[1], p1, look0)], 40, scr, 4.0),
        cam("s1", [(Sh[1], SENS_TOP + Vector((-7.5, -3.2, 3.6)), SENS_TOP + Vector((0.4, -0.6, 0.5))),
                   (Sh[2], SENS_TOP + Vector((-6.6, -2.6, 3.1)), SENS_TOP + Vector((0.4, -0.6, 0.5)))], 40, SENS_TOP, 3.2),
        cam("s2", [(Sh[2], Vector((2.0, -14, 17)), both), (Sh[3], Vector((1.2, -13, 16)), both)], 34, both, 5.6),
        cam("s3", [(Sh[3], scr + Vector((-0.6, -9.0, 8.0)), scr + Vector((0, 1.0, 0.7))), (Sh[4], scr + Vector((0.4, -8.2, 7.4)), scr + Vector((0, 1.0, 0.7)))], 42, scr, 4.0),
        cam("s4", [(Sh[4], MB + Vector((4.5, -9.5, 7.5)), MB + Vector((-0.5, 0.3, 1.2))), (Sh[5], MB + Vector((3.5, -8.6, 6.8)), MB + Vector((-0.5, 0.3, 1.2)))], 38, MB, 4.0),
        cam("s5", [(Sh[5], p1, look0), (N, p0, look0)], 40, scr, 4.0),
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
        sb = since_beat(ff)
        beat = sb < 4
        hi = high(ff)
        red_on = beat or (hi and (ff // 3) % 2 == 0)
        for name, on, st in (("led_r", red_on, 9.0), ("led_g", not hi, 4.0)):
            bpy.data.materials[name].node_tree.nodes["P"].inputs["Emission Strength"].default_value = st if on else 0.0
            bpy.data.objects[name + "_glow"].data.energy = (5.0 if on else 0.0) * st / 9.0
        g = sensor_glow(ff)
        bpy.data.objects["sens_glow"].data.energy = 2.0 + 6.0 * (g - 0.6) / 0.4
        bpy.data.materials["max_led_m"].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 3 + 8 * g
        finger.location = SENS_TOP + Vector((0, -0.1, -0.68 - 0.025 * math.exp(-sb / 2.5)))
        bl = bpy.data.materials["blue_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        bl.default_value = 22.0 if beat else 0.0
        # projected positions for the colour mask (camera picked from the shot markers)
        ci = max(i for i, s in enumerate(Sh) if s <= ff)
        cm = cams[ci]
        scene.camera = cm
        bpy.context.view_layer.update()
        mw = scr_obj.matrix_world
        pts = {"screen": [], "led_r": None, "led_g": None, "sensor": None}
        for v in scr_obj.data.vertices:
            pts["screen"].append(world_to_camera_view(scene, cm, mw @ v.co)[:2])
        for key, p in (("led_r", LED_R + Vector((0, 0, 1.0))), ("led_g", LED_G + Vector((0, 0, 1.0))), ("sensor", SENS_TOP + Vector((0, -0.6, 0.1)))):
            pts[key] = world_to_camera_view(scene, cm, p)[:2]
        # pixel scale of 1 cm at the LEDs / sensor (for mask radii)
        a = world_to_camera_view(scene, cm, LED_R + Vector((0, 0, 1.0)))
        b_ = world_to_camera_view(scene, cm, LED_R + Vector((1.0, 0, 1.0)))
        pts["cm_px"] = abs(b_[0] - a[0]) * 1080
        pts["screen"] = [[x * 1080, (1 - y) * 1920] for x, y in pts["screen"]]
        for key in ("led_r", "led_g", "sensor"):
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
