# Rev C display firmware and calibration

This firmware is for the non-touch Waveshare ESP32-S3-LCD-1.28 and the Rev C measurement PCB. It uses GPIO6/GPIO7 at 100 kHz for three ADS1115s at 0x48, 0x49 and 0x4A. The LCD remains directly connected to the ESP32 on the Waveshare module. The measurement board has no extra MCU.

The firmware compiled successfully with Arduino ESP32 core 3.3.7 and this target:

```
esp32:esp32:esp32s3:FlashSize=16M,PSRAM=enabled,CDCOnBoot=default,PartitionScheme=app3M_fat9M_16MB
```

For example, run `arduino-cli compile --fqbn '<target above>' --output-dir build .` from this directory. Build evidence and hashes are in `build-evidence.json`. No physical module has been flashed or tested with this revision. The supplied merged image is for this exact 16 MB target and includes the application and boot data; do not substitute it for a board with different flash configuration.

## First calibration

Use a stable, current-limited 12 V source and a trusted multimeter. Warm the assembled tester for several minutes. Open its USB serial port at 115200 baud with newline termination. The display intentionally shows FINISH CAL until the open-input baseline and all twelve gain calibrations are stored.

1. Disconnect all twelve input wires. Send `zero`. Expect `ZERO_SAVED`. This command assumes every terminal is open; its spread check cannot prove that condition.
2. For input 1, connect the calibration source negative to **TP19, AGND**, on the isolated measurement side. Leave inputs 2–12 open. Connect input 1 to AGND for the zero-voltage point and send `cal0 1`. Wait for `CAL_LOW_SAVED`.
3. Disconnect input 1 from AGND and connect it to the calibration source positive. Measure the actual source voltage with the meter, for example 12.013 V. Send `calv 1 12.013`. The accepted reference range is strictly above 10 V and below 14 V. Expect `CAL_SAVED`.
4. Disconnect input 1 and repeat steps 2–3 for inputs 2–12, substituting each pin number. Keep the other eleven inputs open during every calibration.
5. Disconnect the calibration source and its AGND wire. Confirm CAL LOADED and NO LIVE PAIR. Connect a floating 12 V source across two inputs and compare the reported voltage and polarity with the meter.

Only AGND is used as the calibration reference. USB_GND is on the other side of the isolation barrier. Avoid attaching grounded test equipment across both domains. In normal use the calibration AGND wire must be removed.

`zero` updates the open-input baseline and retains completed gains. `defaults` clears all calibration. The Preferences namespace is `tester12vc`; old calibration cannot be loaded accidentally. Interrupted partial calibration survives restart, but no measurement is shown until all twelve channels are complete.

## Output and limitations

Serial CSV includes sequence, acquisition-valid flag, twelve raw ADC node voltages, result state, positive pin, negative pin and pair voltage. These raw voltages are around 0.58 V; they are not the DUT terminal voltages. Normal readings average eight scans; calibration averages 64. Display updates are expected a few times per second, subject to actual I2C/LCD timing.

The classifier reports NO LIVE PAIR below approximately 0.5 V, a pair within the intended 0–18 V range, OVER RANGE above 18 V, or MULTI / CHECK for inconsistent input patterns. Faults invalidate the result instead of displaying a stale valid reading. This is not an arbitrary multi-supply analyser; one source and ten open terminals is the supported connection model.
