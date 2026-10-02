# Rev A pre-fabrication validation

Date: 2026-09-30. KiCad 9.0.6. **Computer checks completed; no assembled Rev A hardware has been tested.** This release is a first prototype, not a qualified instrument. Its intended function is voltage and polarity detection for one nominal 12 V DC source across any two of twelve terminals, with the remaining terminals open. It does not energize the DUT or support every possible multi-rail wiring arrangement.

## Results tied to the released design

| Check | Result | Evidence |
|---|---|---|
| Native schematic ERC, four sheets | 0 violations | `erc.json` |
| Native PCB DRC | 0 violations, 0 unconnected items, 0 schematic mismatches | `drc-final.json` |
| Independent physical pad/net comparison | All 356 numbered pads agree with exported schematic nets | `board-audit.json` |
| Input path and isolation net audit | All 12 input resistor paths correct; only U7/U8 bridge power domains | `board-audit.json` |
| Exported-netlist DC model | 1,188 cases: 132 ordered pairs × nine voltages | `circuit-results.json`, `all-pin-pairs.csv` |
| Resistor tolerance corners | 64 combinations; maximum modeled 12 V error 0.03452 V | `circuit-results.json` |
| Component sensitivity study | 20,000 trials; uncalibrated maximum absolute error 0.39038 V | `circuit-results.json` |
| Behavioral startup/shutdown simulation | 12 cases within the modeled ADC absolute voltage window | `spice-results.json`, `spice-*.cir` |
| Firmware classification tests | 1,188 circuit cases plus 132 independent permutations and fault/ambiguity cases passed | `firmware-tests.log` |
| ESP32-S3 firmware compile | Passed; 389,969 bytes program, 139,380 bytes static RAM | `firmware-build.log` |
| Fabrication archive consistency | See generated file, outline, drill and placement checks | `release-checks.json` |

The PCB has 927 track segments and 61 vias. Routed tracks are at least 0.20 mm wide; netclass clearance is 0.20 mm. The board is 90 × 80 mm, two layers, 1.6 mm thick. DRC exclusions are empty. The project leaves footprint filters/type suggestions, missing courtyard notices, and holes-inside-courtyard notices disabled; electrical shorts, clearances, overlapping courtyards, connectivity, outline, and solder-mask checks are enabled. These settings are inspectable in the native project.

Released PCB SHA-256: `8e68fb65e4d7663bc9b04b8eaf4f14a24ec3db056932f1bbd0cf0b777bbf6ff1`. `SHA256SUMS.txt` in the complete package identifies its other files. The native PCB is the finished layout; the historical placement/routing scripts do not regenerate it in one command.

## What the models establish

The DC solver reads the XML netlist exported by KiCad, rather than trusting the design-generation dictionary. It tests 0, 3.3, 5, 9, 12, 15, 18, 24, and 48 V across every ordered terminal pair. Its largest nominal 12 V loading error is 0.02679 V. The nominal linear ADC nodes span 0.85483–2.13888 V across the cases up to 48 V. This last figure is a linear model result, not proof of 48 V operation through the protection switches.

The 20,000-trial sensitivity sweep includes assumed ADC impedance/offset/gain and leakage spreads. Its 99th-percentile absolute uncalibrated error is 0.25983 V, exceeding the intended ±0.15 V acceptance target. **Two-point calibration of all twelve channels and subsequent floating-pair verification are required.** Those sweep distributions are engineering assumptions, not guaranteed manufacturer worst-case bounds or a predicted manufacturing yield.

The ngspice 44.2 models exercise 0/12/18/48 V attached before power-up, followed by 0.1/2/20 ms supply collapse. They exposed startup isolation and shutdown charge-retention problems in earlier iterations. The final circuit adds source bleeds, uses 1 nF filters, a stronger OPA320 buffer, a 220 Ω bias discharge resistor, and regulator reverse protection. At 12 V the final behavioral model settles to 11.97293 V on nominal scaling.

For 2 and 20 ms collapse, the modeled ADC excess above its falling supply is at most 0.03781 V. The extra 0.1 ms stress case reaches **0.29249 V**, close to the +0.3 V absolute limit. This is a small margin and is **not sufficient evidence to qualify hard supply collapse**. The model assumes an ideal LDO with no hold-up credit, a buffer that disconnects below 1.8 V, generic clamp diodes, and switch leakage that changes from 38 µA to 3 µA below 1 V. Actual partial-supply behavior is not covered by validated vendor models. Scope measurements during DUT-first startup, USB removal, brownout, and reconnection are mandatory on the first article. A failing measurement requires a circuit revision before a larger order.

The transient model can leave the protection switches isolated during a 48 V cold start and report approximately 41.46 V. Accordingly, 48 V is only an unqualified DC miswire-survival target; the normal measurement range is 0–18 V. No automotive, mains, ESD, EMC, surge, insulation-withstand, or temperature-extreme qualification has been performed.

## Native and manufacturing review

IC pin assignments and package lands were checked against manufacturer documents linked in the main README. Exact part suffixes matter: ISO1640**B**DR is the eight-pin device; OPA320AIDBVR is the final buffer. The 2026-09-30 JLC sourcing update assigns exact codes to all 114 fitted components. It uses eight Basic and sixteen Extended part types. Twenty-three of the 24 types showed stock for two boards; U7 / C5338283 requires preorder with unconfirmed lead time. See `../sourcing/jlc-review.json` and the README for prices and substitutions. JLC order-level part matching, placement rotations and delivery remain unconfirmed.

Sourcing substitutions preserve all nominal electrical values, connectivity and footprints. The PCB file hash changed only when hidden optimized purchasing fields were added. Regenerated Gerber/drill/stencil drawing commands match the previous release after excluding timestamps; see `manufacturing-sync.json`. Precision resistors and protection IC silicon remain unchanged. Passive ratings were matched by value, tolerance, dielectric, voltage and package; the new 22 uF part is NRND with deep prototype stock. Higher rated voltage does not itself establish effective MLCC capacitance at operating bias. The supply and transient bench tests remain required. Rerun ERC, DRC, pad/net audit, 1,188 DC cases, 64 corners, 20,000 sensitivity trials, 12 transient cases and firmware host tests passed after the update. `jlc-sourcing-checks.json` records BOM/CPL/native-netlist consistency and unchanged-physical-board verification.

The 3D PNG and STEP originate from the released native PCB. Component bodies use KiCad library models; the RECOM body is a representative SOIC model, not an exact manufacturer mechanical model. Display/enclosure fit cannot be inferred from it. The Waveshare ESP32-S3-LCD-1.28 mounts separately and connects by the documented five-wire harness.

The supply connection must be measured under load: U7 needs 4.5–5.5 V after the input fuse. Waveshare VSYS includes a USB diode drop, so a weak USB cable or supply may require a separate regulated USB-domain 5 V feed. Battery-only operation is not supported. The main README specifies the wiring and prevents accidental supply backfeeding or defeat of the isolation boundary.

## First-article acceptance still outstanding

Follow the main README's inspection, current-limited bring-up, calibration, and power-sequencing procedure. Fill in `bench-pairs.csv` for all 132 ordered pairs using a reference DMM. Its empty result columns are intentional: there are no measured results yet. Verify ADC disconnect/fault behavior, multiple-wire rejection, 3.3–18 V accuracy, noise, supply consumption, harness voltage, and isolation continuity before broader testing. Firmware was compiled and host-tested, not exercised against this unbuilt PCB.

Reproduction commands, from the project workspace (substitute your KiCad/Python installation paths):

```sh
kicad-cli sch erc --format json --output hardware/rev-a/validation/erc.json hardware/rev-a/tester12v.kicad_sch
kicad-cli pcb drc --schematic-parity --format json --output hardware/rev-a/validation/drc-final.json hardware/rev-a/tester12v.kicad_pcb
kicad-cli sch export netlist --format kicadxml --output hardware/rev-a/validation/schematic.net hardware/rev-a/tester12v.kicad_sch
python3 hardware/rev-a/scripts/audit_board.py
python3 hardware/rev-a/scripts/test_circuit.py
python3 hardware/rev-a/scripts/test_spice.py
c++ -std=c++17 -Wall -Wextra -Werror hardware/rev-a/scripts/test_firmware.cpp -o /tmp/tester12v-tests
/tmp/tester12v-tests hardware/rev-a/validation/all-pin-pairs.csv
```

`audit_board.py` needs KiCad's `pcbnew`; the circuit scripts need NumPy/SciPy. The ngspice script currently locates the bundled macOS shared library explicitly. These checks supplement manufacturer and assembler review; they do not replace the physical tests above.
