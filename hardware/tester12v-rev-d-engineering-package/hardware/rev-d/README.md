# Rev D USB powered multipin tester

Rev D identifies multiple positive and return pins from **one common DC supply** across twelve inputs. It shows every pin as `+`, `−` or `?` on the round Waveshare ESP32 display. `?` means open or unknown, not a proven faulty or dead pin. At least one input must connect to each pole of the supply for live identification.

One USB cable into the non-touch Waveshare ESP32-S3-LCD-1.28 powers the display, ESP32 and measurement PCB through a five-wire harness. The supply under test provides its own voltage. This board does not supply 12 V and has no switched power outputs.

This is an **unbuilt engineering prototype**. The design is routed, the manufacturing exports match it, and computer tests have passed. Physical validation and JLC placement/DFM review remain. No Rev D order has been placed, and the old Rev B checkout has not been changed.

## Supported connections

Any number of inputs may connect to the positive pole, any number to the common return, and the rest may remain open. This includes eleven positive pins and one return, one positive and eleven returns, or six of each with no open inputs. Full identification across every such assignment targets **9–18 V DC**, including nominal 12 V. Lower voltages can be measured for some connections, but strongly unbalanced groups may become ambiguous; the firmware then withholds pin labels.

All-open, supply-off and only-one-pole-connected conditions can look identical. They produce unknown pin labels. A resistance or continuity test is not included. Multiple independent supplies, arbitrary intermediate rails, high-impedance outputs, PWM/AC and loaded networks between other pins are outside the supported connection model. Observing two voltage groups does not prove they come from one physical supply.

The input circuitry floats relative to USB. `−` means the return of the measured supply, not earth or USB ground. Isolation is functional for low-voltage work; the board is not a mains/CAT-rated instrument. The 48 V values in the stress calculations are not an operating or survival rating.

## Changes from Rev C

The twelve existing measurement channels remain. U8 is a fourth ADS1115, at I2C address 0x4B, which reads a dedicated replica of an open sensing channel through R49 and C28. C27 decouples its supply. This reference is measured during every input scan, so firmware no longer assumes that most DUT inputs are open. The [TI data sheet](https://www.ti.com/lit/ds/symlink/ads1115.pdf) documents the four I2C address selections; U8 uses ADDR tied to SCL.

The updated firmware classifies two live voltage groups relative to that reference, reports all twelve pin states, checks group consistency and rejects unstable scans. A source changing connection partway through an averaging interval does not retain a stale valid display. This is sampled DC measurement, not an instantaneous connection monitor.

The board remains 86 × 62 mm, two layers, 1.6 mm thick, with the same mounting holes, USB harness, isolated power module and external display. Calibration is still required on all twelve input channels. Rev C firmware and calibration are incompatible.

## Cost and stock

Using the September 30, 2026 JLC library snapshot, the nominal parts cost is **$10.5364 per board**, or **$21.0728 for two**. The four added parts total $1.2524 per board compared with Rev C. These estimates exclude attrition, PCB fabrication, assembly/loading fees, shipping, tax, duties, harness and external MCU/display.

The BOM has 89 fitted components: 75 Basic and 14 Extended. There are still fifteen unique part numbers: six Basic and nine Extended. U8 uses the same stocked ADC as U1–U3, so no new component type was introduced. The dated stock snapshot covers two nominal BOMs; it is not reserved stock or a checkout quotation. See [sourcing/jlc-review.json](sourcing/jlc-review.json).

## USB harness

| J4 pin | Tester signal | Waveshare connection |
| --- | --- | --- |
| 1 | USB5V | VSYS, USB-derived power |
| 2 | USB_GND | GND |
| 3 | HOST3V3 | 3V3 |
| 4 | SDA_HOST | GPIO6 |
| 5 | SCL_HOST | GPIO7 |

J4 is JST XH, five pins. Build a harness to the module's labelled pins; do not assume a direct connector match or use wire colours to identify pin 1. Never apply 12 V to J4. R46/R47 are intentionally unpopulated because the Waveshare module provides host I2C pull-ups. Do not connect measurement AGND to USB_GND during normal use.

The main measurement power travels from J4 pin 1 through F1, U4, U7 and U5. J4 pin 3 supplies only the USB side of the I2C isolator. Use a sound 5 V USB cable/source and verify total display-plus-PCB current on the prototype; consumption and startup peaks have not been measured.

## Files to use

- `tester12v.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `bank*.kicad_sch` and `libraries/` are the editable design.
- `previews/pcb-3d.png`, `schematic.pdf` and `assembly.pdf` are generated from that design. The converter and screw-terminal 3D bodies are dimensioned envelopes rather than detailed vendor models.
- `previews/display-*.png` are generated by running the actual display code with mocked hardware; they are not photographs of a tested LCD.
- `manufacturing/tester12v-rev-d-gerbers.zip` is the bare-PCB upload.
- `manufacturing/jlc-bom.csv` and `jlc-cpl-native-angles.csv` are the matching assembly inputs. All 89 fitted parts, including U7, U8 and connectors, are included.
- `manufacturing/pin1-review.csv` and `previews/assembly.pdf` are the orientation references. **CPL angles are native KiCad angles; JLC placement rotations are not approved.**
- `../../firmware/Tester12VRevD/` contains the matching source, compiled images and calibration instructions.
- [validation/REPORT.md](validation/REPORT.md) records completed and outstanding checks.

Upload only Rev D Gerbers, BOM and CPL together. Confirm exact part selections, stock after attrition, Economic service eligibility for the complete BOM, through-hole assembly, all IC/diode/connector orientations and JLC's DFM result before approving an order. Do not reuse Rev B or C placement corrections without review.

## Reproduce the checks

Use KiCad 9's bundled Python. `scripts/export_design.py` refreshes the schematic and fabrication data without rebuilding the PCB, and runs ERC, DRC, schematic parity and the independent 259-pad audit. Compile `test_firmware.cpp` with C++17 both as an executable and as `validation/firmware-check.dylib` using `-shared -fPIC`; then run `evaluate_frontend.py`. Run `test_integration.py` for the actual sketch with mocked hardware and `test_transients.py` for ngspice startup/shutdown cases. The firmware's `compile.py` builds the ESP32 binary without flashing. `package_design.py` verifies and archives the results.

`build_kicad.py` recreates placement and overwrites the routed PCB; it is not a routine export command. `finish_board.py` reconstructs routing from the saved SES and refills planes.
