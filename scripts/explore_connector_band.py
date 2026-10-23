"""Compare connected readout bezel treatments at native RGB565 resolution."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import build_connector_optics as optics


OUT = Path(__file__).resolve().parents[1] / 'output' / 'connector-band-study-2026-10-22'
OUT.mkdir(parents=True, exist_ok=True)
STYLES = ('solid', 'smoked', 'pockets', 'reflected')
SAMPLES = (('cold front', (1, 2), 5.26),
           ('gold burst', (1, 2), 5.80),
           ('other pair', (3, 7), 5.80))
FONT = ImageFont.truetype(str(optics.FONT_PATH), 15)

sheet = Image.new('RGB', (240*len(SAMPLES), 272*len(STYLES)), (9, 10, 11))
pen = ImageDraw.Draw(sheet)
for row, style in enumerate(STYLES):
    optics.BAND_STYLE = style
    for column, (label, pair, seconds) in enumerate(SAMPLES):
        optics.select_preview_pair(*pair)
        frame = optics.frame_at(seconds)
        sheet.paste(frame, (column*240, row*272+32))
        pen.text((column*240+10, row*272+6),
                 f'{style.upper()}  ·  {label}', font=FONT, fill=(235,224,202))
        frame.save(OUT/f'{style}-{label.replace(" ", "-")}-240.png', optimize=True)
    print('rendered', style, flush=True)
sheet.save(OUT/'band-treatment-comparison.png', optimize=True)
print(OUT/'band-treatment-comparison.png')

# Selected treatment: show both the seating transition and a clean connected
# loop, always using the same 240 × 240 RGB565 render that feeds the device.
optics.BAND_STYLE = 'reflected'
optics.select_preview_pair(1, 2)
for label, start, count in (('seating', 3.0, 100),
                            ('connected', 5.0, optics.FPS)):
    frames = [optics.frame_at(start+i/optics.FPS) for i in range(count)]
    frames[0].save(OUT/f'tapered-enamel-{label}-240.webp', save_all=True,
                   append_images=frames[1:], duration=1000//optics.FPS,
                   loop=1 if label == 'seating' else 0,
                   lossless=True, method=1)
frames[40].save(OUT/'tapered-enamel-connected-peak-240.png', optimize=True)
print(OUT/'tapered-enamel-seating-240.webp')
