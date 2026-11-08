# Ролик для Reels «Задача дня» (на основе phone_blender.py): телефон в Blender, на экране — покадровая запись интерфейса (ui/0001.jpg…).
# Камера сама летит к местам нажатий, телефон парит, поворачивается горизонтально и в конце влетает в камеру.
# Запуск: python (с bpy) phone_blender.py  — переменные: UI (папка кадров), OUT (папка рендера), FRAMES, SAMPLES, START, END
import os, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Euler

UI = os.environ['UI']; OUT = os.environ['OUT']; TEX = os.environ.get('TEX', '')
FPS = 30; N = int(os.environ.get('FRAMES', 486))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- геометрия: 1 единица = 100 css-пикселей экрана (экран 440×956) ----------
SW, SH = 4.40, 9.56                       # экран
BW, BH, BR, TH = 4.78, 9.94, 0.86, 0.50   # корпус: ширина, высота, радиус углов, толщина
def rrect(w, h, r, n=24):
    pts = []
    for cx, cy, a0 in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90), (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts
def slab(name, w, h, r, z0, z1, mat, bevel=0.0, seg=6, uv=False):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in rrect(w, h, r)]
    f = bm.faces.new(vs); bm.normal_update()
    if f.normal.z > 0: f.normal_flip()
    ex = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[v for v in ex['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0, z1 - z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if uv:
        lay = bm.loops.layers.uv.new('UV')
        for fc in bm.faces:
            for lp in fc.loops: lp[lay].uv = (lp.vert.co.x / w + .5, lp.vert.co.y / h + .5)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = seg; b.limit_method = 'ANGLE'; b.harden_normals = True
    for p in me.polygons: p.use_smooth = True
    return o
def pmat(name, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    for k, v in kw.items(): b.inputs[k].default_value = v
    return m

# iPhone 18 Pro Max, тёмно-вишнёвый: анодированный алюминий, матовое стекло спины в цвет
ti = pmat('alu', **{'Base Color': (.42, .085, .11, 1), 'Metallic': 1.0, 'Roughness': .32, 'Anisotropic': .2})
backg = pmat('backglass', **{'Base Color': (.30, .06, .08, 1), 'Roughness': .5, 'Coat Weight': .25})
blackg = pmat('blackglass', **{'Base Color': (.004, .004, .005, 1), 'Roughness': .03, 'Coat Weight': 1.0, 'Coat Roughness': .01})
lens = pmat('lens', **{'Base Color': (.01, .012, .02, 1), 'Roughness': .02, 'Coat Weight': 1.0})
ring = pmat('ring', **{'Base Color': (.5, .12, .14, 1), 'Metallic': 1.0, 'Roughness': .2})
flash = pmat('flash', **{'Base Color': (.95, .92, .85, 1), 'Roughness': .3, 'Transmission Weight': .3})

# экран: картинка-эмиссия + стекло сверху (отражения)
scr = bpy.data.materials.new('screen'); scr.use_nodes = True; nt = scr.node_tree; bs = nt.nodes['Principled BSDF']
img = bpy.data.images.load(os.path.join(UI, '0001.jpg')); img.source = 'SEQUENCE'
tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Cubic'
tx.image_user.frame_duration = N; tx.image_user.frame_start = 1; tx.image_user.frame_offset = 0; tx.image_user.use_auto_refresh = True
nt.nodes.remove(bs); em_ = nt.nodes.new('ShaderNodeEmission'); em_.inputs['Strength'].default_value = 1.0   # экран без бликов и отражений
nt.links.new(tx.outputs['Color'], em_.inputs['Color']); nt.links.new(em_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])

phone = bpy.data.objects.new('phone', None); sc.collection.objects.link(phone)
parts = []
parts.append(slab('frame', BW, BH, BR, -TH/2, TH/2, ti, bevel=.11, seg=8))
parts.append(slab('front', BW-.10, BH-.10, BR-.05, TH/2-.01, TH/2+.012, blackg, bevel=.012, seg=3))
parts.append(slab('screen', SW, SH, .62, TH/2+.0125, TH/2+.0135, scr, uv=True))
parts.append(slab('back', BW-.10, BH-.10, BR-.05, -TH/2-.012, -TH/2+.01, backg, bevel=.012, seg=3))
# камерное «плато» на спине (полоса во всю ширину) и три объектива
pl = slab('plateau', BW-.34, 2.0, .55, -TH/2-.10, -TH/2-.01, backg, bevel=.06, seg=5); pl.location = (0, BH/2-1.25, 0); parts.append(pl)
for k, (x, y) in enumerate(((-1.35, BH/2-.85), (-1.35, BH/2-1.70), (-.55, BH/2-1.27))):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.40, depth=.12, location=(x, y, -TH/2-.16)); c = bpy.context.object; c.data.materials.append(ring)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.30, depth=.13, location=(x, y, -TH/2-.165)); c2 = bpy.context.object; c2.data.materials.append(lens)
    parts += [c, c2]
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.17, depth=.06, location=(1.55, BH/2-.95, -TH/2-.115)); bpy.context.object.data.materials.append(flash); parts.append(bpy.context.object)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=.05, depth=.06, location=(1.55, BH/2-1.55, -TH/2-.115)); bpy.context.object.data.materials.append(lens); parts.append(bpy.context.object)
# кнопки по бокам
def btn(x, y, h, w=.06, d=.20):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0)); b = bpy.context.object; b.scale = (w, h, d); b.data.materials.append(ti)
    m = b.modifiers.new('b', 'BEVEL'); m.width = .025; m.segments = 4; parts.append(b)
L = -BW/2 - .025; R = BW/2 + .025
btn(L, 2.9, .45); btn(L, 1.9, .9); btn(L, .85, .9); btn(R, 1.9, 1.3); btn(R, -1.3, .75, w=.03)
for o in parts: o.parent = phone

# ---------- фон: тёмная студия с тёплыми размытыми огнями ----------
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; wn = world.node_tree.nodes; wl = world.node_tree.links
bg = wn['Background']; bg.inputs['Color'].default_value = (.008, .007, .008, 1); bg.inputs['Strength'].default_value = 1
if TEX and os.path.exists(os.path.join(TEX, 'studio.hdr')):
    env = wn.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(TEX, 'studio.hdr'))
    bg2 = wn.new('ShaderNodeBackground'); bg2.inputs['Strength'].default_value = .35; wl.new(env.outputs['Color'], bg2.inputs['Color'])
    lp = wn.new('ShaderNodeLightPath'); mx = wn.new('ShaderNodeMixShader')
    wl.new(lp.outputs['Is Camera Ray'], mx.inputs['Fac']); wl.new(bg2.outputs['Background'], mx.inputs[1]); wl.new(bg.outputs['Background'], mx.inputs[2])
    wl.new(mx.outputs['Shader'], wn['World Output'].inputs['Surface'])
rng = np.random.default_rng(5)
BG = []
NARDY = os.environ.get('NARDY', '/home/user/nardy')
def tex_plane(name, path, size, loc, rot_z, rough=.6, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt_ = m.node_tree; b_ = nt_.nodes['Principled BSDF']
    t_ = nt_.nodes.new('ShaderNodeTexImage'); t_.image = bpy.data.images.load(path)
    nt_.links.new(t_.outputs['Color'], b_.inputs['Base Color']); b_.inputs['Roughness'].default_value = rough
    if emit: nt_.links.new(t_.outputs['Color'], b_.inputs['Emission Color']); b_.inputs['Emission Strength'].default_value = emit
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); o = bpy.context.object; o.scale = (size[0], size[1], 1); o.rotation_euler = (0, 0, rot_z)
    o.data.materials.append(m); o.visible_glossy = False; BG.append(o); return o
# стол: та же столешница, что в игре; доска «Арарат» лежит на нём наискосок
tex_plane('table', os.path.join(NARDY, 'boards', 'table.webp'), (96, 60), (0, 0, -40), math.radians(90), emit=.35)
tex_plane('board', os.path.join(NARDY, 'boards', 'ararat.webp'), (33, 21), (2.5, -3, -39.9), math.radians(97), rough=.35, emit=.3)
# гирлянда: тёплые лампочки на провисающих проводах между телефоном и столом — дают круглое боке
warm = bpy.data.materials.new('bulb'); warm.use_nodes = True; e = warm.node_tree.nodes; e.remove(e['Principled BSDF'])
es = e.new('ShaderNodeEmission'); es.inputs['Color'].default_value = (1, .62, .28, 1); es.inputs['Strength'].default_value = 9
warm.node_tree.links.new(es.outputs[0], e['Material Output'].inputs[0])
for wi, (y0, z0, sag) in enumerate(((19, -16, 4), (-6, -20, 5), (-24, -14, 3.5))):
    for k in range(9):
        u = k / 8; x = -22 + 44 * u; y = y0 + sag * (1 - (2 * u - 1) ** 2) * -1 + rng.uniform(-.6, .6)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=.32, location=(x, y, z0 + rng.uniform(-1, 1)), segments=16, ring_count=8)
        bpy.context.object.data.materials.append(warm); bpy.context.object.visible_glossy = False; bpy.context.object.visible_shadow = False; BG.append(bpy.context.object)

# ---------- свет: большой мягкий сверху-слева, контровые по краям рамки ----------
def area(name, loc, rot, size, energy, col=(1, 1, 1), shape='RECTANGLE', sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col; l.shape = shape
    if sy: l.size_y = sy
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area('key', (-9, 10, 16), (math.radians(-35), math.radians(-28), 0), 10, 2600, (1, .93, .85))
area('tablelight', (0, 0, -8), (0, 0, 0), 40, 9000, (1, .78, .55))   # тёплый свет на стол снизу (телефон не освещает — смотрит вверх)
area('rimL', (-12, -2, 2), (0, math.radians(-80), 0), 3, 900, (1, .85, .7), sy=18)
area('rimR', (12, 3, 3), (0, math.radians(78), 0), 3, 700, (.8, .88, 1), sy=18)
area('top', (0, 0, 22), (0, 0, 0), 14, 350, (1, .97, .94))

# ---------- камера ----------
cam = bpy.data.cameras.new('cam'); cam.lens = 50; cam.sensor_fit = 'VERTICAL'; cam.sensor_height = 36
cam.dof.use_dof = True; cam.dof.aperture_fstop = 0.14
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
D0 = 16.4                    # расстояние, при котором телефон целиком (~80% высоты кадра)
DL = 27.8                    # то же для горизонтального положения (~90% ширины)

# ---------- анимация: ролик «Задача дня» (Reels 9:16) ----------
# телефон всё время горизонтально (игра только горизонтальная); камера: общий план → наезд на доску и кубики
# («как сходишь?») → отъезд, шашки ходят → карточка «Верно!» → телефон влетает в камеру
def io(x): x = min(1, max(0, x)); return 4*x*x*x if x < .5 else 1 - (-2*x + 2)**3 / 2
def oc(x): x = min(1, max(0, x)); return 1 - (1 - x)**3
# ключи камеры: (время, x, y — css-пиксели горизонтального экрана от центра, y вниз; дистанция)
K = [(0, 0, 0, DL), (5.0, 0, 0, DL), (5.9, 55, 0, DL/1.35), (10.4, 105, 5, DL/1.62),
     (11.2, 30, 0, DL/1.25), (13.3, 30, 0, DL/1.25), (14.0, 0, -5, DL/1.22), (17.2, 0, -5, DL/1.30)]
END = 17.25
def cam_at(t):
    for (t0, x0, y0, d0), (t1, x1, y1, d1) in zip(K, K[1:]):
        if t0 <= t <= t1:
            k = io((t - t0) / (t1 - t0) if t1 > t0 else 1)
            return x0 + (x1 - x0)*k, y0 + (y1 - y0)*k, math.exp(math.log(d0) + (math.log(d1) - math.log(d0))*k)
    return K[-1][1], K[-1][2], K[-1][3]
for f in range(1, N + 1):
    t = (f - 1) / FPS; sc.frame_set(f)
    e = oc(t / 1.3)                                              # прилёт снизу с разворотом
    py = -22 * (1 - e); rx = math.radians(40 * (1 - e)); ry = math.radians(-20 * (1 - e)); rz = math.radians(90 - 14 * (1 - e))
    x, y, d = cam_at(t); zoom = DL / d
    calm = 1 / (1 + 2.2 * max(0, zoom - 1))                     # вблизи качается меньше — текст не плывёт
    rx += math.radians(2.4 * math.sin(t * 1.2) * calm); ry += math.radians(2.0 * math.sin(t * .9 + 1) * calm)
    pz = .25 * math.sin(t * 1.5)
    fl = max(0, (t - END) / .95); fly = fl ** 2.4                 # финал: телефон рывком летит в камеру
    phone.location = (0, py, pz + fly * (d - 1.3)); phone.rotation_euler = (rx - math.radians(14) * fly, ry + math.radians(9) * fly, rz)
    phone.keyframe_insert('location'); phone.keyframe_insert('rotation_euler')
    co.location = (x / 100, -y / 100, d); co.rotation_euler = (0, 0, 0); co.keyframe_insert('location')
    cam.dof.focus_distance = max(.5, d - (pz + fly * (d - 1.3))); cam.dof.keyframe_insert('focus_distance')
for o in (phone, co):
    for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, 'fcurves') else []:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------- рендер ----------
# MODE=plate — один раз фон (стол, доска, гирлянда) широким объективом и в высоком разрешении;
# MODE=phone — каждый кадр только телефон на прозрачном фоне (фон в сцене есть: свет и отражения в рамке остаются)
MODE = os.environ.get('MODE', 'phone')
import json
json.dump([[f, *cam_at((f - 1) / FPS)] for f in range(1, N + 1)], open(os.path.join(OUT, 'cam.json') if os.path.isdir(OUT) else OUT + 'cam.json', 'w'))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('SAMPLES', 5))
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 2
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False; sc.cycles.use_adaptive_sampling = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.render.fps = FPS
if MODE == 'plate':
    for o in parts: o.hide_render = True
    co.animation_data_clear(); cam.animation_data_clear() if cam.animation_data else None
    co.location = (0, 0, D0); cam.lens = 35; cam.dof.focus_distance = D0
    sc.render.resolution_x, sc.render.resolution_y = 2160, 3840; sc.cycles.samples = int(os.environ.get('SAMPLES', 64))
    sc.frame_start = sc.frame_end = 1; sc.render.use_motion_blur = False
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.join(OUT, 'plate.png')
    bpy.ops.render.render(write_still=True)
else:
    for o in BG: o.visible_camera = False
    sc.render.film_transparent = True
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .45
    sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get('W', 1080)), int(os.environ.get('H', 1920))
    sc.frame_start = int(os.environ.get('START', 1)); sc.frame_end = int(os.environ.get('END', N))
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.compression = 30
    sc.render.filepath = os.path.join(OUT, '')
    bpy.ops.render.render(animation=True)
print('done')
