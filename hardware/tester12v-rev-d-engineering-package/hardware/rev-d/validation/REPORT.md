# Rev D verification and remaining tests

Rev D passes the computer checks below for the defined single-supply connection model. It has not been assembled or physically tested. CAD, model and host-software results must not be presented as proof that the finished instrument works.

## Completed checks

| Check | Result |
| --- | --- |
| Schematic ERC | Zero reported violations |
| PCB DRC | Zero reported violations, unconnected items or schematic parity issues |
| Independent pad audit | All 259 pad nets match the schematic; twelve input paths and the new reference channel checked |
| Exhaustive ideal firmware cases | 4,782,969 cases: all 531,441 assignments × three source voltages × three reference levels |
| Nodal circuit and actual classifier | 1,594,323 cases: all assignments at 9, 12 and 18 V; no wrong classifications, maximum nominal voltage error 8.3 mV |
| Component sensitivity | 270,000 cases across 300 seeded sets, three supply rails and three DUT voltages; no wrong classifications, maximum voltage error 47.8 mV |
| Independent nodal solver | Cross-check of the reduced model against a full matrix solve for representative balanced and extreme assignments |
| Actual sketch with mocked hardware | Four-ADC acquisition, missing reference ADC, timeout, configuration corruption, invalid reference, all-channel serial calibration, persistence, changing-input rejection and display states passed |
| ESP32 build | Matching sketch compiled; source and binary hashes recorded; not flashed |

Of the 531,441 ternary pin assignments, 523,250 contain at least one positive and one return. Assignments missing either pole intentionally produce unknown results. The tests do not invent a distinction between an unpowered wire and an open one.

The DC model uses typical ADS1115 input impedances and sweeps them over an assumed 0.5–2× range, with 1% resistor variations, assumed ADC gain/offset variation and quantization. Calibration occurs at a 3.3 V rail before a 3.0/3.3/3.6 V rail sweep. These sampled assumptions are not a guaranteed all-corners device model. PCB leakage, temperature drift, asynchronous conversion noise, EMI and real calibration error remain unmeasured. The provisional accuracy target is ±0.15 V near 12 V after room-temperature calibration.

The nominal calculated source loading is about 18 µA at 12 V with six positive and six return connections. The tester makes voltage observations; it does not prove continuity, identify earth, or establish whether electrically similar readings originate from separate supplies.

## Startup and shutdown model

Eighty ngspice cases cover 0, 12, 18 and calculation-only 48 V, with a single pair, positive/negative single-terminal stress and both eleven-to-one group arrangements. Input and reference capacitances are modelled at 1 nF as a conservative assumed envelope for the fitted 470 pF parts and parasitics.

All forty cases with 100 µs or 1 ms rail fall time stayed within the modelled ADC absolute input window. The maximum voltage above the falling rail was 0.240 V and the minimum input was −0.135 V. No credit is taken for ADC internal clamps.

**All forty imposed 1 µs or 10 µs rail-collapse cases failed that voltage-window test.** Those forced internal rail-short cases remain in the results. This design does not claim protection against an abruptly shorted analog supply. The assumption that ordinary USB removal produces a slower decay must be checked physically. These tests are not ESD, surge or 48 V survival qualification.

Power architecture and minimum-load resistors are retained from Rev C. U7 has five parallel 1 kΩ preload resistors, about 25 mA at 5 V, exceeding its 20 mA minimum at the calculated low output voltage. U4 preregulates USB-derived power to 3.3 V; U5 tolerates U7's unregulated output and has EN floating as its data sheet permits. The fourth ADC adds approximately one ADC's operating current, but total consumption, inrush, capacitor derating/stability and temperature rise remain bench checks.

## Required before assembly approval

Confirm the complete BOM is accepted by the chosen JLC service, with sufficient stock after attrition. Review native CPL angles against physical pin 1 coordinates for U1–U8, D1 and connectors. Verify through-hole wave-soldering, tooling/rails, component heights and DFM changes, then obtain a fresh Rev D quote. The previous checkout belongs to another revision.

## Physical test plan

1. Inspect component orientation, soldering, connector pinouts and R46/R47 DNP. Check supply shorts and accidental USB_GND–AGND continuity with power disconnected.
2. Power the tester with no DUT from a current-limited USB source. Measure P3V3, ISO5V_RAW, A3V3 and VBIAS; check current and temperatures after warm-up. Verify converter startup and regulator stability with the actual capacitors.
3. Check the Waveshare harness, real LCD layout and I2C responses at 0x48–0x4B. Disconnect U8 or its supply and confirm the display invalidates measurements.
4. Perform the twelve-channel calibration in the firmware README using a trusted meter and source. Remove the calibration AGND connection afterward.
5. Test all 132 ordered single pairs at 12 V. Then rotate the minority pin through all twelve positions for one-positive/eleven-return and eleven-positive/one-return cases. Test six/six, several open inputs, and mixed connector-bank groups at 9, 12 and 18 V. Record voltage error and 60-second noise; exact 18 V classification has a boundary tolerance from measurement error.
6. Test all open, only one pole connected, supply off, ambiguous intermediate voltages, connection changes during scans, power cycling, partial calibration and saved calibration. Confirm unknown/fault states rather than unsupported dead-pin claims. Separate equal-voltage supplies may look identical to one supply and cannot be ruled out by this tester.
7. Capture supply and analog-node waveforms during USB connection/removal with balanced and eleven-to-one 12 V groups, using appropriate isolated or differential probing. Verify inputs stay within −0.3 V to A3V3+0.3 V and that the firmware recovers without stale valid readings.
8. Recheck accuracy after warming and across the intended room-temperature environment, with representative cables. Only those measurements can establish actual range, accuracy and USB power requirements.
