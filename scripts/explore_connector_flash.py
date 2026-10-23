"""Compare three device-resolution polarity flashes before choosing one."""
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont

import build_connector_optics as optics


OUT = Path(__file__).resolve().parents[1] / 'output' / 'connector-flash-study-2026-10-22'
OUT.mkdir(parents=True, exist_ok=True)
STYLES = ('ribbon', 'liquid', 'filament')
TIMES = (4.16, 4.32, 4.48, 4.64, 4.80)
FONT = ImageFont.truetype(str(optics.FONT_PATH), 15)


sheet = Image.new('RGB', (5 * 240, 3 * 274), (11, 12, 13))
pen = ImageDraw.Draw(sheet)
for row, style in enumerate(STYLES):
    optics.FLASH_STYLE = style
    for column, seconds in enumerate(TIMES):
        frame = optics.frame_at(seconds)
        sheet.paste(frame, (column * 240, row * 274 + 34))
        if column == 0:
            pen.text((11, row * 274 + 7), style.upper(), fill=(235, 225, 198), font=FONT)
        pen.text((column * 240 + 160, row * 274 + 7),
                 f'{seconds % 1:.2f}s', fill=(160, 167, 171), font=FONT)
        frame.save(OUT / f'{style}-{column}.png', optimize=True)
    print(f'rendered {style}', flush=True)
sheet.save(OUT / 'flash-pattern-comparison.png', optimize=True)

# A second view checks whether the chosen style also reads across the longer
# alternate pair while retaining the subdued crossed mark.
optics.select_preview_pair(3, 7)
other = Image.new('RGB', (3 * 240, 3 * 240))
for row, style in enumerate(STYLES):
    optics.FLASH_STYLE = style
    for column, seconds in enumerate((4.2, 4.5, 4.8)):
        other.paste(optics.frame_at(seconds), (column * 240, row * 240))
other.save(OUT / 'other-pair-comparison.png', optimize=True)
print(OUT / 'flash-pattern-comparison.png')

# The liquid variant has the clearest travel and the strongest warm sparkle at
# the actual LCD size. Use it for both recognition states, with only the logo
# state changing when a different pin pair is powered.
optics.FLASH_STYLE = 'liquid'
for label, pair in (('allied', (1, 2)), ('other-pair', (3, 7))):
    optics.select_preview_pair(*pair)
    # Start after the one-off seating exposure jolts so this is a clean loop.
    frames = [optics.frame_at(5 + index / optics.FPS)
              for index in range(optics.FPS)]
    assert len({frame.tobytes() for frame in frames}) == optics.FPS
    frames[35].save(OUT / f'gold-ooze-{label}-240.png', optimize=True)
    frames[40].save(OUT / f'gold-ooze-{label}-peak-240.png', optimize=True)
    frames[0].save(OUT / f'gold-ooze-{label}-240.webp', save_all=True,
                   append_images=frames[1:], duration=1000 // optics.FPS,
                   loop=0, lossless=True, method=1)
    palette_sheet = Image.new('RGB', (240 * 5, 240 * 2))
    for index in range(10):
        palette_sheet.paste(frames[index * 5],
                            ((index % 5) * 240, (index // 5) * 240))
    palette = palette_sheet.quantize(colors=256,
                                     method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE)
               for frame in frames]
    indexed[0].save(OUT / f'gold-ooze-{label}-240.gif', save_all=True,
                    append_images=indexed[1:], duration=1000 // optics.FPS,
                    loop=0, optimize=True, disposal=2)

(OUT / 'selected-pattern.json').write_text(json.dumps({
    'style': 'liquid', 'size': [240, 240], 'frame_rate': optics.FPS,
    'loop_frames': optics.FPS, 'loop_seconds': 1,
    'direction': 'negative to positive', 'palette': 'ice blue to bright gold',
    'accepted_pair': [1, 2], 'other_pair_example': [3, 7],
}, indent=2) + '\n')
print(OUT / 'gold-ooze-allied-240.webp')
