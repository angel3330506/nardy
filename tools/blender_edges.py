# Выброшенные шашки в лотке: шашка стоит на ребре, вид сверху — видна её точёная кромка (Blender, Cycles).
# Результат: boards/ckside-<имя>.png (256×64, прозрачный фон).
import os, math
import bpy
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TEX = os.path.join(ROOT, 'tools', 'tex')
KINDS = {'beech': ('white_maple_veneer.jpg', (.80, .58, .38)), 'walnut': ('walnut_veneer.jpg', (.36, .21, .11)),
         'ivory': (None, (.88, .84, .74)), 'onyx': (None, (.03, .03, .035))}
for name, (tex, tint) in KINDS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    # шашка: диаметр 1, толщина .24, ось вдоль Y (стоит на ребре, мы смотрим сверху на кромку)
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=.5, depth=.24, rotation=(math.radians(90), 0, 0))
    ob = bpy.context.object
    bv = ob.modifiers.new('b', 'BEVEL'); bv.width = .035; bv.segments = 6
    bpy.ops.object.shade_smooth()
    # бороздки на торцах не видны сверху; на кромке — тонкая проточка посередине
    m = bpy.data.materials.new('m'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links.new
    bs = N['Principled BSDF']
    if tex:
        ti = N.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(os.path.join(TEX, tex))
        tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (.7, .7, .7)
        L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], ti.inputs['Vector']); ti.projection = 'BOX'
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        L(ti.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = (*[c * 1.6 for c in tint], 1); L(mx.outputs[2], bs.inputs['Base Color'])
    else:
        bs.inputs['Base Color'].default_value = (*tint, 1)
    bs.inputs['Roughness'].default_value = .35; bs.inputs['Coat Weight'].default_value = .45; bs.inputs['Coat Roughness'].default_value = .08
    ob.data.materials.append(m)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    env = w.node_tree.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(TEX, 'studio.hdr'))
    w.node_tree.links.new(env.outputs['Color'], w.node_tree.nodes['Background'].inputs['Color']); w.node_tree.nodes['Background'].inputs['Strength'].default_value = .3
    k = bpy.data.lights.new('k', 'AREA'); k.size = 2; k.energy = 35
    ko = bpy.data.objects.new('k', k); sc.collection.objects.link(ko); ko.location = (-1, 1.2, 2.2); ko.rotation_euler = (math.radians(-28), math.radians(-24), 0)
    cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = 1.06
    co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co; co.location = (0, 0, 5)
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 512, 128; sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'
    out = os.path.join(ROOT, '.preview', f'ckside-{name}.png'); sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    Image.open(out).resize((256, 64), Image.LANCZOS).save(os.path.join(ROOT, 'boards', f'ckside-{name}.png'), optimize=True)
    print('saved', name)
