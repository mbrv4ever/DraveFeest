# -*- coding: utf-8 -*-
# bouw_bergen.py - rendert het 3D-bergpanorama achter de dorpsstraat van DraveFeest.
# (c) 2026 Dravenlock (Roger & Claudio). GNU GPL v3.0.
# Gebruik:  blender -b --factory-startup -P bouw_bergen.py -- <uitmap> <seizoen> <dag|avond> [snel]
#           seizoen = winter | lente | zomer | herfst
# Maakt:    bergen_<seizoen>_<dag|avond>.png  (1920 x 480, lucht doorzichtig)
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, noise

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
UIT = os.path.abspath(args[0]) if args else os.path.abspath("render")
SEIZOEN = args[1] if len(args) > 1 else "winter"
AVOND = len(args) > 2 and args[2] == "avond"
SNEL = "snel" in args
os.makedirs(UIT, exist_ok=True)
W, H = 1920, 480
BREED = 200.0                     # wereldbreedte die in beeld komt (x van -100 tot 100)
random.seed(21)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 50 if SNEL else 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
try:
    sc.eevee.taa_render_samples = 16 if SNEL else 48
except Exception:
    pass
try:
    sc.view_settings.view_transform = "Standard"
except Exception:
    pass
sc.view_settings.exposure = 0.0

# ------------------------------------------------------------------ seizoenskleuren
S = {
    "winter": dict(sneeuw=-5.0, gras=(0.80, 0.86, 0.95), bos=(0.10, 0.25, 0.16), loof=None),
    "lente":  dict(sneeuw=20.0, gras=(0.20, 0.48, 0.10), bos=(0.10, 0.36, 0.14), loof=[(0.35, 0.70, 0.20), (0.95, 0.70, 0.85), (0.98, 0.98, 0.95)]),
    "zomer":  dict(sneeuw=26.0, gras=(0.26, 0.46, 0.08), bos=(0.08, 0.32, 0.10), loof=[(0.20, 0.50, 0.12), (0.28, 0.58, 0.16)]),
    "herfst": dict(sneeuw=22.0, gras=(0.40, 0.30, 0.08), bos=(0.12, 0.28, 0.14), loof=[(0.90, 0.45, 0.10), (0.80, 0.20, 0.08), (0.95, 0.75, 0.15), (0.55, 0.30, 0.10)]),
}[SEIZOEN]
ROTS = (0.36, 0.33, 0.31)
NEVEL = (0.18, 0.16, 0.40) if AVOND else {"winter": (0.70, 0.80, 0.92), "herfst": (0.92, 0.78, 0.62)}.get(SEIZOEN, (0.68, 0.84, 0.98))

def node(nt, soort, **kw):
    n = nt.nodes.new(soort)
    for k, v in kw.items():
        n.inputs[k].default_value = v
    return n

def grond_mat(naam, nevel):
    """Rots / gras / sneeuw op hoogte en helling, met wat nevel voor de verre bergen."""
    m = bpy.data.materials.new(naam); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.95
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sep_n.inputs[0])
    sep_p = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep_p.inputs[0])
    ruis = node(nt, "ShaderNodeTexNoise", Scale=0.15); nt.links.new(geo.outputs["Position"], ruis.inputs["Vector"])
    # gras -> rots: steile hellingen en hoger dan 10 zijn rots
    hel = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sep_n.outputs["Z"], hel.inputs[0])
    hel.inputs[1].default_value, hel.inputs[2].default_value = 0.55, 0.85      # 0 = steil (rots), 1 = vlak (gras)
    hoog = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sep_p.outputs["Z"], hoog.inputs[0])
    hoog.inputs[1].default_value, hoog.inputs[2].default_value = 16, 9         # boven 16 geen gras meer
    gf = nt.nodes.new("ShaderNodeMath"); gf.operation = "MULTIPLY"
    nt.links.new(hel.outputs[0], gf.inputs[0]); nt.links.new(hoog.outputs[0], gf.inputs[1])
    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    nt.links.new(gf.outputs[0], mix1.inputs[0])
    mix1.inputs[6].default_value = (*ROTS, 1); mix1.inputs[7].default_value = (*S["gras"], 1)
    # sneeuw: boven de sneeuwlijn (met ruis) en niet te steil
    zr = nt.nodes.new("ShaderNodeMath"); zr.operation = "MULTIPLY_ADD"
    nt.links.new(ruis.outputs["Fac"], zr.inputs[0]); zr.inputs[1].default_value = 8.0
    nt.links.new(sep_p.outputs["Z"], zr.inputs[2])
    sn = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(zr.outputs[0], sn.inputs[0])
    sn.inputs[1].default_value, sn.inputs[2].default_value = S["sneeuw"] + 3, S["sneeuw"] + 5
    hel2 = nt.nodes.new("ShaderNodeMapRange"); nt.links.new(sep_n.outputs["Z"], hel2.inputs[0])
    hel2.inputs[1].default_value, hel2.inputs[2].default_value = 0.35, 0.6
    sf = nt.nodes.new("ShaderNodeMath"); sf.operation = "MULTIPLY"
    nt.links.new(sn.outputs[0], sf.inputs[0]); nt.links.new(hel2.outputs[0], sf.inputs[1])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    nt.links.new(sf.outputs[0], mix2.inputs[0]); nt.links.new(mix1.outputs[2], mix2.inputs[6])
    mix2.inputs[7].default_value = (0.95, 0.97, 1.0, 1)
    nt.links.new(mix2.outputs[2], p.inputs["Base Color"])
    if nevel:   # nevel als zachte gloed in de nevelkleur
        p.inputs["Emission Color"].default_value = (*NEVEL, 1)
        p.inputs["Emission Strength"].default_value = nevel
    return m

def effen(naam, kleur, emissie=0.0, ruw=0.9):
    m = bpy.data.materials.new(naam); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*kleur, 1); p.inputs["Roughness"].default_value = ruw
    if emissie:
        p.inputs["Emission Color"].default_value = (*kleur, 1); p.inputs["Emission Strength"].default_value = emissie
    return m

# ------------------------------------------------------------------ hoogtes
def h_ver(x, y):
    """Verre bergketen: scherpe toppen, hoogte tot ~32."""
    r = noise.ridged_multi_fractal(Vector((x * 0.035, y * 0.04, 3.1)), 0.9, 2.1, 5, 1.0, 2.0, noise_basis="PERLIN_ORIGINAL")
    golf = 0.8 + 0.3 * math.sin(x * 0.07 + 1.3) + 0.2 * math.sin(x * 0.19)
    diep = math.sin(math.pi * min(1, max(0, (y - 55) / 60)))     # midden van de strook het hoogst
    return max(0.0, r * 17.0 * golf * diep - 1)

def h_dicht(x, y):
    """Heuvels dichtbij: zacht golvend, hoogte tot ~13."""
    n = noise.fractal(Vector((x * 0.03, y * 0.05, 7.7)), 1.0, 2.0, 4, noise_basis="PERLIN_ORIGINAL")
    golf = 6 + 4 * math.sin(x * 0.06 + 0.4) + 2.5 * math.sin(x * 0.17 + 2)
    diep = math.sin(math.pi * min(1, max(0, (y - 2) / 36)))
    return max(0.0, (golf + n * 4) * diep)

def raster(naam, f, y0, y1, nx, ny, mat):
    bm = bmesh.new()
    xs = [-BREED / 2 - 20 + (BREED + 40) * i / nx for i in range(nx + 1)]
    ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    v = [[bm.verts.new((x, y, f(x, y))) for x in xs] for y in ys]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((v[j][i], v[j][i + 1], v[j + 1][i + 1], v[j + 1][i]))
    bm.verts.index_update()
    me = bpy.data.meshes.new(naam); bm.to_mesh(me); bm.free()
    for pg in me.polygons:
        pg.use_smooth = True
    o = bpy.data.objects.new(naam, me); o.data.materials.append(mat); sc.collection.objects.link(o)
    return o

raster("ver", h_ver, 55, 115, 360 if not SNEL else 180, 60 if not SNEL else 30, grond_mat("ver_mat", 0.18 if not AVOND else 0.12))
raster("dicht", h_dicht, 2, 38, 300 if not SNEL else 150, 36 if not SNEL else 18, grond_mat("dicht_mat", 0.0))

# ------------------------------------------------------------------ bomen op de heuvels
M_STAM = effen("stam", (0.25, 0.15, 0.08))
M_SPAR = effen("spar", S["bos"])
M_SPAR_S = effen("spar_sneeuw", (0.90, 0.94, 1.0))
M_LOOF = [effen("loof%d" % i, k) for i, k in enumerate(S["loof"] or [])]

def kegel(r, h, loc, m):
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=0, depth=h, location=loc)
    o = bpy.context.object; o.data.materials.append(m); return o

def bol(r, loc, m):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=loc)
    o = bpy.context.object; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o

def boom(x, y):
    z = h_dicht(x, y)
    if z < 1.0:
        return
    eps = 0.6
    if abs(h_dicht(x + eps, y) - h_dicht(x - eps, y)) > 1.2:       # te steil
        return
    s = 0.8 + random.random() * 0.7
    if not M_LOOF or random.random() < 0.55:
        kegel(0.9 * s, 3.2 * s, (x, y, z + 1.4 * s), M_SPAR)
        if SEIZOEN == "winter":
            kegel(0.55 * s, 1.4 * s, (x, y, z + 2.5 * s), M_SPAR_S)
    else:
        kegel(0.12 * s, 1.6 * s, (x, y, z + 0.6 * s), M_STAM)
        bol(0.95 * s, (x, y, z + 1.9 * s), random.choice(M_LOOF))

for _ in range(260 if SNEL else 520):
    boom(random.uniform(-BREED / 2 - 5, BREED / 2 + 5), random.uniform(6, 26))

# ------------------------------------------------------------------ boerderijtjes (met licht achter de ramen 's avonds)
M_MUUR = effen("muur", (0.85, 0.80, 0.70)); M_DAK = effen("dak", (0.55, 0.16, 0.10) if SEIZOEN != "winter" else (0.95, 0.97, 1.0))
M_RAAM = effen("raam", (1.0, 0.62, 0.22), emissie=5.0) if AVOND else effen("raam", (0.25, 0.30, 0.40), ruw=0.3)
for x in (-70, -28, 18, 61, 92):
    y = 8 + random.random() * 6; z = h_dicht(x, y)
    if z < 0.5:
        continue
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.7)); o = bpy.context.object
    o.scale = (2.2, 1.6, 1.6); o.data.materials.append(M_MUUR)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.9, radius2=0, depth=1.3, location=(x, y, z + 2.1))
    d = bpy.context.object; d.rotation_euler = (0, 0, math.pi / 4); d.scale = (1.2, 0.9, 1); d.data.materials.append(M_DAK)
    for dx in (-0.5, 0.5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x + dx, y - 0.81, z + 0.8)); r = bpy.context.object
        r.scale = (0.35, 0.05, 0.4); r.data.materials.append(M_RAAM)

# ------------------------------------------------------------------ licht en wereld
wereld = bpy.data.worlds.new("w"); sc.world = wereld; wereld.use_nodes = True
bg = wereld.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.10, 0.10, 0.30, 1) if AVOND else (0.55, 0.70, 0.95, 1)
bg.inputs[1].default_value = 0.45 if AVOND else 0.55
zl = bpy.data.lights.new("zon", "SUN")
zl.energy = 0.9 if AVOND else 2.6
zl.color = (0.55, 0.62, 1.0) if AVOND else ((1.0, 0.82, 0.6) if SEIZOEN == "herfst" else (1.0, 0.95, 0.85))
zl.angle = math.radians(3)
zon = bpy.data.objects.new("zon", zl); sc.collection.objects.link(zon)
zon.rotation_euler = (math.radians(55), 0, math.radians(-55))   # van rechtsvoor, zoals de zon/maan in het spel

# ------------------------------------------------------------------ camera: recht van voren, orthografisch
cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = BREED; cd.sensor_fit = "HORIZONTAL"
cd.clip_end = 1000
cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
hoogte_beeld = BREED * H / W                      # 50 eenheden hoog
cam.location = (0, -300, hoogte_beeld / 2 - 1.0)  # onderrand net onder z=0
cam.rotation_euler = (math.radians(90), 0, 0)

sc.render.filepath = os.path.join(UIT, "bergen_%s_%s.png" % (SEIZOEN, "avond" if AVOND else "dag"))
bpy.ops.render.render(write_still=True)
print("KLAAR", sc.render.filepath)
