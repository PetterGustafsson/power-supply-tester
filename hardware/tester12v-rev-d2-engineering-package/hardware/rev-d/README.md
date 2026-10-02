# Rev D2 USB powered multipin tester

**D2 adds a black board with white wiring labels.** J4 has numbered `5 SCL7`, `4 SDA6`, `3 3V3`, `2 GND`, `1 5V` labels beside its pins on both board faces. The larger back-side key identifies GPIO6/GPIO7 and VSYS. Choose **black solder mask and white silkscreen** in the JLC order; the Gerbers alone do not select the colour. See `manufacturing/fabrication-settings.txt`. D2 changes no electrical connection, copper route or component position.

**D1 is the outward-terminal update.** J1, J2 and J3 have their wire openings facing the lower board edge (the edge labelled 1–12), with screw heads accessible from above. All three blocks rotate 180° about their centres. The twelve input positions, copper routes and ADC assignments are preserved, so labels still run **1–12 from left to right**. Within each connector, library contacts now run 4, 3, 2, 1 from left to right. Use `pin-map.csv` for the contact mapping.

The current editable files stay in `hardware/rev-d/`; their silkscreen and schematic revision are **D2**. The new complete package is `../tester12v-rev-d2-engineering-package.zip`. It supersedes the earlier Rev D/D1 manufacturing downloads and uses the unchanged Rev D firmware and calibration procedure. Parts, cost assumptions, board dimensions and mounting positions are unchanged.

Rev D identifies multiple positive and return pins from **one common DC supply** across twelve inputs. It shows every pin as `+`, `−` or `?` on the round Waveshare ESP32 display. `?` means open or unknown, not a proven faulty or dead pin. At least one input must connect to each pole of the supply for live identification.

One USB cable into the non-touch Waveshare ESP32-S3-LCD-1.28 powers the display, ESP32 and measurement PCB through a five-wire harness. The supply under test provides its own voltage. This board does not supply 12 V and has no switched power outputs.

This is an **unbuilt engineering prototype**. The design is routed, the manufacturing exports match it, and computer tests have passed. Physical validation and JLC placement/DFM review remain. This update has not modified or submitted an order in JLC.

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

Use a matching **five-way JST XH 2.50 mm plug/cable**. Viewed from the component side with the input terminals along the bottom edge, J4 pin 1 is the lower end of the connector, nearest the lower mounting hole. Its pad is square. The plug's wire-entry view and mating-face view are mirrored; identify cavities by the PCB pin they mate with, and check continuity to each ESP32 connection before powering. The labels stay visible beside the housing. `previews/pcb-bottom-wiring.png` shows the solder-side labels and full wiring key.

The main measurement power travels from J4 pin 1 through F1, U4, U7 and U5. J4 pin 3 supplies only the USB side of the I2C isolator. Use a sound 5 V USB cable/source and verify total display-plus-PCB current on the prototype; consumption and startup peaks have not been measured.

## Files to use

- `tester12v.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `bank*.kicad_sch` and `libraries/` are the editable design.
- `previews/pcb-3d.png`, `schematic.pdf` and `assembly.pdf` are generated from that design. The converter and screw-terminal 3D bodies are dimensioned envelopes rather than detailed vendor models. The terminal model now depicts wire openings and screw heads so its facing direction is visible; those small details are illustrative.
- `previews/display-*.png` are generated by running the actual display code with mocked hardware; they are not photographs of a tested LCD.
- `manufacturing/tester12v-rev-d2-gerbers.zip` is the bare-PCB upload.
- `manufacturing/fabrication-settings.txt` specifies black solder mask, white silkscreen and the five-wire harness mapping.
- `manufacturing/jlc-bom.csv` and `jlc-cpl-native-angles.csv` are the matching assembly inputs. All 89 fitted parts, including U7, U8 and connectors, are included.
- `manufacturing/pin1-review.csv` and `previews/assembly.pdf` are the orientation references. **CPL angles are native KiCad angles; JLC placement rotations are not approved.**
- `../../firmware/Tester12VRevD/` contains the matching source, compiled images and calibration instructions.
- [validation/REPORT.md](validation/REPORT.md) records completed and outstanding checks.

Upload only the enclosed D2 Gerbers, BOM and CPL together. Confirm exact part selections, stock after attrition, Economic service eligibility for the complete BOM, through-hole assembly, all IC/diode/connector orientations and JLC's DFM result before approving an order. Select black solder mask and white silkscreen. Do not reuse earlier placement corrections without review.

For J1–J3, **wire openings toward the lower board edge and screws upward** is the assembly requirement. The CPL now records 180° in KiCad coordinates. JLC may use a different library zero angle, so do not rely on that number alone. The XY350V manufacturer drawing in `sources/XY350V.pdf` shows the mounting arrangement but does not assign numbered contacts; the rightmost contact-1 convention is defined by this project's footprint. `manufacturing/terminal-orientation.txt` and the assembly drawing give the physical direction to check. The supplied JLC screenshot appears to show the terminal models lying on their side, with screw heads facing the edge; an in-plane rotation alone would not correct a tilted library model. Verify the physical assembly direction against the drawing.

## Reproduce the checks

Use KiCad 9's bundled Python. `scripts/export_design.py` refreshes the schematic and fabrication data without rebuilding the PCB, and runs ERC, DRC, schematic parity and the independent 259-pad audit. Compile `test_firmware.cpp` with C++17 both as an executable and as `validation/firmware-check.dylib` using `-shared -fPIC`; then run `evaluate_frontend.py`. Run `test_integration.py` for the actual sketch with mocked hardware and `test_transients.py` for ngspice startup/shutdown cases. The firmware's `compile.py` builds the ESP32 binary without flashing. `package_design.py` verifies and archives the results.

`build_kicad.py` recreates placement and overwrites the routed PCB; it is not a routine export command. `finish_board.py` reconstructs routing from the saved SES and refills planes.

`orient_terminals.py` applies the D-to-D1 mechanical update without rerouting and checks that all pad locations/nets and copper tracks remain unchanged. The saved SES placements and DSN reflect D1. The ERC, DRC, schematic parity and pad audit were rerun for D1; the existing Rev D electrical simulations and firmware results remain applicable because the input-to-ADC circuit is unchanged.

`label_harness.py` applies the D2 silkscreen and board-stackup colours without changing pads or routes. ERC, DRC, schematic parity and the pad audit were rerun for D2, including the per-pin silkscreen mapping on both board faces. Render with `kicad-cli pcb render --use-board-stackup-colors` to display the specified black/white finish.
