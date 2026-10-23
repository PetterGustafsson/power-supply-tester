"""Render a gold, text-free connector shimmer study at LCD resolution.

Every frame is rounded through the display's RGB565 colour format before export.
The irregular light passes are seeded so previews remain reproducible.
"""

from pathlib import Path
import json
import math
import random

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'output/connector-base-240-rgb565.png'
DEST = ROOT / 'output/connector-shimmer-240.gif'
LOSSLESS = ROOT / 'output/connector-shimmer-240.webp'
STILL = ROOT / 'output/connector-shimmer-frame-240.png'
SIZE = 240
FPS = 5
DURATION = 30

base = np.asarray(Image.open(SOURCE).convert('RGB'), dtype=np.float32)
yy, xx = np.mgrid[:SIZE, :SIZE]
radius = np.hypot(xx + .5 - 120, yy + .5 - 120)
angle = np.arctan2(yy + .5 - 120, xx + .5 - 120)

# Only the machined metal catches this moving reflection. The insert and the
# black outside of the round display remain absolutely still.
metal = np.zeros((SIZE, SIZE), dtype=np.float32)
for centre, width, weight in ((62.5, 4.3, .74), (69.5, 1.8, .85),
                              (79.5, 2.8, .55), (98.5, 5.4, 1.0),
                              (107.0, 2.1, .43)):
    metal = np.maximum(metal, weight * np.exp(-.5 * ((radius - centre) / width) ** 4))
metal *= np.clip((base.mean(axis=2) - 34) / 110, 0, 1)
pin_geometry = json.loads((ROOT / 'output/geometry.json').read_text())['pin_centres_mm']
pin_glints = []
for x_mm, y_mm in pin_geometry.values():
    px, py = 120 + 15 * x_mm, 120 + 15 * y_mm
    dot = np.exp(-.5 * (((xx - (px - 1.5)) / 1.9) ** 2 +
                        ((yy - (py - 1.8)) / 1.7) ** 2))
    pin_glints.append((math.atan2(py - 120, px - 120), dot))

rng = random.Random(20261022)
events = []
start = 1.5
while start < DURATION - 3.5:
    events.append((start, rng.uniform(2.5, 3.3), rng.uniform(-math.pi, math.pi),
                   rng.choice((-1, 1)), rng.uniform(1.05, 1.6)))
    start += rng.uniform(4.0, 5.9)


def rgb565(image):
    pixels = np.clip(image, 0, 255).astype(np.uint16)
    r = pixels[:, :, 0] >> 3
    g = pixels[:, :, 1] >> 2
    b = pixels[:, :, 2] >> 3
    return np.stack((r * 255 // 31, g * 255 // 63, b * 255 // 31), axis=2).astype(np.uint8)


def frame_at(seconds):
    strength = np.zeros((SIZE, SIZE), dtype=np.float32)
    gold_flash = np.zeros((SIZE, SIZE), dtype=np.float32)
    for start, duration, beginning, direction, travel in events:
        progress = (seconds - start) / duration
        if not 0 < progress < 1:
            continue
        centre = beginning + direction * travel * progress
        delta = np.arctan2(np.sin(angle - centre), np.cos(angle - centre))
        # A broad soft reflection carries one fine, brighter highlight.
        sweep = .48 * np.exp(-.5 * (delta / .26) ** 2)
        sweep += .37 * np.exp(-.5 * (delta / .065) ** 2)
        envelope = math.sin(math.pi * progress) ** 1.4
        strength = np.maximum(strength, metal * sweep * envelope)
        for pin_angle, dot in pin_glints:
            difference = math.atan2(math.sin(pin_angle - centre),
                                    math.cos(pin_angle - centre))
            gold_flash = np.maximum(gold_flash,
                                    dot * .78 * math.exp(-.5 * (difference / .19) ** 2) * envelope)
    tint = np.array((1.0, .97, .8), dtype=np.float32)
    lit = base + strength[:, :, None] * (255 - base) * tint
    lit += gold_flash[:, :, None] * (255 - lit) * np.array((1.0, .98, .72))
    return Image.fromarray(rgb565(lit))


frames = [frame_at(index / FPS) for index in range(DURATION * FPS)]
frames[min(len(frames) - 1, round((events[0][0] + events[0][1] * .5) * FPS))].save(STILL)
frames[0].save(LOSSLESS, save_all=True, append_images=frames[1:],
               duration=1000 // FPS, loop=0, lossless=True, method=6)

# GIF needs one shared palette; sampling the base and several lit states keeps
# the static steel free of per-frame palette flicker.
swatches = Image.new('RGB', (SIZE * 2, SIZE * 2))
for slot, index in enumerate((0, 17, 47, 91)):
    swatches.paste(frames[index], ((slot % 2) * SIZE, (slot // 2) * SIZE))
palette = swatches.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
indexed[0].save(DEST, save_all=True, append_images=indexed[1:], duration=1000 // FPS,
                loop=0, optimize=True, disposal=2)
print(f'{DEST} ({len(frames)} RGB565 frames, {FPS} fps, {DURATION} s; {len(events)} irregular light passes)')
