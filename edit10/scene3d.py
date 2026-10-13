#!/usr/bin/env python3
"""Photoreal ESP32 + 1.3" SH1106 OLED over I2C (Blender, procedural, units = cm). Half breadboard
on the green mat, ESP32 DevKit V1, OLED module with a per-frame screen texture, four jumpers
(GND black, VCC red, SCL yellow, SDA blue) and glowing data pulses that run along SDA/SCL
whenever timeline.busy(). 24 fps, 384 frames.
Run: python3 edit10/scene3d.py [--preview] [--start N --end M --step S] [--out DIR]
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
from timeline import FPS, N, SHOTS, busy  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
TEX = os.path.join(HERE, "work", "tex")
OLED = os.path.join(HERE, "work", "oled")
TOP = 0.9                                     # breadboard top
E = Vector((-1.75, 0, TOP + 0.95))            # ESP32 pcb centre (on header pins)
M = Vector((2.35, 0.05, TOP + 1.0))           # OLED module pcb centre
R90 = (math.radians(90), 0, 0)


def bez(p0, p1, p2, p3, n=48):
    return [p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3
            for t in (i / (n - 1) for i in range(n))]


def poly_wire(name, pts, col, r=0.055):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q.x, q.y, q.z, 1)
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(k.pbr(name + "m", col, rough=0.35))
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


def key_bool(target, prop, states, on_val, off_val=0.0):
    k.interp("CONSTANT")
    prev = None
    for f in range(-1, N + 1):
        v = states(max(f, 0))
        if v != prev:
            setattr(target, prop, on_val if v else off_val)
            target.keyframe_insert(prop, frame=f)
            prev = v
    k.interp("BEZIER")


def build_board():
    k.box("bb_body", (8.4, 5.6, TOP), Vector((0, 0, TOP / 2)), k.pbr("bb_side", (0.9, 0.89, 0.85), rough=0.55))
    plane("bb_top", (8.4, 5.6), Vector((0, 0, TOP + 0.003)), tex_mat("bb_top_m", os.path.join(TEX, "breadboard.png"), rough=0.6))
    pcb = k.pbr("esp_pcb", (0.015, 0.015, 0.018), rough=0.35)
    blk = k.pbr("esp_blk", (0.02, 0.02, 0.022), rough=0.45)
    steel = k.pbr("steel", (0.8, 0.81, 0.83), rough=0.18, metal=1.0)
    gold = k.pbr("gold", (0.95, 0.72, 0.3), rough=0.25, metal=1.0)
    # ESP32 DevKit V1 straddling the channel
    k.box("esp_board", (5.2, 2.8, 0.16), E, pcb)
    for sy in (-1.27, 1.27):
        k.box("esp_hdr", (3.9, 0.25, 0.25), Vector((E.x - 0.3, sy, TOP + 0.13)), blk)
        for i in range(15):
            x = E.x - 2.08 + i * 0.254
            k.box("esp_pin", (0.064, 0.064, 0.8), Vector((x, sy, TOP + 0.4)), gold)
            k.box("esp_pad", (0.15, 0.15, 0.03), Vector((x, sy, E.z + 0.09)), gold)
    k.box("esp_mod", (1.8, 2.5, 0.08), E + Vector((1.55, 0, 0.12)), blk)
    k.box("esp_shield", (1.55, 1.8, 0.28), E + Vector((1.45, 0, 0.28)), steel)
    k.text("esp_lbl", "ESP32", 0.36, E + Vector((1.45, 0.05, 0.43)), [k.pbr("etch", (0.4, 0.41, 0.43), 0.5, 1.0)],
           extrude=0.0, rot=(0, 0, 0))
    k.box("esp_usb", (0.6, 0.75, 0.3), E + Vector((-2.45, 0, 0.23)), steel)
    k.box("esp_chip", (0.45, 0.45, 0.1), E + Vector((-1.1, 0.4, 0.13)), blk)
    for sy in (-0.85, 0.85):
        k.box("esp_btn", (0.4, 0.35, 0.15), E + Vector((-2.0, sy, 0.15)), steel)
    k.text("esp_silk", "ESP32 DEVKIT V1", 0.17, E + Vector((-0.75, -0.75, 0.085)), [k.emit("silk", (0.85, 0.85, 0.85), 0.9)],
           extrude=0.0)
    pw = k.pbr("pwr_led", (0.5, 0.02, 0.02), rough=0.2, em=(1.0, 0.04, 0.02), ems=25.0)
    k.box("esp_pwr", (0.15, 0.1, 0.07), E + Vector((-1.6, -0.6, 0.12)), pw)
    bl = k.pbr("blue_led", (0.02, 0.05, 0.4), rough=0.2, em=(0.1, 0.35, 1.0), ems=0.0)
    k.box("esp_bl", (0.15, 0.1, 0.07), E + Vector((-1.6, 0.6, 0.12)), bl)
    key_bool(bl.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value",
             lambda f: busy(f) and (f // 3) % 2 == 0, 22.0)
    k.box("usb_plug", (0.8, 1.1, 0.55), E + Vector((-3.1, 0, 0.23)), k.pbr("plug", (0.05, 0.05, 0.05), 0.4))
    cable = bez(E + Vector((-3.5, 0, 0.23)), E + Vector((-6, 0.5, -0.5)), Vector((-12, 6, 0.3)), Vector((-20, 14, 0.3)))
    poly_wire("usb_cable", cable, (0.03, 0.03, 0.03), r=0.22)
    # SH1106 OLED module
    k.box("oled_pcb", (3.5, 3.6, 0.16), M, k.pbr("oled_edge", (0.08, 0.27, 0.62), 0.4))
    plane("oled_top", (3.5, 3.6), M + Vector((0, 0, 0.082)), tex_mat("oled_pcb_m", os.path.join(TEX, "oled_pcb.png"), 0.35))
    k.box("oled_glass", (3.45, 2.1, 0.14), M + Vector((0, -0.3, 0.15)), k.pbr("glass", (0.01, 0.01, 0.012), rough=0.05))

    def sb(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "oled_tex"
        tex.interpolation = "Closest"
        tex.image = bpy.data.images.load(os.path.join(OLED, "0000.png"))
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 2.2
        nt.links.new(tex.outputs["Color"], e.inputs["Color"])
        return e
    plane("oled_screen", (2.95, 1.48), M + Vector((0, -0.25, 0.225)), k.node_mat("oled_scr", sb))
    bpy.ops.object.light_add(type="AREA", location=M + Vector((0, -0.25, 0.6)))
    sl = bpy.context.object
    sl.data.size = 2.6
    sl.data.color = (0.75, 0.92, 1.0)
    sl.data.energy = 0.0
    k.interp("CONSTANT")
    for f, e in ((-1, 0.0), (6, 2.5)):
        sl.data.energy = e
        sl.data.keyframe_insert("energy", frame=f)
    k.interp("BEZIER")
    for i in range(4):                                         # OLED header pins into the breadboard
        x = M.x + (i - 1.5) * 0.254
        k.box("oled_pin", (0.064, 0.064, 1.0), Vector((x, M.y + 1.6, TOP + 0.5)), gold)
        k.box("oled_hdr", (0.25, 0.25, 0.25), Vector((x, M.y + 1.6, TOP + 0.13)), blk)
    # jumpers ESP32 -> OLED header: GND, VCC, SCL, SDA
    paths = {}
    for i, (name, col) in enumerate((("gnd", (0.04, 0.04, 0.04)), ("vcc", (0.85, 0.08, 0.05)),
                                     ("scl", (1.0, 0.8, 0.05)), ("sda", (0.1, 0.35, 0.95)))):
        a = Vector((E.x + 0.5 + i * 0.254, 1.27 + 0.254 * 2, TOP))
        b = Vector((M.x + (i - 1.5) * 0.254, M.y + 1.6 + 0.254 * 2, TOP))
        pts = bez(a, a + Vector((0, 0.2, 2.2 + 0.25 * i)), b + Vector((0, 0.3, 2.2 + 0.25 * i)), b)
        poly_wire(f"w_{name}", pts, col)
        paths[name] = pts
    return paths


def build_pulses(paths):
    """Glowing packets that slide along SDA and SCL while the bus is busy."""
    for name, col, phase in (("sda", (0.35, 0.65, 1.0), 0.0), ("scl", (1.0, 0.85, 0.2), 0.5)):
        pts = paths[name]
        m = k.emit(f"pulse_{name}", col, 1.4)
        for j in range(3):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=pts[0], segments=16, ring_count=8)
            o = bpy.context.object
            o.data.materials.append(m)
            bpy.ops.object.light_add(type="POINT", location=pts[0])
            lt = bpy.context.object
            lt.data.color = col
            lt.data.energy = 0.25
            lt.data.shadow_soft_size = 0.1
            k.interp("LINEAR")
            for f in range(-1, N + 1):
                u = ((max(f, 0) / 14.0) + j / 3 + phase) % 1.0
                p = pts[min(len(pts) - 1, int(u * (len(pts) - 1)))]
                for ob in (o, lt):
                    ob.location = p
                    ob.keyframe_insert("location", frame=f)
            k.interp("BEZIER")
            on = [(f, busy(f)) for f in range(N + 1)]
            k.interp("CONSTANT")
            prev = None
            for f, v in on:
                if v != prev:
                    for ob in (o, lt):
                        ob.hide_render = not v
                        ob.keyframe_insert("hide_render", frame=f)
                    prev = v
            k.interp("BEZIER")


def build(sc):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs["Strength"].default_value = 0.3
    plane("mat", (300, 300), Vector((0, 0, 0)), tex_mat("mat_m", os.path.join(TEX, "mat.png"), rough=0.75, scale=12.0, bump=0.05))
    plane("wall", (600, 300), Vector((0, 60, 60)), k.pbr("wall_m", (0.05, 0.055, 0.07), rough=0.8), rot=R90)
    k.area("key", (-30, -40, 70), (0, 0, 1), 60000, 35)
    k.area("fill", (45, -30, 40), (0, 0, 1), 20000, 40, col=(0.85, 0.9, 1.0))
    k.area("rim", (-35, 40, 30), (0, 0, 2), 25000, 25, col=(0.7, 0.4, 1.0))
    paths = build_board()
    build_pulses(paths)

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
    scr = M + Vector((0, -0.25, 0.23))
    mid = Vector((0.3, 0.3, 1.4))
    wires = Vector((0.4, 1.9, 2.4))
    cams = [
        cam("s0", [(Sh[0], scr + Vector((1.1, -7.0, 6.6)), scr), (Sh[1], scr + Vector((0.6, -6.0, 5.8)), scr)], 50, scr, 2.8),
        cam("s1", [(Sh[1], Vector((0.3, -7.5, 17)), mid), (Sh[2], Vector((0.3, -6.5, 15)), mid)], 35, mid, 5.6),
        cam("s2", [(Sh[2], Vector((-2.5, -7.0, 8.5)), wires), (Sh[3], Vector((2.5, -7.0, 8.0)), wires)], 42, wires, 2.8),
        cam("s3", [(Sh[3], scr + Vector((-0.6, -4.6, 4.8)), scr), (Sh[4], scr + Vector((0.3, -4.0, 4.3)), scr)], 50, scr, 2.8),
        cam("s4", [(Sh[4], scr + Vector((3.8, -4.6, 4.6)), scr), (Sh[5], scr + Vector((2.6, -4.8, 4.2)), scr)], 48, scr, 2.8),
        cam("s5", [(Sh[5], Vector((-5, -8.5, 7.5)), mid), (Sh[6], Vector((4, -9, 7.5)), mid)], 38, mid, 4.0),
        cam("s6", [(Sh[6], Vector((-1, -9, 9)), mid), (N, Vector((-1.5, -10.5, 10)), mid)], 38, mid, 4.0),
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
