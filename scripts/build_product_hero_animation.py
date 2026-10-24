"""Prepare and encode the three-mode product GIF; render its LCD with Blender.

blender -b -P scripts/build_product_hero.py -- --final --scene-only
python3 scripts/build_product_hero_animation.py prepare --final
blender -b output/product-render/product-hero.blend -P scripts/render_product_hero_screen.py
python3 scripts/build_product_hero_animation.py encode

The static product is rendered once. The LCD uses the same native camera,
emission material, color management, and geometric occlusion for every frame.
"""
from pathlib import Path
import json
import hashlib
import sys

import numpy as np
from PIL import GifImagePlugin, Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/product-render'
WORK = ROOT / 'output/product-render-frames'
SOURCE = ROOT / 'output/connector-finished-ui-2026-10-22'
FPS = 25


def prepare():
    from build_connector_optics import frame_at, select_preview_pair

    (WORK / 'ui').mkdir(parents=True, exist_ok=True)
    (WORK / 'lcd').mkdir(exist_ok=True)
    main = Image.open(SOURCE / 'complete-experience-240.webp')
    other = Image.open(SOURCE / 'other-pair-thunderstorm-240.webp')
    # 3s idle, 1s insertion, 3s recognized, 3s other pair, 1s release.
    timeline = [(main, i, 'idle') for i in range(0, 150, 2)]
    timeline += [(main, i, 'seating') for i in range(150, 200, 2)]
    timeline += [(main, i, 'recognized') for i in range(200, 300, 2)]
    timeline += [(main, i, 'recognized') for i in range(250, 300, 2)]
    timeline += [(other, i % 100, 'other-pair') for i in range(0, 150, 2)]
    # Generate the release for the other pair so its muted mark and polarity
    # stay correct during unseating instead of briefly restoring the red mark.
    select_preview_pair(3, 7)
    timeline += [(None, i, 'release') for i in range(300, 350, 2)]
    for index, (source, frame, mode) in enumerate(timeline, 1):
        if source is None:
            image = frame_at(frame / 50)
        else:
            source.seek(frame)
            image = source.convert('RGB')
        image.save(WORK / 'ui' / f'frame-{index:04d}.png')
    Image.new('RGB', (240, 240)).save(WORK / 'black.png')
    width = 6000 if '--final' in sys.argv else 1200
    manifest = dict(width=width, height=width * 3 // 4, fps=FPS, frames=len(timeline),
                    duration_seconds=len(timeline) / FPS,
                    modes=['idle', 'recognized', 'other-pair'],
                    timeline=[dict(frame=i, mode=mode, source_frame=frame)
                              for i, (_, frame, mode) in enumerate(timeline, 1)],
                    semantics='Illustrated voltage and polarity; no live device operation.')
    (WORK / 'timeline.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared {len(timeline)} LCD frames at {FPS} fps.', flush=True)


def encode_variant(base, patches, crop, manifest, target, width):
    left, top, right, bottom = crop
    if width != base.width:
        scale = width / base.width
        base = base.resize((width, round(base.height * scale)), Image.Resampling.LANCZOS)
        left, top, right, bottom = [round(v * scale) for v in crop]
        patches = [p.resize((right - left, bottom - top), Image.Resampling.LANCZOS)
                   for p in patches]
    print(f'Encoding {base.width} × {base.height}: {target.name}', flush=True)
    under = base.crop((left, top, right, bottom))
    # GIF local color tables let the studio use all 256 colors while the LCD
    # has its own stable palette. Only the small LCD rectangle is updated.
    sampled = Image.new('RGB', (under.width * 8, under.height * 5))
    for j, i in enumerate(np.linspace(0, len(patches) - 1, 40).astype(int)):
        sampled.paste(patches[i], ((j % 8) * under.width, (j // 8) * under.height))
    display_palette = sampled.quantize(colors=232, method=Image.Quantize.MEDIANCUT)
    colors = np.asarray(sampled, dtype=np.float32).reshape(-1, 3)
    red, green, blue = colors.T
    accent_mask = (((red > 3 * green) & (red > 2 * blue) & (red > 30)) |
                   ((green > 1.15 * red) & (green > 1.05 * blue) & (green > 20)) |
                   ((blue > 1.3 * red) & (blue > 1.05 * green) & (blue > 20)))
    accents = colors[accent_mask].astype(np.uint8)
    if not len(accents):
        raise ValueError('Expected red logo and green readout accents')
    accent_image = Image.fromarray(accents.reshape(1, len(accents), 3))
    accent_palette = accent_image.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
    palette = Image.new('P', (1, 1))
    palette.putpalette(display_palette.getpalette()[:232 * 3] + accent_palette.getpalette()[:24 * 3])
    first_rgb = base.copy()
    first_rgb.paste(patches[0], (left, top))
    studio_palette = first_rgb.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    first = first_rgb.quantize(palette=studio_palette, dither=Image.Dither.FLOYDSTEINBERG)
    indexed = [patch.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
               for patch in patches]

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wb') as stream:
        header, _ = GifImagePlugin.getheader(first, info={'loop': 0})
        for block in header:
            stream.write(block)
        for block in GifImagePlugin.getdata(first, duration=1000 // FPS, disposal=1):
            stream.write(block)
        for patch in indexed[1:]:
            for block in GifImagePlugin.getdata(patch, offset=(left, top),
                    duration=1000 // FPS, disposal=1, include_color_table=True):
                stream.write(block)
        stream.write(b';')
    # Verify duration and every frame's update rectangle. Later frames cannot
    # change the exterior because the encoded rectangles cover only the LCD.
    check = Image.open(target)
    duration = 0
    for i in range(check.n_frames):
        check.seek(i)
        duration += check.info['duration']
        if i and tuple(check.dispose_extent) != (left, top, right, bottom):
            raise ValueError('GIF update extends beyond the stationary LCD rectangle')
    assert check.size == base.size
    assert duration == manifest['duration_seconds'] * 1000
    assert check.n_frames == manifest['frames']
    assert check.info.get('loop') == 0
    print(f'Verified {check.n_frames} frames, {duration / 1000:g}s, {target.stat().st_size / 1024**2:.2f} MiB; exterior is static.', flush=True)
    if width <= 1600:
        for name, index in [('idle', 25), ('recognized', 125), ('other-pair', 200)]:
            check.seek(index)
            check.convert('RGB').save(OUT / f'animation-{name}-preview.png')
    return dict(path=target.relative_to(ROOT).as_posix(), width=base.width,
                height=base.height, bytes=target.stat().st_size,
                sha256=hashlib.sha256(target.read_bytes()).hexdigest())


def encode():
    manifest = json.loads((WORK / 'timeline.json').read_text())
    projection = json.loads((WORK / 'projection.json').read_text())
    base = Image.open(WORK / 'background.png').convert('RGB')
    crop = projection['crop']
    under = base.crop(crop).convert('RGBA')
    patches = []
    for i in range(1, manifest['frames'] + 1):
        with Image.open(WORK / 'lcd' / f'frame-{i:04d}.png') as image:
            lcd = image.convert('RGBA')
        if lcd.size != under.size:
            raise ValueError(f'Unexpected LCD render size: {lcd.size} versus {under.size}')
        patches.append(Image.alpha_composite(under, lcd).convert('RGB'))

    if base.width == 6000:
        still = base.convert('RGBA')
        with Image.open(WORK / 'hero-lcd.png') as image:
            still.alpha_composite(image.convert('RGBA'), tuple(crop[:2]))
        still.convert('RGB').save(OUT / 'power-supply-tester-hero.png')
        still.convert('RGB').resize((1600, 1200), Image.Resampling.LANCZOS).save(
            OUT / 'power-supply-tester-hero-preview.png')
        variants = [(6000, OUT / 'power-supply-tester-three-modes-6000.gif'),
                    (1600, ROOT / 'docs/images/power-supply-tester.gif')]
    else:
        variants = [(base.width, OUT / 'power-supply-tester-three-modes.gif')]
    manifest['exports'] = [encode_variant(base, patches, crop, manifest, target, width)
                           for width, target in variants]
    manifest['crop'] = crop
    manifest['renderer'] = 'I15 CAD / Blender Cycles / AgX / fixed camera'
    manifest['source_art'] = [p.relative_to(ROOT).as_posix() for p in (
        SOURCE / 'complete-experience-240.webp', SOURCE / 'other-pair-thunderstorm-240.webp')]
    manifest['release_generator'] = 'scripts/build_connector_optics.py:frame_at with pair (3, 7)'
    manifest['scene'] = 'output/product-render/product-hero.blend'
    if base.width == 6000:
        manifest['additional_exports'] = [dict(path=path.relative_to(ROOT).as_posix(),
            bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            for path in (OUT / 'power-supply-tester-hero.png', OUT / 'product-hero.blend')]
    (OUT / 'animation-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    {'prepare': prepare, 'encode': encode}[sys.argv[1]]()
