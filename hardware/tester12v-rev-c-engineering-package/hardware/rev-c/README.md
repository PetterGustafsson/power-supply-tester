# Rev C USB powered pair detector

One USB cable into the Waveshare ESP32-S3-LCD-1.28 powers the ESP32, its round LCD, and this measurement board through a five-wire harness. No battery or separate tester supply is required. The device being measured provides its own voltage; this board does not produce 12 V or energize its twelve inputs.

This is the cheaper, routed engineering prototype. The schematic, PCB, firmware and manufacturing exports match. Computer checks are complete, but JLC placement/DFM review and physical validation remain. It is not a validated product or a completed JLC order. The earlier Rev B checkout has not been replaced or paid.

## Measurement scope

Connect one DC source between any two of inputs 1–12 and leave the other ten inputs open. The intended range is 0–18 V, nominally 12 V. The firmware identifies a pair above its 0.5 V threshold and reports relative polarity. It cannot distinguish a disconnected source from a source at zero volts. Multiple sources, connected loads between other pins, and arbitrary multi-rail wiring are outside this design's validated model.

The measurement domain floats relative to USB. U6 isolates I2C; U7 transfers power across that boundary. This is functional isolation for low-voltage work, not a mains/CAT instrument. A 48 V calculation in the reports is a stress calculation, not a permitted operating or survival rating.

## What changed

Each input now uses two 1 MΩ resistors, a 4.7 kΩ bias resistor and a 470 pF capacitor ahead of an ADS1115. Strong attenuation replaces the three ADG4612 switch ICs and their supporting protection circuit. A passive bias divider replaces the op amp. The nominal ratio is 426.532 and one ADC count corresponds to about 13.3 mV at the input. Firmware averages readings and requires calibration before showing a measurement.

The board is 86 × 62 mm, two layers, 1.6 mm thick. Its isolated converter is the stocked through-hole EVISUN B0305S-1WR3, C7465186. This exact manufacturer and pinout matter. JLC lists this converter and the new screw terminals for Economic and Standard assembly. The 3.3 V regulator before the converter gives more margin for voltage drop through the display module's USB input path than the old converter's 4.5 V minimum input allowed.

## Cost and availability

The September 30, 2026 JLC library snapshot gives **$9.284 per board**, or **$18.568 for two**, at nominal fitted quantities and displayed 1+ prices. The equivalent Rev B catalogue calculation was $37.8786 per board, a 75.5% reduction. These figures exclude attrition, fabrication, assembly, loading fees, freight, duties, tax, harness and the external MCU/display.

There are 85 fitted components: 72 Basic components across six part numbers, and 13 Extended components across nine part numbers. All fifteen part numbers showed sufficient stock for two nominal BOMs. Stock is not reserved. See [the dated sourcing record](sourcing/jlc-review.json). Full Economic service acceptance and a new checkout total still need confirmation with the complete order.

## USB and display wiring

Use the **non-touch Waveshare ESP32-S3-LCD-1.28**, matching the supplied firmware. J4 is a JST XH five-pin connector. Make a harness to the module's labelled pins; this is not a claim that its connector is directly compatible with J4.

| J4 pin | Tester signal | Waveshare connection |
| --- | --- | --- |
| 1 | USB5V | VSYS, USB-derived power |
| 2 | USB_GND | GND |
| 3 | HOST3V3 | 3V3 |
| 4 | SDA_HOST | GPIO6 |
| 5 | SCL_HOST | GPIO7 |

The 3V3 connection powers the host side of U6 only. The main measurement supply comes from pin 1 through F1, U4, U7 and U5. Never apply 12 V to J4. Identify pin 1 from the square pad and assembly drawing, not cable colours. Do not connect AGND to USB_GND during normal measurements. R46 and R47 remain unpopulated because this Waveshare module already has I2C pull-ups.

The design allocates up to roughly 200 mA of USB-derived current for the measurement board during initial power budgeting; actual consumption and startup peaks have not been measured. Use a sound 5 V USB cable/source with capacity for the display module as well. Confirm the complete unit's current before assuming a particular computer port is sufficient. No battery is needed.

## Files and ordering status

- `tester12v.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `bank*.kicad_sch`, and `libraries/` are the editable design.
- `previews/schematic.pdf`, `previews/assembly.pdf` and `previews/pcb-3d.png` show that design. U7 and the screw terminals use dimensioned envelope models, not detailed manufacturer models.
- `manufacturing/tester12v-rev-c-gerbers.zip` contains bare PCB fabrication files.
- `manufacturing/jlc-bom.csv` contains all 85 fitted components, including U7 and the connectors.
- `manufacturing/jlc-cpl-native-angles.csv` uses native KiCad angles. **JLC rotations are not verified.** Check every IC, D1, U7 and connector against `pin1-review.csv` and the assembly drawing before approving placement. Do not reuse Rev B viewer corrections blindly.
- `manufacturing/stencil/` omits paste on R46/R47. Their crossed-out schematic symbols mean intentionally not fitted.
- `../../firmware/Tester12VRevC/` contains the matching source and compiled images. Rev A/B firmware and calibration are incompatible.
- `validation/REPORT.md` distinguishes completed checks from remaining work.

Before ordering, upload the Rev C Gerbers, BOM and CPL together, confirm all fifteen exact part selections and their stock/attrition quantities, review component orientation and through-hole assembly, and obtain JLC's final price and DFM result. The current package does not claim those website steps have happened.

## Reproducing the checks

Use KiCad 9's bundled Python for the scripts. `export_design.py` refreshes the schematic and manufacturing files and runs ERC, DRC, schematic/PCB parity and the independent pad audit. `evaluate_frontend.py`, `test_transients.py` and the C++ `test_firmware.cpp` reproduce the models and host tests. See the firmware README for compilation.

Do not run `build_kicad.py` as a routine export: its main function regenerates the placement and overwrites the routed PCB. `finish_board.py` is a routing reconstruction aid, not an idempotent release command.
