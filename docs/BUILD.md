# Build, restore and regenerate

## Working baseline

- Measurement PCB: **Rev D2** (`hardware/rev-d/`).
- Enclosure: **I15**, current 3MF/STLs in `case-cad/current/`.
- Display: non-touch **Waveshare ESP32-S3-LCD-1.28**, 16 MB flash.
- Arduino ESP32 core: **3.3.7**.
- Working application and optical asset: `firmware/releases/d2-live-2026-10-23/`.

The firmware is operator-confirmed on the assembled prototype. It reads real
ADCs; the separate optical demo sketches simulate electrical states.

## Tools

Use Python 3.10+ and create the environment from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install Arduino CLI and the matching Espressif board core. The board package
index is `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.

```sh
arduino-cli core install esp32:esp32@3.3.7 \
  --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
```

## Compile the firmware

```sh
arduino-cli compile \
  --fqbn 'esp32:esp32:esp32s3:FlashSize=16M,PSRAM=enabled,CDCOnBoot=default,PartitionScheme=app3M_fat9M_16MB' \
  --output-dir firmware/Tester12VRevD/build firmware/Tester12VRevD
```

`python firmware/Tester12VRevD/compile.py` also compiles and records hashes.
It finds `arduino-cli` on PATH, or uses the `ARDUINO_CLI` environment variable.
The checked-in release contains the exact installed binary, independently of
changes made by a future local build.

## Flash an existing tester

Close serial monitors and stop the local calibration server before opening the
USB port. List ports with `python -m serial.tools.list_ports` and set the tester
port for the current machine:

```sh
TESTER_PORT=/dev/cu.usbmodemXXXXX
python scripts/flash_serial.py --port "$TESTER_PORT" --baud 230400 write_flash \
  0x10000 firmware/releases/d2-live-2026-10-23/app.bin
```

This application-only command preserves the existing partition table, optical
asset and NVS calibration. The paced wrapper is included because this board's
USB serial bridge required paced writes during bring-up. A successful flash
reports `Hash of data verified.`

If the optical asset is missing or being restored, write the matching binary:

```sh
python scripts/flash_serial.py --port "$TESTER_PORT" --baud 230400 write_flash \
  0x610000 firmware/releases/d2-live-2026-10-23/live50.bin
```

## Initial installation on a matching blank board

The release contains the bootloader, partition table and OTA boot data as well
as the application and optical asset. Its address manifest is
[`flash-manifest.json`](../firmware/releases/d2-live-2026-10-23/flash-manifest.json).
Use this full initial-install command for the same 16 MB hardware target:

```sh
python scripts/flash_serial.py --port "$TESTER_PORT" --baud 230400 write_flash \
  --flash_mode dio --flash_freq 80m --flash_size 16MB \
  0x0 firmware/releases/d2-live-2026-10-23/bootloader.bin \
  0x8000 firmware/releases/d2-live-2026-10-23/partitions.bin \
  0xe000 firmware/releases/d2-live-2026-10-23/boot_app0.bin \
  0x10000 firmware/releases/d2-live-2026-10-23/app.bin \
  0x610000 firmware/releases/d2-live-2026-10-23/live50.bin
```

A new measurement board needs its own baseline and calibration. Follow the
[firmware calibration procedure](../firmware/Tester12VRevD/README.md). The
saved NVS files in the prototype's engineering records belong to that physical
board and retain the measured/copied-gain provenance.

## Local calibration and test interface

```sh
python tools/calibration-ui/server.py --serial-port "$TESTER_PORT"
```

Open `http://127.0.0.1:8765/`. The guided two-pass calibration and supply-test
workflow are described in [the UI guide](../tools/calibration-ui/README.txt).
Runtime state is created in `output/calibration-ui/`, which is ignored by Git.

## Host regression tests

```sh
clang++ -std=c++17 -O2 hardware/rev-d/scripts/test_preview_detection.cpp -o /tmp/tester-preview
/tmp/tester-preview
python hardware/rev-d/scripts/test_integration.py
python hardware/rev-d/scripts/test_calibration_commands.py
```

The standalone test exercises noisy pairs, the four-pin cable, confirmation,
dropouts, polarity, offsets and range/fault guards. The integration test runs
the actual sketch's acquisition, calibration, display publication and serial
measurement code against simulated hardware. Neither test opens a USB port.

## Artwork and poster

The checked-in device asset is ready to flash. To regenerate it, install
`rsvg-convert` (librsvg) and the Python dependencies, then run:

```sh
python scripts/build_live_optics_asset.py
```

Inputs include `output/geometry.json`, the chrome/gold connector images and
SVGs, `output/allied-vision-logo.svg`, and the bundled Inter font. The script
packages 311 RGB565 frames and updates `LiveMark.h`. Its asset manifest records
the binary format, section counts and SHA-256. Regeneration intentionally writes
generated files; compare hashes before replacing a known installed release.

For the broader artwork studies, run `python scripts/build_connector_optics.py`.
Older Node rendering helpers use `npm ci` and the `sharp` dependency.

The assembled product render uses the current I15 meshes and approved display
animation. Its [export and regeneration guide](../output/product-render/README.md)
covers the 6000 × 4500 still and GIF master, the lighter README GIF, and the
self-contained Blender scene.

The final poster is generated with Blender 4.2 and ReportLab:

```sh
blender --background --python scripts/build_final_layout_poster_scene.py
python scripts/build_final_layout_poster_pdf.py
```

Inputs are the I15 3MF, I9 component meshes, bundled Inter font and the assembly
parameters in the scene script. The render is 5600 × 3960; the PDF is A2 landscape
with vector labels. `-- --preview` after the Blender script and `--preview`
after the PDF script produce a smaller review version. Poppler can export PNGs:

```sh
pdftoppm -scale-to 5600 -singlefile -png \
  output/pdf/power-supply-tester-final-layout.pdf \
  output/final-layout-poster/power-supply-tester-final-layout
```

The current CAD exporter uses only the Python standard library:

```sh
python scripts/export_current_enclosure.py
```

## Source material and historical records

Older revision guides preserve the decisions and measurements made at the time.
The original engineering package ZIPs contain their historical firmware snapshots.
Current source and binary links are listed in the root README. Font licenses,
manufacturer references and supplied logo attribution are listed in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
