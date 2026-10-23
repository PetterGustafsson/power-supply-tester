"""Package the current optical preview as exact RGB565 frames for ESP32 flash.

The firmware is an explicitly simulated display demo. It does not sample the
tester inputs or alter the saved calibration. Frames are XOR deltas compressed
with zlib and stored in the unused FAT data partition, not in the application.
"""

from pathlib import Path
import hashlib
import json
import struct
import zlib

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output' / 'connector-finished-ui-2026-10-22'
OUTPUT.mkdir(parents=True, exist_ok=True)
WIDTH = HEIGHT = 240
FPS = 50
RAW_BYTES = WIDTH * HEIGHT * 2
MAX_COMPRESSED_BYTES = 50000  # ConnectorOpticsDemo.ino decode buffer.
MAGIC = b'OPTICS50'
VERSION = 1
HEADER = struct.Struct('<8s8I')
FRAME = struct.Struct('<IIBBBBB')
assert FRAME.size == 13


def rgb565(im):
    rgb = np.asarray(im.convert('RGB'), dtype=np.uint16)
    assert rgb.shape == (HEIGHT, WIDTH, 3)
    return (((rgb[:, :, 0] >> 3) << 11) |
            ((rgb[:, :, 1] >> 2) << 5) |
            (rgb[:, :, 2] >> 3)).astype(np.uint16)


def preview_frames(name):
    animation = Image.open(ROOT / 'output' / name)
    return [rgb565(frame_at(animation, index))
            for index in range(animation.n_frames)]


def frame_at(animation, index):
    animation.seek(index)
    return animation.copy()


main = preview_frames('connector-optics-240.webp')
assert len(main) == 500
storm = preview_frames('connector-thunderstorm-240.webp')
storm_gif = Image.open(ROOT / 'output' / 'connector-thunderstorm-240.gif')
durations = []
for index in range(storm_gif.n_frames):
    storm_gif.seek(index)
    durations.append(storm_gif.info.get('duration', 20))
assert len(storm) == len(durations)
storm = [frame for frame, duration in zip(storm, durations)
         for _ in range(duration // 20)]
assert len(storm) == 100

all_frames = main + storm
keyframes = {0, 250, 500}
metas = []
payload = bytearray()
previous = np.zeros((HEIGHT, WIDTH), dtype=np.uint16)
largest = 0
for index, current in enumerate(all_frames):
    keyframe = index in keyframes
    if keyframe:
        delta = current
    else:
        delta = np.bitwise_xor(current, previous)
    raw = delta.astype('>u2').tobytes()
    encoded = zlib.compress(raw, 6)
    # Fast optical transitions can have a larger XOR delta than a complete
    # frame. Store those as independent keyframes to fit the installed player.
    if not keyframe and len(encoded) > MAX_COMPRESSED_BYTES:
        keyframe = True
        delta = current
        raw = delta.astype('>u2').tobytes()
        encoded = zlib.compress(raw, 6)
    assert len(encoded) <= MAX_COMPRESSED_BYTES
    assert zlib.decompress(encoded) == raw
    restored = delta if keyframe else np.bitwise_xor(delta, previous)
    assert np.array_equal(restored, current)
    changed = current != previous
    if np.any(changed):
        ys, xs = np.nonzero(changed)
        box = (int(xs.min()), int(ys.min()),
               int(xs.max()) + 1, int(ys.max()) + 1)
    else:
        box = (0, 0, 0, 0)
    if index == 500:
        box = (0, 0, WIDTH, HEIGHT)
    metas.append(FRAME.pack(len(payload), len(encoded), *box, int(keyframe)))
    payload.extend(encoded)
    largest = max(largest, len(encoded))
    previous = current

data_offset = ((HEADER.size + FRAME.size * len(metas) + 4095) // 4096) * 4096
header = HEADER.pack(MAGIC, VERSION, WIDTH, FPS, len(main), len(storm),
                     data_offset, len(payload), zlib.crc32(payload))
asset = bytearray(header)
asset.extend(b''.join(metas))
asset.extend(bytes(data_offset - len(asset)))
asset.extend(payload)
target = OUTPUT / 'optics50.bin'
target.write_bytes(asset)
report = {
    'format': MAGIC.decode(), 'version': VERSION, 'width': WIDTH,
    'height': HEIGHT, 'fps': FPS, 'main_frames': len(main),
    'storm_frames': len(storm), 'main_loop_seconds': len(main) / FPS,
    'helix_loop_seconds': 50 / FPS, 'data_offset': data_offset,
    'payload_bytes': len(payload), 'asset_bytes': len(asset),
    'largest_frame_bytes': largest, 'asset_sha256': hashlib.sha256(asset).hexdigest(),
    'source_main': 'output/connector-optics-240.webp',
    'source_storm': 'output/connector-thunderstorm-240.webp',
    'flash_pattern': 'one cold-to-gold directional ooze for every powered pair',
    'recognized_logo': 'static red Allied Vision emblem',
    'semantics': 'simulated display art; voltage and pin states are not measurements',
}
(OUTPUT / 'asset-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
