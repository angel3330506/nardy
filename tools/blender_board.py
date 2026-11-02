# 3D-рендер доски в Blender (Cycles): рельеф и раскладка узора — из tools/render_real.py (layers=True),
# материалы — PBR-шпон Poly Haven (цвет, нормали, шероховатость) под лаком, бронза — металл; свет — студийная HDRI + софтбокс.
# Запуск: сначала  python3 tools/render_real.py layers  (пишет .preview/layers-ararat.npz),
# затем python с пакетом bpy:  python tools/blender_board.py <папка с текстурами и studio.hdr>
import os, sys, math
import numpy as np
import bpy

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TEX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'tools', 'tex')
L = np.load(os.path.join(ROOT, '.preview', 'layers-ararat.npz'))
h, body, metal, alb = L['h'], L['body'], L['metal'], L['alb']
HH, WW = h.shape                                             # 1400 × 2200, 2 пикселя на единицу доски
U = 100.0                                                     # единиц доски на метр сцены: доска 11 × 7 м
HK = 1 / 2 / U * .6                                           # высота: h в пикселях → метры (рельеф чуть сглажен)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- сетка по карте высот ----------
step = 1
hs = h[::step, ::step]; ny, nx = hs.shape
ys, xs = np.mgrid[0:ny, 0:nx]
co = np.stack([xs * step / 2 / U, -ys * step / 2 / U, hs * HK], -1).reshape(-1, 3).astype(np.float32)
q = (ys[:-1, :-1] * nx + xs[:-1, :-1]).ravel()
quads = np.stack([q, q + nx, q + nx + 1, q + 1], -1).astype(np.int32)
me = bpy.data.meshes.new('board')
me.vertices.add(len(co)); me.vertices.foreach_set('co', co.ravel())
me.loops.add(quads.size); me.loops.foreach_set('vertex_index', quads.ravel())
me.polygons.add(len(quads)); me.polygons.foreach_set('loop_start', np.arange(0, quads.size, 4, dtype=np.int32))
uv = me.uv_layers.new(name='UV')
uvv = np.stack([co[:, 0] / (WW / 2 / U), 1 + co[:, 1] / (HH / 2 / U)], -1)
uv.data.foreach_set('uv', uvv[quads.ravel()].ravel())
me.update(calc_edges=True); me.validate()
me.polygons.foreach_set('use_smooth', np.ones(len(quads), bool))
ob = bpy.data.objects.new('board', me); sc.collection.objects.link(ob)

# ---------- карты-маски ----------
def img(name, arr):
    """Массив H×W×(1|3|4) 0..1 → картинка Blender (без гамма-коррекции)."""
    a = np.atleast_3d(arr).astype(np.float32)
    if a.shape[2] == 1: a = np.repeat(a, 3, 2)
    if a.shape[2] == 3: a = np.concatenate([a, np.ones_like(a[..., :1])], 2)
    im = bpy.data.images.new(name, a.shape[1], a.shape[0], alpha=True, float_buffer=True)
    im.colorspace_settings.name = 'Non-Color'                 # до записи пикселей: смена цветового пространства сбрасывает буфер
    im.pixels.foreach_set(a[::-1].ravel()); im.update(); im.pack()
    return im
R, G = alb[..., 0], alb[..., 1]
mask = img('mask', np.stack([R, G, metal, body], -1))
mcol = img('metalcol', np.where(metal[..., None] > .01, np.clip(alb, 0, 1) ** 1.5 * np.array((1, .9, .66)), 0))   # sRGB → линейный, теплее

def tex(nt, path, color=True):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(path)
    n.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    n.extension = 'MIRROR'; return n

# ---------- материал ----------
mat = bpy.data.materials.new('nardy'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; Lk = nt.links.new
for n in list(N): N.remove(n)
out = N.new('ShaderNodeOutputMaterial')
tc = N.new('ShaderNodeTexCoord')
mp = N.new('ShaderNodeMapping'); Lk(tc.outputs['UV'], mp.inputs['Vector'])
mp.inputs['Scale'].default_value = (2.2, 1.0, 1)              # волокна вдоль пунктов, как на настоящих нардах
mp2 = N.new('ShaderNodeMapping'); Lk(tc.outputs['UV'], mp2.inputs['Vector'])
mp2.inputs['Scale'].default_value = (2.6, 1.3, 1)
mp2.inputs['Location'].default_value = (.37, .21, 0)
tm = N.new('ShaderNodeTexImage'); tm.image = mask; tm.interpolation = 'Cubic'; tm.extension = 'EXTEND'; Lk(tc.outputs['UV'], tm.inputs['Vector'])
tmc = N.new('ShaderNodeTexImage'); tmc.image = mcol; tmc.extension = 'EXTEND'; Lk(tc.outputs['UV'], tmc.inputs['Vector'])
sep = N.new('ShaderNodeSeparateColor'); Lk(tm.outputs['Color'], sep.inputs['Color'])
wd = tex(nt, os.path.join(TEX, 'walnut_veneer.jpg')); Lk(mp.outputs['Vector'], wd.inputs['Vector'])
wn = tex(nt, os.path.join(TEX, 'walnut_veneer_nor_gl.jpg'), False); Lk(mp.outputs['Vector'], wn.inputs['Vector'])
wr = tex(nt, os.path.join(TEX, 'walnut_veneer_Rough.jpg'), False); Lk(mp.outputs['Vector'], wr.inputs['Vector'])
ld = tex(nt, os.path.join(TEX, 'white_maple_veneer.jpg')); Lk(mp2.outputs['Vector'], ld.inputs['Vector'])
# у узла Mix с типом RGBA цветовые входы A/B — 6 и 7, цветовой выход — 2 (по имени нашлись бы числовые)
CA, CB, CO = 6, 7, 2
# морилка: орех темнее и теплее, светлый бук — тёплый кремовый
st = N.new('ShaderNodeMix'); st.data_type = 'RGBA'; st.blend_type = 'MULTIPLY'; st.inputs['Factor'].default_value = 1
Lk(wd.outputs['Color'], st.inputs[CA]); st.inputs[CB].default_value = (.34, .19, .075, 1)
lt = N.new('ShaderNodeMix'); lt.data_type = 'RGBA'; lt.blend_type = 'MULTIPLY'; lt.inputs['Factor'].default_value = 1
Lk(ld.outputs['Color'], lt.inputs[CA]); lt.inputs[CB].default_value = (.80, .56, .36, 1)
# доли и затемнения из масок: цвет = орех·R + бук·G
def mul(a, s):
    m = N.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = 'MULTIPLY'; m.inputs['Factor'].default_value = 1
    Lk(a, m.inputs[CA]); cmb = N.new('ShaderNodeCombineColor'); [Lk(s, cmb.inputs[i]) for i in range(3)]
    Lk(cmb.outputs['Color'], m.inputs[CB]); return m.outputs[CO]
add = N.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs['Factor'].default_value = 1
Lk(mul(st.outputs[CO], sep.outputs['Red']), add.inputs[CA]); Lk(mul(lt.outputs[CO], sep.outputs['Green']), add.inputs[CB])
wood = N.new('ShaderNodeBsdfPrincipled')
Lk(add.outputs[CO], wood.inputs['Base Color'])
rr = N.new('ShaderNodeMapRange'); Lk(wr.outputs['Color'], rr.inputs['Value']); rr.inputs['To Min'].default_value = .35; rr.inputs['To Max'].default_value = .6
Lk(rr.outputs['Result'], wood.inputs['Roughness'])
nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = .6; Lk(wn.outputs['Color'], nm.inputs['Color']); Lk(nm.outputs['Normal'], wood.inputs['Normal'])
wood.inputs['Coat Weight'].default_value = .7                 # лак
wood.inputs['Coat Roughness'].default_value = .1
wood.inputs['Coat IOR'].default_value = 1.5
# бронза
br = N.new('ShaderNodeBsdfPrincipled')
Lk(tmc.outputs['Color'], br.inputs['Base Color']); br.inputs['Metallic'].default_value = 1; br.inputs['Roughness'].default_value = .32
mx = N.new('ShaderNodeMixShader'); Lk(sep.outputs['Blue'], mx.inputs['Fac']); Lk(wood.outputs['BSDF'], mx.inputs[1]); Lk(br.outputs['BSDF'], mx.inputs[2])
tr = N.new('ShaderNodeBsdfTransparent')
cut = N.new('ShaderNodeMixShader'); Lk(tm.outputs['Alpha'], cut.inputs['Fac']); Lk(tr.outputs['BSDF'], cut.inputs[1]); Lk(mx.outputs['Shader'], cut.inputs[2])
Lk(cut.outputs['Shader'], out.inputs['Surface'])
ob.data.materials.append(mat)

# ---------- свет и камера ----------
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
wn_ = world.node_tree.nodes; env = wn_.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(TEX, 'studio.hdr'))
bg = wn_['Background']; world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = .35
key = bpy.data.lights.new('key', 'AREA'); key.shape = 'RECTANGLE'; key.size = 9; key.size_y = 5; key.energy = 5000
ko = bpy.data.objects.new('key', key); sc.collection.objects.link(ko)
ko.location = (-4.5, 5.0, 8); ko.rotation_euler = (math.radians(-40), math.radians(-35), 0)   # свет сверху-слева под углом — резьба читается
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = WW / 2 / U
co_ = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co_); sc.camera = co_
co_.location = (WW / 4 / U, -HH / 4 / U, 20)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.environ.get('SAMPLES', 96)); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = WW, HH
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = os.path.join(ROOT, '.preview', 'blender-ararat.png')
bpy.ops.render.render(write_still=True)
print('rendered', sc.render.filepath)
