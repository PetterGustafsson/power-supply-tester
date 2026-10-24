"""Render the assembled I15 tester from preserved CAD and the approved LCD art.

Preview (default): blender -b -P scripts/build_product_hero.py
Final, after composition approval: add -- --final
Save the scene without rendering: add --scene-only
No firmware or device operations are performed.
"""
from pathlib import Path
import math
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/product-render'
OUT.mkdir(parents=True, exist_ok=True)
ST = ROOT / 'case-cad/cad_I9/stl'
CURRENT = ROOT / 'case-cad/current'
FINAL = '--final' in sys.argv
S = .001
G = Vector((0, -10, 59.88))
UP = Vector((0, .766044443, .642787610))
NORMAL = Vector((0, -.642787610, .766044443))
MODULE = Matrix(((1, 0, 0, 0), (0, UP.y, NORMAL.y, 0),
                 (0, UP.z, NORMAL.z, 0), (0, 0, 0, 1)))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def linear(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb)


def material(name, color, roughness=.5, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*linear(color), 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    return mat


ivory = material('Marble ivory filament', 'E7E4DA', .49)
nodes, links = ivory.node_tree.nodes, ivory.node_tree.links
coord = nodes.new('ShaderNodeTexCoord')
speckle = nodes.new('ShaderNodeTexVoronoi')
speckle.inputs['Scale'].default_value = 95
links.new(coord.outputs['Generated'], speckle.inputs['Vector'])
ramp = nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .075
ramp.color_ramp.elements[0].color = (*linear('57544C'), 1)
ramp.color_ramp.elements[1].position = .14
ramp.color_ramp.elements[1].color = (*linear('E6E1D4'), 1)
links.new(speckle.outputs['Distance'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])

charcoal = material('Charcoal base', '242528', .60)
orange = material('Orange crown', 'FF6A13', .37)
rubber = material('Rubber feet', '141516', .8)
cable = material('Soft black cable jacket', '141516', .42)
metal = material('Nickel plated connector', 'CFD2D5', .21, 1)
glass = material('LCD black glass perimeter', '010204', .18)
glass.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = .08


def imported(path, mat, transform=None):
    # Apply print-to-assembly transforms in mm before the common metric scale.
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=1)
    obj = bpy.context.object
    obj.data.materials.append(mat)
    obj.matrix_world = Matrix.Scale(S, 4) @ (transform or Matrix.Identity(4))
    bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    return obj


imported(CURRENT / 'I15_base_print.stl', charcoal)
# The preserved top prints upright on the split edge at world Z = 6.5 mm.
imported(CURRENT / 'I15_top_print.stl', ivory, Matrix.Translation((0, 0, 6.5)))
# Crown prints visible face down. Undo its 180-degree print rotation.
crown_transform = (Matrix.Translation(G) @ MODULE @ Matrix.Translation((0, 0, 2.8))
                   @ Matrix.Rotation(math.pi, 4, 'X'))
imported(CURRENT / 'I15_crown_print.stl', orange, crown_transform)
for name, mat in [
    ('render/display_LCM', glass),
    ('render/display_PCB', charcoal),
    ('REF_grommet_foot_x4', rubber),
    ('REF_cable_12pin_7mm', cable),
    ('REF_cable_12pin_7mm_external', cable),
    ('REF_HR10A-10P-12S(73)_female_plug', metal),
]:
    imported(ST / f'{name}.stl', mat)

# The actual 240px device artwork is mapped directly to the active circular LCD.
# 12.03 V is the illustration's preview reading, not a new live measurement.
art = bpy.data.images.load(str(ROOT / 'output/connector-finished-ui-2026-10-22/275-recognized.png'))
art.pack()
lcd_mat = bpy.data.materials.new('Approved powered LCD — illustrative 12.03 V')
lcd_mat.use_nodes = True
n, l = lcd_mat.node_tree.nodes, lcd_mat.node_tree.links
n.clear()
texture = n.new('ShaderNodeTexImage')
texture.image = art
texture.interpolation = 'Linear'
emission = n.new('ShaderNodeEmission')
emission.inputs['Strength'].default_value = .82
output = n.new('ShaderNodeOutputMaterial')
l.new(texture.outputs['Color'], emission.inputs['Color'])
l.new(emission.outputs[0], output.inputs['Surface'])
segments = 192
vertices = [(0, 0, 0)] + [(16.1 * math.cos(2 * math.pi * i / segments),
                           16.1 * math.sin(2 * math.pi * i / segments), 0) for i in range(segments)]
faces = [(0, i + 1, (i + 1) % segments + 1) for i in range(segments)]
mesh = bpy.data.meshes.new('Active LCD circle')
mesh.from_pydata(vertices, [], faces)
mesh.update()
uv = mesh.uv_layers.new(name='Screen artwork UV')
for polygon in mesh.polygons:
    for loop_index in polygon.loop_indices:
        p = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        uv.data[loop_index].uv = (p.x / 32.2 + .5, p.y / 32.2 + .5)
lcd = bpy.data.objects.new('Powered screen', mesh)
scene.collection.objects.link(lcd)
lcd.matrix_world = Matrix.Scale(S, 4) @ Matrix.Translation(G + NORMAL * .035) @ MODULE
mesh.materials.append(lcd_mat)

# A seamless warm grey studio with soft contact shadows and long metal highlights.
floor_mat = material('Warm stone studio', 'AEAAA2', .82)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.00205))
bpy.context.object.data.materials.append(floor_mat)
world = bpy.data.worlds.new('Neutral studio')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (*linear('E8E7E3'), 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .12
scene.world = world
target = Vector((8, -70, 17)) * S


def area(name, position, energy, size, color='FFFFFF', size_y=None):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = energy
    light.color = linear(color)
    light.size = size
    if size_y:
        light.shape = 'RECTANGLE'
        light.size_y = size_y
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = Vector(position) * S
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()


area('Large soft key', (-230, -240, 400), 1.8, .38, 'FFF1DC', .24)
area('Cool fill', (280, -170, 240), .55, .36, 'E6EDFF', .50)
area('Crown and connector rim', (70, 220, 340), 1.2, .30, 'FFFFFF', .16)
area('Chrome strip reflection', (160, -320, 170), .35, .045, 'FFFFFF', .32)

camera_data = bpy.data.cameras.new('Product camera')
camera = bpy.data.objects.new('Product camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
azimuth, elevation = math.radians(-24), math.radians(38)
camera.location = target + Vector((math.sin(azimuth) * math.cos(elevation),
                                   -math.cos(azimuth) * math.cos(elevation),
                                   math.sin(elevation))) * .58
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.lens = 61
camera_data.clip_start = .01
camera_data.clip_end = 250

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128 if FINAL else 32
scene.cycles.use_denoising = True
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'METAL'
    if any(d.type == 'METAL' for d in prefs.devices):
        scene.cycles.device = 'GPU'
except (TypeError, RuntimeError):
    pass
scene.render.resolution_x = 6000 if FINAL else 1200
scene.render.resolution_y = 4500 if FINAL else 900
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / ('power-supply-tester-hero.png' if FINAL else 'power-supply-tester-hero-preview.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'product-hero.blend'))
if '--scene-only' not in sys.argv:
    bpy.ops.render.render(write_still=True)
