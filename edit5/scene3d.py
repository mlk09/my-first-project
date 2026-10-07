#!/usr/bin/env python3
"""3D product-demo for the ESP32 water-level short (procedural Blender, no assets).

A clear acrylic tank fills from a tap; an HC-SR04 on a bridge over the tank pings the
surface; an ESP32 on a breadboard drives 3 LEDs (green/yellow/red), a buzzer and a 0.96"
OLED that counts the % up. Bright studio look, slow camera moves, one camera per shot.
24 fps (like the reference). Run: python3 edit5/scene3d.py [--preview] [--step N]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "edit2"))
import scene3d as k  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

FRAMES = os.path.join(HERE, "work", "frames3d")
OLED = os.path.join(HERE, "work", "oled")
FPS = 24
# shot starts (frames). Last shot runs to END.
SHOTS = [0, 41, 82, 123, 164, 205, 246, 300]
END = 336
TANK_H, TANK_IN = 2.4, 0.84
FILL0, FILL1 = 30, 240           # tap runs from FILL0 to FILL1


def pct(f):
    """Water level % over time: 8 % idle, rises to 100 % at FILL1, eased near the top."""
    if f <= FILL0:
        return 8.0
    if f >= FILL1:
        return 100.0
    u = (f - FILL0) / (FILL1 - FILL0)
    return 8 + 92 * (1 - (1 - u) ** 1.6)


def build_world(sc):
    w = bpy.data.worlds.new("studio")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.12, 0.15, 0.22, 1)
    bg.inputs["Strength"].default_value = 0.6


def glass(name, col=(0.95, 0.98, 1.0), ior=1.49, rough=0.02):
    def b(nt):
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Transmission Weight"].default_value = 1.0
        p.inputs["Roughness"].default_value = rough
        p.inputs["IOR"].default_value = ior
        return p
    return k.node_mat(name, b)


def oled_mat():
    def b(nt):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "oled_tex"
        tex.image = bpy.data.images.load(os.path.join(OLED, "008.png"))
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Strength"].default_value = 1.6
        nt.links.new(tex.outputs["Color"], e.inputs["Color"])
        return e
    return k.node_mat("oled", b)


def led(name, loc, col, on_frame):
    lens_off = k.pbr(name + "_off", tuple(c * 0.35 for c in col), rough=0.2)
    m = k.pbr(name + "_m", tuple(c * 0.5 for c in col), rough=0.15, em=col, ems=0.0)
    k.cyl(name + "_body", 0.1, 0.22, loc + Vector((0, 0, 0.11)), m, verts=32)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=loc + Vector((0, 0, 0.22)))
    dome = bpy.context.object
    bpy.ops.object.shade_smooth()
    dome.data.materials.append(m)
    em = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    k.interp("CONSTANT")
    for f, v in ((0, 0.0), (on_frame, 6.0)):
        em.default_value = v
        em.keyframe_insert("default_value", frame=f)
    k.interp("BEZIER")
    bpy.ops.object.light_add(type="POINT", location=loc + Vector((0, -0.1, 0.35)))
    lt = bpy.context.object
    lt.data.color = col
    lt.data.shadow_soft_size = 0.05
    k.interp("CONSTANT")
    for f, v in ((0, 0.0), (on_frame, 12.0)):
        lt.data.energy = v
        lt.data.keyframe_insert("energy", frame=f)
    k.interp("BEZIER")
    return lens_off


def hcsr04(loc):
    blue = k.pbr("sr_pcb", (0.02, 0.15, 0.55), rough=0.4)
    alu = k.pbr("sr_alu", (0.82, 0.83, 0.86), rough=0.25, metal=1.0)
    mesh = k.pbr("sr_mesh", (0.05, 0.05, 0.06), rough=0.7)
    k.box("sr_board", (1.1, 0.5, 0.05), loc, blue)
    for sx in (-0.28, 0.28):
        k.cyl("sr_can", 0.17, 0.26, loc + Vector((sx, 0, -0.15)), alu, verts=40)
        k.cyl("sr_face", 0.14, 0.02, loc + Vector((sx, 0, -0.285)), mesh, verts=40)
    k.box("sr_xtal", (0.16, 0.08, 0.05), loc + Vector((0, 0.12, -0.05)), alu)
    for i in range(4):
        k.box("sr_pin", (0.03, 0.03, 0.18), loc + Vector((-0.12 + i * 0.08, 0.22, 0.1)), alu)


def esp32(loc):
    pcb = k.pbr("esp_pcb", (0.03, 0.03, 0.035), rough=0.4)
    shield = k.pbr("esp_shield", (0.75, 0.76, 0.78), rough=0.2, metal=1.0)
    gold = k.pbr("esp_gold", (0.9, 0.72, 0.3), rough=0.25, metal=1.0)
    k.box("esp_board", (1.0, 2.0, 0.06), loc + Vector((0, 0, 0.32)), pcb)
    k.box("esp_wroom", (0.62, 0.72, 0.07), loc + Vector((0, 0.45, 0.39)), shield)
    k.box("esp_ant", (0.62, 0.3, 0.02), loc + Vector((0, 0.92, 0.36)), k.pbr("esp_ant_m", (0.05, 0.05, 0.05), 0.3))
    k.box("esp_usb", (0.28, 0.2, 0.1), loc + Vector((0, -1.0, 0.38)), shield)
    for s in (-1, 1):
        k.box("esp_hdr", (0.08, 1.8, 0.25), loc + Vector((s * 0.45, 0, 0.17)), pcb)
        for i in range(15):
            k.box("esp_pin", (0.03, 0.03, 0.05), loc + Vector((s * 0.45, -0.84 + i * 0.12, 0.37)), gold)
    k.cyl("esp_led", 0.03, 0.02, loc + Vector((0.3, -0.7, 0.36)), k.emit("esp_bl", (0.2, 0.5, 1.0), 1.4))
    k.text("esp_lbl", "ESP32", 0.13, loc + Vector((0, 0.1, 0.36)), [k.emit("esp_t", (0.9, 0.9, 0.9), 1.0)],
           extrude=0.0, rot=(0, 0, math.radians(90)))


def wire(name, pts, col, r=0.03):
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
    o.data.materials.append(k.pbr(name + "m", col, rough=0.4))


def build(sc):
    build_world(sc)
    # table: warm light-grey matte with a soft gradient sweep behind
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    bpy.context.object.data.materials.append(k.pbr("table", (0.32, 0.3, 0.28), rough=0.35))
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 12, 0), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(k.pbr("sweep", (0.06, 0.09, 0.16), rough=0.9))
    k.area("key", (-4, -5, 7), (0, 0, 1), 1100, 4)
    k.area("fill", (5, -4, 3), (0, 0, 1), 250, 6, (0.9, 0.95, 1.0))
    k.area("rim", (2, 5, 5), (0, 0, 1.5), 1400, 3, (0.4, 0.7, 1.0))

    # ---- acrylic tank (square, open top) + water + tap
    T = Vector((0.4, 0.6, 0))
    bpy.ops.mesh.primitive_cube_add(size=1, location=T + Vector((0, 0, TANK_H / 2)))
    tank = bpy.context.object
    tank.scale = (1.9, 1.9, TANK_H)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for poly in tank.data.polygons:
        poly.select = poly.normal.z > 0.9
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    sol = tank.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.05
    bev = tank.modifiers.new("bev", "BEVEL")
    bev.width = 0.02
    bev.segments = 2
    tank.data.materials.append(glass("acrylic"))
    # level marks on the tank front
    for i, p in enumerate((50, 90)):
        z = 0.06 + (TANK_H - 0.2) * p / 100
        k.box(f"mark{i}", (0.25, 0.01, 0.02), T + Vector((0.95 - 0.13, -0.98, z)),
              k.emit(f"markm{i}", (1.0, 0.75, 0.1) if p == 50 else (1.0, 0.15, 0.1), 1.3))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    water = bpy.context.object
    water.scale = (1.9 - 0.14, 1.9 - 0.14, 1)
    bpy.ops.object.transform_apply(location=True, scale=True)
    water.location = T + Vector((0, 0, 0.06))
    water.data.materials.append(glass("water", (0.15, 0.55, 1.0), ior=1.33, rough=0.03))
    k.interp("LINEAR")
    for f in range(0, END + 1, 4):
        water.scale = (1, 1, max(0.02, (TANK_H - 0.2) * pct(f) / 100))
        water.keyframe_insert("scale", frame=f)
    k.interp("BEZIER")
    # tap + falling stream
    chrome = k.pbr("chrome", (0.9, 0.9, 0.92), rough=0.08, metal=1.0)
    k.cyl("tap_post", 0.08, 1.6, T + Vector((-1.25, 0.6, TANK_H + 0.2)), chrome)
    k.cyl("tap_arm", 0.07, 1.0, T + Vector((-0.8, 0.6, TANK_H + 1.0)), chrome, rot=(0, math.radians(90), 0))
    k.cyl("tap_nose", 0.08, 0.25, T + Vector((-0.32, 0.6, TANK_H + 0.9)), chrome)
    stream = k.cyl("stream", 0.06, 1, Vector((0, 0, 0)), glass("stream_m", (0.7, 0.9, 1.0), 1.33, 0.05), verts=24)
    stream.location = T + Vector((-0.32, 0.6, 0))
    k.interp("LINEAR")
    for f in range(0, END + 1, 4):
        top = TANK_H + 0.78
        bottom = 0.06 + (TANK_H - 0.2) * pct(f) / 100
        stream.scale = (1, 1, top - bottom)
        stream.location.z = (top + bottom) / 2
        stream.keyframe_insert("scale", frame=f)
        stream.keyframe_insert("location", frame=f)
    k.interp("BEZIER")
    k.show(stream, [(FILL0, FILL1)])

    # ---- sensor bridge over the tank
    br = k.pbr("bridge", (0.1, 0.1, 0.12), rough=0.5)
    k.box("bridge", (2.3, 0.18, 0.08), T + Vector((0, -0.25, TANK_H + 0.06)), br)
    hcsr04(T + Vector((0.25, -0.25, TANK_H + 0.02)))
    # ultrasonic pings: rings travelling down to the water surface
    for i in range(8):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.015, location=(0, 0, 0))
        ring = bpy.context.object
        ring.data.materials.append(k.emit(f"ping{i}", (0.2, 0.75, 1.0), 1.4))
        f0 = 44 + i * 5
        k.interp("LINEAR")
        surf = 0.06 + (TANK_H - 0.2) * pct(f0 + 10) / 100
        for f, z, s in ((f0, TANK_H - 0.3, 0.6), (f0 + 10, surf + 0.02, 2.2)):
            ring.location = T + Vector((0.25 + 0.28 * (i % 2 * 2 - 1), -0.25, z))
            ring.scale = (s, s, s)
            ring.keyframe_insert("location", frame=f)
            ring.keyframe_insert("scale", frame=f)
        k.interp("BEZIER")
        k.show(ring, [(f0, f0 + 11)])

    # ---- breadboard + ESP32 + LEDs + OLED + buzzer
    B = Vector((-0.9, -2.0, 0))
    k.box("breadboard", (3.6, 1.8, 0.2), B + Vector((0, 0, 0.1)), k.pbr("bb", (0.93, 0.92, 0.88), rough=0.6))
    for s in (-1, 1):
        k.box("rail_r", (3.4, 0.03, 0.005), B + Vector((0, s * 0.78, 0.201)), k.emit("rr", (0.8, 0.1, 0.1), 0.6))
    esp32(B + Vector((-1.15, 0.0, 0)))
    c_g, c_y, c_r = (0.1, 1.0, 0.25), (1.0, 0.75, 0.05), (1.0, 0.08, 0.05)
    f_y = next(f for f in range(END) if pct(f) >= 50)
    f_r = next(f for f in range(END) if pct(f) >= 90)
    for i, (col, on) in enumerate(((c_g, 0), (c_y, f_y), (c_r, f_r))):
        led(f"led{i}", B + Vector((-0.2 + i * 0.32, -0.45, 0.2)), col, on)
    # OLED module
    O = B + Vector((1.05, -0.15, 0.2))
    k.box("oled_pcb", (0.95, 0.12, 0.9), O + Vector((0, 0, 0.5)), k.pbr("oled_pcb_m", (0.02, 0.18, 0.55), rough=0.4))
    bpy.ops.mesh.primitive_plane_add(size=1, location=O + Vector((0, -0.065, 0.55)), rotation=(math.radians(90), 0, 0))
    scr = bpy.context.object
    scr.scale = (0.84, 0.42, 1)
    scr.data.materials.append(oled_mat())
    k.box("oled_frame", (0.9, 0.02, 0.5), O + Vector((0, -0.055, 0.55)), k.pbr("oled_glass", (0.01, 0.01, 0.01), rough=0.1))
    scr.location.y -= 0.01
    k.cyl("buzzer", 0.18, 0.22, B + Vector((1.25, 0.55, 0.31)), k.pbr("buzz_m", (0.03, 0.03, 0.03), rough=0.5))
    # jumper wires
    cols = [(0.9, 0.5, 0.05), (0.1, 0.4, 0.95), (0.95, 0.85, 0.1), (0.55, 0.2, 0.75)]
    for i, col in enumerate(cols):
        wire(f"w{i}", [B + Vector((-0.75, -0.6 + i * 0.12, 0.4)), Vector((-1.5 - i * 0.06, -0.9, 1.4)),
                       Vector((-1.0, -0.6, TANK_H + 0.5 + i * 0.06)), T + Vector((0.13 + i * 0.08, -0.03, TANK_H + 0.12))], col)
    for i, col in enumerate(cols[:2]):
        wire(f"wo{i}", [B + Vector((-0.75, 0.3 + i * 0.12, 0.4)), B + Vector((0.2, 0.7, 0.9)),
                        O + Vector((-0.2 + i * 0.12, 0.05, 1.0))], col)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3, location=B + Vector((-1.15, -2.4, 0.38)),
                                        rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(k.pbr("usb_cable", (0.02, 0.02, 0.02), rough=0.5))

    # ---- cameras (one per shot)
    tank_top = T + Vector((0, 0, TANK_H))
    oled_c = O + Vector((0, -0.06, 0.55))
    leds_c = B + Vector((0.12, -0.45, 0.3))
    S = SHOTS
    cams = [
        k.camera("s1", [(S[0], Vector((-4.2, -6.6, 3.8)), Vector((-0.2, -0.4, 1.2))),
                        (S[1], Vector((-3.4, -6.2, 3.4)), Vector((-0.2, -0.4, 1.2)))], lens_keys=[(S[0], 30)]),
        k.camera("s2", [(S[1], tank_top + Vector((-1.6, -2.6, 0.8)), tank_top + Vector((0.2, 0.1, -0.5))),
                        (S[2], tank_top + Vector((-1.2, -2.3, 0.5)), tank_top + Vector((0.2, 0.1, -0.6)))], lens_keys=[(S[1], 32)]),
        k.camera("s3", [(S[2], T + Vector((1.6, -3.4, 0.6)), T + Vector((0, 0, 1.0))),
                        (S[3], T + Vector((0.9, -3.2, 0.9)), T + Vector((0, 0, 1.3)))], lens_keys=[(S[2], 28)]),
        k.camera("s4", [(S[3], oled_c + Vector((0.35, -2.6, 0.5)), oled_c + Vector((0, 0, -0.1))),
                        (S[4], oled_c + Vector((-0.2, -2.2, 0.35)), oled_c + Vector((0, 0, -0.1)))], lens_keys=[(S[3], 40)]),
        k.camera("s5", [(S[4], leds_c + Vector((-1.2, -2.4, 1.0)), leds_c + Vector((0.3, 0, 0.1))),
                        (S[5], leds_c + Vector((0.6, -2.2, 0.9)), leds_c + Vector((0.3, 0, 0.1)))], lens_keys=[(S[4], 35)]),
        k.camera("s6", [(S[5], tank_top + Vector((0.9, -2.4, 0.2)), tank_top + Vector((0, 0, -0.4))),
                        (S[6], tank_top + Vector((0.5, -2.0, 0.35)), tank_top + Vector((0, 0, -0.3)))], lens_keys=[(S[5], 30)]),
        k.camera("s7", [(S[6], Vector((3.0, -6.6, 3.0)), Vector((-0.2, -0.4, 1.2))),
                        (S[7], Vector((2.0, -6.2, 3.3)), Vector((-0.2, -0.4, 1.2)))], lens_keys=[(S[6], 30)]),
        k.camera("s8", [(S[7], Vector((-1.6, -6.6, 3.0)), Vector((-0.2, -0.4, 1.3))),
                        (END, Vector((-0.9, -6.0, 2.8)), Vector((-0.2, -0.4, 1.3)))], lens_keys=[(S[7], 30)]),
    ]
    for f, cam in zip(S, cams):
        sc.timeline_markers.new(cam.name, frame=f).camera = cam
    sc.camera = cams[0]

    imgs = {}

    def upd(scene, *_):
        p = int(round(pct(scene.frame_current)))
        if p not in imgs:
            imgs[p] = bpy.data.images.load(os.path.join(OLED, f"{p:03d}.png"), check_existing=True)
        bpy.data.materials["oled"].node_tree.nodes["oled_tex"].image = imgs[p]
    bpy.app.handlers.frame_change_pre.append(upd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=END - 1)
    args = ap.parse_args(sys.argv[1:])
    os.makedirs(FRAMES, exist_ok=True)
    sc = k.reset()
    sc.render.fps = FPS
    build(sc)
    k.setup_render(sc, args.preview)
    cy = sc.cycles
    cy.max_bounces, cy.transmission_bounces, cy.glossy_bounces, cy.transparent_max_bounces = 10, 8, 3, 8
    cy.samples = 8 if args.preview else 10
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.render.filepath = os.path.join(FRAMES, "")
    sc.frame_start, sc.frame_end, sc.frame_step = args.start, args.end, args.step
    bpy.ops.render.render(animation=True)
