D2 LOCAL CALIBRATION UI — TWO PASSES

Launch from the project root:
firmware/.venv/bin/python tools/calibration-ui/launch.py
Then open http://127.0.0.1:8765 on this machine.
Or double-click tools/calibration-ui/Open calibration.command.
The launcher starts a detached local service; closing the terminal or Codex turn
will not close it. Reopening the launcher reuses a running service. A deliberate
new pass can be started with the page's Start again from input 1 button.

The server must be the only program using /dev/cu.usbmodem58760426031.
Stop other serial monitors first. A device with protocol-2 batch firmware is
required. The UI verifies protocol, baseline, pass ID and saved zero-point mask
before enabling captures. It never sends zero or defaults.

FIRST PASS — ALL INPUTS AT 0 V:
- Turn the DC output OFF before moving the positive lead.
- Keep negative on AGND and USB connected; leave other eleven inputs open.
- Connect positive to INP1, set 0.00 V, then turn the output ON.
- Enter the actual multimeter reading and confirm the wiring; Capture 0 V.
- After the save acknowledgement, turn the output OFF. Continue to INP2.
- Repeat through INP12, keeping the supply set to 0.00 V for this entire pass.

SECOND PASS — ALL INPUTS AT ABOUT 12 V:
- After all twelve zeros, the page returns to INP1.
- Turn the output OFF, move positive to the displayed input and set about 12 V.
- Keep negative on AGND, other eleven inputs open and USB connected.
- Turn output ON. Enter the actual multimeter reading and save this input.
- Turn output OFF before continuing to the next input. Repeat through INP12.
- Remove the AGND connection before the final floating pin-pair check.

The software never operates the manual bench supply. OUTPUT ON/OFF refers to
the supply's own controls. Output OFF alone cannot provide a known 0 V point.

Each input has its own zero point. All twelve are stored together in device NVS
with a pass ID and validity mask, so USB reconnects and server restarts can resume.
The UI rechecks the matching pass and mask before allowing more captures. A point
interrupted before acknowledgement must be checked and captured again; captures
are never automatically repeated. Starting a new pass clears batch low-point
metadata only, preserving the open-input baseline and previously saved gains.
Each gain is replaced only when the device acknowledges CAL_SAVED. Old passes
remain in the output/calibration-ui/passes archive.

Live ADC node voltages come from actual firmware telemetry. The voltage preview
is an approximation using the selected input's own host-observed zero and stored
or nominal gain; it assumes a reference ratio of one. It is not an independent
accuracy measurement. Firmware uses its ratio-corrected 64-scan averages and the
operator's entered meter voltage. The final page shows measured pin-pair voltage.

The page requires fresh valid data, stable readings, a plausible selected input,
other inputs appearing open, a meter entry and wiring confirmation. These guards
assist wiring but cannot prove every external connection. HTTP requests time out
and automatically retry read-only polling if the page loses the local service.

Records: output/calibration-ui/pass.json, stored.json, passes/<id>/ and serial.log.
Service metadata and logs: output/calibration-ui/server.json and server.log.
The HTTP server binds only to 127.0.0.1 and uses same-origin command request tokens.
It does not publish or upload. Stop the process identified in server.json before
flashing firmware, and relaunch afterward. Run server.py directly for foreground
debugging. --restart-pass starts a new pass without erasing existing gain settings.

Tests use fake serial data and never open USB:
firmware/.venv/bin/python -m unittest discover -s tools/calibration-ui -v

SHARED INP1 GAIN AND SUPPLY TESTING

Use INP1 gain + test requests calcopy 1 after a protocol capability check.
INP1 must already have a measured, saved gain. The firmware copies that gain to
all twelve inputs, keeps each input's existing open-input/reference baseline,
and saves copied_mask=FFE in NVS. Inputs 2–12 are labeled copied; this does not
claim they were individually calibrated. An actual later calv clears that pin's
copied bit. Reconnects retain the source, copied flags, and recorded checks.

After the acknowledgement, the page switches to Power supply test. Turn DC output
OFF, REMOVE AGND/pogo, connect positive and negative to two different numbered
inputs (initially INP1 and INP2), leave the other ten open, then turn about 12 V ON.
The displayed voltage and +/−/? labels come from firmware classification. Select
another pair or Swap for the reverse direction; always turn output OFF before
moving leads. Compare with the actual multimeter and optionally Record supply
check. Checks use an explicit ±0.10 V comparison target and require matching pin
polarity; voltage or polarity failures are recorded without adjusting calibration.
Test several pairs spanning all three input banks. A passing check never relabels
copied gains as measured calibrations. No voltage is assumed from a supply setting.
