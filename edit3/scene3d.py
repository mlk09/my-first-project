#!/usr/bin/env python3
"""Builds and renders the 3D animation for "Robot and the Haunted Bag".

Everything is modelled, shaded and animated procedurally in this file, with no
downloaded assets: Bolt the robot, the haunted bag, a misty forest, a graveyard,
a pumpkin patch, the haunted house on the hill, the moon, bats, fireflies, candy
and hearts, plus 35 camera set-ups (see SHOTS).

Animation is evaluated per frame by a frame-change handler (apply()), so every
motion is a function of time and the shots line up with edit3/timeline.py.

Run:
  python3 edit3/scene3d.py --storyboard          # one still per shot (fast check)
  python3 edit3/scene3d.py --frames 0 4320       # render frames [start, end)
Options: --pct (resolution %), --samples (Eevee TAA samples).
Several processes can render the same range at once: each claims frames with
placeholder files, so `--frames 0 4320` in two terminals splits the work.

Needs the `bpy` module (pip install bpy). Renders with Eevee, which uses the GPU
(your RTX card) when one is present and falls back to Mesa's llvmpipe on CPU.
"""
import argparse
import math
import os
import random
import sys

import bpy  # noqa: I001  (bpy must be imported before bmesh)
import bmesh
from mathutils import Matrix, Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import CUTS, DURATION, FPS, NFRAMES  # noqa: E402

WORK = os.path.join(HERE, "work")
FONT_SPOOKY = os.path.join(HERE, "assets", "fonts", "Creepster.ttf")
FONT_ROUND = os.path.join(HERE, "assets", "fonts", "Fredoka-Bold.ttf")
SHADOWS = "--shadows" in sys.argv
RES = (1280, 536)  # 2.39:1, letterboxed to 1920x1080 in post like the reference
TAU = math.tau

FOG_COL = (0.055, 0.075, 0.115)
SKY_HORIZON = (0.05, 0.068, 0.105)
SKY_ZENITH = (0.006, 0.008, 0.022)
MOON_POS = Vector((-42.0, 150.0, 56.0))
HOUSE_POS = Vector((30.0, 22.0, 0.0))
STUMP = Vector((0.0, 1.6, 0.0))
STONE = Vector((-19.0, -2.2, 0.0))  # Bolt's hiding gravestone

# ===================================================================== helpers


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    if isinstance(a, (tuple, list, Vector)):
        return tuple(lerp(x, y, u) for x, y in zip(a, b))
    return a + (b - a) * u


EASES = {
    "s": smooth,
    "l": lambda u: u,
    "i": lambda u: u * u,
    "o": lambda u: 1 - (1 - u) ** 2,
    "b": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
    "h": lambda u: 0.0 if u < 1 else 1.0,
}


class Track:
    """Keyframes (t, value[, ease]) where ease shapes the segment ending at that key."""

    def __init__(self, *keys):
        self.k = [(k[0], k[1], k[2] if len(k) > 2 else "s") for k in keys]

    def __call__(self, t):
        k = self.k
        if t <= k[0][0]:
            return k[0][1]
        for (t0, v0, _), (t1, v1, e) in zip(k, k[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
                return lerp(v0, v1, EASES[e](u))
        return k[-1][1]


def window(t, t0, t1, fade=0.2):
    """1 inside [t0, t1] with soft edges, 0 outside."""
    return smooth((t - t0) / fade) * smooth((t1 - t) / fade)


def wob(t, f, seed):
    return noise.noise(Vector((t * f, seed * 7.31, 0.5)))


def path_y(x):
    y = 0.4 * math.sin(0.13 * x)
    if x > 12:
        y += 0.06 * (x - 12) ** 2
    return y


def ground_h(x, y):
    d = abs(y - path_y(x))
    h = noise.noise(Vector((x * 0.12, y * 0.12, 0.3))) * 0.45 * smooth((d - 2.5) / 5)
    h += noise.noise(Vector((x * 0.7, y * 0.7, 1.7))) * 0.035
    h += 3.8 * math.exp(-((x - HOUSE_POS.x) ** 2 + (y - HOUSE_POS.y) ** 2) / (2 * 7.5 ** 2))
    h += 3.0 * smooth((y - 14) / 30) + 2.0 * smooth((-y - 16) / 25)
    return h


def yaw_to(dx, dy):
    """Yaw (about Z) that turns local +Y towards (dx, dy)."""
    return math.atan2(-dx, dy)


def ang_lerp(a, b, u):
    d = (b - a + math.pi) % TAU - math.pi
    return a + d * u


# ================================================================ scene setup

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
COL = SC.collection
FOG = None
MATS = {}


def link(obj, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    COL.objects.link(obj)
    obj.parent = parent
    obj.location = loc
    obj.rotation_euler = rot
    if scale is not None:
        obj.scale = scale if hasattr(scale, "__len__") else (scale,) * 3
    return obj


def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.2
    return link(e, parent, loc, rot)


def mesh_obj(name, bm, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=None,
             smooth_shade=True, sharp_angle=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth_shade:
        for p in me.polygons:
            p.use_smooth = True
        if sharp_angle is not None and hasattr(me, "set_sharp_from_angle"):
            me.set_sharp_from_angle(angle=sharp_angle)
    if mat is not None:
        me.materials.append(mat)
    return link(bpy.data.objects.new(name, me), parent, loc, rot, scale)


def shared(name, me, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    return link(bpy.data.objects.new(name, me), parent, loc, rot, scale)


# ------------------------------------------------------------------ geometry


def bm_sphere(r=1.0, u=24, v=12, scale=(1, 1, 1), m=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r,
                              matrix=m or Matrix.Identity(4))
    for vert in bm.verts:
        vert.co.x *= scale[0]
        vert.co.y *= scale[1]
        vert.co.z *= scale[2]
    return bm


def bm_cyl(r1, r2, depth, seg=16, m=None, caps=True, bm=None):
    bm = bm or bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1,
                          radius2=r2, depth=depth, matrix=m or Matrix.Identity(4))
    return bm


def bm_rbox(sx, sy, sz, bev=0.05, seg=3, bm=None, m=None):
    tmp = bmesh.new()
    bmesh.ops.create_cube(tmp, size=1.0)
    for v in tmp.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bmesh.ops.bevel(tmp, geom=list(tmp.verts) + list(tmp.edges), offset=bev, segments=seg,
                    affect="EDGES", profile=0.5)
    if m is not None:
        bmesh.ops.transform(tmp, matrix=m, verts=tmp.verts)
    if bm is None:
        return tmp
    me = bpy.data.meshes.new("tmp")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def bm_tube(points, radius, seg=8, closed=False, bm=None, taper=None):
    """Sweeps a circle along a polyline (arcs, rings, rope, mouths...)."""
    bm = bm or bmesh.new()
    pts = [Vector(p) for p in points]
    n = len(pts)
    rings = []
    for i, p in enumerate(pts):
        if closed:
            tan = pts[(i + 1) % n] - pts[i - 1]
        else:
            tan = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tan.normalize()
        ref = Vector((0, 0, 1)) if abs(tan.z) < 0.9 else Vector((1, 0, 0))
        nx = tan.cross(ref).normalized()
        ny = tan.cross(nx).normalized()
        r = radius * (taper(i / max(n - 1, 1)) if taper else 1.0)
        rings.append([bm.verts.new(p + (nx * math.cos(a) + ny * math.sin(a)) * r)
                      for a in (TAU * k / seg for k in range(seg))])
    last = n if closed else n - 1
    for i in range(last):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    if not closed:
        for ring, flip in ((rings[0], True), (rings[-1], False)):
            c = bm.verts.new(sum((v.co for v in ring), Vector()) / seg)
            for k in range(seg):
                tri = (ring[k], ring[(k + 1) % seg], c)
                bm.faces.new(tri[::-1] if flip else tri)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def bm_prism(outline, depth, bm=None, m=None):
    """Extrudes a 2D outline (x, z) along Y by `depth` (front face at y=0)."""
    bm = bm or bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in outline]
    f = bm.faces.new(vs)
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, -depth, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if m is not None:
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return bm


def arc_points(cx, cz, r, a0, a1, n=12, y=0.0):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), y,
             cz + r * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


def heart_outline(s=1.0, n=40):
    pts = []
    for i in range(n):
        a = TAU * i / n
        x = 16 * math.sin(a) ** 3
        z = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((x * s / 17, z * s / 17))
    return pts[::-1]


def text_obj(name, body, font, size=1.0, extrude=0.03, bevel=0.006, mat=None, parent=None,
             loc=(0, 0, 0), rot=(math.pi / 2, 0, 0)):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(font)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_line = 0.85
    if mat:
        cu.materials.append(mat)
    return link(bpy.data.objects.new(name, cu), parent, loc, rot)


# ------------------------------------------------------------------ materials


def build_fog_group():
    ng = bpy.data.node_groups.new("Fog", "ShaderNodeTree")
    ng.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader")
    ng.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    cam = N.new("ShaderNodeCameraData")
    dens = N.new("ShaderNodeMath")
    dens.operation, dens.name = "MULTIPLY", "density"
    dens.inputs[1].default_value = -0.05
    L.new(cam.outputs["View Distance"], dens.inputs[0])
    ex = N.new("ShaderNodeMath")
    ex.operation = "EXPONENT"
    L.new(dens.outputs[0], ex.inputs[0])
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(ex.outputs[0], inv.inputs[1])
    geo, sep = N.new("ShaderNodeNewGeometry"), N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])
    hf = N.new("ShaderNodeMapRange")
    hf.inputs["From Min"].default_value = 0.0
    hf.inputs["From Max"].default_value = 16.0
    hf.inputs["To Min"].default_value = 1.0
    hf.inputs["To Max"].default_value = 0.4
    L.new(sep.outputs["Z"], hf.inputs["Value"])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L.new(inv.outputs[0], mul.inputs[0])
    L.new(hf.outputs[0], mul.inputs[1])
    mx = N.new("ShaderNodeMath")
    mx.operation, mx.name = "MULTIPLY", "fogmax"
    mx.inputs[1].default_value = 0.93
    L.new(mul.outputs[0], mx.inputs[0])
    em = N.new("ShaderNodeEmission")
    em.name = "fogcol"
    em.inputs["Color"].default_value = (*FOG_COL, 1)
    mix = N.new("ShaderNodeMixShader")
    L.new(mx.outputs[0], mix.inputs[0])
    L.new(gi.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], go.inputs[0])
    return ng


def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    m.node_tree.nodes.clear()
    MATS[name] = m
    return m, m.node_tree.nodes, m.node_tree.links


def finish(m, N, L, shader, fog=True):
    out = N.new("ShaderNodeOutputMaterial")
    if fog:
        g = N.new("ShaderNodeGroup")
        g.node_tree = FOG
        L.new(shader, g.inputs[0])
        shader = g.outputs[0]
    L.new(shader, out.inputs["Surface"])
    return m


def mat_pbr(name, color, rough=0.6, metal=0.0, coat=0.0, bump=0.0, bump_scale=30.0,
            var=0.0, var_scale=3.0, obj_base=False, emit_obj=0.0, fresnel_glow=0.0, fog=True):
    m, N, L = new_mat(name)
    b = N.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if obj_base or emit_obj or fresnel_glow:
        oi = N.new("ShaderNodeObjectInfo")
    if obj_base:
        L.new(oi.outputs["Color"], b.inputs["Base Color"])
    if emit_obj:
        L.new(oi.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit_obj
    if fresnel_glow:  # rim glow, colour and strength from the object colour
        lw = N.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.35
        k = N.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = fresnel_glow
        pw = N.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 3.0
        L.new(lw.outputs["Facing"], pw.inputs[0])
        L.new(pw.outputs[0], k.inputs[0])
        k2 = N.new("ShaderNodeMath")
        k2.operation = "MULTIPLY"
        L.new(k.outputs[0], k2.inputs[0])
        L.new(oi.outputs["Alpha"], k2.inputs[1])
        L.new(oi.outputs["Color"], b.inputs["Emission Color"])
        L.new(k2.outputs[0], b.inputs["Emission Strength"])
    if var and not obj_base:  # large-scale colour variation
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = var_scale
        ramp = N.new("ShaderNodeMix")
        ramp.data_type = "RGBA"
        ramp.inputs[6].default_value = (*[c * (1 - var) for c in color], 1)
        ramp.inputs[7].default_value = (*[min(1, c * (1 + var)) for c in color], 1)
        L.new(nz.outputs["Fac"], ramp.inputs["Factor"])
        L.new(ramp.outputs[2], b.inputs["Base Color"])
    if bump:
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = bump_scale
        nz.inputs["Detail"].default_value = 6
        bp = N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        L.new(nz.outputs["Fac"], bp.inputs["Height"])
        L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return finish(m, N, L, b.outputs[0], fog)


def mat_emit(name, color=(1, 1, 1), strength=5.0, obj_color=False, fog=False):
    m, N, L = new_mat(name)
    e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    if obj_color:
        oi = N.new("ShaderNodeObjectInfo")
        L.new(oi.outputs["Color"], e.inputs["Color"])
    return finish(m, N, L, e.outputs[0], fog)


def build_materials():
    global FOG
    FOG = build_fog_group()
    # Bolt
    mat_pbr("bolt_shell", (0.82, 0.78, 0.7), rough=0.32, metal=0.25, coat=0.3)
    mat_pbr("bolt_orange", (0.95, 0.33, 0.06), rough=0.35, metal=0.1, coat=0.4)
    mat_pbr("bolt_dark", (0.012, 0.014, 0.018), rough=0.12, coat=1.0)
    mat_pbr("bolt_joint", (0.22, 0.23, 0.25), rough=0.4, metal=0.8)
    mat_emit("bolt_eye", (0.05, 0.75, 1.0), 1.6, obj_color=True)
    mat_emit("bulb", (1.0, 0.65, 0.25), 7.0, obj_color=True)
    m, N, L = new_mat("bolt_wheel")
    b = N.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.5
    tc, wv = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 2.2
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.inputs[6].default_value = (0.05, 0.05, 0.06, 1)
    mx.inputs[7].default_value = (0.95, 0.33, 0.06, 1)
    gt = N.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.75
    L.new(wv.outputs["Fac"], gt.inputs[0])
    L.new(gt.outputs[0], mx.inputs["Factor"])
    L.new(mx.outputs[2], b.inputs["Base Color"])
    finish(m, N, L, b.outputs[0])
    # Bag
    mat_pbr("burlap", (0.4, 0.28, 0.15), rough=0.95, bump=0.35, bump_scale=140,
            fresnel_glow=4.0)
    mat_pbr("patch_blue", (0.16, 0.22, 0.42), rough=0.9, bump=0.2, bump_scale=200)
    mat_pbr("patch_red", (0.5, 0.12, 0.1), rough=0.9, bump=0.2, bump_scale=200)
    mat_pbr("rope", (0.55, 0.42, 0.25), rough=0.9, bump=0.3, bump_scale=80)
    mat_emit("bag_eye", (0.4, 1.0, 0.3), 4.5, obj_color=True)
    mat_pbr("mouth_dark", (0.02, 0.0, 0.01), rough=0.6, emit_obj=0.7)
    mat_pbr("teeth", (0.85, 0.82, 0.7), rough=0.5)
    mat_emit("tear", (0.4, 0.8, 1.0), 6.0)
    # World props
    mat_pbr("bark", (0.06, 0.048, 0.04), rough=0.9, bump=0.5, bump_scale=8, var=0.3)
    mat_pbr("stump", (0.17, 0.11, 0.065), rough=0.85, bump=0.4, bump_scale=12)
    mat_pbr("stone", (0.2, 0.21, 0.23), rough=0.85, bump=0.35, bump_scale=6, var=0.35,
            var_scale=4)
    mat_pbr("moss_stone", (0.12, 0.16, 0.1), rough=0.9, bump=0.3, bump_scale=9, var=0.4)
    mat_pbr("engrave", (0.04, 0.04, 0.05), rough=0.9)
    mat_pbr("pumpkin", (0.85, 0.32, 0.035), rough=0.45, coat=0.2, var=0.2, var_scale=5)
    mat_pbr("stem", (0.17, 0.16, 0.05), rough=0.8)
    mat_pbr("jack_face", (0.0, 0.0, 0.0), rough=0.9, emit_obj=7.0)
    mat_pbr("house_wall", (0.06, 0.05, 0.075), rough=0.9, bump=0.2, bump_scale=4)
    mat_pbr("house_roof", (0.025, 0.025, 0.04), rough=0.7)
    mat_emit("window", (1, 1, 1), 2.4, obj_color=True, fog=True)
    mat_pbr("grass", (0.13, 0.11, 0.055), rough=0.9, var=0.3)
    mat_pbr("fence", (0.09, 0.07, 0.05), rough=0.9, bump=0.3, bump_scale=10)
    mat_pbr("bat", (0.02, 0.018, 0.025), rough=0.8)
    mat_emit("bat_eye", (1.0, 0.25, 0.1), 6.0)
    mat_pbr("candy", (1, 1, 1), rough=0.25, coat=1.0, obj_base=True, emit_obj=0.35)
    mat_emit("heart", (1.0, 0.3, 0.55), 6.0, obj_color=True)
    mat_emit("firefly", (1, 1, 1), 10.0, obj_color=True, fog=True)
    mat_emit("text_glow", (1, 1, 1), 1.3, obj_color=True)
    mat_emit("owl_eye", (1.0, 0.85, 0.2), 9.0, obj_color=True, fog=True)
    # Moon (no fog: it sits behind the fog layer)
    m, N, L = new_mat("moon")
    e = N.new("ShaderNodeEmission")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 4
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.inputs[6].default_value = (0.78, 0.76, 0.68, 1)
    mx.inputs[7].default_value = (1.0, 0.97, 0.86, 1)
    L.new(nz.outputs["Fac"], mx.inputs["Factor"])
    L.new(mx.outputs[2], e.inputs["Color"])
    e.inputs["Strength"].default_value = 4.0
    finish(m, N, L, e.outputs[0], fog=False)
    # Ground: dirt path / dry grass from a colour attribute
    m, N, L = new_mat("ground")
    b = N.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.92
    ca = N.new("ShaderNodeVertexColor")
    ca.layer_name = "Col"
    sp = N.new("ShaderNodeSeparateColor")
    L.new(ca.outputs["Color"], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.2
    grass = N.new("ShaderNodeMix")
    grass.data_type = "RGBA"
    grass.inputs[6].default_value = (0.022, 0.035, 0.022, 1)
    grass.inputs[7].default_value = (0.06, 0.06, 0.03, 1)
    L.new(nz.outputs["Fac"], grass.inputs["Factor"])
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.inputs[7].default_value = (0.11, 0.085, 0.06, 1)
    L.new(sp.outputs[0], mx.inputs["Factor"])
    L.new(grass.outputs[2], mx.inputs[6])
    L.new(mx.outputs[2], b.inputs["Base Color"])
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 18
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.4
    L.new(nz2.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    finish(m, N, L, b.outputs[0])
    # Drifting ground-fog cards (alpha-blended)
    m, N, L = new_mat("fogcard")
    m.surface_render_method = "BLENDED"
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    gr = N.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    L.new(tc.outputs["Object"], gr.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.45
    mr.inputs["From Max"].default_value = 0.75
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    a1 = N.new("ShaderNodeMath")
    a1.operation = "MULTIPLY"
    L.new(mr.outputs[0], a1.inputs[0])
    L.new(gr.outputs["Fac"], a1.inputs[1])
    a2 = N.new("ShaderNodeMath")
    a2.operation = "MULTIPLY"
    a2.name = "opacity"
    a2.inputs[1].default_value = 0.55
    L.new(a1.outputs[0], a2.inputs[0])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.13, 0.16, 0.22, 1)
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(a2.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    finish(m, N, L, mix.outputs[0], fog=False)


def build_world():
    w = bpy.data.worlds.new("Night")
    SC.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    N, L = w.node_tree.nodes, w.node_tree.links
    N.clear()
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.02
    mr.inputs["From Max"].default_value = 0.55
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    sky = N.new("ShaderNodeMix")
    sky.data_type = "RGBA"
    sky.inputs[6].default_value = (*SKY_HORIZON, 1)
    sky.inputs[7].default_value = (*SKY_ZENITH, 1)
    L.new(mr.outputs[0], sky.inputs["Factor"])
    # stars
    vor = N.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 260
    vor.inputs["Randomness"].default_value = 1.0
    L.new(tc.outputs["Generated"], vor.inputs["Vector"])
    st = N.new("ShaderNodeMath")
    st.operation = "LESS_THAN"
    st.inputs[1].default_value = 0.035
    L.new(vor.outputs["Distance"], st.inputs[0])
    stz = N.new("ShaderNodeMath")
    stz.operation = "MULTIPLY"
    L.new(st.outputs[0], stz.inputs[0])
    L.new(mr.outputs[0], stz.inputs[1])
    stv = N.new("ShaderNodeMath")
    stv.operation = "MULTIPLY"
    stv.inputs[1].default_value = 0.9
    L.new(stz.outputs[0], stv.inputs[0])
    # moon halo
    md = (MOON_POS / MOON_POS.length)
    dot = N.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = md
    L.new(tc.outputs["Generated"], dot.inputs[0])
    hmr = N.new("ShaderNodeMapRange")
    hmr.inputs["From Min"].default_value = 0.88
    hmr.inputs["From Max"].default_value = 1.0
    L.new(dot.outputs["Value"], hmr.inputs["Value"])
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    L.new(hmr.outputs[0], pw.inputs[0])
    halo = N.new("ShaderNodeMix")
    halo.data_type = "RGBA"
    halo.blend_type = "ADD"
    halo.inputs[7].default_value = (0.32, 0.36, 0.5, 1)
    L.new(pw.outputs[0], halo.inputs["Factor"])
    L.new(sky.outputs[2], halo.inputs[6])
    add = N.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs[7].default_value = (1, 1, 1, 1)
    L.new(stv.outputs[0], add.inputs["Factor"])
    L.new(halo.outputs[2], add.inputs[6])
    bg = N.new("ShaderNodeBackground")
    bg.name = "bg"
    L.new(add.outputs[2], bg.inputs["Color"])
    out = N.new("ShaderNodeOutputWorld")
    L.new(bg.outputs[0], out.inputs["Surface"])
    return bg


# ================================================================ environment

ENV = {}


def build_ground():
    xs = range(-80, 81, 1)
    ys = range(-50, 91, 1)
    verts, cols = [], []
    for y in ys:
        for x in xs:
            verts.append((x, y, ground_h(x, y)))
            d = abs(y - path_y(x))
            p = 1 - smooth((d - 0.55) / 0.9)
            cols.append(p)
    nx = len(xs)
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
             for j in range(len(ys) - 1) for i in range(nx - 1)]
    me = bpy.data.meshes.new("ground")
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    attr = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    for i, p in enumerate(cols):
        attr.data[i].color = (p, 0, 0, 1)
    me.materials.append(MATS["ground"])
    link(bpy.data.objects.new("ground", me))


def tree_mesh(seed, height=7.0):
    rnd = random.Random(seed)
    bm = bmesh.new()

    def seg(p, d, length, r0, r1):
        q = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bm_cyl(r0, r1, length, seg=6, m=Matrix.Translation(p + d * (length / 2)) @ q,
               caps=False, bm=bm)
        return p + d * length

    def branch(p, d, length, r, depth):
        for i in range(3):
            d = (d + Vector((rnd.uniform(-.4, .4), rnd.uniform(-.4, .4),
                             rnd.uniform(-.15, .2)))).normalized()
            r1 = r * 0.8
            p = seg(p, d, length / 3, r, r1)
            r = r1
            if depth > 0 and i == 1 and rnd.random() < 0.6:
                a = rnd.uniform(0, TAU)
                nd = (d * 0.3 + Vector((math.cos(a), math.sin(a), rnd.uniform(-.1, .4)))).normalized()
                branch(p, nd, length * 0.55, r * 0.6, depth - 1)
        if depth > 0:
            for _ in range(rnd.randint(2, 3)):
                a = rnd.uniform(0, TAU)
                nd = (d * 0.45 + Vector((math.cos(a), math.sin(a), rnd.uniform(-.05, .5))) *
                      rnd.uniform(.7, 1.0)).normalized()
                branch(p, nd, length * rnd.uniform(.55, .75), r * 0.68, depth - 1)

    bm_cyl(0.75, 0.32, 0.6, seg=7, m=Matrix.Translation((0, 0, 0.25)), bm=bm)
    # trunk
    p, d, r = Vector((0, 0, 0)), Vector((0, 0, 1)), 0.34
    for i in range(4):
        d = (d + Vector((rnd.uniform(-.18, .18), rnd.uniform(-.18, .18), 0))).normalized()
        p = seg(p, d, height * 0.15, r, r * 0.85)
        r *= 0.85
        if i >= 2:
            a = rnd.uniform(0, TAU)
            branch(p, Vector((math.cos(a), math.sin(a), 0.5)).normalized(), height * 0.4, r * 0.65, 2)
    for _ in range(3):
        a = rnd.uniform(0, TAU)
        branch(p, (d + Vector((math.cos(a), math.sin(a), 0.2)) * 0.8).normalized(),
               height * 0.45, r * 0.7, 2)
    me = bpy.data.meshes.new(f"tree{seed}")
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(MATS["bark"])
    return me


def in_zone(x, y):
    """Areas kept clear of trees so the action and the cameras have room."""
    if abs(y - path_y(x)) < 3.4:
        return True
    zones = [(-47, -33, -6, 9), (-28, -14, -8, 6), (-15, -3, -5, 5), (-3, 4, -3, 5), (5, 24, -4, 11),
             (22, 38, 14, 30)]
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in zones)


def build_trees():
    meshes = [tree_mesh(s, h) for s, h in ((1, 7.5), (2, 9), (3, 6.5), (4, 10), (5, 8))]
    rnd = random.Random(7)
    n = 0
    for gy in range(-26, 56, 6):
        for gx in range(-62, 52, 6):
            x, y = gx + rnd.uniform(-2.2, 2.2), gy + rnd.uniform(-2.2, 2.2)
            if in_zone(x, y) or rnd.random() < 0.18:
                continue
            s = rnd.uniform(0.8, 1.35)
            shared(f"tree_{n}", meshes[rnd.randrange(5)], loc=(x, y, ground_h(x, y) - 0.1),
                   rot=(rnd.uniform(-.04, .04), rnd.uniform(-.04, .04), rnd.uniform(0, TAU)),
                   scale=s)
            n += 1
    # framing trees placed by hand near the action
    for i, (x, y, s) in enumerate([(-30, 4.5, 1.1), (-24.5, 5.2, 1.0), (-14.5, 5.0, 1.2),
                                   (-2.5, 5.5, 1.1), (5.5, 4.6, 1.0), (-8, -5.5, 1.1),
                                   (4.0, -4.5, 1.2), (-36, -4.2, 1.2), (10.5, -4.4, 1.0),
                                   (16, -2.8, 1.1), (-27, -9, 1.2), (-12, -8, 1.0)]):
        shared(f"ftree_{i}", meshes[i % 5], loc=(x, y, ground_h(x, y) - 0.1),
               rot=(0, 0, i * 1.7), scale=s)
    # the owl tree: a hollow with two glowing eyes that blink at Bolt
    x, y = -21.5, 4.2
    # a dedicated straight old tree, so the hollow sits right on the bark
    bm = bm_cyl(0.8, 0.42, 0.5, seg=10, m=Matrix.Translation((0, 0, 0.25)))
    bm_tube([(0, 0, 0), (0, 0, 2.0), (0.05, 0.02, 3.4), (0.25, 0.1, 5.0), (0.5, 0.2, 6.4)], 0.42,
            seg=10, bm=bm, taper=lambda u: 1 - 0.75 * u)
    for p0, p1, p2 in (((0.05, 0.02, 3.2), (-1.0, 0.3, 4.2), (-1.9, 0.1, 4.6)),
                       ((0.2, 0.1, 4.4), (1.2, -0.2, 5.2), (2.1, 0.2, 5.4)),
                       ((0.15, 0.05, 3.8), (0.4, 1.0, 4.8), (0.6, 1.8, 5.9))):
        bm_tube([p0, p1, p2], 0.13, seg=7, bm=bm, taper=lambda u: 1 - 0.7 * u)
    mesh_obj("owl_tree", bm, MATS["bark"], loc=(x, y, ground_h(x, y) - 0.1))
    hole = mesh_obj("owl_hole", bm_sphere(0.32, 16, 8, scale=(1.0, 0.25, 1.35)),
                    MATS["engrave"], loc=(x, y - 0.3, 2.55))
    hole.rotation_euler = (0, 0, 0)
    ENV["owl_eyes"] = []
    for sx in (-0.11, 0.11):
        e = mesh_obj("owl_eye", bm_sphere(0.065, 12, 6, scale=(1, 0.5, 1)), MATS["owl_eye"],
                     loc=(x + sx, y - 0.37, 2.6))
        ENV["owl_eyes"].append(e)


def build_stump():
    bm = bm_cyl(0.62, 0.44, 0.25, seg=14, m=Matrix.Translation((0, 0, 0.12)))
    bm_cyl(0.46, 0.44, 0.38, seg=14, m=Matrix.Translation((0, 0, 0.42)), bm=bm)
    mesh_obj("stump", bm, MATS["stump"], loc=(STUMP.x, STUMP.y, ground_h(STUMP.x, STUMP.y) - 0.02))
    top = bmesh.new()
    for i, r in enumerate((0.43, 0.33, 0.22, 0.11)):
        bm_tube(arc_points(0, 0, r, 0, TAU, 28)[:-1], 0.008, seg=4, closed=True, bm=top)
    mesh_obj("stump_rings", top, MATS["engrave"], loc=(STUMP.x, STUMP.y, 0.615),
             rot=(math.pi / 2, 0, 0))


def build_graveyard():
    rnd = random.Random(11)
    spots = [(-26, -3.2), (-24.5, -5.4), (-23, -2.6), (-22.2, -6.8), (-20.6, -5.8),
             (-17.2, -5.6), (-15.6, -3.4), (-15.2, -6.6), (-25.8, -7.6), (-27.8, -5.2),
             (-26.5, 2.4), (-24.2, 3.2), (-28.5, 3.5), (-22.8, 2.3), (-13.8, -4.6)]
    for i, (x, y) in enumerate(spots):
        w, h = rnd.uniform(0.45, 0.7), rnd.uniform(0.55, 0.95)
        kind = rnd.random()
        if kind < 0.6:
            bm = bm_rbox(w, 0.14, h, bev=0.03, m=Matrix.Translation((0, 0, h / 2)))
            bm_cyl(w / 2, w / 2, 0.14, seg=16, bm=bm,
                   m=Matrix.Translation((0, 0, h)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        elif kind < 0.85:
            bm = bm_rbox(0.12, 0.12, h * 1.2, bev=0.02, m=Matrix.Translation((0, 0, h * 0.6)))
            bm_rbox(w * 0.85, 0.12, 0.12, bev=0.02, bm=bm, m=Matrix.Translation((0, 0, h * 0.85)))
        else:
            bm = bm_rbox(w, w * 0.8, h * 0.6, bev=0.04, m=Matrix.Translation((0, 0, h * 0.3)))
        face = yaw_to(0, 1) if y < 0 else yaw_to(0, -1)
        mesh_obj(f"grave_{i}", bm, MATS["stone" if i % 3 else "moss_stone"],
                 loc=(x, y, ground_h(x, y) - 0.05),
                 rot=(rnd.uniform(-.12, .12), rnd.uniform(-.12, .12), face + rnd.uniform(-.3, .3)),
                 sharp_angle=0.6)
    # Bolt's hiding stone (big, faces the path)
    w, h = 0.95, 0.7
    bm = bm_rbox(w, 0.2, h, bev=0.04, m=Matrix.Translation((0, 0, h / 2)))
    bm_cyl(w / 2, w / 2, 0.2, seg=24, bm=bm,
           m=Matrix.Translation((0, 0, h)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    big = mesh_obj("big_stone", bm, MATS["stone"], loc=(STONE.x, STONE.y, ground_h(STONE.x, STONE.y) - 0.04),
                   rot=(0.03, -0.04, 0.05), sharp_angle=0.6)
    text_obj("rip", "R.I.P.", FONT_ROUND, size=0.2, extrude=0.01, bevel=0.0,
             mat=MATS["engrave"], parent=big, loc=(0, 0.105, 0.55), rot=(math.pi / 2, 0, math.pi))
    # broken fence along the graveyard
    rnd = random.Random(5)
    bm = bmesh.new()
    for i in range(9):
        x = -29 + i * 1.0
        if i in (5, 9):
            continue
        hh = rnd.uniform(0.7, 1.0)
        bm_rbox(0.09, 0.07, hh, bev=0.01, bm=bm,
                m=Matrix.Translation((x, -1.9 + rnd.uniform(-.05, .05), hh / 2 + ground_h(x, -1.9)))
                @ Matrix.Rotation(rnd.uniform(-.15, .15), 4, "Y"))
    for x0, x1 in ((-29, -24.2), (-23.3, -21.0)):
        for z in (0.35, 0.65):
            m = Matrix.Translation(((x0 + x1) / 2, -1.85, z)) @ Matrix.Rotation(rnd.uniform(-.06, .06), 4, "Y")
            bm_rbox(x1 - x0, 0.04, 0.08, bev=0.01, bm=bm, m=m)
    mesh_obj("fence", bm, MATS["fence"], sharp_angle=0.6)


def pumpkin_mesh(r):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 - 0.08 * abs(math.sin(4 * a))
        v.co.x *= k
        v.co.y *= k
        v.co.z *= 0.72
        if abs(v.co.z) > 0.6 * r:  # dimple top and bottom
            v.co.z *= 0.9
    return bm


def build_pumpkins():
    rnd = random.Random(21)
    pts = []
    while len(pts) < 17:
        x = rnd.uniform(-13.5, -4.5)
        side = rnd.choice((-1, 1))
        y = path_y(x) + side * rnd.uniform(1.35, 3.6)
        if all((x - a) ** 2 + (y - b) ** 2 > 1.3 for a, b, _ in pts):
            pts.append((x, y, rnd.uniform(0.26, 0.42)))
    ENV["pumpkins"] = []
    for i, (x, y, r) in enumerate(sorted(pts, key=lambda p: -p[0])):
        root = empty(f"pumpkin_{i}", loc=(x, y, ground_h(x, y) + r * 0.62),
                     rot=(0, 0, yaw_to(rnd.uniform(-1, 1), path_y(x) - y) + rnd.uniform(-.3, .3)))
        mesh_obj(f"pumpkin_body_{i}", pumpkin_mesh(r), MATS["pumpkin"], parent=root)
        stem = bm_tube([(0, 0, 0), (0.01, 0, 0.06), (0.04, 0, 0.11)], r * 0.12, seg=6,
                       taper=lambda u: 1 - 0.4 * u)
        mesh_obj(f"stem_{i}", stem, MATS["stem"], parent=root, loc=(0, 0, r * 0.62))
        # carved face projected onto the front of the pumpkin
        bm = bmesh.new()
        shapes = [[(-0.42, 0.12), (-0.18, 0.12), (-0.3, 0.36)],
                  [(0.18, 0.12), (0.42, 0.12), (0.3, 0.36)],
                  [(-0.08, -0.02), (0.08, -0.02), (0, 0.12)]]
        mouth = [(-0.5, -0.12)]
        for k in range(7):
            xx = -0.5 + (k + 0.5) / 7
            mouth.append((xx, -0.12 if k % 2 else -0.22))
        mouth += [(0.5, -0.12), (0.35, -0.42), (0.0, -0.5), (-0.35, -0.42)]
        shapes.append(mouth[::-1])
        for sh in shapes:
            vs = []
            for sx, sz in sh:
                px, pz = sx * r, sz * r * 0.72
                py = math.sqrt(max(0.0, 1 - (px / r) ** 2 - (pz / (0.72 * r)) ** 2)) * r * 0.93 + 0.012
                vs.append(bm.verts.new((px, py, pz)))
            bm.faces.new(vs)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        face = mesh_obj(f"jack_{i}", bm, MATS["jack_face"], parent=root, smooth_shade=False)
        face.color = (0, 0, 0, 1)
        ENV["pumpkins"].append((root, face, i))
    ENV["pumpkin_lights"] = []
    for i, (x, y) in enumerate(((-11.5, 2.4), (-6.5, -2.2), (-8.5, 2.8))):
        L = bpy.data.lights.new(f"pumpkin_light_{i}", "POINT")
        L.color = (1.0, 0.45, 0.12)
        L.shadow_soft_size = 0.4
        L.use_shadow = False
        ENV["pumpkin_lights"].append(link(bpy.data.objects.new(L.name, L), loc=(x, y, 0.6)))


def build_house():
    root = empty("house", loc=(HOUSE_POS.x, HOUSE_POS.y, ground_h(HOUSE_POS.x, HOUSE_POS.y) - 0.3),
                 rot=(0, 0, yaw_to(-0.75, -1)))
    W, R = MATS["house_wall"], MATS["house_roof"]
    mesh_obj("house_body", bm_rbox(7, 5, 4.5, bev=0.05, m=Matrix.Translation((0, 0, 2.25))), W,
             parent=root, rot=(0, 0.02, 0), sharp_angle=0.6)
    mesh_obj("house_up", bm_rbox(5, 4, 3, bev=0.05, m=Matrix.Translation((0.4, 0, 6))), W,
             parent=root, rot=(0, -0.03, 0.02), sharp_angle=0.6)
    for loc, r, h in (((0, 0, 4.5), 4.6, 2.2), ((0.4, 0, 7.5), 3.6, 2.6)):
        mesh_obj("roof", bm_cyl(r, 0.05, h, seg=4, m=Matrix.Translation((0, 0, h / 2))
                                @ Matrix.Rotation(math.pi / 4, 4, "Z")), R,
                 parent=root, loc=loc, smooth_shade=False)
    mesh_obj("tower", bm_cyl(1.0, 1.0, 9, seg=10, m=Matrix.Translation((0, 0, 4.5))), W,
             parent=root, loc=(-3.6, 1.2, 0), sharp_angle=0.6)
    mesh_obj("spire", bm_cyl(1.35, 0.02, 3.6, seg=10, m=Matrix.Translation((0, 0, 1.8))), R,
             parent=root, loc=(-3.6, 1.2, 9), rot=(0.08, 0.05, 0), smooth_shade=False)
    mesh_obj("chimney", bm_rbox(0.6, 0.6, 2.4, bev=0.03, m=Matrix.Translation((0, 0, 1.2))), W,
             parent=root, loc=(2.2, 1.0, 6.5), rot=(0, 0.1, 0), sharp_angle=0.6)
    ENV["windows"] = []
    wins = [(-1.8, 1.2), (0.0, 1.4), (1.8, 1.2), (-1.4, 3.3), (1.6, 3.3), (0.4, 5.9),
            (-0.9, 6.3), (1.6, 6.0)]
    for i, (x, z) in enumerate(wins):
        bm = bm_rbox(0.8, 0.06, 1.0, bev=0.02)
        w = mesh_obj(f"window_{i}", bm, MATS["window"], parent=root,
                     loc=(x, 2.52 if z < 4.5 else 2.02, z))
        ENV["windows"].append(w)
    for i, z in enumerate((3.2, 5.6, 7.6)):  # tower windows
        w = mesh_obj(f"twindow_{i}", bm_rbox(0.4, 0.06, 0.7, bev=0.02), MATS["window"], parent=root,
                     loc=(-3.6, 2.22, z))
        ENV["windows"].append(w)
    door = mesh_obj("door", bm_rbox(1.0, 0.08, 1.8, bev=0.02, m=Matrix.Translation((0, 0, 0.9))),
                    MATS["window"], parent=root, loc=(0, 2.53, 0))
    ENV["door"] = door


def build_sky_props():
    mesh_obj("moon", bm_sphere(8.0, 32, 16), MATS["moon"], loc=MOON_POS)
    # fog cards drifting over the ground
    ENV["fogcards"] = []
    for i, (x, y, z, s) in enumerate(((-21, -1, 0.3, 14), (-8, 1.5, 0.35, 13), (4, 2, 0.4, 14),
                                      (-34, 3, 0.45, 13), (16, 5, 0.5, 14), (-15, -6, 0.6, 12))):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
        c = mesh_obj(f"fogcard_{i}", bm, MATS["fogcard"], loc=(x, y, z), rot=(0, 0, i * 0.7),
                     scale=(s / 2, s / 2, 1), smooth_shade=False)
        if hasattr(c, "visible_shadow"):
            c.visible_shadow = False
        ENV["fogcards"].append((c, Vector((x, y, z))))
    # dry grass tufts joined into one mesh
    rnd = random.Random(3)
    bm = bmesh.new()
    n = 0
    while n < 650:
        x, y = rnd.uniform(-45, 26), rnd.uniform(-9, 12)
        d = abs(y - path_y(x))
        if d < 0.9 or (d > 6 and rnd.random() < 0.6):
            continue
        n += 1
        z = ground_h(x, y)
        for k in range(5):
            a = rnd.uniform(0, TAU)
            h = rnd.uniform(0.18, 0.42)
            lean = Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(0.05, 0.16)
            base = Vector((x + rnd.uniform(-.05, .05), y + rnd.uniform(-.05, .05), z - 0.02))
            side = Vector((-math.sin(a), math.cos(a), 0)) * 0.018
            v1, v2 = bm.verts.new(base - side), bm.verts.new(base + side)
            v3 = bm.verts.new(base + lean + Vector((0, 0, h)))
            bm.faces.new((v1, v2, v3))
    tufts = mesh_obj("grass", bm, MATS["grass"], smooth_shade=False)
    if hasattr(tufts, "visible_shadow"):
        tufts.visible_shadow = False
    # rocks
    bm = bmesh.new()
    for _ in range(60):
        x, y = rnd.uniform(-40, 24), rnd.uniform(-8, 10)
        if abs(y - path_y(x)) < 1.0:
            continue
        s = rnd.uniform(0.08, 0.3)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s,
                                   matrix=Matrix.Translation((x, y, ground_h(x, y)))
                                   @ Matrix.Diagonal((1, rnd.uniform(.6, 1), rnd.uniform(.4, .7), 1)))
    mesh_obj("rocks", bm, MATS["stone"], smooth_shade=False)


def build_lights():
    sun = bpy.data.lights.new("moonlight", "SUN")
    sun.color = (0.55, 0.66, 1.0)
    sun.energy = 1.6
    sun.angle = math.radians(3)
    d = -(MOON_POS.normalized())
    o = link(bpy.data.objects.new("moonlight", sun))
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ENV["sun"] = o
    rim = bpy.data.lights.new("rim", "SUN")
    rim.color = (0.55, 0.4, 1.0)
    rim.energy = 0.45
    rim.use_shadow = False
    o = link(bpy.data.objects.new("rim", rim))
    o.rotation_euler = Vector((0.6, -1.0, -0.35)).to_track_quat("-Z", "Y").to_euler()
    ENV["rim"] = o


# ====================================================================== Bolt

BOLT = {}


def build_bolt():
    M = MATS
    root = empty("bolt")
    wheel = mesh_obj("bolt_wheel", bm_sphere(0.17, 24, 12), M["bolt_wheel"], parent=root,
                     loc=(0, 0, 0.17))
    tilt = empty("bolt_tilt", parent=root, loc=(0, 0, 0.17))
    mesh_obj("bolt_skirt", bm_tube(arc_points(0, 0, 0.2, 0, TAU, 25)[:-1], 0.04, seg=8, closed=True),
             M["bolt_joint"], parent=tilt, loc=(0, 0, 0.08), rot=(math.pi / 2, 0, 0))
    mesh_obj("bolt_body", bm_rbox(0.5, 0.42, 0.44, bev=0.12, seg=4), M["bolt_shell"], parent=tilt,
             loc=(0, 0, 0.29))
    mesh_obj("bolt_chest", bm_rbox(0.3, 0.05, 0.2, bev=0.04, seg=3), M["bolt_orange"], parent=tilt,
             loc=(0, 0.2, 0.3))
    chest_btn = mesh_obj("bolt_btn", bm_sphere(0.035, 12, 6, scale=(1, 0.5, 1)), M["bolt_eye"],
                         parent=tilt, loc=(0.07, 0.23, 0.33))
    chest_btn.color = (1.0, 0.35, 0.2, 1)
    mesh_obj("bolt_neck", bm_cyl(0.07, 0.06, 0.12, seg=12), M["bolt_joint"], parent=tilt,
             loc=(0, 0, 0.56))
    head = empty("bolt_headpivot", parent=tilt, loc=(0, 0, 0.6))
    mesh_obj("bolt_head", bm_rbox(0.62, 0.46, 0.42, bev=0.13, seg=4), M["bolt_shell"], parent=head,
             loc=(0, 0, 0.22))
    mesh_obj("bolt_screen", bm_rbox(0.5, 0.06, 0.3, bev=0.08, seg=3), M["bolt_dark"], parent=head,
             loc=(0, 0.205, 0.22))
    for sx in (-1, 1):
        mesh_obj("bolt_ear", bm_cyl(0.07, 0.07, 0.08, seg=14,
                                    m=Matrix.Rotation(math.pi / 2, 4, "Y")),
                 M["bolt_orange"], parent=head, loc=(sx * 0.33, 0, 0.22))
    # antenna with the glowing lamp bulb that lights Bolt's way
    mesh_obj("bolt_ant", bm_tube([(0, 0, 0), (0.01, 0, 0.1), (0.03, 0, 0.2)], 0.012, seg=6),
             M["bolt_joint"], parent=head, loc=(0.1, 0, 0.42))
    bulb = mesh_obj("bolt_bulb", bm_sphere(0.05, 16, 8), M["bulb"], parent=head,
                    loc=(0.13, 0, 0.66))
    bl = bpy.data.lights.new("bolt_lamp", "POINT")
    bl.color = (1.0, 0.62, 0.28)
    bl.energy = 22
    bl.shadow_soft_size = 0.05
    lamp = link(bpy.data.objects.new("bolt_lamp", bl), parent=head, loc=(0.13, 0.05, 0.66))
    eyes, happy = [], []
    for sx in (-1, 1):
        e = mesh_obj("bolt_eye", bm_sphere(1.0, 16, 8), M["bolt_eye"], parent=head,
                     loc=(sx * 0.12, 0.24, 0.24), scale=(0.045, 0.02, 0.075))
        e.color = (0.05, 0.75, 1.0, 1)
        eyes.append(e)
        h = mesh_obj("bolt_happy", bm_tube(arc_points(0, -0.02, 0.055, 0.25, math.pi - 0.25, 10, 0),
                                           0.014, seg=6), M["bolt_eye"], parent=head,
                     loc=(sx * 0.12, 0.245, 0.24))
        h.color = (0.05, 0.75, 1.0, 1)
        happy.append(h)
    smile = mesh_obj("bolt_smile", bm_tube(arc_points(0, 0.05, 0.06, math.pi + 0.5, TAU - 0.5, 10, 0),
                                           0.011, seg=6), M["bolt_eye"], parent=head,
                     loc=(0, 0.245, 0.13))
    smile.color = (0.05, 0.75, 1.0, 1)
    omouth = mesh_obj("bolt_omouth", bm_tube(arc_points(0, 0, 0.03, 0, TAU, 17, 0)[:-1], 0.01,
                                             seg=6, closed=True), M["bolt_eye"], parent=head,
                      loc=(0, 0.245, 0.12))
    omouth.color = (0.05, 0.75, 1.0, 1)
    arms = []
    for sx in (-1, 1):
        sh = empty("bolt_shoulder", parent=tilt, loc=(sx * 0.3, 0, 0.42))
        mesh_obj("bolt_sjoint", bm_sphere(0.065, 12, 6), M["bolt_joint"], parent=sh)
        mesh_obj("bolt_arm", bm_cyl(0.042, 0.038, 0.24, seg=10), M["bolt_shell"], parent=sh,
                 loc=(sx * 0.02, 0, -0.14))
        mesh_obj("bolt_hand", bm_sphere(0.065, 12, 6), M["bolt_orange"], parent=sh,
                 loc=(sx * 0.02, 0, -0.29))
        arms.append(sh)
    sym = {}
    sym["?"] = text_obj("sym_q", "?", FONT_ROUND, size=0.42, extrude=0.03, mat=M["text_glow"])
    sym["!"] = text_obj("sym_x", "!", FONT_ROUND, size=0.42, extrude=0.03, mat=M["text_glow"])
    for s in sym.values():
        s.color = (1.0, 0.85, 0.2, 1)
    BOLT.update(root=root, wheel=wheel, tilt=tilt, head=head, eyes=eyes, happy=happy,
                smile=smile, omouth=omouth, arms=arms, bulb=bulb, lamp=lamp, sym=sym, btn=chest_btn)


# ======================================================================= Bag

BAG = {}


def build_bag():
    M = MATS
    root = empty("bag")
    body = empty("bag_body", parent=root)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=1.0)
    for v in bm.verts:
        u = v.co.z
        pinch = 1.0 if u < 0.35 else 1 - 0.62 * smooth((u - 0.35) / 0.65)
        lump = 1 + 0.05 * noise.noise(v.co * 2.3)
        v.co.x *= 0.33 * pinch * lump
        v.co.y *= 0.29 * pinch * lump
        v.co.z = (v.co.z * 0.34 if v.co.z > -0.75 else -0.255 - (0.75 + v.co.z) * 0.1)
    sack = mesh_obj("bag_sack", bm, M["burlap"], parent=body)
    sack.color = (0.4, 1.0, 0.3, 0.0)
    tuft = bmesh.new()
    bmesh.ops.create_cone(tuft, cap_ends=False, segments=16, radius1=0.07, radius2=0.15, depth=0.12,
                          matrix=Matrix.Translation((0, 0, 0.06)))
    for v in tuft.verts:
        if v.co.z > 0.1:
            v.co.z += 0.03 * math.sin(math.atan2(v.co.y, v.co.x) * 5)
    sack_top = mesh_obj("bag_tuft", tuft, M["burlap"], parent=body, loc=(0, 0, 0.3))
    sack_top.color = (0.4, 1.0, 0.3, 0.0)
    mesh_obj("bag_rope", bm_tube(arc_points(0, 0, 0.085, 0, TAU, 21)[:-1], 0.018, seg=6, closed=True),
             M["rope"], parent=body, loc=(0, 0, 0.31), rot=(math.pi / 2, 0, 0))
    mesh_obj("bag_rope_end", bm_tube([(0.08, 0, 0.31), (0.14, 0.04, 0.24), (0.17, 0.06, 0.15)],
                                     0.015, seg=6), M["rope"], parent=body)
    mesh_obj("bag_patch1", bm_rbox(0.12, 0.02, 0.1, bev=0.01, seg=2), M["patch_blue"], parent=body,
             loc=(0.25, 0.17, -0.12), rot=(0.1, 0.15, 0.9))
    mesh_obj("bag_patch2", bm_rbox(0.09, 0.02, 0.08, bev=0.01, seg=2), M["patch_red"], parent=body,
             loc=(-0.22, 0.2, 0.1), rot=(-0.2, -0.1, -0.7))
    eyes = []
    for sx in (-1, 1):
        e = mesh_obj("bag_eye", bm_sphere(1.0, 16, 8), M["bag_eye"], parent=body,
                     loc=(sx * 0.1, 0.272, 0.08), scale=(0.05, 0.02, 0.06))
        e.color = (0.4, 1.0, 0.3, 1)
        eyes.append(e)
    # jagged grin: dark crescent + three teeth
    outline = [(-0.13, 0.02)] + [(x / 10 * 0.13, 0.03 - 0.008 * (x / 10) ** 2) for x in range(-9, 10)] \
        + [(0.13, 0.02)] + [(math.cos(a) * 0.13, -math.sin(a) * 0.08 + 0.02)
                            for a in (k / 16 * math.pi for k in range(1, 16))]
    mbm = bm_prism(outline, 0.02)
    for k, x in enumerate((-0.07, 0.0, 0.07)):
        bm_prism([(x - 0.022, 0.025), (x + 0.022, 0.025), (x, -0.015)], 0.02, bm=mbm,
                 m=Matrix.Translation((0, 0.004, 0)))
    mouth = mesh_obj("bag_mouth", mbm, M["mouth_dark"], parent=body, loc=(0, 0.292, -0.07),
                     smooth_shade=False)
    mouth.color = (0.25, 0.02, 0.04, 1)
    tear = mesh_obj("bag_tear", bm_sphere(1.0, 12, 6, scale=(0.018, 0.012, 0.026)), M["tear"],
                    parent=body, loc=(0.1, 0.27, 0.0))
    gl = bpy.data.lights.new("bag_glow", "POINT")
    gl.color = (0.35, 1.0, 0.3)
    gl.energy = 0
    gl.shadow_soft_size = 0.3
    gl.use_shadow = False
    glow = link(bpy.data.objects.new("bag_glow", gl), parent=body, loc=(0, 0.6, 0.1))
    BAG.update(root=root, body=body, eyes=eyes, mouth=mouth, tear=tear, glow=glow, top=sack_top)


# ============================================================ small props

PROPS = {}


def build_props():
    M = MATS
    rnd = random.Random(42)
    # candy: wrapped sweets in bright colours
    cols = [(1, 0.15, 0.2), (0.2, 0.6, 1), (1, 0.85, 0.1), (0.3, 1, 0.35), (0.9, 0.3, 1),
            (1, 0.5, 0.1)]
    cbm = bm_sphere(0.045, 12, 6, scale=(1.3, 1, 1))
    for sx in (-1, 1):
        bm_cyl(0.005, 0.035, 0.04, seg=8, bm=cbm,
               m=Matrix.Translation((sx * 0.072, 0, 0)) @ Matrix.Rotation(sx * math.pi / 2, 4, "Y"))
    cme = bpy.data.meshes.new("candy")
    cbm.to_mesh(cme)
    cbm.free()
    for p in cme.polygons:
        p.use_smooth = True
    cme.materials.append(M["candy"])
    PROPS["candy"] = []
    for i in range(28):
        o = shared(f"candy_{i}", cme)
        o.color = (*cols[i % len(cols)], 1)
        PROPS["candy"].append(o)
    # hearts
    hme = bpy.data.meshes.new("heart")
    hb = bm_prism(heart_outline(0.12), 0.03)
    hb.to_mesh(hme)
    hb.free()
    hme.materials.append(M["heart"])
    PROPS["hearts"] = []
    for i in range(7):
        o = shared(f"heart_{i}", hme)
        o.color = (1.0, 0.3 + 0.1 * (i % 3), 0.55, 1)
        PROPS["hearts"].append(o)
    # fireflies / wisps
    fme = bpy.data.meshes.new("firefly")
    fb = bm_sphere(0.025, 8, 4)
    fb.to_mesh(fme)
    fb.free()
    fme.materials.append(M["firefly"])
    PROPS["flies"] = []
    for i in range(70):
        base = Vector((rnd.uniform(-34, 24), rnd.uniform(-7, 9), rnd.uniform(0.4, 2.6)))
        base.y = path_y(base.x) + (base.y - path_y(base.x))
        PROPS["flies"].append((shared(f"fly_{i}", fme), base, rnd.uniform(0, 100)))
    # bats
    PROPS["bats"] = []
    wing_outline = [(0, 0), (0.06, 0.05), (0.18, 0.08), (0.3, 0.05), (0.27, -0.01), (0.21, -0.05),
                    (0.15, -0.01), (0.1, -0.05), (0.05, -0.02)]
    for i in range(7):
        r = empty(f"bat_{i}")
        mesh_obj("bat_body", bm_sphere(0.045, 10, 6, scale=(0.8, 1.4, 0.8)), M["bat"], parent=r)
        for sx in (-1, 1):
            pv = empty("bat_wingpivot", parent=r, loc=(sx * 0.03, 0, 0))
            wb = bm_prism([(sx * x, z) for x, z in wing_outline][::sx], 0.004)
            mesh_obj("bat_wing", wb, M["bat"], parent=pv, rot=(math.pi / 2, 0, 0), smooth_shade=False)
            mesh_obj("bat_eye", bm_sphere(0.008, 6, 4), M["bat_eye"], parent=r, loc=(sx * 0.016, 0.05, 0.015))
        PROPS["bats"].append((r, [c for c in r.children if c.name.startswith("bat_wingpivot")]))
    # titles
    title = text_obj("title", "ROBOT AND THE\nHAUNTED BAG", FONT_SPOOKY, size=1.15, extrude=0.08,
                     bevel=0.012, mat=M["text_glow"], loc=(-40, 6.5, 2.2))
    title.color = (1.0, 0.42, 0.08, 1)
    theend = text_obj("theend", "THE END...?", FONT_SPOOKY, size=1.4, extrude=0.08, bevel=0.012,
                      mat=M["text_glow"], loc=(23.5, 13, 6.0))
    theend.color = (1.0, 0.42, 0.08, 1)
    PROPS.update(title=title, theend=theend)


def build_blobs():
    """Soft dark discs on the ground under the characters (fake contact shadows)."""
    m, N, L = new_mat("blob")
    m.surface_render_method = "BLENDED"
    tc, gr = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeTexGradient")
    gr.gradient_type = "QUADRATIC_SPHERE"
    L.new(tc.outputs["Object"], gr.inputs["Vector"])
    oi = N.new("ShaderNodeObjectInfo")
    k = N.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    L.new(gr.outputs["Fac"], k.inputs[0])
    L.new(oi.outputs["Alpha"], k.inputs[1])
    tr, dark = N.new("ShaderNodeBsdfTransparent"), N.new("ShaderNodeEmission")
    dark.inputs["Color"].default_value = (0, 0, 0, 1)
    mix = N.new("ShaderNodeMixShader")
    L.new(k.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(dark.outputs[0], mix.inputs[2])
    finish(m, N, L, mix.outputs[0], fog=False)
    for name in ("bolt", "bag"):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
        o = mesh_obj(f"blob_{name}", bm, m, smooth_shade=False)
        PROPS[f"blob_{name}"] = o


def place_blob(o, p, r, strength):
    gz = ground_h(p.x, p.y)
    h = max(0.0, p.z - gz)
    k = 1.0 / (1.0 + 0.9 * h)
    o.location = (p.x, p.y, gz + 0.025)
    o.scale = (r * (1 + 0.4 * h), r * (1 + 0.4 * h), 1)
    o.color = (0, 0, 0, strength * k * k)


# ========================================================== character motion


class PTrack(Track):
    """Track over positions; ('P', x) means 'on the path at x' and follows its curve."""

    @staticmethod
    def _xy(v):
        return (v[1], path_y(v[1])) if v[0] == "P" else v

    def __call__(self, t):
        k = self.k
        if t <= k[0][0]:
            return self._xy(k[0][1])
        for (t0, v0, _), (t1, v1, e) in zip(k, k[1:]):
            if t <= t1:
                u = EASES[e]((t - t0) / (t1 - t0) if t1 > t0 else 1.0)
                if v0[0] == "P" and v1[0] == "P":
                    x = lerp(v0[1], v1[1], u)
                    return (x, path_y(x))
                return lerp(self._xy(v0), self._xy(v1), u)
        return self._xy(k[-1][1])


def P(x):
    return ("P", x)


HIDE = (-19.2, -3.2)
BOLT_XY = PTrack(
    (0, P(-34)), (12, P(-34)), (21, P(-20)), (23.5, P(-20)), (30.5, P(-1.2)),
    (39.2, P(-1.2)), (41.2, (-0.45, 0.95)), (47.0, (-0.45, 0.95)), (48.0, (-1.6, -0.4), "o"),
    (64.9, (-1.6, -0.4)), (65.8, P(-2.8), "i"), (74.0, P(-17.4), "l"), (76.0, (-17.6, -2.95), "l"),
    (78.5, HIDE, "o"), (118.0, HIDE), (120.0, (-17.7, -2.85)), (122.0, (-17.9, -1.25), "o"),
    (140.0, (-17.9, -1.25)), (142.0, (-14.0, 0.5)),
    (146.5, (-14.0, 0.5)), (148.5, P(-4.0), "o"), (154.0, P(-4.0)), (155.5, P(-2.0), "i"),
    (166.5, P(17.0), "l"), (168.5, P(20.0), "o"),
)
FLY_C, FLY_R = Vector((-9.0, 0.5)), 5.0


def bolt_xy(t):
    if 142.0 <= t < 146.5:
        a = math.pi + TAU * smooth((t - 142.0) / 4.5)
        return (FLY_C.x + FLY_R * math.cos(a), FLY_C.y + FLY_R * math.sin(a))
    return BOLT_XY(t)


BOLT_LIFT = Track((0, 0.0), (21.3, 0.0), (21.55, 0.18, "o"), (21.85, 0.0, "i"),
                  (47.0, 0.0), (47.45, 0.35, "o"), (48.0, 0.0, "i"),
                  (140.0, 0.0), (142.0, 1.6), (146.5, 1.6), (148.5, 0.0, "s"))


def bolt_pos(t):
    x, y = bolt_xy(t)
    z = ground_h(x, y) + BOLT_LIFT(t)
    if 142.0 <= t < 146.5:
        z += 0.3 * math.sin((t - 142) * 2.1)
    if 148.5 <= t < 154.0:  # happy hop
        z += abs(math.sin((t - 148.5) * math.pi * 1.6)) * 0.12
    return Vector((x, y, z))


BAG_HOVER = Track((0, 0.0), (50, 0.0), (53, 1.0))
BAG_STUMP = Vector((STUMP.x, STUMP.y, 0.6 + 0.29))
BAG_LATE = Track(
    (78.5, (-17.0, -0.6, 1.05)), (80.0, (-17.0, -0.6, 1.05)), (86.0, (-18.0, -0.4, 1.1)),
    (90.0, (-18.6, -0.9, 1.0)), (93.0, (-18.6, -0.9, 1.0)), (96.0, (-19.1, -2.25, 1.62)),
    (106.0, (-19.1, -2.25, 1.62)), (109.0, (-19.1, -0.95, 0.31)), (124.0, (-19.1, -0.95, 0.31)),
    (129.0, (-19.0, -1.0, 0.55)), (131.0, (-18.42, -1.2, 0.78)), (134.0, (-18.42, -1.2, 0.78)),
    (136.0, (-18.6, -0.9, 1.0)), (140.0, (-18.6, -0.9, 1.0)),
)


def bag_pos(t):
    if t < 64.0:
        p = BAG_STUMP.copy()
        p.z += BAG_HOVER(t) * 0.75
        if t > 53:
            p.z += 0.08 * math.sin((t - 53) * 2.2)
        if t > 50:
            p.x += 0.04 * math.sin(t * 1.3)
        return p
    if t < 66.5:
        a = Vector((STUMP.x, STUMP.y, BAG_STUMP.z + 0.75))
        return a.lerp(Vector((-0.6, 0.6, 1.25)), smooth((t - 64) / 2.5))
    if t < 78.5:
        tt = min(t, 76.0)
        x, y = bolt_xy(tt - 1.4)
        f = Vector((x, y, ground_h(x, y) + 1.0 + 0.12 * math.sin(t * 5)))
        f = Vector((-0.6, 0.6, 1.25)).lerp(f, smooth((t - 66.5) / 1.2))
        if t > 76.0:
            f = f.lerp(Vector(BAG_LATE(78.5)), smooth((t - 76) / 2.5))
        return f
    if t < 140.0:
        p = Vector(BAG_LATE(t))
        if 97.5 <= t < 98.3:  # hiccup jolt
            p.z += 0.18 * math.sin((t - 97.5) / 0.8 * math.pi)
        if t < 106 or t > 129:
            p.z += 0.05 * math.sin(t * 2.4)
        return p
    if t < 148.5:
        b = bolt_pos(t)
        hold = b + Vector((0, 0, 1.33))
        return Vector(BAG_LATE(140)).lerp(hold, smooth((t - 140) / 1.0))
    if t < 154.0:
        b = bolt_pos(t)
        a = (t - 148.5) * 2.6
        return b + Vector((0.85 * math.cos(a), 0.85 * math.sin(a), 0.9 + 0.15 * math.sin(a * 2)))
    ride = bolt_pos(t) + Matrix.Rotation(BOLT_YAW[fidx(t)], 3, "Z") @ Vector((0, -0.3, 1.02))
    if t < 155.5:
        b = bolt_pos(154.0)
        start = b + Vector((0.85 * math.cos(5.5 * 2.6), 0.85 * math.sin(5.5 * 2.6), 0.9))
        return start.lerp(ride, smooth((t - 154) / 1.5))
    if t > 173.5:  # pops up off Bolt's back to look at the camera
        ride += Vector((0, 0, 0.35 * smooth((t - 173.5) / 0.8) + 0.04 * math.sin(t * 3)))
    return ride


def fidx(t):
    return max(0, min(NFRAMES, int(round(t * FPS))))


def precompute_yaw(pos_fn, face_fn, rate, extra=None, speed_min=0.35):
    yaws, cur = [], None
    for f in range(NFRAMES + 1):
        t = f / FPS
        p0, p1 = pos_fn(t - 0.08), pos_fn(t + 0.08)
        v = Vector((p1[0] - p0[0], p1[1] - p0[1]))
        target = face_fn(t)
        if target is not None and not isinstance(target, Vector) and not isinstance(target, tuple):
            want = target
        elif target is not None:
            pp = pos_fn(t)
            want = yaw_to(target[0] - pp[0], target[1] - pp[1])
        elif v.length / 0.16 > speed_min:
            want = yaw_to(v.x, v.y)
        else:
            want = cur if cur is not None else yaw_to(1, 0)
        cur = want if cur is None else ang_lerp(cur, want, rate)
        yaws.append(cur)
    if extra:
        yaws = [y + extra(f / FPS) for f, y in enumerate(yaws)]
    return yaws


def bolt_face(t):
    if 30.5 <= t < 47.0:
        return (STUMP.x, STUMP.y)
    if 47.0 <= t < 64.9:
        b = bag_pos(t)
        return (b.x, b.y)
    if 78.5 <= t < 118.0:
        return (-19.15, 1.0)
    if 135.0 <= t < 140.0:  # celebrate facing the camera
        return (-18.4, 3.0)
    if 122.0 <= t < 140.0:
        b = bag_pos(t)
        return (b.x, b.y)
    if 167.5 <= t:
        return (HOUSE_POS.x, HOUSE_POS.y)
    return None


def bolt_spin(t):
    # panic spin before running away, happy spin in the dance
    return TAU * 1.0 * smooth((t - 64.9) / 0.8) * (t < 66) + \
        (TAU * 2 * smooth((t - 150.0) / 2.5) if 150 <= t < 152.6 else 0.0)


def bag_face(t):
    if t < 50.0:
        return (-1.2, -0.8)
    if t < 66.5:
        b = bolt_pos(t)
        return (b.x, b.y)
    if 78.5 <= t < 90.0:
        return yaw_to(-1, -0.3) + 1.0 * math.sin((t - 80) * 0.75)
    if 90.0 <= t < 106.0:
        return HIDE
    if 106.0 <= t < 123.0:
        return 0.0
    if 135.0 <= t < 140.0:
        return (-18.6, 3.0)
    if 123.0 <= t < 140.0:
        b = bolt_pos(t)
        return (b.x, b.y)
    if 154.0 <= t < 173.5:
        return BOLT_YAW[fidx(t)]
    if t >= 173.5:
        c = CAM_TRACE.get(fidx(t))
        return (c.x, c.y) if c is not None else None
    return None


BOLT_YAW = []
BAG_YAW = []
CAM_TRACE = {}

# ============================================================= expressions

BOLT_EYE = Track(  # (width, height) scale of the eyes
    (0, (1, 1)), (21.0, (1, 1)), (21.15, (1.45, 1.45), "o"), (23.0, (1.45, 1.45)), (23.6, (1, 1)),
    (39.0, (1, 1)), (39.5, (1.05, 0.7)), (44.4, (1.05, 0.7)), (44.55, (1.5, 1.5), "o"),
    (51.5, (1.5, 1.5)), (51.7, (1.4, 1.4), "o"), (64.8, (1.4, 1.4)), (65.2, (1.1, 0.55)),
    (78.5, (1.1, 0.55)), (79.0, (1, 1)), (90.5, (1, 1)), (90.7, (1.5, 1.5), "o"), (93.0, (1.5, 1.5)),
    (93.3, (1.1, 0.12)), (97.6, (1.1, 0.12)), (98.0, (1.3, 1.3), "o"), (102, (1.3, 1.3)),
    (102.5, (1, 1)), (106, (1, 1)), (107, (1, 0.8)), (118, (1, 0.8)), (119, (1, 1)),
)
BOLT_HAPPY = Track((0, 0.0), (131.0, 0.0), (131.3, 1.0), (180, 1.0))
BOLT_OMOUTH = Track((0, 0.0), (21.0, 0.0), (21.1, 1.0), (23.3, 1.0), (23.6, 0.0),
                    (44.5, 0.0), (44.6, 1.0), (64.8, 1.0), (79.0, 1.0), (79.4, 0.0),
                    (90.5, 0.0), (90.6, 1.0), (102.3, 1.0), (102.6, 0.0))
BOLT_EYE_TILT = Track((0, 0.0), (106.0, 0.0), (107, 0.35), (118, 0.35), (119, 0.0))
# arm raise (forward) and inward rotation, per side: (raise, inward)
ARM_R = Track((0, (0.15, 0.0)), (41.4, (0.15, 0.0)), (43.6, (1.45, -0.1)), (44.6, (1.55, -0.1)),
              (45.4, (0.2, 0.0), "o"), (47.0, (0.2, 0.0)), (47.3, (0.9, 0.4), "o"),
              (48.5, (0.15, 0.0)), (64.9, (0.15, 0.0)), (65.6, (-0.6, 0.0)), (78.5, (-0.6, 0.0)),
              (79.2, (0.15, 0.0)), (92.8, (0.15, 0.0)), (93.4, (2.55, 0.45), "o"), (97.6, (2.55, 0.45)),
              (100.0, (1.0, 0.2)), (102.5, (0.15, 0.0)), (122.0, (0.15, 0.0)), (123.3, (1.35, 0.0)),
              (128.8, (1.35, 0.0)), (130.0, (1.4, 0.5)), (134.0, (1.4, 0.5)), (135, (0.4, 0.0)),
              (140.0, (2.9, 0.1)), (148.5, (2.9, 0.1)), (149.5, (2.6, -0.2)), (154, (2.6, -0.2)),
              (155.5, (0.15, 0.0)))
ARM_L = Track((0, (0.15, 0.0)), (47.0, (0.15, 0.0)), (47.3, (0.9, 0.4), "o"), (48.5, (0.15, 0.0)),
              (64.9, (0.15, 0.0)), (65.6, (-0.6, 0.0)), (78.5, (-0.6, 0.0)), (79.2, (0.15, 0.0)),
              (92.8, (0.15, 0.0)), (93.4, (2.55, 0.45), "o"), (97.6, (2.55, 0.45)), (99.0, (2.4, 0.4)),
              (101.0, (0.15, 0.0)), (128.8, (0.15, 0.0)), (130.0, (1.4, 0.5)), (134.0, (1.4, 0.5)),
              (135, (0.4, 0.0)), (140.0, (2.9, 0.1)), (148.5, (2.9, 0.1)), (149.5, (2.6, -0.2)),
              (154, (2.6, -0.2)), (155.5, (0.15, 0.0)))
HEAD_ROLL = Track((0, 0.0), (35.4, 0.0), (35.9, 0.28, "b"), (38.8, 0.28), (39.3, 0.0),
                  (101.6, 0.0), (101.9, 0.25, "b"), (104.5, 0.25), (105.0, 0.0),
                  (124.0, 0.0), (124.5, 0.12), (128.5, 0.12), (129.0, 0.0))
BODY_LEAN_SIDE = Track((0, 0.0), (80.6, 0.0), (81.4, 0.32), (82.8, 0.32), (83.3, 0.0),
                       (84.4, 0.0), (85.0, 0.35), (88.0, 0.35), (88.5, 0.0))
SYM_Q = Track((0, 0.0), (35.5, 0.0), (35.8, 1.0, "b"), (38.5, 1.0), (38.8, 0.0),
              (102.1, 0.0), (102.4, 1.0, "b"), (104.6, 1.0), (104.9, 0.0))
SYM_X = Track((0, 0.0), (44.5, 0.0), (44.8, 1.0, "b"), (46.5, 1.0), (46.8, 0.0),
              (47.0, 0.0), (47.2, 1.3, "b"), (49.2, 1.3), (49.5, 0.0))

BAG_EYES_OPEN = Track((0, 0.0), (51.4, 0.0), (51.55, 1.0, "o"), (97.4, 1.0), (97.5, 0.15),
                      (97.9, 0.15), (98.1, 1.3, "o"), (102, 1.3), (103, 1.0), (106.5, 1.0),
                      (107.5, 0.55), (123, 0.55), (124.2, 1.25, "b"), (129, 1.25), (130, 0.32),
                      (180, 0.32))
BAG_MOUTH = Track((0, 0.0), (52.4, 0.0), (52.7, 0.45, "b"), (59.4, 0.45), (59.8, 1.25, "o"),
                  (62.6, 1.25), (63.2, 0.5), (93.0, 0.5), (94.5, 0.9), (97.4, 0.9), (97.5, 1.5, "o"),
                  (98.4, 1.5), (99.0, 0.6), (106.0, 0.6), (107.0, 0.25), (180, 0.25))
BAG_FROWN = Track((0, 0.0), (106.0, 0.0), (107.0, 1.0), (124.5, 1.0), (125.5, 0.0))
BAG_EYE_TILT = Track((0, 0.0), (51.5, 0.0), (51.6, 0.45), (97.4, 0.45), (98, 0.0), (106, 0.0),
                     (107.5, -0.5), (123, -0.5), (124.2, 0.0))
BAG_GLOW = Track((0, 0.0), (44.3, 0.0), (44.5, 0.5), (45.2, 0.0), (51.4, 0.0), (51.6, 1.0, "o"),
                 (59.5, 1.0), (60.2, 2.0), (62.5, 2.0), (63.5, 1.0), (106.0, 1.0), (108.0, 0.25),
                 (124.0, 0.25), (126.0, 0.9), (180, 0.9))
# haunted green -> friendly lilac once they become friends
BAG_TINT = Track((0, (0.4, 1.0, 0.3)), (124.0, (0.4, 1.0, 0.3)), (128.0, (0.85, 0.5, 1.0)))
BAG_SQUASH = Track((0, 0.0), (44.35, 0.0), (44.45, 0.18, "o"), (44.75, -0.1), (45.0, 0.0),
                   (45.8, 0.0), (45.9, 0.25, "o"), (46.2, -0.15), (46.5, 0.05), (46.7, 0.0),
                   (50.0, 0.0), (50.4, -0.15), (51.0, 0.0), (97.5, 0.0), (97.6, -0.3, "o"),
                   (97.9, 0.25), (98.3, 0.0), (106, 0.0), (109, 0.18), (123, 0.18), (124.5, 0.0),
                   (130.5, 0.0), (131.0, 0.25, "o"), (131.6, -0.12), (132.2, 0.0))
TEAR = Track((0, 0.0), (109.0, 0.0), (112.5, 1.0, "l"))


# ===================================================================== camera

def V(*a):
    return Vector(a)


def bolt_head(t, dz=1.0):
    return bolt_pos(t) + V(0, 0, dz)


def bag_c(t, dz=0.0):
    return bag_pos(t) + V(0, 0, dz)


def mid(t):
    return (bolt_pos(t) + bag_pos(t)) * 0.5


def follow(fn, off):
    off = V(*off)
    return lambda t: fn(t) + off


def lin(t0, t1, a, b, ease="s"):
    tr = Track((t0, tuple(a)), (t1, tuple(b), ease))
    return lambda t: V(*tr(t))


def orbit(center_fn, r, z, a0, a1, t0, t1, ease="s"):
    def f(t):
        u = EASES[ease](clamp((t - t0) / (t1 - t0)))
        a = a0 + (a1 - a0) * u
        c = center_fn(t)
        return V(c.x + r * math.cos(a), c.y + r * math.sin(a), c.z + z)
    return f


def fly_cam(t):
    b = bolt_pos(t)
    c = V(FLY_C.x, FLY_C.y, 0)
    out = V(b.x - c.x, b.y - c.y, 0)
    if out.length < 0.5:
        out = V(-1, -0.3, 0)
    return c + out.normalized() * (out.length + 3.2) + V(0, 0, b.z + 0.25)


def const(v):
    v = V(*v)
    return lambda t: v


# (start, end, pos(t), target(t), lens, fstop, shake)
SHOTS = [
    # 1 establishing: crane down from the moon through the branches
    (0, 6, lin(0, 6, (-34, -22, 10), (-37, -7, 1.9)), lin(0, 6, (-36, 30, 24), (-27, 3, 1.6)), 26, 8, 0.0),
    # 2 title in the fog
    (6, 12, lin(6, 12, (-40, -3.5, 2.0), (-40, -1.2, 2.15)), const((-40, 6.5, 2.2)), 32, 5.6, 0.004),
    # 3 Bolt's lamp appears out of the fog
    (12, 17, lin(12, 17, (-23.2, 1.9, 0.42), (-23.5, 1.7, 0.5)), follow(bolt_pos, (0, 0, 0.75)), 35, 4, 0.004),
    # 4 tracking close-up of Bolt
    (17, 21, follow(bolt_pos, (1.55, -1.05, 1.0)), follow(bolt_pos, (0, 0, 0.95)), 50, 2.8, 0.004),
    # 5 the owl eyes: over Bolt's shoulder
    (21, 25, lin(21, 25, (-18.4, -2.0, 1.2), (-18.6, -1.7, 1.25)), lin(21, 25, (-21.3, 3.4, 2.1), (-21.5, 3.7, 2.45)), 30, 4, 0.004),
    # 6 side tracking through the pumpkin patch
    (25, 30, follow(bolt_pos, (0.8, -4.6, 0.75)), follow(bolt_pos, (0.6, 0, 0.55)), 32, 3.5, 0.004),
    # 7 discovery: push past Bolt to the bag on the stump
    (30, 35, lin(30, 35, (-2.9, 0.9, 1.25), (-2.4, 1.0, 1.15)), lin(30, 35, (-0.6, 0.9, 0.9), (-0.3, 1.1, 0.9)), 32, 4, 0.003),
    # 8 Bolt is curious (from behind the bag)
    (35, 39, lin(35, 39, (0.55, 1.25, 1.0), (0.4, 1.0, 1.0)), follow(bolt_pos, (0, 0, 0.95)), 55, 2.8, 0.003),
    # 9 the slow reach
    (39, 44, lin(39, 44, (0.1, -1.9, 0.85), (0.05, -1.45, 0.85)), const((-0.3, 1.2, 0.75)), 38, 4, 0.003),
    # 10 extreme close-up: the bag twitches
    (44, 47, lin(44, 47, (1.0, -0.3, 1.1), (0.85, -0.1, 1.05)), const((-0.15, 1.4, 0.9)), 30, 2.8, 0.004),
    # 11 Bolt jumps back
    (47, 50, const((-0.3, 2.1, 1.0)), lin(47, 50, (-0.6, 0.6, 0.75), (-1.2, -0.1, 0.75)), 28, 4, 0.006),
    # 12 low angle: the bag rises
    (50, 55, lin(50, 55, (0.9, -0.6, 0.3), (0.75, -0.3, 0.35)), lambda t: bag_c(t, 0.05), 24, 5.6, 0.006),
    # 13 Bolt shaking
    (55, 59, const((-0.7, 0.7, 1.15)), follow(bolt_pos, (0, 0, 0.9)), 35, 2.8, 0.01),
    # 14 WOOOO: pumpkins light up in a wave
    (59, 61.5, lin(59, 61.5, (-10.8, -2.7, 0.7), (-10.5, -2.55, 0.75)), lin(59, 61.5, (-2.0, 0.6, 1.2), (-1.6, 0.7, 1.25)), 30, 8, 0.006),
    # 14b close-up: the bag's WOOOO
    (61.5, 64, lin(61.5, 64, (-1.05, 0.3, 1.2), (-0.85, 0.5, 1.3)), lambda t: bag_c(t, 0.0), 32, 2.8, 0.008),
    # 15 Bolt spins and runs at the camera
    (64, 68, const((-5.8, -1.7, 0.6)), follow(bolt_pos, (0, 0, 0.7)), 26, 4, 0.008),
    # 16 chase: tracking through the pumpkins
    (68, 71, follow(bolt_pos, (-0.6, 4.7, 1.1)), follow(bolt_pos, (-0.8, 0, 0.75)), 30, 4, 0.008),
    # 16b running at the camera, the bag looming behind him
    (71, 74, follow(bolt_pos, (-2.3, -0.6, 0.55)), lambda t: bolt_pos(t) * 0.6 + bag_pos(t) * 0.4 + V(0, 0, 0.35), 28, 5.6, 0.01),
    # 17 into the graveyard
    (74, 79, const((-22.8, -0.7, 0.45)), follow(bolt_pos, (0, 0, 0.7)), 28, 4, 0.006),
    # 18 Bolt hides behind a gravestone
    (79, 83, lin(79, 83, (-20.6, -5.6, 0.8), (-20.4, -5.2, 0.8)), const((-19.1, -2.8, 0.85)), 40, 4, 0.004),
    # 19 POV peeking: the bag searches
    (83, 88, const((-18.35, -2.9, 0.95)), lambda t: bag_c(t), 45, 2.0, 0.006),
    # 20 the bag's close-up: spotted?
    (88, 93, lin(88, 93, (-17.8, -2.9, 1.25), (-17.9, -2.8, 1.25)), lambda t: bag_c(t, 0.02), 28, 2.8, 0.004),
    # 21 the bag looms over the stone
    (93, 97, const((-17.6, -4.1, 0.5)), lambda t: bag_c(t, -0.25), 24, 5.6, 0.006),
    # 22 HIC! candy bursts out
    (97, 102, lin(97, 102, (-15.6, -5.2, 1.6), (-15.9, -5.0, 1.5)), const((-19.0, -2.6, 1.05)), 30, 5.6, 0.006),
    # 23 Bolt peeks, candy on his head
    (102, 106, const((-18.2, -2.3, 1.3)), follow(bolt_pos, (0, 0, 1.0)), 30, 2.8, 0.003),
    # 24 the sad bag
    (106, 112, lin(106, 112, (-19.0, 0.4, 0.62), (-19.05, 0.15, 0.55)), lambda t: bag_c(t, 0.02), 50, 2.8, 0.002),
    # 25 wide: lonely in the moonlight
    (112, 118, lin(112, 118, (-12.5, 3.5, 2.8), (-13.6, 2.6, 2.1)), const((-19.0, -1.6, 0.6)), 35, 6, 0.002),
    # 26 Bolt rolls over and offers his hand
    (118, 121, lin(118, 121, (-15.6, -4.9, 1.0), (-15.9, -4.6, 1.0)), follow(bolt_pos, (0, 0, 0.6)), 32, 4, 0.002),
    # 26b the offered hand
    (121, 124, lin(121, 124, (-18.3, 0.9, 0.9), (-18.4, 0.7, 0.88)), const((-18.5, -1.1, 0.62)), 40, 2.8, 0.002),
    # 27 hope: over Bolt's shoulder onto the bag
    (124, 129, lin(124, 129, (-17.6, 0.35, 0.95), (-17.75, 0.2, 0.95)), lambda t: bag_c(t, 0.05), 28, 2.8, 0.002),
    # 28 the hug + hearts
    (129, 134, lin(129, 134, (-18.4, 1.3, 1.0), (-18.3, 0.9, 1.05)), const((-18.25, -1.2, 0.8)), 40, 4, 0.002),
    # 29 candy ring: orbit around the new friends
    (134, 137, orbit(lambda t: V(-18.25, -1.1, 0), 3.3, 1.2, 0.35, 0.85, 134, 137), const((-18.25, -1.1, 1.0)), 32, 4, 0.002),
    # 29b Bolt's happy face, candy circling
    (137, 140, lin(137, 140, (-18.0, 1.7, 1.3), (-18.05, 1.5, 1.25)), lambda t: bolt_pos(t) * 0.75 + bag_pos(t) * 0.25 + V(0, 0, 0.75), 45, 2.8, 0.002),
    # 30 they fly over the pumpkin patch
    (140, 143.5, fly_cam, lambda t: bolt_pos(t) + V(0, 0, 0.9), 26, 8, 0.004),
    # 30b low wide: flying over the lit pumpkins
    (143.5, 147, lin(143.5, 147, (-6.0, -6.4, 0.35), (-6.6, -6.1, 0.4)), lambda t: bolt_pos(t) * 0.5 + V(-4.5, 0.75, 1.6), 22, 8, 0.004),
    # 31 hero orbit: lit pumpkins, fireflies, dance
    (147, 150.5, orbit(lambda t: V(-4.6, 0.0, 0), 4.2, 1.5, -1.35, -0.85, 147, 150.5), const((-4.2, 0.0, 1.0)), 30, 6, 0.003),
    # 31b the happy spin
    (150.5, 154, lin(150.5, 154, (-4.2, -2.5, 1.05), (-4.0, -2.3, 1.05)), const((-4.0, -0.1, 1.15)), 35, 4, 0.003),
    # 32 walking home: the house lights up warm
    (154, 156.5, follow(bolt_pos, (-3.4, -2.3, 0.9)), lin(154, 156.5, (6, 6, 2.6), (14, 10, 3.2)), 32, 8, 0.004),
    # 32b the haunted house lights up, window by window
    (156.5, 160, lin(156.5, 160, (16.5, 4.5, 2.2), (17.5, 6.0, 2.7)), const((30.0, 22.0, 6.0)), 38, 8, 0.002),
    # 33 front tracking: best friends
    (160, 163, follow(bolt_pos, (3.0, 1.0, 0.95)), follow(bolt_pos, (0, 0, 1.0)), 45, 2.8, 0.004),
    # 33b side tracking
    (163, 166, follow(bolt_pos, (0.4, -3.3, 0.85)), follow(bolt_pos, (0.4, 0, 0.9)), 35, 4, 0.004),
    # 34 crane up past the moon
    (166, 171, lin(166, 171, (12.0, -3.2, 1.3), (11.0, -5.5, 7.5)), lin(166, 171, (17.5, 2.0, 1.2), (20.0, 30.0, 18.0)), 30, 8, 0.0),
    # 35 THE END...?
    (171, 175, lin(171, 175, (13.5, -3.6, 1.7), (15.0, -1.8, 1.8)), lin(171, 175, (23.0, 9.0, 4.0), (22.5, 10.0, 4.6)), 30, 8, 0.002),
    # 36 the wink
    (175, 180, lambda t: bolt_pos(t) + V(-1.6, -2.6, 1.35), lambda t: bag_c(t, -0.15), 40, 2.8, 0.002),
]


def shot_at(t):
    for s in SHOTS:
        if s[0] <= t < s[1]:
            return s
    return SHOTS[-1]


def cam_state(t):
    t0, t1, pos, tgt, lens, fstop, shake = shot_at(t)
    p, g = Vector(pos(t)), Vector(tgt(t))
    if shake:
        k = 1.0 + 3.0 * window(t, 52.1, 52.9, 0.1) + 2.0 * window(t, 97.5, 98.4, 0.1)
        for i in range(3):
            p[i] += wob(t, 1.3, i) * shake * 6 * k
            g[i] += wob(t, 1.1, i + 5) * shake * 10 * k
    return p, g, lens, fstop


# ===================================================================== apply


def setv(obj, v, attr="default_value"):
    if abs(getattr(obj, attr) - v) > 1e-5:
        setattr(obj, attr, v)


def set_vis(o, s):
    o.scale = (s, s, s) if not hasattr(s, "__len__") else s
    o.hide_render = (s == 0) if not hasattr(s, "__len__") else False


def billboard(o, cam_obj, pos, size):
    o.location = pos
    o.rotation_euler = cam_obj.matrix_world.to_euler()
    set_vis(o, size)


def apply(t):
    cam = SC.camera
    p, g, lens, fstop = cam_state(t)
    cam.location = p
    cam.rotation_euler = (g - p).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = max(0.2, (g - p).length)
    cam.data.dof.aperture_fstop = fstop
    cam.matrix_world = Matrix.Translation(p) @ cam.rotation_euler.to_matrix().to_4x4()

    # --- atmosphere
    dens = 0.04 + 0.02 * window(t, 6, 12, 1) - 0.012 * window(t, 147, 180, 2)
    # only touch shared shader/world values when they change: any write makes Eevee
    # re-sync every material and re-bake the world lighting
    setv(FOG.nodes["density"].inputs[1], -round(dens, 4))
    flash = window(t, 52.15, 52.45, 0.03) + 0.6 * window(t, 52.6, 52.72, 0.03)
    setv(ENV["sun"].data, 1.6 + 9.0 * round(flash, 3), "energy")
    setv(SC.world.node_tree.nodes["bg"].inputs["Strength"], 1.0 + 5.0 * round(flash, 3))
    for c, base in ENV["fogcards"]:
        c.location = base + Vector((0.12 * t % 8 - 4, 0.05 * math.sin(t * 0.1), 0))

    # --- Bolt
    fi = fidx(t)
    bp = bolt_pos(t)
    B = BOLT
    B["root"].location = bp
    B["root"].rotation_euler = (0, 0, BOLT_YAW[fi])
    dist = DIST[fi]
    B["wheel"].rotation_euler = (-dist / 0.17, 0, 0)
    sp = SPEED[fi]
    shake = 0.05 * window(t, 51.6, 64.8, 0.3) + 0.03 * window(t, 79, 93, 0.5) + 0.06 * window(t, 93.2, 97.6, 0.2)
    lean = clamp(sp * 0.07, 0, 0.3)
    side = BODY_LEAN_SIDE(t)
    if 142 <= t < 146.5:
        side += 0.35
    B["tilt"].rotation_euler = (-lean + shake * wob(t, 25, 1), -side + shake * wob(t, 27, 2), 0)
    look = 0.35 * math.sin(t * 0.9) * window(t, 12.5, 20.5, 1) + 0.4 * wob(t, 0.6, 9) * window(t, 79, 93, 0.5)
    B["head"].rotation_euler = (-0.12 * window(t, 39, 44, 0.5), -HEAD_ROLL(t), look)
    ew, eh = BOLT_EYE(t)
    blink = 0.0
    for bt in (14.2, 18.6, 26.0, 32.4, 37.4, 55.8, 82.0, 86.1, 110.0, 114.6, 120.8, 126.4, 158.0, 163.2, 170.0):
        blink = max(blink, window(t, bt, bt + 0.14, 0.05))
    eh *= (1 - 0.92 * blink)
    happy = BOLT_HAPPY(t)
    tilt = BOLT_EYE_TILT(t)
    tremble = 0.006 * wob(t, 30, 3) * (window(t, 51.6, 64.8, 0.3) + window(t, 90.6, 93, 0.2))
    for i, e in enumerate(B["eyes"]):
        sx = -1 if i == 0 else 1
        e.scale = (0.045 * ew * (1 - happy), 0.02, max(0.0005, 0.075 * eh * (1 - happy)))
        e.hide_render = happy > 0.5
        e.location = (sx * 0.12 + tremble + 0.03 * math.sin(look), 0.24, 0.24 + tremble)
        e.rotation_euler = (0, sx * tilt, 0)
    for h in B["happy"]:
        set_vis(h, happy)
    om = BOLT_OMOUTH(t)
    set_vis(B["omouth"], (0.8 + 0.4 * om * (0.85 + 0.15 * math.sin(t * 9))) * om)
    set_vis(B["smile"], (1 - om) * (1 + 0.35 * happy))
    for arm, tr, sx in ((B["arms"][1], ARM_R, 1), (B["arms"][0], ARM_L, -1)):
        r, inward = tr(t)
        if 64.9 < t < 78.5:  # pumping arms while running
            r += 0.6 * math.sin(t * 14 + (0 if sx > 0 else math.pi)) * smooth((t - 65.6) / 0.4)
        if 148.5 <= t < 154 or 160 <= t < 171:
            r += 0.25 * math.sin(t * 6 + (0 if sx > 0 else math.pi))
        arm.rotation_euler = (r, 0, sx * inward)
    flick = 1.0 - 0.6 * window(t, 51.6, 64, 0.2) * (0.5 + 0.5 * math.sin(t * 37) * math.sin(t * 13))
    B["bulb"].color = (1.0 * flick, 0.65 * flick, 0.25 * flick, 1)
    setv(B["lamp"].data, round(22 * flick, 2), "energy")
    B["btn"].color = (1.0, 0.35 + 0.3 * math.sin(t * 3), 0.2, 1)
    sym_base = bp + V(0.32, 0, 1.55)
    billboard(B["sym"]["?"], cam, sym_base, SYM_Q(t))
    billboard(B["sym"]["!"], cam, sym_base, SYM_X(t))

    place_blob(PROPS["blob_bolt"], bp, 0.42, 0.85)

    # --- Bag
    G = BAG
    gp = bag_pos(t)
    G["root"].location = gp
    place_blob(PROPS["blob_bag"], gp - V(0, 0, 0.28), 0.36, 0.8)
    G["root"].rotation_euler = (0, 0, BAG_YAW[fi])
    sq = BAG_SQUASH(t)
    if 131 <= t < 134:
        sq += 0.06 * math.sin(t * 9)
    G["body"].scale = (1 + sq * 0.5, 1 + sq * 0.5, 1 - sq)
    float_sway = BAG_HOVER(t) if t < 106 else (0.6 if t > 124 else 0.0)
    G["body"].rotation_euler = (0.08 * math.sin(t * 1.7) * float_sway, 0.1 * math.sin(t * 1.3) * float_sway, 0)
    if 154 <= t:
        G["body"].rotation_euler = (0.25, 0, 0)
    eo = BAG_EYES_OPEN(t)
    blink = max(window(t, bt, bt + 0.14, 0.05) for bt in (86.9, 113.0, 136.0, 162.5))
    tint = BAG_TINT(t)
    tilt = BAG_EYE_TILT(t)
    for i, e in enumerate(G["eyes"]):
        sx = -1 if i == 0 else 1
        wink = window(t, 175.5, 176.4, 0.08) if i == 0 else 0.0
        h = eo * (1 - blink) * (1 - 0.95 * wink)
        e.scale = (0.05 * (1 + 0.15 * (eo > 1.1)), 0.02, max(0.0005, 0.06 * h))
        e.hide_render = h < 0.02
        e.rotation_euler = (0, sx * tilt, 0)
        e.color = (*tint, 1)
    mo = BAG_MOUTH(t)
    if 59.8 <= t < 62.6:
        mo += 0.12 * math.sin(t * 20)
    fr = BAG_FROWN(t)
    G["mouth"].scale = (1 - 0.3 * fr, 1, max(0.02, mo))
    G["mouth"].rotation_euler = (0, math.pi * fr, 0)
    G["mouth"].hide_render = mo <= 0.02
    tr = TEAR(t)
    G["tear"].location = (0.11, 0.268, 0.03 - 0.17 * tr)
    set_vis(G["tear"], 1.0 if 109.0 < t < 112.4 else 0.0)
    glow = BAG_GLOW(t) * (0.85 + 0.15 * math.sin(t * 4))
    setv(G["glow"].data, round(9 * glow, 2), "energy")
    if tuple(G["glow"].data.color) != tuple(tint):
        G["glow"].data.color = tint
    for o in G["body"].children:
        if o.name.startswith(("bag_sack", "bag_tuft")):
            o.color = (*tint, glow * 0.6)

    # --- environment
    for root, face, i in ENV["pumpkins"]:
        on = smooth((t - (59.3 + i * 0.28)) / 0.25)
        if t >= 155:
            on = max(on, 1.0)
        fl = on * (0.8 + 0.2 * math.sin(t * 11 + i * 2.1) * math.sin(t * 7.3 + i))
        face.color = (1.0 * fl, 0.42 * fl, 0.08 * fl, 1)
    lit = smooth((t - 60) / 3)
    for k, L in enumerate(ENV["pumpkin_lights"]):
        setv(L.data, round(70 * lit * (0.85 + 0.15 * math.sin(t * 9 + k)), 1), "energy")
    for k, e in enumerate(ENV["owl_eyes"]):
        o = window(t, 20.8, 24.2, 0.1) * (1 - window(t, 22.5, 22.65, 0.04))
        e.scale = (1, 1, max(0.02, o))
        e.hide_render = o < 0.05
        e.color = (1, 0.85, 0.2, 1)
    warm = smooth((t - 156.6) / 3)
    woo = window(t, 59.5, 63, 0.3)
    for k, w in enumerate(ENV["windows"]):
        wk = smooth((t - 156.6 - k * 0.25) / 0.6)
        c = lerp((0.3, 0.16, 0.55), (1.0, 0.68, 0.3), wk)
        c = lerp(c, (0.4, 1.0, 0.3), woo * (0.5 + 0.5 * math.sin(t * 13 + k)))
        b = 0.12 + 0.88 * wk
        w.color = (c[0] * b, c[1] * b, c[2] * b, 1)
    ENV["door"].color = (0.8 * warm, 0.5 * warm, 0.2 * warm, 1)

    # fireflies: ghostly green wisps that turn into warm golden fireflies
    fw = smooth((t - 126) / 10)
    fcol = lerp((0.35, 1.0, 0.45), (1.0, 0.8, 0.3), fw)
    fb = 0.25 + 0.75 * fw
    for o, base, ph in PROPS["flies"]:
        o.location = base + Vector((wob(t, 0.15, ph) * 1.5, wob(t, 0.15, ph + 3) * 1.5,
                                    wob(t, 0.2, ph + 6) * 0.5))
        tw = fb * (0.55 + 0.45 * math.sin(t * 3 + ph))
        o.color = (fcol[0] * tw, fcol[1] * tw, fcol[2] * tw, 1)

    # candy
    candies = PROPS["candy"]
    ring_c = (bolt_pos(t) + bag_pos(t)) * 0.5
    for i, o in enumerate(candies):
        cp = CANDY[i](t)
        if cp is None:
            set_vis(o, 0)
            continue
        if 134.0 <= t < 147.0 and i > 0:
            a = TAU * i / (len(candies) - 1) + (t - 134) * 1.6
            ring = ring_c + V(1.15 * math.cos(a), 1.15 * math.sin(a), 0.75 + 0.12 * math.sin(a * 3 + t * 2))
            u = smooth((t - 134 - i * 0.04) / 1.2)
            cp = cp.lerp(ring, u)
            s = 1.0 - smooth((t - 146.2) / 0.5)
        else:
            s = 1.0 if t < 147.0 or i == 0 else 0.0
        o.location = cp
        o.rotation_euler = (t * 3 + i, t * 2.1 + i * 2, i)
        set_vis(o, s * (1.25 if i == 0 else 1.0))

    # hearts
    for i, o in enumerate(PROPS["hearts"]):
        t0 = 130.3 + i * 0.55
        u = (t - t0) / 3.2
        if 0 <= u <= 1:
            base = V(-18.2, -1.2, 1.2)
            o.location = base + V(0.6 * math.sin(i * 2.4 + u * 4), 0.3 * math.cos(i * 1.7), 0.2 + u * 1.7)
            o.rotation_euler = (math.pi / 2, 0, cam.rotation_euler.z + 0.3 * math.sin(u * 6))
            set_vis(o, math.sin(min(u * 4, 1) * math.pi / 2) * (1 - smooth((u - 0.7) / 0.3)) * 1.3)
        else:
            set_vis(o, 0)

    # bats crossing in front of the camera
    fwd = (g - p).normalized()
    right = fwd.cross(V(0, 0, 1)).normalized()
    up = right.cross(fwd)
    for i, (o, wings) in enumerate(PROPS["bats"]):
        vis = False
        for w0, w1, d0, h0 in ((0.4, 6.0, 9.0, 1.2), (68.6, 73.8, 5.5, 0.6), (166.4, 171.0, 8.0, 0.8)):
            if w0 <= t < w1:
                u = (t - w0 - i * 0.3) / (w1 - w0 - 1.5)
                if 0 <= u <= 1:
                    d = d0 + (i % 3) * 1.3
                    span = d * 0.9
                    pos = p + fwd * d + right * (-span + 2 * span * u) + up * (h0 + 0.35 * math.sin(i * 2 + t * 3) + (i % 2) * 0.5)
                    o.location = pos
                    o.rotation_euler = (0.2 * math.sin(t * 5 + i), 0, yaw_to(right.x, right.y))
                    flap = math.sin(t * 22 + i * 1.3)
                    for k, wp in enumerate(wings):
                        wp.rotation_euler = (0, (1 if k == 0 else -1) * 0.9 * flap, 0)
                    vis = True
        set_vis(o, 1.0 if vis else 0.0)
        for c in o.children_recursive:
            c.hide_render = not vis

    # titles
    tvis = 1.0 if 6.0 <= t < 12.0 else 0.0
    PROPS["title"].hide_render = not tvis
    fl = smooth((t - 6.3) / 0.5) * (1 - 0.7 * window(t, 7.0, 7.12, 0.03) - 0.6 * window(t, 7.4, 7.5, 0.03))
    PROPS["title"].color = (1.0 * fl, 0.4 * fl, 0.06 * fl, 1)
    PROPS["title"].scale = (1 + 0.03 * (t - 6),) * 3
    fwd0 = (g - p).normalized()
    up0 = fwd0.cross(V(0, 0, 1)).normalized().cross(fwd0)
    ev = t >= 171.0 and t < 175.0
    PROPS["theend"].hide_render = not ev
    if ev:
        PROPS["theend"].rotation_euler = cam.matrix_world.to_euler()
        PROPS["theend"].location = p + fwd0 * 9.0 + up0 * 1.6
        fl = smooth((t - 171.5) / 0.8)
        PROPS["theend"].color = (1.0 * fl, 0.4 * fl, 0.06 * fl, 1)


def on_frame(scene, depsgraph=None):
    apply(scene.frame_current / FPS)


# ============================================================ precompute


def precompute():
    global BOLT_YAW, BAG_YAW, DIST, SPEED, CANDY
    BOLT_YAW[:] = precompute_yaw(bolt_xy, bolt_face, 0.16, extra=bolt_spin)
    DIST, SPEED = [0.0], [0.0]
    prev = bolt_pos(0)
    for f in range(1, NFRAMES + 1):
        cur = bolt_pos(f / FPS)
        d = (Vector((cur.x, cur.y)) - Vector((prev.x, prev.y))).length
        DIST.append(DIST[-1] + d)
        SPEED.append(d * FPS)
        prev = cur
    # camera positions for the bag's final look-at-the-camera
    for f in range(fidx(173.5), NFRAMES + 1):
        CAM_TRACE[f] = cam_state(f / FPS)[0]
    BAG_YAW[:] = precompute_yaw(lambda t: tuple(bag_pos(t))[:2] if t < 154 else bolt_xy(t),
                                bag_face, 0.12)
    CANDY = [candy_track(i) for i in range(len(PROPS["candy"]))]


def candy_track(i):
    """Ballistic candy from the bag's mouth, with a couple of bounces."""
    rnd = random.Random(100 + i)
    t_launch = 98.0 + i * 0.035
    mouth = bag_pos(t_launch) + V(0, -0.3, -0.05)
    if i == 0:  # the one that lands on Bolt's head (a running gag to the end)
        def head(t):
            if t < 100.6:
                return None
            yaw = BOLT_YAW[fidx(t)]
            top = bolt_pos(t) + Matrix.Rotation(yaw, 3, "Z") @ V(-0.05, 0, 1.25)
            if t < 101.5:
                u = (t - 100.6) / 0.9
                start = bag_pos(100.6) + V(0, -0.3, -0.05)
                return start.lerp(top, u) + V(0, 0, 0.7 * math.sin(u * math.pi))
            return top
        return head
    a = rnd.uniform(-1.6, 1.6) + math.pi * 1.5
    spd = rnd.uniform(1.0, 2.6)
    vel = V(math.cos(a) * spd, math.sin(a) * spd, rnd.uniform(1.5, 3.8))
    pts = []
    pos = mouth.copy()
    dt = 1 / FPS
    for _ in range(int(9 * FPS)):
        pts.append(pos.copy())
        vel.z -= 9.8 * dt
        pos += vel * dt
        floor = ground_h(pos.x, pos.y) + 0.04
        if (pos - V(STONE.x, STONE.y, pos.z)).length < 0.5 and pos.z < 1.2:
            vel.x, vel.y = -vel.x * 0.4, -vel.y * 0.4
        if pos.z < floor:
            pos.z = floor
            vel.z = -vel.z * 0.35
            vel.x *= 0.6
            vel.y *= 0.6
            if abs(vel.z) < 0.4:
                vel = V(0, 0, 0)

    def f(t):
        if t < t_launch:
            return None
        k = int((t - t_launch) * FPS)
        return pts[min(k, len(pts) - 1)].copy()
    return f


# ================================================================ render setup


def setup_render(samples, pct):
    SC.render.engine = "BLENDER_EEVEE"
    SC.render.resolution_x, SC.render.resolution_y = RES
    SC.render.resolution_percentage = pct
    SC.render.fps = FPS
    SC.frame_start, SC.frame_end = 0, NFRAMES - 1
    SC.render.image_settings.file_format = "PNG"
    SC.render.image_settings.color_mode = "RGB"
    SC.render.use_overwrite = False
    SC.render.use_placeholder = True
    SC.eevee.taa_render_samples = samples
    # shadow maps cost ~3 s/frame on a CPU (llvmpipe); characters get soft contact
    # shadows instead (see build_blobs). Pass --shadows on a GPU for real ones.
    for k, v in (("use_raytracing", False), ("use_shadows", SHADOWS), ("shadow_ray_count", 1),
                 ("shadow_step_count", 4), ("use_gtao", True), ("use_volumetric_shadows", False)):
        if hasattr(SC.eevee, k):
            setattr(SC.eevee, k, v)
    SC.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "AgX - Punchy", "None"):
        try:
            SC.view_settings.look = look
            break
        except TypeError:
            continue
    SC.view_settings.exposure = 0.35
    cd = bpy.data.cameras.new("cam")
    cd.sensor_width = 36
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.05
    cd.clip_end = 600
    cd.dof.use_dof = True
    SC.camera = link(bpy.data.objects.new("cam", cd))


def build_all(samples=6, pct=100):
    build_materials()
    build_world()
    build_ground()
    build_trees()
    build_stump()
    build_graveyard()
    build_pumpkins()
    build_house()
    build_sky_props()
    build_lights()
    build_bolt()
    build_bag()
    build_props()
    build_blobs()
    setup_render(samples, pct)
    precompute()
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(on_frame)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", action="store_true")
    ap.add_argument("--shots", default="", help="comma list of shot numbers for --storyboard")
    ap.add_argument("--at", default="", help="comma list of times (s) to render as stills")
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--samples", type=int, default=6)
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--out", default=os.path.join(WORK, "frames"))
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--save", default="")
    ap.add_argument("--shadows", action="store_true", help="real shadow maps (use on a GPU)")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    a = ap.parse_args(argv)
    build_all(a.samples, a.pct)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
    if a.storyboard or a.at:
        out = os.path.join(WORK, "story")
        os.makedirs(out, exist_ok=True)
        if a.at:
            times = [(f"t{float(x):07.2f}", float(x)) for x in a.at.split(",")]
        else:
            pick = [int(x) for x in a.shots.split(",")] if a.shots else range(1, len(SHOTS) + 1)
            times = []
            for n in pick:
                s0, s1 = SHOTS[n - 1][:2]
                for k, u in enumerate((0.15, 0.85)):
                    times.append((f"s{n:02d}_{k}", s0 + (s1 - s0) * u))
        SC.render.use_overwrite = True
        SC.render.use_placeholder = False
        for name, t in times:
            SC.frame_set(fidx(t))
            SC.render.filepath = os.path.join(out, name + ".png")
            bpy.ops.render.render(write_still=True)
        return
    if a.frames:
        os.makedirs(a.out, exist_ok=True)
        SC.frame_start, SC.frame_end = a.frames[0], a.frames[1] - 1
        SC.frame_step = a.step
        SC.render.filepath = os.path.join(a.out, "f_#####")
        bpy.ops.render.render(animation=True)


DIST, SPEED, CANDY = [], [], []

if __name__ == "__main__":
    main()
