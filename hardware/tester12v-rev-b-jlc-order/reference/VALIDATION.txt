# Rev B validation - 30 September 2026

Status: computer checks pass. Unbuilt prototype; no physical verification.

| Check | Result |
|---|---|
| KiCad ERC | 0 violations |
| KiCad DRC with schematic parity | 0 violations, 0 unconnected items, 0 mismatches |
| Native schematic to PCB | All 352 numbered pads agree; only U7/U8 cross isolation domains |
| PCB | 90 x 80 mm; 2 layers; 1.6 mm; 0.2 mm minimum tracks; 0.6/0.3 mm vias |
| DC exported-netlist tests | 1,188 cases: 132 ordered pairs at nine voltages |
| Precision resistor corners | 64 cases; worst modeled 12 V error 0.03452 V |
| ADC/leakage sensitivity | 20,000 assumed trials; 99% uncalibrated error 0.25983 V; calibration required |
| Behavioral startup/shutdown | 12 cases at 0/12/18/48 V and 0.1/2/20 ms collapse; all ADC voltage window checks pass |
| Firmware host tests | 1,188 netlist cases, 132 independent permutations, fault/NaN/ambiguity/window checks |
| Source and manufacturing | BOM/CPL/native fields, DNP stencil, drills, outline and archive checks in release-checks.json |

The Rev B differences are explicitly checked against Rev A in `rev-b-design-delta.json`; unexpected value/pin/footprint/position changes fail the export. U7, the four local power capacitors, filter values and zener footprint are the permitted circuit changes. Power routing and five zener-adjacent detours changed. Sensing ratios, firmware scaling, protected switches and 0.1% measurement resistors are retained. Rev A remains in its separate directory.

## Changed components

MPS MIE1W0505BGLVH replaces unavailable RECOM. Manufacturer Rev1.0 pp2/4/14/16 establish its pinout, regulated output, no minimum load, capacitor recommendations and 4x5mm LGA land pattern. All 12 pin numbers are preserved; the four physically joined pad pairs are split into adjacent same-net polygons. EN is tied to input; VSEL is tied to output to select 5V. Input/output lands remain on their own side of the isolation corridor. Local 10uF+100nF input and 22uF+100nF output capacitors and return vias are fitted. The 35mA output budget is an engineering allocation, not measured current, versus the converter's 200mA capacity.

A conservative additive output allowance (accuracy, load/line regulation, ripple) is 4.60-5.40V. The TLV75533 operating maximum is 5.5V. This does not model abnormal overshoot or real switching behavior. Confirm VIN=4.5-5.5V at U7 after PTC/cable/host diode drops. Measure current, ripple, startup and regulator temperature on the first article.

The Basic 470pF X7R filters are tested at 600pF, above 470pF x1.10 tolerance x1.15 temperature =594.55pF. Worst modeled ADC overshoot is 0.098247V, below the +0.3V absolute voltage bound. The previous 1nF C0G release modeled 0.29249V. A proposed Basic 1nF X7R at 1.3nF was rejected after exceeding 0.3V. These are behavioral simulations with an ideal LDO, assumed low-supply buffer/switch behavior and generic diodes, not validated vendor startup models.

The nominal input RC pole increases from 18.0kHz to 38.3kHz. DC gain and firmware scale remain 37.3. Reduced filtering can increase white noise roughly 1.46x if this pole dominates; converter interference and aliasing are unmodeled. Record at least 60 seconds of noise and calibrated DC error on each ADC bank. Positive capacitance stress is used for discharge safety; MLCC bias/aging decrease does not increase this discharge time but affects noise filtering.

Hongjiacheng BZT52C12 has the required <=100nA leakage at 8V/25C. Its 350mW rating exceeds the conservative 1.84mW current-limited 48V dissipation bound by over 190x. SOD-123 lands replace SOD-123F, retaining cathode pin 1. The actual Zener knee and temperature leakage are not qualified by the generic SPICE diode.

## Limits and physical acceptance

Normal measurement scope is one isolated DC source at 0-18V on any two inputs, with other terminals open. The board is sense-only. 48V is a current-limited DC miswire design target, not a verified operating rating. Its behavioral cold-start model can isolate the switch and under-report about 41.46V. ESD, EMC, automotive transients, mains/CAT isolation and temperature extremes are not qualified.

The 20,000-trial ADC/leakage distributions are assumptions, not production yield or manufacturer-guaranteed worst cases. All twelve channels need two-point calibration followed by floating-pair tests. Firmware host tests and compilation do not prove hardware operation.

Follow README bring-up: inspect placement, verify isolation continuity, current-limit 5V power, check rails/reference/enable, detect all ADCs, test no-source and fault cases, calibrate, complete all 132 ordered pairs, and scope DUT-first/USB-first startup, shutdown and brownout. Avoid grounding the isolated side through ordinary oscilloscope leads. The blank result columns in bench-pairs.csv intentionally contain no fabricated measurements.

All 24 primary BOM types showed stock; availability and attrition must be rechecked at JLC. JLC-specific placement rotations and DFM, especially U7 LGA lands/paste and pin 1, remain order-stage checks. The 3D body for U7 is a dimensioned envelope, not a manufacturer mechanical model. The separate Waveshare display and enclosure are not included in the PCB geometry.

## Reproduction

Run `refresh_manufacturing.py`, `test_circuit.py`, `test_spice.py`, `check_rev_b_engineering.py` and `package_release.py` with KiCad Python. Compile/run `test_firmware.cpp` against `all-pin-pairs.csv`. `apply_rev_b.py` resets from preserved Rev A, followed by `route_rev_b.py`; do not run either over independent layout edits. `build_kicad.py` creates an UNROUTED placement and is not a release regeneration command. The final native PCB is authoritative.
