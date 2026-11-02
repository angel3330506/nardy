# Шашки и грани кубика в Blender (Cycles), по слоям tools/pieces_layers.py.
# Результат: boards/ck-<имя>.png (128×128) и boards/die-<1..6>.png (256×256) с прозрачным фоном.
import os, sys, math
import numpy as np
import bpy
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PRE, OUTD, TEX = os.path.join(ROOT, '.preview'), os.path.join(ROOT, 'boards'), os.path.join(ROOT, 'tools', 'tex')


def render(name, out_png, size, die=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    L = np.load(os.path.join(PRE, name + '.npz'))
    h, alb, alpha = L['h'], L['alb'], L['alpha']
    n = h.shape[0]
    ys, xs = np.mgrid[0:n, 0:n]
    co = np.stack([xs / n, -ys / n, h], -1).reshape(-1, 3).astype(np.float32)
    q = (ys[:-1, :-1] * n + xs[:-1, :-1]).ravel()
    quads = np.stack([q, q + n, q + n + 1, q + 1], -1).astype(np.int32)
    me = bpy.data.meshes.new('p')
    me.vertices.add(len(co)); me.vertices.foreach_set('co', co.ravel())
    me.loops.add(quads.size); me.loops.foreach_set('vertex_index', quads.ravel())
    me.polygons.add(len(quads)); me.polygons.foreach_set('loop_start', np.arange(0, quads.size, 4, dtype=np.int32))
    uv = me.uv_layers.new(name='UV'); uvv = np.stack([co[:, 0], 1 + co[:, 1]], -1)
    uv.data.foreach_set('uv', uvv[quads.ravel()].ravel())
    me.update(calc_edges=True); me.polygons.foreach_set('use_smooth', np.ones(len(quads), bool))
    ob = bpy.data.objects.new('p', me); sc.collection.objects.link(ob)
    a = np.concatenate([np.clip(alb, 0, 1) ** 2.2, alpha[..., None]], -1).astype(np.float32)
    im = bpy.data.images.new('a', n, n, alpha=True, float_buffer=True); im.colorspace_settings.name = 'Non-Color'
    im.pixels.foreach_set(a[::-1].ravel()); im.update(); im.pack()
    mat = bpy.data.materials.new('m'); mat.use_nodes = True; nt = mat.node_tree; N = nt.nodes; Lk = nt.links.new
    bs = N['Principled BSDF']; tc = N.new('ShaderNodeTexCoord')
    ti = N.new('ShaderNodeTexImage'); ti.image = im; ti.interpolation = 'Cubic'; Lk(tc.outputs['UV'], ti.inputs['Vector'])
    Lk(ti.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = .4 if die else .35
    bs.inputs['Coat Weight'].default_value = .6 if die else .8
    bs.inputs['Coat Roughness'].default_value = .08
    if die or 'ivory' in name:                                # кость/пластик кубика — слегка просвечивает
        bs.inputs['Subsurface Weight'].default_value = .15; bs.inputs['Subsurface Radius'].default_value = (.02, .015, .01)
    tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
    Lk(ti.outputs['Alpha'], mx.inputs['Fac']); Lk(tr.outputs['BSDF'], mx.inputs[1]); Lk(bs.outputs['BSDF'], mx.inputs[2])
    Lk(mx.outputs['Shader'], N['Material Output'].inputs['Surface'])
    me.materials.append(mat)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(TEX, 'studio.hdr'))
    w.node_tree.links.new(env.outputs['Color'], w.node_tree.nodes['Background'].inputs['Color'])
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = .6 if die else .35
    key = bpy.data.lights.new('k', 'AREA'); key.size = 1.2; key.energy = 60 if die else 90
    ko = bpy.data.objects.new('k', key); sc.collection.objects.link(ko)
    ko.location = (-.4, .6, 1.4); ko.rotation_euler = (math.radians(-25), math.radians(-30), 0)
    cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = 1
    co_ = bpy.data.objects.new('c', cam); sc.collection.objects.link(co_); sc.camera = co_; co_.location = (.5, -.5, 5)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = n; sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    tmp = os.path.join(PRE, name + '.png'); sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    Image.open(tmp).resize((size, size), Image.LANCZOS).save(out_png, optimize=True)
    print('saved', out_png)


for k in (() if 'dice' in sys.argv else ('ivory', 'onyx', 'beech', 'walnut')):
    render(f'piece-ck-{k}', os.path.join(OUTD, f'ck-{k}.png'), 128)
for v in range(1, 7):
    render(f'piece-die-{v}', os.path.join(OUTD, f'die-{v}.png'), 256, die=True)
