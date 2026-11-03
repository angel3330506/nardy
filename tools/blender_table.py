# Фон партии в Blender: старый стол во дворике в Ереване. Столешница из досок со щелями (PBR «wood_table_worn»,
# Poly Haven, CC0), над ней виноградный навес — настоящие листья, которые камера не видит, но они отбрасывают
# тени от солнца. Результат: boards/table.webp.  Запуск: python (с bpy) tools/blender_table.py
import os, sys, math, random
import numpy as np
import bpy
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TEX = os.path.join(ROOT, 'tools', 'tex')
TW, TH = 24.0, 15.0                                           # кадр 2400×1500 пикселей, 100 пикселей на метр сцены
rnd = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def tex(nt, name, color=True):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(TEX, name))
    n.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; return n

# ---------- материал досок: у каждой доски свой кусок текстуры ----------
wm = bpy.data.materials.new('table'); wm.use_nodes = True
nt = wm.node_tree; N = nt.nodes; Lk = nt.links.new
bs = N['Principled BSDF']
tc = N.new('ShaderNodeTexCoord'); oi = N.new('ShaderNodeObjectInfo')
off = N.new('ShaderNodeVectorMath'); off.operation = 'MULTIPLY_ADD'
Lk(tc.outputs['Object'], off.inputs[0]); off.inputs[1].default_value = (.16, .16, .16)
cr = N.new('ShaderNodeCombineXYZ'); Lk(oi.outputs['Random'], cr.inputs['X']); Lk(oi.outputs['Random'], cr.inputs['Y'])
mul = N.new('ShaderNodeVectorMath'); mul.operation = 'SCALE'; Lk(cr.outputs['Vector'], mul.inputs[0]); mul.inputs['Scale'].default_value = 9.3
Lk(mul.outputs['Vector'], off.inputs[2])
d = tex(nt, 'table_Diffuse.jpg'); n_ = tex(nt, 'table_nor_gl.jpg', False); r = tex(nt, 'table_Rough.jpg', False)
for t in (d, n_, r): Lk(off.outputs['Vector'], t.inputs['Vector'])
hue = N.new('ShaderNodeHueSaturation'); Lk(d.outputs['Color'], hue.inputs['Color'])
Lk(oi.outputs['Random'], hue.inputs['Value']); hue.inputs['Saturation'].default_value = .95
vmap = N.new('ShaderNodeMapRange'); Lk(oi.outputs['Random'], vmap.inputs['Value']); vmap.inputs['To Min'].default_value = .8; vmap.inputs['To Max'].default_value = 1.15
Lk(vmap.outputs['Result'], hue.inputs['Value'])
Lk(hue.outputs['Color'], bs.inputs['Base Color']); Lk(r.outputs['Color'], bs.inputs['Roughness'])
nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.2; Lk(n_.outputs['Color'], nm.inputs['Color']); Lk(nm.outputs['Normal'], bs.inputs['Normal'])

# ---------- столешница: 6 широких досок со щелями и скруглёнными кромками ----------
edges = np.cumsum([0] + [rnd.uniform(2.3, 3.0) for _ in range(6)]); edges = edges / edges[-1] * (TH + 1.2) - .6
for k in range(6):
    y0, y1 = edges[k] + .03, edges[k + 1] - .03
    bpy.ops.mesh.primitive_cube_add(size=1, location=(TW / 2, -(y0 + y1) / 2, -.2 + rnd.uniform(-.02, .02)))
    b = bpy.context.object; b.scale = (TW + 2, y1 - y0, .4)
    b.rotation_euler = (rnd.uniform(-.004, .004), 0, rnd.uniform(-.002, .002))
    bev = b.modifiers.new('bev', 'BEVEL'); bev.width = .06; bev.segments = 4
    b.data.materials.append(wm)
# под щелями — темнота
bpy.ops.mesh.primitive_plane_add(size=60, location=(TW / 2, -TH / 2, -1))
dm = bpy.data.materials.new('dark'); dm.diffuse_color = (0, 0, 0, 1); bpy.context.object.data.materials.append(dm)

# ---------- виноградный навес: листья только отбрасывают тень ----------
lp = os.path.join(ROOT, '.preview', 'grape_leaf.png')
im = Image.new('L', (512, 512), 0); dr = ImageDraw.Draw(im)
pts = []
for t in np.linspace(0, 2 * math.pi, 300):
    lobes = .74 + .26 * (1 - abs(math.sin(2.5 * (t - math.pi / 2)))) ** 2.2
    notch = 1 - .55 * math.exp(-((t - 3 * math.pi / 2) / .22) ** 2)
    teeth = 1 + .035 * abs(math.sin(t * 22))
    rr = 240 * lobes * notch * teeth
    pts.append((256 + rr * math.cos(t), 256 + rr * math.sin(t)))
dr.polygon(pts, fill=255); im.save(lp)
lm = bpy.data.materials.new('leaf'); lm.use_nodes = True; ln = lm.node_tree
lt = ln.nodes.new('ShaderNodeTexImage'); lt.image = bpy.data.images.load(lp); lt.image.colorspace_settings.name = 'Non-Color'
lb = ln.nodes['Principled BSDF']; lb.inputs['Base Color'].default_value = (.08, .2, .03, 1)
lb.inputs['Transmission Weight'].default_value = .25                      # лист пропускает немного света
ln.links.new(lt.outputs['Color'], lb.inputs['Alpha'])
leaves = bpy.data.collections.new('vine'); sc.collection.children.link(leaves)
bpy.ops.mesh.primitive_plane_add(size=1); proto = bpy.context.object; proto.data.materials.append(lm)
sc.collection.objects.unlink(proto)
def cover(x, y):                                              # навес гуще у верхнего края и по бокам, к середине редеет
    return min(1, max(0, 1.1 - y / (TH * .6)) ** 1.3 + max(0, 1 - x / (TW * .2)) ** 2 * .8 + max(0, 1 - (TW - x) / (TW * .2)) ** 2 * .7)
SUN = (math.radians(26), math.radians(-14))                   # солнце чуть сверху-слева: тени сдвинуты вниз-вправо
from mathutils import Euler, Vector
SD = Euler((SUN[0], SUN[1], 0)).to_matrix() @ Vector((0, 0, -1))   # куда светит солнце
def above(x, y, z):                                           # точка на высоте z, тень от которой падает в (x, −y)
    k = z / -SD.z
    return (x - SD.x * k, -y - SD.y * k, z)
n = 0
while n < 520:
    x, y = rnd.uniform(-3, TW + 3), rnd.uniform(-3, TH + 2)
    if rnd.random() > cover(min(max(x, 0), TW), min(max(y, 0), TH)): continue
    z = rnd.uniform(12, 26)                                  # навес высоко над столом — края теней размыты
    o = proto.copy(); leaves.objects.link(o)
    s = rnd.uniform(1.1, 2.0); o.scale = (s, s, 1)
    o.location = above(x, y, z)
    o.rotation_euler = (rnd.uniform(-.6, .6), rnd.uniform(-.6, .6), rnd.uniform(0, 2 * math.pi))
    o.visible_camera = False; o.visible_glossy = False
    n += 1
for _ in range(8):                                            # лоза — изогнутые ветви
    x, y, a = rnd.uniform(-2, TW), rnd.uniform(-1, TH * .3), rnd.uniform(-.4, .4)
    z = rnd.uniform(14, 20); pts = []
    for k in range(30):
        a += rnd.gauss(0, .12); x += .3 * math.cos(a); y += .18 * math.sin(a); pts.append(above(x, y, z))
    cu = bpy.data.curves.new('v', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = rnd.uniform(.04, .08)
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    v = bpy.data.objects.new('vine', cu); leaves.objects.link(v); v.visible_camera = False; v.visible_glossy = False

# ---------- стакан армуды с чаем на блюдце, рядом ложечка и сахар ----------
CM = .39                                                      # сантиметр в единицах сцены (доска 50 см ≈ 19 единиц)
def lathe(name, prof, mat, loc, seg=96, solid=0.0, cap=True):
    """Тело вращения по профилю [(радиус, высота)] в сантиметрах."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * CM * math.cos(a), r * CM * math.sin(a), z * CM)) for a in np.linspace(0, 2 * math.pi, seg, endpoint=False)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    if cap and prof[0][0] > 0: bm.faces.new(list(reversed(rings[0])))   # дно; у колец-ободков дна нет
    bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc
    if solid: m = o.modifiers.new('s', 'SOLIDIFY'); m.thickness = solid * CM
    o.modifiers.new('sub', 'SUBSURF').levels = 1
    o.data.materials.append(mat); return o
def pmat(name, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    for k, v in kw.items(): b.inputs[k].default_value = v
    return m
glass = pmat('glass', **{'Base Color': (1, 1, 1, 1), 'Transmission Weight': 1.0, 'Roughness': .02, 'IOR': 1.5})
tea = pmat('tea', **{'Base Color': (.55, .16, .03, 1), 'Transmission Weight': .85, 'Roughness': .05, 'IOR': 1.33})
porcelain = pmat('porc', **{'Base Color': (.93, .93, .94, 1), 'Roughness': .18, 'Coat Weight': .6})
gold = pmat('gold', **{'Base Color': (.9, .66, .3, 1), 'Metallic': 1.0, 'Roughness': .25})
silver = pmat('silver', **{'Base Color': (.88, .88, .86, 1), 'Metallic': 1.0, 'Roughness': .18})
sugar = pmat('sugar', **{'Base Color': (.97, .96, .93, 1), 'Roughness': .7, 'Subsurface Weight': .3})
X0, Y0 = 22.6, -11.2                                         # правый нижний угол стола, у края доски
lathe('saucer', [(0, 0), (4.0, 0), (5.6, .6), (6.3, 1.2), (6.4, 1.35)], porcelain, (X0, Y0, 0), solid=.25)
lathe('rim', [(6.25, 1.36), (6.45, 1.36), (6.45, 1.46), (6.25, 1.46), (6.25, 1.36)], gold, (X0, Y0, 0), cap=False)
# чашка армянского кофе: фарфор, золотой ободок, ручка; кофе с плотной пенкой
lathe('cup', [(1.6, 0), (2.2, .3), (2.9, 1.6), (3.25, 3.4), (3.4, 5.2), (3.45, 5.6)], porcelain, (X0, Y0, 1.0 * CM), solid=.22)
lathe('cuprim', [(3.36, 5.58), (3.5, 5.58), (3.5, 5.7), (3.36, 5.7), (3.36, 5.58)], gold, (X0, Y0, 1.0 * CM), cap=False)
foam = bpy.data.materials.new('foam'); foam.use_nodes = True; fn = foam.node_tree.nodes; fb = fn['Principled BSDF']
noise = fn.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 60; noise.inputs['Detail'].default_value = 8
ramp = fn.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (.035, .016, .008, 1); ramp.color_ramp.elements[1].color = (.17, .09, .04, 1)
foam.node_tree.links.new(noise.outputs['Fac'], ramp.inputs['Fac']); foam.node_tree.links.new(ramp.outputs['Color'], fb.inputs['Base Color'])
fb.inputs['Roughness'].default_value = .35; fb.inputs['Coat Weight'].default_value = .5
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=3.22 * CM, depth=.3 * CM, location=(X0, Y0, (1.0 + 4.7) * CM)); bpy.context.object.data.materials.append(foam)
bpy.ops.mesh.primitive_torus_add(major_radius=1.25 * CM, minor_radius=.28 * CM, location=(X0 + 4.3 * CM, Y0, 4.0 * CM), rotation=(math.radians(90), 0, 0))
h_ = bpy.context.object; h_.scale = (1, 1.25, 1); h_.data.materials.append(porcelain)
# чайная ложечка: вытянутая чаша и тонкая ручка с утолщением на конце
ang = math.radians(35); ux, uy = math.cos(ang), math.sin(ang)
bx, by = X0 - 4.0 * CM * ux, Y0 - 4.0 * CM * uy               # чаша ложки на блюдце, ручка лежит на краю и уходит наружу
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(bx, by, 1.55 * CM)); bowl = bpy.context.object
bowl.scale = (1.5 * CM, .95 * CM, .32 * CM); bowl.rotation_euler = (0, 0, ang); bowl.data.materials.append(silver)
for p_ in bowl.data.polygons: p_.use_smooth = True
hl = 9.5 * CM
bpy.ops.mesh.primitive_cylinder_add(radius=.17 * CM, depth=hl, location=(bx - ux * (1.4 * CM + hl / 2), by - uy * (1.4 * CM + hl / 2), 1.95 * CM))
hd = bpy.context.object; hd.rotation_euler = (math.radians(90), math.radians(-1.5), ang + math.radians(90)); hd.data.materials.append(silver)
hd.rotation_mode = 'XYZ'
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(bx - ux * (1.4 * CM + hl), by - uy * (1.4 * CM + hl), 2.1 * CM)); tip = bpy.context.object
tip.scale = (.9 * CM, .45 * CM, .14 * CM); tip.rotation_euler = (0, 0, ang); tip.data.materials.append(silver)
for k, (dx, dy, rz) in enumerate(((-9.5, -1.0, .3), (-10.2, 1.6, -.4))):
    bpy.ops.mesh.primitive_cube_add(size=1.6 * CM, location=(X0 + dx * CM, Y0 + dy * CM, .8 * CM)); c = bpy.context.object
    c.rotation_euler = (0, 0, rz); c.data.materials.append(sugar); bv = c.modifiers.new('b', 'BEVEL'); bv.width = .12 * CM; bv.segments = 2

# ---------- свет и камера ----------
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.6; sun.angle = math.radians(1.4); sun.color = (1, .93, .8)
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (SUN[0], SUN[1], 0)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .62, .75, 1)   # небо — холодная заливка теней
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .9
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = TW
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co; co.location = (TW / 2, -TH / 2, 30)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('SAMPLES', 128)); sc.cycles.max_bounces = 10; sc.cycles.transmission_bounces = 10; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 2400, 1500
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium Contrast'
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(ROOT, '.preview', 'blender-table.png')
bpy.ops.render.render(write_still=True)
Image.open(sc.render.filepath).convert('RGB').save(os.path.join(ROOT, 'boards', 'table.webp'), 'WEBP', quality=80, method=6)
print('saved table')
