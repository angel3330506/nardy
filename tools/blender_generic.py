# 3D-рендер доски в Blender по слоям из  python3 tools/render_real.py layers <доска>:
# сетка по карте высот, цвет — альбедо (дерево с фото шпона), лак/кожа/сукно — по карте глянца, металл — по маске.
# Запуск: python (с bpy) tools/blender_generic.py <доска> [папка с studio.hdr]
import os, sys, math
import numpy as np
import bpy

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NAME = sys.argv[1]
TEX = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'tools', 'tex')
L = np.load(os.path.join(ROOT, '.preview', f'layers-{NAME}.npz'))
h, alb, gloss, metal, alpha = L['h'], L['alb'], L['gloss'], L['metal'], L['alpha']
HH, WW = h.shape
U = 100.0
HK = 1 / 2 / U * .6

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

ys, xs = np.mgrid[0:HH, 0:WW]
co = np.stack([xs / 2 / U, -ys / 2 / U, h * HK], -1).reshape(-1, 3).astype(np.float32)
q = (ys[:-1, :-1] * WW + xs[:-1, :-1]).ravel()
quads = np.stack([q, q + WW, q + WW + 1, q + 1], -1).astype(np.int32)
me = bpy.data.meshes.new('board')
me.vertices.add(len(co)); me.vertices.foreach_set('co', co.ravel())
me.loops.add(quads.size); me.loops.foreach_set('vertex_index', quads.ravel())
me.polygons.add(len(quads)); me.polygons.foreach_set('loop_start', np.arange(0, quads.size, 4, dtype=np.int32))
uv = me.uv_layers.new(name='UV')
uvv = np.stack([co[:, 0] / (WW / 2 / U), 1 + co[:, 1] / (HH / 2 / U)], -1)
uv.data.foreach_set('uv', uvv[quads.ravel()].ravel())
me.update(calc_edges=True)
me.polygons.foreach_set('use_smooth', np.ones(len(quads), bool))
ob = bpy.data.objects.new('board', me); sc.collection.objects.link(ob)
del co, quads, uvv

def img(name, arr, space='Non-Color'):
    a = np.atleast_3d(arr).astype(np.float32)
    if a.shape[2] == 1: a = np.repeat(a, 3, 2)
    if a.shape[2] == 3: a = np.concatenate([a, np.ones_like(a[..., :1])], 2)
    im = bpy.data.images.new(name, a.shape[1], a.shape[0], alpha=True, float_buffer=True)
    im.colorspace_settings.name = space                       # до записи пикселей: смена пространства сбрасывает буфер
    im.pixels.foreach_set(a[::-1].ravel()); im.update(); im.pack()
    return im
col = img('albedo', np.clip(alb, 0, 1) ** 2.2)               # альбедо было в sRGB
prm = img('params', np.stack([np.clip(gloss, 0, 1), np.clip(metal, 0, 1), np.clip(alpha, 0, 1)], -1))

mat = bpy.data.materials.new('m'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; Lk = nt.links.new
for n in list(N): N.remove(n)
out = N.new('ShaderNodeOutputMaterial'); tc = N.new('ShaderNodeTexCoord')
ti = N.new('ShaderNodeTexImage'); ti.image = col; ti.interpolation = 'Cubic'; ti.extension = 'EXTEND'; Lk(tc.outputs['UV'], ti.inputs['Vector'])
tp = N.new('ShaderNodeTexImage'); tp.image = prm; tp.extension = 'EXTEND'; Lk(tc.outputs['UV'], tp.inputs['Vector'])
sep = N.new('ShaderNodeSeparateColor'); Lk(tp.outputs['Color'], sep.inputs['Color'])
bs = N.new('ShaderNodeBsdfPrincipled')
Lk(ti.outputs['Color'], bs.inputs['Base Color'])
Lk(sep.outputs['Green'], bs.inputs['Metallic'])
rough = N.new('ShaderNodeMapRange'); Lk(sep.outputs['Red'], rough.inputs['Value'])
rough.inputs['To Min'].default_value = .85; rough.inputs['To Max'].default_value = .3          # сукно матовое, лак гладкий
Lk(rough.outputs['Result'], bs.inputs['Roughness'])
coat = N.new('ShaderNodeMath'); coat.operation = 'MULTIPLY'; coat.inputs[1].default_value = .8
Lk(sep.outputs['Red'], coat.inputs[0]); Lk(coat.outputs['Value'], bs.inputs['Coat Weight'])
bs.inputs['Coat Roughness'].default_value = .09
tr = N.new('ShaderNodeBsdfTransparent')
cut = N.new('ShaderNodeMixShader'); Lk(sep.outputs['Blue'], cut.inputs['Fac']); Lk(tr.outputs['BSDF'], cut.inputs[1]); Lk(bs.outputs['BSDF'], cut.inputs[2])
Lk(cut.outputs['Shader'], out.inputs['Surface'])
ob.data.materials.append(mat)

world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
env = world.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(TEX, 'studio.hdr'))
bg = world.node_tree.nodes['Background']; world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = .35
key = bpy.data.lights.new('key', 'AREA'); key.shape = 'RECTANGLE'; key.size = 9; key.size_y = 5; key.energy = 5000
ko = bpy.data.objects.new('key', key); sc.collection.objects.link(ko)
ko.location = (-4.5, 5.0, 8); ko.rotation_euler = (math.radians(-40), math.radians(-35), 0)
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = max(WW, HH) / 2 / U   # по большей стороне: у крышки она — высота
co_ = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co_); sc.camera = co_
co_.location = (WW / 4 / U, -HH / 4 / U, 20)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.environ.get('SAMPLES', 128)); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = WW, HH
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
sc.view_settings.exposure = float(os.environ.get('EXPOSURE', 0))   # белой доске (gravura) нужна поправка, иначе свет выбивает её в чистый белый
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = os.path.join(ROOT, '.preview', f'blender-{NAME}.png')
bpy.ops.render.render(write_still=True)
print('rendered', sc.render.filepath)
