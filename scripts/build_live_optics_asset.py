"""Build the optical connector background for the live Rev D firmware.

The generic frames omit illustrative electrical overlays. Recognized pair 1/2
frames preserve the approved current effects and static red emblem. Voltage
numerals are always drawn by the device from its live ADC reading.
"""

from pathlib import Path
import hashlib
import json
import struct
import zlib

import numpy as np
from PIL import Image

import build_connector_optics as art

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'live-optics-2026-10-22'
OUT.mkdir(parents=True, exist_ok=True)
HEADER = struct.Struct('<8s8I')
FRAME = struct.Struct('<IIBBBBB')
WIDTH = 240
RAW_BYTES = WIDTH * WIDTH * 2
MAX_COMPRESSED_BYTES = 50000
SECTIONS = (140, 21, 50, 50, 50)  # idle, insert, generic powered, withdraw, recognized
INSERT_SOURCES = [150 + round(index * 49 / 20) for index in range(21)]
SOURCES = (list(range(140)), INSERT_SOURCES,
           list(range(200, 250)), list(range(300, 350)),
           list(range(200, 250)))


def rgb565(image):
    rgb = np.asarray(image.convert('RGB'), dtype=np.uint16)
    return (((rgb[:, :, 0] >> 3) << 11) |
            ((rgb[:, :, 1] >> 2) << 5) |
            (rgb[:, :, 2] >> 3)).astype(np.uint16)


# Strip only the illustrative measurement layers. Retain exact material,
# reflection, datum, annulus, insertion optics and idle numeral rendering.
original_polarity_ooze = art.polarity_ooze
original_polarity = art.POLARITY
original_logo = art.LOGO
original_logo_glow = art.LOGO_GLOW
art.polarity_ooze = lambda image, *args, **kwargs: image
art.voltage_readout = lambda image, *args, **kwargs: image
art.POLARITY = np.zeros_like(art.POLARITY)
art.LOGO = np.zeros_like(art.LOGO)
art.LOGO_GLOW = np.zeros_like(art.LOGO_GLOW)

payload = bytearray()
metas = []
previous = np.zeros((WIDTH, WIDTH), dtype=np.uint16)
largest = 0
starts = (0, 140, 161, 211, 261)
preview = {}
for index, source_index in enumerate(sum(SOURCES, [])):
    if index == 261:
        # Preserve the approved pair 1/2 effects and static red mark exactly.
        # Only the illustrative voltage stays absent for live ADC lettering.
        art.polarity_ooze = original_polarity_ooze
        art.POLARITY = original_polarity
        art.LOGO = original_logo
        art.LOGO_GLOW = original_logo_glow
        art.QUIET_FRAMES.clear()
    current = rgb565(art.frame_at(source_index / art.FPS))
    if index in (0, 161, 286):
        preview[index] = Image.fromarray(np.asarray(art.frame_at(source_index / art.FPS)))
    keyframe = index in starts
    delta = current if keyframe else np.bitwise_xor(current, previous)
    raw = delta.astype('>u2').tobytes()
    encoded = zlib.compress(raw, 6)
    if not keyframe and len(encoded) > MAX_COMPRESSED_BYTES:
        keyframe = True
        delta = current
        raw = delta.astype('>u2').tobytes()
        encoded = zlib.compress(raw, 6)
    assert len(encoded) <= MAX_COMPRESSED_BYTES
    assert zlib.decompress(encoded) == raw
    assert np.array_equal(current, delta if keyframe else np.bitwise_xor(delta, previous))
    changed = current != previous
    if np.any(changed):
        ys, xs = np.nonzero(changed)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    else:
        box = (0, 0, 0, 0)
    metas.append(FRAME.pack(len(payload), len(encoded), *box, int(keyframe)))
    payload.extend(encoded)
    largest = max(largest, len(encoded))
    previous = current
    if index % 25 == 0:
        print(f'frame {index}/311', flush=True)

offset = ((HEADER.size + FRAME.size * len(metas) + 4095) // 4096) * 4096
header = HEADER.pack(b'LIVE50__', 1, WIDTH, art.FPS, len(metas), offset,
                     len(payload), zlib.crc32(payload), 0)
asset = bytearray(header)
asset.extend(b''.join(metas))
asset.extend(bytes(offset - len(asset)))
asset.extend(payload)
assert len(asset) <= 0x910000
target = OUT / 'live50.bin'
target.write_bytes(asset)
for index, image in preview.items():
    image.save(OUT / f'{index:03d}-clean.png')

# The original static red mark, no wordmark. Two 34x21 layers are tiny enough
# to keep in the app: opaque RGB565 and eight-bit coverage for antialiasing.
mark = art.ALLIED_MARK.resize((68, 42), Image.Resampling.LANCZOS)
mark = mark.resize((34, 21), Image.Resampling.LANCZOS)
pixels = np.asarray(mark, dtype=np.uint8)
color = (((pixels[:, :, 0].astype(np.uint16) >> 3) << 11) |
         ((pixels[:, :, 1].astype(np.uint16) >> 2) << 5) |
         (pixels[:, :, 2].astype(np.uint16) >> 3))
header_path = ROOT / 'firmware' / 'Tester12VRevD' / 'LiveMark.h'
header_path.write_text(
    '#pragma once\n#include <stdint.h>\nnamespace live_mark {\n'
    'constexpr uint16_t color[34*21] = {' + ','.join(map(str, color.flat)) + '};\n'
    'constexpr uint8_t alpha[34*21] = {' + ','.join(map(str, pixels[:, :, 3].flat)) + '};\n'
    '}\n')
manifest = {
    'format': 'LIVE50__', 'version': 1, 'fps': art.FPS,
    'sections': dict(zip(('idle', 'insert', 'powered', 'withdraw', 'recognized'), SECTIONS)),
    'frame_count': len(metas), 'asset_bytes': len(asset),
    'asset_sha256': hashlib.sha256(asset).hexdigest(),
    'largest_compressed_frame_bytes': largest,
    'semantics': 'approved pair 1/2 art without fixed voltage; other pairs use live rendering',
}
(OUT / 'asset-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
