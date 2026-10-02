# Rev C verification and remaining tests

The Rev C design passes the computer checks below. It has not been built or physically tested. The files are an engineering prototype package; a zero-error CAD report does not establish real hardware performance.

## Completed checks

| Check | Result |
| --- | --- |
| KiCad electrical rules | Zero reported violations on all four sheets |
| Routed PCB design rules | Zero reported violations, zero unconnected items, zero schematic parity issues |
| Independent connectivity audit | All 243 physical pad nets match the exported schematic; twelve input chains and USB harness checked |
| Isolation topology | Only U6 and U7 bridge the USB and measurement domains |
| DC network model | 1,320 nominal cases spanning all 132 ordered pairs; maximum model error within 0–18 V is 18.4 mV after model calibration |
| Component sensitivity model | 6,000 calibrated 12 V cases across 500 seeded component sets and three rail voltages; maximum model error 48.9 mV, no wrong pair/polarity |
| Firmware classifier and normalization | 3,564 pair/voltage/bias cases plus ambiguous-input, acquisition-failure, NaN, baseline and legacy-gain checks passed |
| Firmware build | Successful for ESP32-S3, 16 MB flash, PSRAM enabled; not flashed |
| Sourcing | Fifteen selected part numbers showed stock for two nominal BOMs on September 30, 2026; not reserved |

The DC model includes selected-channel ADS1115 loading using typical datasheet impedances, 1% resistor variation, assumed ADC gain/offset variation and quantization. It is not a vendor transistor-level simulation or proof of worst-case accuracy. Leakage, temperature drift, converter noise, ADC timing and real calibration uncertainty are not included in that 48.9 mV result. The design target remains ±0.15 V near 12 V after room-temperature calibration, pending measurement.

The independent audit checks the model's 2 MΩ input chain, 4.7 kΩ bias paths, bias divider and capacitors against the actual exported schematic. It also verifies converter pin assignments, ADC addresses, the floating TPS709 enable pin, the reverse-protection diode, the preload and intentionally unpopulated pull-ups.

## Power and shutdown checks

The ngspice passive network run contains 48 startup/shutdown cases. All 24 cases with 100 µs or 1 ms rail fall time stayed inside the modelled ADC absolute input window, including calculation-only ±48 V single-terminal stress. The maximum excursion above the falling rail was 0.194 V and the minimum input was −0.135 V. The model allows 600 pF per node and gives no credit to ADC internal clamps.

**All 24 forced 1 µs or 10 µs rail-collapse cases failed that voltage-window criterion.** These represent an abrupt imposed rail short; they remain recorded in `transient-results.json`. This design does not promise survival of a forcibly shorted analog rail. The assumption that ordinary USB removal is slower than 100 µs must be verified on the board. No claim of ESD, surge or 48 V survival follows from these simulations.

U7 requires at least 20 mA output load. Five 1 kΩ resistors in parallel provide about 25 mA at 5 V, or 22.9 mA at 4.625 V with +1% resistance, before the analog electronics load. Each resistor dissipates 25 mW at 5 V. The converter output capacitors total about 10.1 µF, below its 2,400 µF specified capacitive-load limit. U5 tolerates the unregulated output and its enable pin is intentionally floating as TI permits.

U4 supplies the converter from regulated 3.3 V. Using a conservative 150 mA example, the PTC's 2.3 Ω maximum post-trip resistance drops 0.345 V. At 4.2 V on J4, U4 would see about 3.855 V, above 3.3 V plus its 238 mV maximum dropout specification at 500 mA. This is a headroom calculation, not a tested minimum USB voltage. Current, transient startup and thermal rise still require measurement. The display module adds its own current demand.

## Before approving JLC assembly

Confirm the entire BOM is accepted by the chosen assembly service, including the wave-soldered converter and connectors. Recheck stock after attrition quantities, not just the nominal BOM. Review every polarized component and IC in the placement viewer using the physical pin 1 coordinates. Native KiCad angles have been exported; JLC rotations have not been approved. Confirm rails, tooling, component heights and any DFM changes before accepting the quote. The former Rev B checkout is not a Rev C order.

## Physical prototype test sequence

1. Inspect U7 and all IC orientations, solder bridges and DNP pull-ups. With power disconnected, check for low-resistance supply shorts and accidental USB_GND–AGND continuity. A resistance check is not an isolation certification.
2. Power from a current-limited USB source with no DUT attached. Measure J4 power, P3V3, ISO5V_RAW, A3V3 and VBIAS; confirm approximately 3.3 V, 5 V unregulated, 3.3 V and 0.579 V respectively. Record current and inspect temperatures after 15 minutes.
3. Verify the actual Waveshare harness, display operation and reliable I2C responses at all three ADC addresses. Check effective U5 output capacitance/stability with the fitted capacitors and load.
4. Follow the firmware calibration procedure. Validate every one of the 132 ordered pin pairs at 12 V; include representative 1, 3.3, 5, 9, 15 and 18 V checks. At the 18 V limit allow classification tolerance from measured error rather than assuming an exact digital boundary. Compare against a trusted meter and record noise over at least 60 seconds.
5. With a current-limited 12 V source attached, measure analog input and supply waveforms while USB is plugged and unplugged, at short and long cable lengths. Use isolated/differential probing to avoid defeating isolation. Confirm input pins stay within −0.3 V to A3V3+0.3 V, and the unit restarts without stale readings or corruption.
6. Test open leads, reversed polarity, a second connected source, interrupted I2C, repeated boot, partial calibration and saved calibration after power removal. Confirm the intended error states rather than false valid measurements.
7. Recheck offset and accuracy after warming up and across the intended room-temperature environment. Establish an actual working range and accuracy only from those results. ESD/transient testing would be a separate qualification activity.

Until these steps are complete, claims that the design is 100% certain to work or ready for unrestricted use would be unjustified.
