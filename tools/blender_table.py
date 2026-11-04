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
from mathutils import Euler, Vector, Matrix
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
_before_props = set(bpy.data.objects)                         # всё, что дальше, — отдельные картинки-предметы (PROPS=1)
X0, Y0 = 19.8, -11.5                                          # кофе справа внизу; в игре ставится вплотную к правому краю доски
lathe('saucer', [(0, 0), (4.0, 0), (5.6, .6), (6.3, 1.2), (6.4, 1.35)], porcelain, (X0, Y0, 0), solid=.25)
lathe('rim', [(6.25, 1.36), (6.45, 1.36), (6.45, 1.46), (6.25, 1.46), (6.25, 1.36)], gold, (X0, Y0, 0), cap=False)
# чашка армянского кофе: фарфор, золотой ободок, ручка; кофе с плотной пенкой
lathe('cup', [(1.6, 0), (2.2, .3), (2.9, 1.6), (3.25, 3.4), (3.4, 5.2), (3.45, 5.6)], porcelain, (X0, Y0, 1.0 * CM), solid=.22)
lathe('cuprim', [(3.36, 5.58), (3.5, 5.58), (3.5, 5.7), (3.36, 5.7), (3.36, 5.58)], gold, (X0, Y0, 1.0 * CM), cap=False)
foam = bpy.data.materials.new('foam'); foam.use_nodes = True; fn = foam.node_tree.nodes; fb = fn['Principled BSDF']
noise = fn.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 60; noise.inputs['Detail'].default_value = 8
ramp = fn.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (.05, .025, .012, 1); ramp.color_ramp.elements[1].color = (.30, .17, .08, 1)
foam.node_tree.links.new(noise.outputs['Fac'], ramp.inputs['Fac']); foam.node_tree.links.new(ramp.outputs['Color'], fb.inputs['Base Color'])
fb.inputs['Roughness'].default_value = .35; fb.inputs['Coat Weight'].default_value = .5
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=3.22 * CM, depth=.3 * CM, location=(X0, Y0, (1.0 + 4.7) * CM)); bpy.context.object.data.materials.append(foam)
bpy.ops.mesh.primitive_torus_add(major_radius=1.25 * CM, minor_radius=.28 * CM, location=(X0 + 4.3 * CM, Y0, 4.0 * CM), rotation=(math.radians(90), 0, 0))
h_ = bpy.context.object; h_.scale = (1, 1.25, 1); h_.data.materials.append(porcelain)
# чайная ложечка: вытянутая чаша и тонкая ручка с утолщением на конце
ang = math.radians(-120);                                     # ложечка лежит на блюдце, ручкой вверх-вправо, от доски
ux, uy = math.cos(ang), math.sin(ang)
bx, by = X0 - 5.0 * CM * ux, Y0 - 5.0 * CM * uy               # чаша ложки на блюдце, ручка лежит на краю и уходит наружу
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(bx, by, 1.0 * CM)); bowl = bpy.context.object
bowl.scale = (1.25 * CM, .8 * CM, .28 * CM); bowl.rotation_euler = (0, 0, ang); bowl.data.materials.append(silver)
for p_ in bowl.data.polygons: p_.use_smooth = True
hl = 9.5 * CM
bpy.ops.mesh.primitive_cylinder_add(radius=.17 * CM, depth=hl, location=(bx - ux * (1.15 * CM + hl / 2), by - uy * (1.15 * CM + hl / 2), 1.95 * CM))
hd = bpy.context.object; hd.rotation_euler = (math.radians(90), math.radians(-1.5), ang + math.radians(90)); hd.data.materials.append(silver)
hd.rotation_mode = 'XYZ'
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(bx - ux * (1.15 * CM + hl), by - uy * (1.15 * CM + hl), 2.1 * CM)); tip = bpy.context.object
tip.scale = (.9 * CM, .45 * CM, .14 * CM); tip.rotation_euler = (0, 0, ang); tip.data.materials.append(silver)
for k, (dx, dy, rz) in enumerate(((8.4, -2.6, .3), (9.0, 1.0, -.4))):   # сахар — справа от блюдца
    bpy.ops.mesh.primitive_cube_add(size=1.6 * CM, location=(X0 + dx * CM, Y0 + dy * CM, .8 * CM)); c = bpy.context.object
    c.rotation_euler = (0, 0, rz); c.data.materials.append(sugar); bv = c.modifiers.new('b', 'BEVEL'); bv.width = .12 * CM; bv.segments = 2

# ---------- пачка сигарет Cigaronne King Size: чёрная матовая, линия откидной крышки,
# серебряная эмблема и KING SIZE вверху, надпись Cigaronne курсивом, белое поле предупреждения внизу ----------
PX, PY = 1.6, -5.2                                           # слева у доски: видна и на компьютере, и на телефоне
pw, pd, ph = 5.5 * CM, 2.2 * CM, 8.8 * CM                     # ширина, толщина, высота пачки (лежит лицом вверх)
def pack_textures():
    from PIL import ImageFont
    W_, H_ = 550, 880
    col = Image.new('RGB', (W_, H_), (7, 7, 8)); met = Image.new('L', (W_, H_), 0)
    dc, dm = ImageDraw.Draw(col), ImageDraw.Draw(met)
    rng_ = np.random.default_rng(3)
    n = (rng_.normal(0, 3, (H_, W_))).astype(np.int16)
    col = Image.fromarray(np.clip(np.asarray(col, np.int16) + n[..., None], 0, 255).astype(np.uint8)); dc = ImageDraw.Draw(col)
    dc.line([(0, 250), (W_, 250)], fill=(4, 4, 5), width=3)                 # линия откидной крышки
    dc.line([(0, 253), (W_, 253)], fill=(40, 40, 44), width=1)
    silver = (205, 205, 210)
    cx = W_ // 2                                                             # эмблема: три пика
    for i, dx in enumerate((-26, 0, 26)):
        hgt = 34 if i == 1 else 26
        pts = [(cx + dx - 14, 150), (cx + dx, 150 - hgt), (cx + dx + 14, 150)]
        dc.line(pts, fill=silver, width=4, joint='curve'); dm.line(pts, fill=255, width=4)
    # серебряный росчерк вместо надписи
    # надпись Cigaronne серебряным курсивом (шрифт Great Vibes, OFL) и KING SIZE под эмблемой
    fs = ImageFont.truetype(os.path.join(ROOT, 'tools', 'fonts', 'GreatVibes-Regular.ttf'), 118)
    dc.text((cx, 440), 'Cigaronne', font=fs, fill=silver, anchor='mm'); dm.text((cx, 440), 'Cigaronne', font=fs, fill=255, anchor='mm')
    fk = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 22)
    dc.text((cx, 200), 'K I N G   S I Z E', font=fk, fill=silver, anchor='mm'); dm.text((cx, 200), 'K I N G   S I Z E', font=fk, fill=255, anchor='mm')
    # белое поле предупреждения с чёрной рамкой
    dc.rectangle([28, 600, W_ - 28, H_ - 40], fill=(245, 245, 242), outline=(0, 0, 0), width=6)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 66)
    for k, word in enumerate(('Курение', 'убивает')):
        dc.text((cx, 680 + k * 86), word, font=f, fill=(10, 10, 10), anchor='mm')
    pc = os.path.join(ROOT, '.preview', 'pack_col.png'); pm = os.path.join(ROOT, '.preview', 'pack_met.png')
    col.save(pc); met.save(pm); return pc, pm
pc, pm = pack_textures()
blackm = pmat('packblack', **{'Base Color': (.01, .01, .012, 1), 'Roughness': .6})
bpy.ops.mesh.primitive_cube_add(size=1, location=(PX, PY, pd / 2)); pk = bpy.context.object
pk.scale = (pw, ph, pd); pk.rotation_euler = (0, 0, math.radians(-5)); bv = pk.modifiers.new('b', 'BEVEL'); bv.width = .05 * CM; bv.segments = 2
pk.data.materials.append(blackm)
# лицевая сторона — плоскость с картинкой; серебро — металл по маске
fm_ = bpy.data.materials.new('packface'); fm_.use_nodes = True; ft = fm_.node_tree; fb_ = ft.nodes['Principled BSDF']
ti_ = ft.nodes.new('ShaderNodeTexImage'); ti_.image = bpy.data.images.load(pc)
tm_ = ft.nodes.new('ShaderNodeTexImage'); tm_.image = bpy.data.images.load(pm); tm_.image.colorspace_settings.name = 'Non-Color'
ft.links.new(ti_.outputs['Color'], fb_.inputs['Base Color']); ft.links.new(tm_.outputs['Color'], fb_.inputs['Metallic'])
rr_ = ft.nodes.new('ShaderNodeMapRange'); ft.links.new(tm_.outputs['Color'], rr_.inputs['Value']); rr_.inputs['To Min'].default_value = .7; rr_.inputs['To Max'].default_value = .22
ft.links.new(rr_.outputs['Result'], fb_.inputs['Roughness'])
bpy.ops.mesh.primitive_plane_add(size=1, location=(PX, PY, pd + .002)); face = bpy.context.object
face.scale = (pw * .985, ph * .985, 1); face.rotation_euler = (0, 0, math.radians(-5)); face.data.materials.append(fm_)
# серебряные метки «X» на боковой грани видны чуть-чуть — опускаем

# ---------- чётки: чёрный оникс, серебряные разделители, серебряный конус и ажурный армянский крест ----------
# Лежат на столе как брошенные: петля неровная, бусины чуть разного размера, крест повёрнут по ходу нити.
RX, RY = 1.55, -10.25                                         # слева у доски, под пачкой
onyx = pmat('onyx', **{'Base Color': (.006, .006, .007, 1), 'Roughness': .05, 'IOR': 1.55, 'Coat Weight': 1.0, 'Coat Roughness': .02})
silver2 = pmat('silver2', **{'Base Color': (.9, .9, .88, 1), 'Metallic': 1.0, 'Roughness': .16})
oxid = pmat('oxid', **{'Base Color': (.1, .1, .1, 1), 'Metallic': 1.0, 'Roughness': .5})   # чернёное серебро в углублениях
cord = pmat('cord', **{'Base Color': (.03, .03, .035, 1), 'Roughness': .55})
BR = .15                                                     # радиус бусины (~8 мм)
def sphere(x, y, r, mat, z=None, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, r if z is None else z), segments=seg, ring_count=seg // 2)
    o = bpy.context.object; o.data.materials.append(mat)
    for p_ in o.data.polygons: p_.use_smooth = True
    return o
# неровная петля: эллипс плюс пара гармоник и лёгкий поворот; низ петли (t = π) — место конуса
def loop_pt(t):
    x = .80 * math.sin(t) + .07 * math.sin(2 * t) + .05 * math.cos(3 * t) - .04 * math.sin(4 * t)
    y = 1.40 * math.cos(t) + .09 * math.sin(2 * t) + .05 * math.cos(3 * t)
    r_ = math.radians(-9); return (RX + x * math.cos(r_) - y * math.sin(r_), RY + 1.2 + x * math.sin(r_) + y * math.cos(r_))
curve = [loop_pt(t) for t in np.linspace(math.pi, 3 * math.pi, 1441)]   # начинаем снизу
seg = np.hypot(np.diff([c[0] for c in curve]), np.diff([c[1] for c in curve])); cum = np.concatenate([[0], np.cumsum(seg)])
nb = int(cum[-1] / (BR * 2.1)); nb -= nb % 2
loop = [curve[int(np.searchsorted(cum, cum[-1] * (k + .5) / nb))] for k in range(nb)]   # k=0 и k=nb-1 — по бокам от конуса
gap = (cum[-1] / nb) / 2                                      # конус садится в разрыв внизу петли
for k, (x, y) in enumerate(loop):
    if k in (nb // 5, 2 * nb // 5, nb - 1 - 2 * nb // 5, nb - 1 - nb // 5):   # серебряные разделители-рондели
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=BR * .78, depth=BR * .62, location=(x, y, BR * .8))
        o = bpy.context.object; nx, ny = loop[(k + 1) % nb][0] - loop[k - 1][0], loop[(k + 1) % nb][1] - loop[k - 1][1]
        o.rotation_euler = (math.radians(90), 0, math.atan2(ny, nx) + math.pi / 2); o.data.materials.append(silver2)
        bv = o.modifiers.new('b', 'BEVEL'); bv.width = BR * .16; bv.segments = 4
        for p_ in o.data.polygons: p_.use_smooth = True
    else:
        sphere(x, y, BR * rnd.uniform(.95, 1.04), onyx)
cu = bpy.data.curves.new('cord', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = BR * .1; cu.bevel_resolution = 3
sp = cu.splines.new('POLY'); sp.points.add(len(loop) - 1)
for p_, (x, y) in zip(sp.points, loop): p_.co = (x, y, BR * .75, 1)
cd = bpy.data.objects.new('cord', cu); sc.collection.objects.link(cd); cd.data.materials.append(cord)
# подвеска строится вниз от точки (0, 0) и потом поворачивается целиком
bx, by = curve[0]
_before_pend = set(bpy.data.objects)
def prism(pts, z0, h, mat, name, bev=.18):
    """Плоская пластина по контуру pts толщиной h, с фаской по краю (сетка, а не кривая: без полос на вогнутых углах)."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts]); bm.normal_update()
    if f.normal.z < 0: f.normal_flip()
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, verts=[v for v in ex['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0, h))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = (0, 0, z0)
    bv = o.modifiers.new('b', 'BEVEL'); bv.width = h * bev; bv.segments = 3; bv.limit_method = 'ANGLE'; bv.harden_normals = False
    o.modifiers.new('t', 'TRIANGULATE'); o.data.materials.append(mat); return o
cw, ch = .21, .30                                             # конус-«щиток»: серебряный треугольник с чернёным орнаментом
prism([(bx - cw, by + .03), (bx + cw, by + .03), (bx, by - ch)], 0, BR * 1.3, silver2, 'cone', .25)
prism([(bx - cw * .58, by - .02), (bx + cw * .58, by - .02), (bx, by - ch * .66)], BR * 1.3, .004, oxid, 'cone_in')
prism([(bx - cw * .3, by - .05), (bx + cw * .3, by - .05), (bx, by - ch * .45)], BR * 1.3 + .004, .004, silver2, 'cone_in2')
sphere(bx, by - ch - .075, BR * .62, silver2)                  # серебряная бусина и ушко под конусом
bpy.ops.mesh.primitive_torus_add(major_radius=.075, minor_radius=.02, location=(bx, by - ch - .215, .03), major_segments=48, minor_segments=16)
bpy.context.object.data.materials.append(silver2)
for p_ in bpy.context.object.data.polygons: p_.use_smooth = True
# армянский крест: ветви расширяются и раздваиваются завитками; ажурный — внутри чернёный узор, в центре розетка
cx, cy = bx, by - ch - .285 - .58
def arm_pts(L, w0, w1):
    return [(-w0, w0), (-w1, L * .78), (-w1 * 1.35, L), (-w1 * .4, L * .87), (0, L * .97), (w1 * .4, L * .87), (w1 * 1.35, L), (w1, L * .78), (w0, w0)]
ARMS = ((0, .50), (-90, .44), (180, .68), (90, .44))          # верх (к ушку), право, низ — длиннее, лево
def cross_outline(k):
    # внешний контур — с раздвоенными концами; внутренние слои — вложенные гладкие лопасти (иначе зубцы концов
    # оказываются посреди ветвей); k — насколько слой утоплен внутрь от края
    out = []
    for ang, L in ARMS:
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        if k >= 1: pts = arm_pts(L, .085, .15)
        else:
            d = (1 - k) * .16; w0, w1 = max(.012, .085 - d * .55), max(.02, .15 - d * .75)
            pts = [(-w0, w0), (-w1, L * .80 - d * .6), (0, L * .88 - d * .6), (w1, L * .80 - d * .6), (w0, w0)]
        out += [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts][:-1]
    return out
# слои: толстый серебряный край, чернёная полоса, серебряная филигрань, снова чернь, выпуклый серебряный центр
for k_, z_, h_, m_ in ((1.0, 0, .06, silver2), (.84, .06, .003, oxid), (.72, .063, .008, silver2), (.58, .071, .003, oxid), (.44, .074, .012, silver2)):
    prism(cross_outline(k_), z_, h_, m_, 'cross%.2f' % k_)
for k in range(8):                                            # розетка в центре
    a_ = k * math.pi / 4
    sphere(cx + .08 * math.cos(a_), cy + .08 * math.sin(a_), .024, silver2, .09, 24)
sphere(cx, cy, .045, silver2, .09, 32)
for ang, L in ARMS:                                           # бусинки-зерно на концах ветвей
    a_ = math.radians(ang + 90); L *= .86
    sphere(cx + L * math.cos(a_), cy + L * math.sin(a_), .03, silver2, .075, 24)
# вся подвеска чуть повёрнута — лежит, как упала
piv = bpy.data.objects.new('pend', None); sc.collection.objects.link(piv); piv.location = (bx, by, 0)
for o in set(bpy.data.objects) - _before_pend - {piv}:
    o.parent = piv; o.matrix_parent_inverse = Matrix.Translation((-bx, -by, 0))
piv.rotation_euler = (0, 0, math.radians(14))

props = [o for o in bpy.data.objects if o not in _before_props]
# Пачка и чётки — отдельными картинками (PROPS=1): в игре их ставят вплотную к доске на любом экране.
# Стол рисуется без них (по умолчанию), чтобы они не «плавали» относительно доски.
PROPS = bool(os.environ.get('PROPS'))
if PROPS:
    for o in bpy.data.objects:
        if o not in props and o.type in ('MESH', 'CURVE') and o.name != 'catcher': o.hide_render = True
    for o in leaves.all_objects: o.hide_render = True
    bpy.ops.mesh.primitive_plane_add(size=60, location=(TW / 2, -TH / 2, 0)); ct = bpy.context.object; ct.name = 'catcher'
    ct.is_shadow_catcher = True
    sc.render.film_transparent = True
else:
    for o in props: o.hide_render = True
# без навеса: для отдельного слоя тени (листва качается в игре)
if os.environ.get('NOVINE'):
    for o in leaves.all_objects: o.hide_render = True

# ---------- свет и камера ----------
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.6; sun.angle = math.radians(1.4); sun.color = (1, .93, .8)
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (SUN[0], SUN[1], 0)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .62, .75, 1)   # небо — холодная заливка теней
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .9
if PROPS:
    # в отражениях глянца (оникс, серебро, фарфор) вокруг — тёплый тёмный стол, а не голубое небо,
    # и мягкий блик от большого окна сверху-слева (виден только в отражениях, освещение не меняет)
    wn = world.node_tree.nodes; wl = world.node_tree.links; bg = wn['Background']; out = wn['World Output']
    bg2 = wn.new('ShaderNodeBackground'); bg2.inputs['Color'].default_value = (.16, .11, .07, 1); bg2.inputs['Strength'].default_value = 1.0
    lp = wn.new('ShaderNodeLightPath'); mx = wn.new('ShaderNodeMixShader')
    wl.new(lp.outputs['Is Glossy Ray'], mx.inputs['Fac']); wl.new(bg.outputs['Background'], mx.inputs[1]); wl.new(bg2.outputs['Background'], mx.inputs[2])
    wl.new(mx.outputs['Shader'], out.inputs['Surface'])
    win = bpy.data.lights.new('window', 'SUN'); win.energy = 3.0; win.angle = math.radians(16); win.color = (1, .97, .92)
    wo = bpy.data.objects.new('window', win); sc.collection.objects.link(wo); wo.rotation_euler = (math.radians(24), math.radians(-18), 0)
    wo.visible_diffuse = False; wo.visible_transmission = False; wo.visible_volume_scatter = False; wo.visible_shadow = False
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = TW
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co; co.location = (TW / 2, -TH / 2, 30)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('SAMPLES', 128)); sc.cycles.max_bounces = 10; sc.cycles.transmission_bounces = 10; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 2400, 1500
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium Contrast'
sc.render.image_settings.file_format = 'PNG'
NV = bool(os.environ.get('NOVINE'))
if PROPS: sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = os.path.join(ROOT, '.preview', 'blender-table%s.png' % ('-props' if PROPS else '-novine' if NV else ''))
if PROPS:
    # предметы рендерим вдвое крупнее (для чётких экранов) и только нужные куски кадра:
    # слева — пачка и чётки, справа внизу — кофе с сахаром. 3900 px картинки = 1100 единиц доски.
    sc.render.resolution_percentage = 200; sc.render.use_border = True; sc.render.use_crop_to_border = True
    for part, (x0, x1, y0, y1), cuts in (('left', (0, .3, 0, 1), (('pack', 0, 1460), ('beads', 1460, 3000))),
                                          ('right', (.68, 1, 0, .62), (('cup', 0, 9999),))):
        sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = x0, x1, y0, y1
        sc.render.filepath = os.path.join(ROOT, '.preview', f'blender-props-{part}.png')
        bpy.ops.render.render(write_still=True)
        im = Image.open(sc.render.filepath).convert('RGBA'); px = np.asarray(im).copy()
        px[..., 3][px[..., 3] < 10] = 0; im = Image.fromarray(px); a = px[..., 3]   # убираем шум ловца теней
        for name, cy0, cy1 in cuts:
            cy1 = min(cy1, a.shape[0])
            from PIL import ImageFilter
            mk = np.asarray(Image.fromarray(((a[cy0:cy1] > 30) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)))   # без одиночных «светлячков»
            ys, xs = np.nonzero(mk)
            box = (max(0, xs.min() - 12), cy0 + max(0, ys.min() - 12), min(a.shape[1], xs.max() + 13), cy0 + min(cy1 - cy0, ys.max() + 13))
            im.crop(box).save(os.path.join(ROOT, 'boards', f'prop-{name}.webp'), 'WEBP', quality=88, method=6, alpha_quality=90)
            # точка в картинке-предмете → для чашки нужны центр кофе и сахар (в пикселях картинки)
            ox, oy = x0 * 4800 + box[0], (1 - y1) * 3000 + box[1]
            px_ = lambda X, Y: (round(X * 200 - ox), round(-Y * 200 - oy))
            print('prop', name, im.crop(box).size, box)
            if name == 'cup': print('cup centre', px_(X0, Y0), 'sugar', [px_(X0 + dx * CM, Y0 + dy * CM) for dx, dy in ((8.4, -2.6), (9.0, 1.0))])
else:
    bpy.ops.render.render(write_still=True)
if not PROPS and not NV: Image.open(sc.render.filepath).convert('RGB').save(os.path.join(ROOT, 'boards', 'table.webp'), 'WEBP', quality=80, method=6)
print('saved table', 'novine' if NV else '')
