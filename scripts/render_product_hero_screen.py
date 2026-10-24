"""Blender LCD pass for build_product_hero_animation.py (load product-hero.blend)."""
from pathlib import Path
import json
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'output/product-render-frames'
manifest = json.loads((WORK / 'timeline.json').read_text())
scene = bpy.context.scene
scene.render.resolution_x = manifest['width']
scene.render.resolution_y = manifest['height']
scene.render.resolution_percentage = 100
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.fps = manifest['fps']
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'METAL'
    scene.cycles.device = 'GPU' if any(d.type == 'METAL' for d in prefs.devices) else 'CPU'
except (TypeError, RuntimeError):
    scene.cycles.device = 'CPU'
lcd = bpy.data.objects['Powered screen']
texture = next(n for n in lcd.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE')
texture.image = bpy.data.images.load(str(WORK / 'black.png'))
scene.render.filepath = str(WORK / 'background.png')
bpy.ops.render.render(write_still=True)

# The original CAD still occludes the LCD, including the crown's inner lip.
occluders = bpy.data.collections.new('LCD occluding geometry')
scene.collection.children.link(occluders)
for obj in list(scene.objects):
    if obj.type == 'MESH' and obj != lcd:
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        occluders.objects.link(obj)
bpy.context.view_layer.layer_collection.children[occluders.name].holdout = True
scene.render.film_transparent = True
scene.cycles.samples = 8
scene.cycles.use_denoising = False
scene.cycles.use_animated_seed = False
scene.cycles.seed = 0

points = [world_to_camera_view(scene, scene.camera, lcd.matrix_world @ v.co)
          for v in lcd.data.vertices]
width, height = manifest['width'], manifest['height']
left = max(0, math.floor(min(p.x for p in points) * width) - 3)
right = min(width, math.ceil(max(p.x for p in points) * width) + 3)
low = max(0, math.floor(min(p.y for p in points) * height) - 3)
high = min(height, math.ceil(max(p.y for p in points) * height) + 3)
scene.render.use_border = True
scene.render.use_crop_to_border = True
scene.render.border_min_x, scene.render.border_max_x = (left + .001) / width, (right + .001) / width
scene.render.border_min_y, scene.render.border_max_y = (low + .001) / height, (high + .001) / height
(WORK / 'projection.json').write_text(json.dumps(dict(crop=[left, height - high, right, height - low]), indent=2) + '\n')
sequence = bpy.data.images.load(str(WORK / 'ui/frame-0001.png'))
sequence.source = 'SEQUENCE'
texture.image = sequence
texture.image_user.frame_start = 1
texture.image_user.frame_duration = manifest['frames']
texture.image_user.use_auto_refresh = True
scene.frame_start = 1
scene.frame_end = manifest['frames']
scene.render.filepath = str(WORK / 'lcd/frame-')
bpy.ops.render.render(animation=True)
if width == 6000:
    texture.image = bpy.data.images.load(str(ROOT / 'output/connector-finished-ui-2026-10-22/275-recognized.png'))
    scene.cycles.samples = 32
    scene.render.filepath = str(WORK / 'hero-lcd.png')
    bpy.ops.render.render(write_still=True)
