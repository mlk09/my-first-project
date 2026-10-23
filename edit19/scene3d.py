#!/usr/bin/env python3
"""Photoreal ESP32 + OLED + TTP223 touch sensor '3 modes' (Blender, procedural, units = cm). Re-uses
the ESP32 + 1.3" OLED breadboard from edit10 (same channel look); adds a blue TTP223 module tilted on a
stand (its red indicator LED + a cyan ring glow light up while timeline.touching()), a KY-040 knob that
picks the mode (timeline.knob()) and a blue LED + buzzer driven by timeline.led(). 24 fps, 468 frames.
Run: python3 edit15/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402
from timeline import FPS, N, SHOTS, knob, touching, led, busy  # noqa: E402
_spec = importlib.util.spec_from_file_location("edit10_scene3d", os.path.join(HERE, "..", "edit10", "scene3d.py"))
b10 = importlib.util.module_from_spec(_spec)   # edit10 ESP32 + OLED board (+ edit2 helpers as b10.k)
_spec.loader.exec_module(b10)
k = b10.k
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
TEX19 = os.path.join(HERE, "work", "tex")
b10.TEX = os.path.join(HERE, "..", "edit10", "work", "tex")
D = Vector((1.6, 5.4, 0))                      # touch-sensor stand
TILT = 38.0                                    # module tilted towards the camera (deg)
PAD = D + Vector((0, 0.3, 2.4))                # TTP223 pad centre
PADC = PAD + Vector((0, 0, 0.0))               # camera target
MB = Vector((1.0, -6.4, 0))                    # mini breadboard (knob + LEDs)
ENC = MB + Vector((-2.2, 0, 0.9))
KNOB = ENC + Vector((0, 0, 2.3))
R90 = (math.radians(90), 0, 0)


def ttp_tex():
    """Blue TTP223 pcb artwork: concentric touch rings + silkscreen."""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(TEX19, exist_ok=True)
    path = os.path.join(TEX19, "ttp.png")
    im = Image.new("RGB", (600, 600), (20, 70, 175))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 599, 599), outline=(15, 50, 130), width=14)
    for k in range(5):
        r = 190 - k * 38
        d.ellipse((300 - r, 290 - r, 300 + r, 290 + r), outline=(235, 240, 250), width=12)
    fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    d.text((300, 540), "Touch Sensor", font=fnt, fill=(235, 240, 250), anchor="mm")
    for k, lab in enumerate(("GND", "VCC", "SIG")):
        d.text((110 + k * 190, 50), lab, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30),
               fill=(235, 240, 250), anchor="mm")
    im.save(path)
    return path


def build_touch():
    blk = bpy.data.materials["esp_blk"]
    gold = bpy.data.materials["gold"]
    k.box("ttp_stand", (3.2, 2.6, 0.9), D + Vector((0, 0, 0.45)), bpy.data.materials["bb_side"])
    b10.plane("ttp_stand_top", (3.2, 2.6), D + Vector((0, 0, 0.903)), bpy.data.materials["bb_top_m"])
    root = bpy.data.objects.new("ttp_root", None)
    bpy.context.collection.objects.link(root)
    before = set(bpy.data.objects)
    k.box("ttp_pcb", (2.6, 2.6, 0.12), Vector((0, 0, 0)), k.pbr("ttp_edge", (0.05, 0.2, 0.6), 0.4))
    b10.plane("ttp_top", (2.6, 2.6), Vector((0, 0, 0.062)), b10.tex_mat("ttp_m", ttp_tex(), rough=0.35))
    k.box("ttp_chip", (0.4, 0.3, 0.1), Vector((-0.95, -1.0, 0.11)), blk)

    def ledm(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (0.3, 0.02, 0.02, 1)
        p.inputs["Emission Color"].default_value = (1.0, 0.1, 0.05, 1)
        p.inputs["Emission Strength"].default_value = 0.0
        return p
    k.box("ttp_led", (0.18, 0.12, 0.08), Vector((0.95, -1.05, 0.1)), k.node_mat("ttp_led", ledm))

    def glow(nt):
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (0.3, 0.9, 1.0, 1)
        e.inputs["Strength"].default_value = 0.0
        return e
    bpy.ops.mesh.primitive_torus_add(major_radius=1.05, minor_radius=0.035, location=(0, 0.05, 0.08),
                                     major_segments=64, minor_segments=8)
    bpy.context.object.data.materials.append(k.node_mat("ttp_glow", glow))
    for i in range(3):
        k.box("ttp_pin", (0.064, 0.064, 0.8), Vector(((i - 1) * 0.254, 1.12, -0.45)), gold)
    for o in [o for o in bpy.data.objects if o not in before]:
        o.parent = root
    root.location = PAD
    root.rotation_euler = (math.radians(TILT), 0, 0)
    k.box("ttp_post", (0.5, 0.5, PAD.z - 0.9), D + Vector((0, 0.9, (PAD.z + 0.9) / 2)), blk)
    for i, col in enumerate(((0.04, 0.04, 0.04), (0.85, 0.08, 0.05), (1.0, 0.8, 0.05))):
        a = Vector((D.x - 1.0 + (i - 1) * 0.254, D.y - 0.9, 0.9))
        e = Vector((b10.E.x - 0.2 - i * 0.254, 1.27 + 0.254 * 2, b10.TOP))
        b10.poly_wire(f"w_ttp{i}", b10.bez(a, a + Vector((0, -0.4, 1.4)), e + Vector((0, 0.8, 1.6)), e), col, r=0.05)


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
    for name, x, col in (("led_b", 1.0, (0.1, 0.35, 1.0)),):
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
            (ENC + Vector((0.4, 1.4, 0)), (0.95, 0.95, 0.95)), (MB + Vector((1.0, 1.3, 0.9)), (0.1, 0.35, 0.95)),
            (MB + Vector((3.0, 1.0, 0.9)), (0.4, 0.2, 0.7))]
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
    build_touch()
    build_controls()

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
    pty = Vector((1.2, 1.4, 2.4))                     # pad + OLED + LED (count)
    game = Vector((1.6, -0.3, 1.4))                   # OLED + touch pad + knob + LED
    kn = Vector((0.6, -3.6, 1.6))                     # knob + OLED
    cams = [
        cam("s0", [(Sh[0], Vector((2.6, -15, 19)), game), (Sh[1], Vector((2.0, -13.5, 17.5)), game)], 35, game, 5.6),
        cam("s1", [(Sh[1], Vector((0.8, -12, 25)), mid1), (Sh[2], Vector((0.8, -11, 23)), mid1)], 32, mid1, 8.0),
        cam("s2", [(Sh[2], PADC + Vector((2.4, -8.0, 6.0)), PADC), (Sh[3], PADC + Vector((1.4, -7.0, 5.2)), PADC)], 42, PADC, 2.8),
        cam("s3", [(Sh[3], kn + Vector((-2.0, -13.0, 13.5)), kn + Vector((0, 2.6, 0.6))),
                   (Sh[4], kn + Vector((-1.0, -12.0, 12.5)), kn + Vector((0, 2.6, 0.6)))], 36, kn, 4.0),
        cam("s4", [(Sh[4], Vector((0.8, -15, 19)), game), (Sh[5], Vector((1.8, -13.5, 17)), game)], 35, game, 5.6),
        cam("s5", [(Sh[5], pty + Vector((-3.0, -13.0, 9.0)), pty), (Sh[6], pty + Vector((-1.6, -11.5, 8.0)), pty)], 36, pty, 4.0),
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
        on = led(ff)
        bpy.data.materials["led_b"].node_tree.nodes["P"].inputs["Emission Strength"].default_value = 12.0 if on else 0.0
        bpy.data.objects["led_b_glow"].data.energy = 8.0 if on else 0.0
        t = touching(ff)
        bpy.data.materials["ttp_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 30.0 if t else 0.0
        bpy.data.materials["ttp_glow"].node_tree.nodes["Emission"].inputs["Strength"].default_value = 4.0 if t else 0.0
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
