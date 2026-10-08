#!/usr/bin/env python3
"""Photoreal 'Tap to Light' scene (Blender, procedural): green cutting mat, full-size breadboard,
ESP32 DevKit V1 with power/onboard LEDs, four 5 mm LEDs (R/Y/G/B) with resistors and jumpers,
white USB cable, phone on a stand running our App Inventor style controller, a blurred neon
'IoT LAB' sign behind. LEDs follow timeline.leds(); room dims for party mode. 24 fps, 336 frames.
Run: python3 edit7/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
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
from timeline import FPS, N, SHOTS, leds, power, dim  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
APP = os.path.join(HERE, "work", "app")
TEX = os.path.join(HERE, "work", "tex")
TOP = 0.38                                   # breadboard top surface
E = Vector((-2.2, 0, TOP + 0.27))            # ESP32 pcb centre
LED_X = [-0.2, 0.5, 1.2, 1.9]
LED_COL = [(1.0, 0.05, 0.03), (1.0, 0.62, 0.02), (0.1, 1.0, 0.15), (0.05, 0.25, 1.0)]
PH = Vector((0.7, 3.1, 0))                   # phone stand


def wire(name, pts, col, r=0.022, mat=None):
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


def key_switch(sock, states, on_val):
    """CONSTANT keyframes on a socket/property for a per-frame bool list."""
    k.interp("CONSTANT")
    prev = None
    for f in range(-1, N + 1):
        v = states(max(f, 0))
        if v != prev:
            sock.default_value = on_val if v else 0.0
            sock.keyframe_insert("default_value", frame=f)
            prev = v
    k.interp("BEZIER")


def key_light(light, states, on_val):
    k.interp("CONSTANT")
    prev = None
    for f in range(-1, N + 1):
        v = states(max(f, 0))
        if v != prev:
            light.data.energy = on_val if v else 0.0
            light.data.keyframe_insert("energy", frame=f)
            prev = v
    k.interp("BEZIER")


def build_breadboard():
    k.box("bb_body", (6.6, 2.2, TOP), Vector((0, 0, TOP / 2)), k.pbr("bb_side", (0.9, 0.89, 0.85), rough=0.55))
    plane("bb_top", (6.6, 2.2), Vector((0, 0, TOP + 0.002)), tex_mat("bb_top_m", os.path.join(TEX, "breadboard.png"), rough=0.6))


def build_esp32():
    pcb = k.pbr("esp_pcb", (0.015, 0.015, 0.018), rough=0.35)
    blk = k.pbr("esp_blk", (0.02, 0.02, 0.022), rough=0.45)
    steel = k.pbr("esp_steel", (0.8, 0.81, 0.83), rough=0.18, metal=1.0)
    gold = k.pbr("esp_gold", (0.95, 0.72, 0.3), rough=0.25, metal=1.0)
    k.box("esp_board", (2.1, 1.0, 0.05), E, pcb)
    for sy in (-0.41, 0.41):                                   # headers into the breadboard
        k.box("esp_hdr", (1.5, 0.1, 0.1), Vector((-2.3, sy, TOP + 0.05)), blk)
        for i in range(15):
            x = -3.0 + i * 0.1
            k.box("esp_pin", (0.024, 0.024, 0.32), Vector((x, sy, TOP + 0.14)), gold)
            k.box("esp_pad", (0.06, 0.06, 0.012), Vector((x, sy, E.z + 0.03)), gold)
    k.box("esp_mod", (0.72, 0.98, 0.04), E + Vector((0.66, 0, 0.045)), blk)       # WROOM substrate
    k.box("esp_shield", (0.66, 0.7, 0.07), E + Vector((0.6, 0, 0.1)), steel)
    k.text("esp_lbl", "ESP-WROOM-32", 0.075, E + Vector((0.6, 0.12, 0.137)), [k.pbr("etch", (0.45, 0.46, 0.48), 0.5, 1.0)],
           extrude=0.0, rot=(0, 0, math.radians(90)))
    for i in range(5):                                         # antenna meander
        k.box("esp_ant", (0.03, 0.6 if i % 2 == 0 else 0.03, 0.006), E + Vector((0.9 + i * 0.03, 0.0, 0.071)), gold)
    k.box("esp_usb", (0.22, 0.3, 0.12), E + Vector((-1.0, 0, 0.09)), steel)
    k.box("esp_cp2102", (0.18, 0.18, 0.04), E + Vector((-0.6, 0.15, 0.045)), blk)
    k.box("esp_reg", (0.2, 0.14, 0.06), E + Vector((-0.55, -0.25, 0.055)), blk)
    for sy in (-0.33, 0.33):                                   # EN / BOOT buttons
        k.box("esp_btn", (0.16, 0.16, 0.06), E + Vector((-0.78, sy, 0.055)), steel)
        k.cyl("esp_btn_cap", 0.045, 0.05, E + Vector((-0.78, sy, 0.1)), blk, verts=16)
    k.text("esp_silk", "ESP32 DEVKIT V1", 0.07, E + Vector((-0.22, -0.32, 0.027)), [k.emit("silk", (0.85, 0.85, 0.85), 0.9)],
           extrude=0.0, rot=(0, 0, 0))
    pw = k.pbr("pwr_led", (0.5, 0.02, 0.02), rough=0.2, em=(1.0, 0.04, 0.02), ems=0.0)
    bl = k.pbr("blue_led", (0.02, 0.05, 0.4), rough=0.2, em=(0.1, 0.35, 1.0), ems=0.0)
    k.box("esp_pwr", (0.06, 0.04, 0.03), E + Vector((-0.35, 0.3, 0.04)), pw)
    k.box("esp_bl", (0.06, 0.04, 0.03), E + Vector((-0.35, -0.08, 0.04)), bl)
    key_switch(pw.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], power, 25.0)
    key_switch(bl.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"],
               lambda f: power(f) and (f // 8) % 2 == 0 and f < 110, 25.0)
    for name, pos, col, states in (("pwr_glow", (-0.35, 0.3), (1, 0.05, 0.03), power),
                                   ("bl_glow", (-0.35, -0.08), (0.1, 0.35, 1), lambda f: power(f) and (f // 8) % 2 == 0 and f < 110)):
        bpy.ops.object.light_add(type="POINT", location=E + Vector((pos[0], pos[1], 0.12)))
        g = bpy.context.object
        g.name = name
        g.data.color = col
        g.data.shadow_soft_size = 0.03
        key_light(g, states, 0.6)
    # white USB cable to the left edge of the mat
    k.box("usb_plug", (0.3, 0.26, 0.14), E + Vector((-1.24, 0, 0.09)), k.pbr("plug", (0.92, 0.92, 0.9), rough=0.4))
    wire("usb_cable", [E + Vector((-1.38, 0, 0.09)), E + Vector((-1.9, 0.2, 0.0)), Vector((-5.2, 1.6, 0.08)),
                       Vector((-8.0, 5.0, 0.08))], (0.92, 0.92, 0.9), r=0.065)


def build_leds():
    leg = k.pbr("leg", (0.8, 0.8, 0.82), 0.2, 1.0)
    out = []
    for i, (x, col) in enumerate(zip(LED_X, LED_COL)):
        def b(nt, col=col):
            p = nt.nodes.new("ShaderNodeBsdfPrincipled")
            p.inputs["Base Color"].default_value = (*[0.08 + 0.8 * c for c in col], 1)
            p.inputs["Roughness"].default_value = 0.08
            p.inputs["Transmission Weight"].default_value = 0.6
            p.inputs["IOR"].default_value = 1.5
            p.inputs["Emission Color"].default_value = (*col, 1)
            p.inputs["Emission Strength"].default_value = 0.0
            return p
        m = k.node_mat(f"led{i}", b)
        c = Vector((x + 0.05, 0.21, TOP))
        for dx, h in ((-0.05, 0.42), (0.05, 0.36)):
            k.box("led_leg", (0.018, 0.018, h), c + Vector((dx, 0, h / 2)), leg)
        k.cyl("led_rim", 0.135, 0.035, c + Vector((0, 0, 0.36)), m, verts=32)
        k.cyl("led_body", 0.12, 0.2, c + Vector((0, 0, 0.47)), m, verts=32)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=c + Vector((0, 0, 0.57)), segments=32, ring_count=16)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(m)
        bpy.ops.object.light_add(type="POINT", location=c + Vector((0, -0.05, 0.55)))
        g = bpy.context.object
        g.data.color = col
        g.data.shadow_soft_size = 0.12
        key_switch(m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], lambda f, i=i: leds(f)[i], 3.2)
        key_light(g, lambda f, i=i: leds(f)[i], 24.0)
        # resistor: cathode column -> top power rail
        r0 = Vector((x + 0.1, 0.31, TOP))
        for yy in (0.31, 0.71):
            k.box("res_leg", (0.016, 0.016, 0.16), Vector((x + 0.1, yy, TOP + 0.08)), leg)
        wire(f"res_wire{i}", [Vector((x + 0.1, 0.31, TOP + 0.16)), Vector((x + 0.1, 0.51, TOP + 0.17)),
                              Vector((x + 0.1, 0.71, TOP + 0.16))], (0.8, 0.8, 0.82), r=0.009, mat=leg)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.2, location=r0 + Vector((0, 0.2, 0.17)),
                                            rotation=(math.radians(90), 0, 0), vertices=24)
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(k.pbr(f"res{i}", (0.78, 0.66, 0.48), rough=0.5))
        for j, bc in enumerate(((0.45, 0.25, 0.08), (0.8, 0.1, 0.05), (0.1, 0.1, 0.1), (0.85, 0.65, 0.2))):
            k.cyl("band", 0.048, 0.02, r0 + Vector((0, 0.13 + j * 0.04, 0.17)), k.pbr(f"band{i}{j}", bc, 0.4),
                  rot=(math.radians(90), 0, 0), verts=24)
        out.append(c + Vector((0, 0, 0.5)))
        # jumper: ESP32 GPIO -> LED anode column
        jc = [(1.0, 0.45, 0.05), (1.0, 0.85, 0.05), (0.1, 0.7, 0.2), (0.1, 0.35, 0.95)][i]
        a = Vector((-2.8 + i * 0.2, 0.51, TOP))
        bend = Vector((x, 0.11, TOP))
        wire(f"jmp{i}", [a, a + Vector((0, 0.05, 0.3 + 0.05 * i)), (a + bend) / 2 + Vector((0, 0.3, 0.45 + 0.05 * i)),
                         bend + Vector((0, -0.05, 0.28)), bend], jc, r=0.024)
    wire("gnd", [Vector((-1.6, 0.51, TOP)), Vector((-1.5, 0.6, 0.85)), Vector((-1.0, 0.71, TOP))], (0.04, 0.04, 0.04), r=0.024)
    return out


def build_phone():
    blk = k.pbr("phone_body", (0.025, 0.025, 0.03), rough=0.22, metal=0.5)
    stand = k.pbr("stand_m", (0.12, 0.12, 0.13), rough=0.35, metal=0.8)
    k.box("stand_base", (2.0, 1.6, 0.1), PH + Vector((0, 0.4, 0.05)), stand)
    k.box("stand_lip", (2.0, 0.25, 0.35), PH + Vector((0, -0.3, 0.2)), stand)
    root = bpy.data.objects.new("phone_root", None)
    bpy.context.collection.objects.link(root)
    root.location = PH + Vector((0, -0.1, 0.25))
    parts = [k.box("phone", (2.5, 0.16, 5.4), PH + Vector((0, 0, 2.95)), blk)]

    def b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "app_tex"
        tex.image = bpy.data.images.load(os.path.join(APP, "0000.png"))
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 1.0
        nt.links.new(tex.outputs["Color"], e.inputs["Color"])
        return e
    parts.append(plane("screen", (2.36, 5.12), PH + Vector((0, -0.085, 2.95)), k.node_mat("app", b),
                       rot=(math.radians(90), 0, 0)))
    parts.append(k.cyl("cam_hole", 0.05, 0.02, PH + Vector((0, -0.085, 5.5)), k.pbr("lens", (0, 0, 0), 0.1),
                       rot=(math.radians(90), 0, 0), verts=16))
    bpy.context.view_layer.update()
    for o in parts:
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    root.rotation_euler = (math.radians(-12), 0, math.radians(-14))
    bpy.context.view_layer.update()
    return parts[1].matrix_world.translation.copy()


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    m = plane("mat", (40, 40), Vector((0, 0, 0)), tex_mat("mat_m", os.path.join(TEX, "mat.png"), rough=0.75, scale=4.0, bump=0.05))
    plane("wall", (60, 30), Vector((0, 12, 6)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=(math.radians(90), 0, 0))
    m.name = "mat"
    sign = k.text("sign", "IoT LAB", 1.5, Vector((-0.5, 11.5, 7.5)), [k.emit("neon", (0.2, 0.9, 1.0), 1.4)], extrude=0.05)
    sign.name = "sign"
    k.text("sign2", "</>", 1.0, Vector((5.5, 11.5, 5.0)), [k.emit("neon2", (1.0, 0.25, 0.8), 1.4)], extrude=0.05)
    key = k.area("key", (-4, -5, 9), (0, 0, 0.5), 1400, 4)
    fill = k.area("fill", (6, -4, 5), (0, 0, 1), 450, 6, col=(0.85, 0.9, 1.0))
    rim = k.area("rim", (-6, 6, 4), (0, 0, 1), 600, 3, col=(0.6, 0.4, 1.0))
    k.interp("BEZIER")
    for f in range(0, N + 1, 2):
        n = dim(f)
        bg.inputs["Strength"].default_value = 0.35 * (1 - 0.85 * n)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
        for lt, e in ((key, 1400), (fill, 450)):
            lt.data.energy = e * (1 - 0.88 * n)
            lt.data.keyframe_insert("energy", frame=f)

    build_breadboard()
    build_esp32()
    led_pts = build_leds()
    scr = build_phone()

    def cam(name, keys, lens, focus, fstop):
        c = k.camera(name, keys, lens_keys=[(keys[0][0], lens)])
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        fo = bpy.data.objects.new(name + "_f", None)
        bpy.context.collection.objects.link(fo)
        fo.location = focus
        c.data.dof.focus_object = fo
        return c

    Sh = SHOTS
    ledc = (led_pts[1] + led_pts[2]) / 2
    esp = E + Vector((0.1, 0, 0.1))
    mid = Vector((-0.3, 0.8, 1.9))
    cams = [
        cam("s0", [(Sh[0], Vector((-2.9, -7.6, 3.6)), mid + Vector((-0.2, 0, 0.2))), (Sh[1], Vector((-2.3, -6.8, 3.3)), mid + Vector((-0.2, 0, 0.2)))], 34, ledc, 2.8),
        cam("s1", [(Sh[1], esp + Vector((-1.5, -2.7, 1.5)), esp + Vector((0.3, 0.1, -0.1))), (Sh[2], esp + Vector((0.3, -2.5, 1.3)), esp + Vector((0.3, 0.1, -0.1)))], 40, esp, 1.8),
        cam("s2", [(Sh[2], scr + Vector((0.4, -5.6, 0.4)), scr), (Sh[3], scr + Vector((0.2, -4.7, 0.3)), scr)], 38, scr, 2.8),
        cam("s3", [(Sh[3], Vector((-2.2, -7.0, 3.0)), mid + Vector((0, 0, -0.1))),
                   (Sh[4], Vector((-1.5, -6.5, 2.8)), mid + Vector((0, 0, -0.1)))], 36, ledc, 3.2),
        cam("s4", [(Sh[4], Vector((-1.4, -2.0, 1.0)), Vector((0.6, 0.2, 0.75))),
                   (Sh[5], Vector((0.4, -2.1, 0.95)), Vector((1.6, 0.2, 0.75)))], 40, ledc, 1.4),
        cam("s5", [(Sh[5], Vector((4.5, -7.5, 5.0)), mid + Vector((0, 0, -0.4))),
                   (Sh[6], Vector((2.0, -8.6, 4.2)), mid + Vector((0, 0, -0.4)))], 32, ledc, 2.4),
        cam("s6", [(Sh[6], Vector((-2.4, -7.0, 3.4)), mid), (N, Vector((-2.9, -8.0, 3.8)), mid)], 34, ledc, 2.8),
    ]
    for f, c in zip(Sh, cams):
        sc.timeline_markers.new(c.name, frame=f).camera = c
    sc.camera = cams[0]

    imgs = {}

    def upd(scene, *_):
        f = scene.frame_current
        if f not in imgs:
            imgs[f] = bpy.data.images.load(os.path.join(APP, f"{min(max(f, 0), N - 1):04d}.png"), check_existing=True)
        bpy.data.materials["app"].node_tree.nodes["app_tex"].image = imgs[f]
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
