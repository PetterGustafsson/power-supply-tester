# Rev D display firmware and calibration

## Response update, October 23, 2026

The operator confirmed the latest revision responds in approximately 1–2 seconds
after reconnecting the 1–2 cable and remains steady, then confirmed that it works
well. The exact installed app and matching display asset are preserved in
[`../releases/d2-live-2026-10-23/`](../releases/d2-live-2026-10-23/).

The LCD detection path now evaluates four-scan windows during normal acquisition.
It uses the middle two samples of each input, then requires two consecutive
windows with matching pin masks and voltage agreement within 5% (0.4 V minimum). Powered
contacts must keep their polarity throughout each window; one bounded spike
on an otherwise quiet input is tolerated. The provisional pole ripple allowance
is the larger of 1.5 V and 20% of the detected supply voltage. This addresses
the observed 1–2 cable ripple and intermittent unused-input spikes that kept
the previous display detector idle or caused withdrawal.

For the provisional model only, a bounded shared offset of the powered
contacts may be removed before the balance check. This accommodates sequential
mux samples at different ripple phases without changing the measured voltage
difference or shifting quiet inputs. This does not change stored calibration
or the strict classifier used by the measurement CSV.

After identification, each accepted window verifies fresh voltage with the
same polarity on every known powered contact and verifies that the other
inputs remain quiet. Reference imbalance may vary within a bounded allowance
without restarting identification. The displayed provisional voltage is
smoothed across these windows. Missing poles, new energized contacts, reversed
polarity and a supply-off window cannot refresh the previous pair; a new pair
still requires confirmation. Repeated rejected windows expire the remembered
pair rather than turning it into an unlimited hold.

Confirmed previews are published directly to the display task without serial
or LCD transfers in the acquisition loop. A completed, valid eight-scan result
takes precedence. The strict 0.25 V stability guard, CSV validity, calibration
math and saved settings are retained; a filtered LCD preview remains provisional
when the underlying batch is rejected. The existing one-second insertion and
approved optical artwork are retained.

`DISPLAY_PREVIEW` records the signal and confirmation timestamps. Regression
tests cover a noisy pair, the observed four-pin connection, intermittent
contacts, polarity changes, stray signals and ADC faults. Installation and
physical timing evidence are in
[the response update record](../../output/fast-response-2026-10-23/flash-evidence.json).

## Installed live optical display, October 22, 2026

The connected tester now runs the real ADS1115 measurement firmware with the
finished connector artwork on its LCD. The optical asset is stored in the
FFat partition at `0x610000`; the application at `0x10000` draws the measured
voltage from live classified readings. For pair 1/2, the asset contains the
approved red Allied Vision emblem, material reflections, and cold-to-gold
current animation, with the demo's fixed voltage removed. Other pairs use the
live renderer for their polarity and effects.
Idle keeps the numbered brass pins and orange orientation sheen. A detected
powered pair triggers 21 optical insertion frames sampled across one second,
then a powered loop. Two consecutive valid zero-voltage batches trigger
withdrawal. A rejected or ambiguous batch keeps the last confirmed powered
image for up to six seconds; the measurement CSV still reports the rejected
batches without a voltage. The original October 22 preview required two
agreeing rejected eight-scan batches; the October 23 detector above replaces
that path. Such a display reading is provisional; the CSV and test console
continue to mark those batches invalid until they pass the strict stability
check. Other powered
pairs get a muted crossed mark.

The app and asset both passed the board's flash hash check. The saved NVS
calibration status remains `mask=FFF` and `copied_mask=FFE`. Two powered
insertions measured 966 and 965 ms on the tester, with all 21 frames shown and
no display errors. The recognized loop stayed active through rejected batches;
the valid pair 1/2 readings averaged about 12.29 V. The operator confirmed the
powered artwork on the physical LCD. At the previous open-input check, 40 of 40
scans were valid, and idle playback ran at 37–39 displayed fps. The local test
console is running. See the
[installation record](../../output/live-optics-2026-10-22/flash-evidence-recognized.json)
and [asset manifest](../../output/live-optics-2026-10-22/asset-manifest.json).

A later app-only response update starts the display from two agreeing, robust
pair estimates even if the strict scan rejects the batch. In a physical plug-in
test, the first changing batch was sequence 87, the display preview was ready
by sequence 89, and the first strictly valid supply batch was sequence 92.
The insertion then completed in 965 ms. The strict CSV and test console still
reported the preview batches as invalid. See the
[response update record](../../output/live-optics-2026-10-22/flash-evidence-fast-detect.json).

Regenerate the asset with `python3 scripts/build_live_optics_asset.py`, using
the Homebrew Python with NumPy and Pillow. Build the sketch with the target
listed below. The art generator is based on `scripts/build_connector_optics.py`;
the live asset strips illustrative electrical layers from the generic frames,
then packages the approved pair 1/2 powered frames without fixed numerals.

## Previous live build for cable testing, October 22, 2026

The previous source was compiled and application-only flashed at `0x10000` on
the connected Rev D tester. The flash hash passed and the saved NVS calibration
was unchanged. The device restarted into `LIVE_CONNECTOR`, reported baseline
validity and gain mask `FFF` with copied mask `FFE`, and completed 36 of 36
captured open-input scans without acquisition errors. At that point the
cinematic optical demo asset was not played by the measurement firmware. See
[that installation record](../../output/live-firmware-2026-10-22/flash-evidence.json).

This firmware is for the non-touch Waveshare ESP32-S3-LCD-1.28 and the Rev D measurement PCB. It uses GPIO6/GPIO7 at 100 kHz for four ADS1115s at 0x48, 0x49, 0x4A and 0x4B. The LCD remains directly connected to the ESP32 on the Waveshare module. The measurement board has no extra MCU.

That earlier display preserved the original connector artwork's metal reflections, knurling, recesses and plastic without surface washes or an artificial border. Bold circular lettering sat on the existing outer solid ring: a larger 27 px voltage reading with a smaller unit on the same baseline, and 16 px essential state labels. Fine dark outlines retained contrast across reflections; amber identified an action such as `HOLD STEADY`, and coral identified a fault or over-range reading. Outer pin IDs followed the contact circle; the three inner IDs stayed upright. Its flashes, trails and contact bursts ran between classified negative and positive pins. Titles, the redundant `DC` label and calibration labels remained removed. That build and previews are in [the bold display with flashes directory](../../output/bold-flashes-2026-10-19/).

`scripts/build_lcd_typography.py` generates fill and outline atlases plus pair spacing from the pinned font in `assets/fonts/inter/`, including its SIL Open Font License. Pin/unit faces use weight 650, statuses 750, and tabular values 700. The outlines are baked at 2x resolution into four-bit masks, adding one bilinear mask sample per pixel without runtime dilation. Generation requires Pillow with Raqm for kerning and tabular numerals (available through `/opt/homebrew/bin/python3` on the development machine). The PSRAM scene cache, serial measurement format and uninterrupted ADC averaging batches are retained. No measurement or calibration maths have changed for this visual update.

`scripts/build_electron_paths.py` generates 66 short pin-pair paths and a stencil updated for the current bold Inter labels. The restored effect retains its 4.2-second cycle, at most eleven illustrative routes and at most four contact bursts per frame. Flashes stay within the connector face and clear immediately on missing, stale, uncertain or invalid measurements. They illustrate classified polarity rather than measured current or individual external wire topology. Graphics still run only after a complete averaging batch, and stationary artwork/text reuse the PSRAM cache.

The firmware compiled successfully with Arduino ESP32 core 3.3.7 and this target:

```
esp32:esp32:esp32s3:FlashSize=16M,PSRAM=enabled,CDCOnBoot=default,PartitionScheme=app3M_fat9M_16MB
```

For example, run `arduino-cli compile --fqbn '<target above>' --output-dir build .` from this directory. Build evidence and hashes are in `build-evidence.json`. The supplied merged image is for this exact 16 MB target and includes the application and boot data; do not substitute it for a board with different flash configuration.

Initial USB bring-up on a user-confirmed D2 PCBA was performed on October 17, 2026. All four ADC addresses responded, and the standard Rev D firmware completed 38 valid averaged scans over a 20-second capture with no acquisition errors. An initial ADC fault was not reproduced during diagnostic and standard-firmware rechecks; its cause remains unconfirmed. The installed firmware reports `FINISH CAL`. The user subsequently reported approximately 5 V at USB5V and 3.3 V at HOST3V3, both relative to USB_GND. The open-input baseline was subsequently saved with a `ZERO_SAVED` acknowledgement after the user confirmed all twelve inputs were disconnected. Input 1 two-point gain calibration was subsequently saved with `CAL_SAVED pin=1` and mask `001`, using the user-reported multimeter reading of 12.03 V (the supply displayed 12.05 V). Gains for inputs 3–12, isolated-rail voltage checks, independent known-voltage tests, and the remaining first-article checks are still pending. See the [bring-up record](../../output/bringup-2026-10-17/flash-record.json) and [final serial log](../../output/bringup-2026-10-17/release-recheck.log). The original compile-time build evidence remains unchanged.

On October 18, an intermittent measurement-board communication fault recurred while resuming calibration: the diagnostic consistently found only the onboard IMU, with four valid scans among 439 samples. After the user reported the connection working, all four ADCs responded and a 20-second diagnostic capture produced 37 valid scans with no errors. The standard release was restored and verified; eight early invalid scans were followed by sustained valid acquisition. Input 2's two-point calibration was then saved using user-reported multimeter readings of 0.00 V and 11.98 V (the supply displayed 12.00 V at the high point). The `CAL_SAVED pin=2` acknowledgement reported mask `003`, confirming that inputs 1 and 2 are marked complete and that input 1's completion bit survived restart. Inputs 3–12 remain pending. See the [resume record](../../output/calibration-2026-10-18/resume-record.json).

## Two-pass firmware update, October 19, 2026

The protocol-2 update was compiled and application-only flashed to the connected D2 tester. The flash hash was verified, and the device reported a valid saved open-input baseline and gain mask `003` after restart. Current settings were backed up before flashing. The local page resumed at INP1 in the 0 V pass, with no captures made automatically. Build/flash evidence and live ADC validation are in [the update record](../../output/calibration-batch-2026-10-19/build-evidence.json). The original build evidence and rollback binary remain unchanged.

## Shared gain and supply tests, October 19, 2026

The user chose to reuse INP1's saved two-point gain for all twelve inputs, then verify with a supply. The shared-gain update was application-only flashed and hash verified after backing up current settings. `calcopy 1` acknowledged gain `427.9315796`, gain mask `FFF`, and copied mask `FFE`. Each input's previously measured open-input/reference baseline is retained. Inputs 2–12 are explicitly identified as using copied gains rather than individual measurements. Physical supply verification remains pending; no passing checks have been inferred from the calibration copy.

The local UI now opens in Power supply test mode. With output OFF, remove AGND/pogo, connect source positive to INP1 and negative to INP2, keep the other ten open, then enable about 12 V and compare with the multimeter. The page supports other pairs, swapping direction and recording voltage/polarity checks with an explicit ±0.10 V comparison target. Readings and pin labels come from the actual firmware CSV. A passing comparison retains the copied-gain label.

`calcopy <pin>` requires an existing measured source gain and a valid baseline. It copies only the gain, stores copied provenance in NVS, and enables normal measurement. `calv` with a newly measured two-point calibration clears the copied bit for that pin. Status reports `copied_mask`; the connector graphics identify shared calibration with SHARED CAL. See [shared-gain evidence](../../output/shared-calibration-2026-10-19/build-evidence.json).

## Live connector graphics, October 19, 2026

The round LCD now uses the existing connector artwork and mating-face pin layout. Amber identifies measured positive pins, cyan identifies returns, and neutral pins remain unknown. A live voltage and moving paths follow the classified connections; the animation illustrates polarity, not a current measurement. Only one common supply is supported. The SHARED CAL footer retains the distinction between measured and copied gains.

No-voltage, uncertain wiring, ADC fault, calibration capture and stale-data states clear the live voltage and animation. Display updates run outside complete averaging batches, leaving mux conversion timing and acquisition timeouts intact. Calibration math, NVS settings and the serial CSV format are unchanged.

The production renderer is exercised by `hardware/rev-d/scripts/test_display_graphics.cpp`, including animation, pin masks, byte order, framebuffer bounds and clearing stale states. `hardware/rev-d/scripts/test_integration.py` runs the actual sketch with mocked ADCs, display and NVS, and `test_calibration_commands.py` covers the calibration command parser. Build hashes, test logs, rendered previews and installation evidence are in [the graphics update directory](../../output/live-graphics-2026-10-19/); its `build/Tester12VRevD.ino.bin` is the graphics application. Historical release binaries and evidence remain in their original locations.

The graphics application was installed at `0x10000` after a 64 KiB settings backup, with the flash hash verified. The connected tester reported `DISPLAY_READY: LIVE_CONNECTOR`, resumed valid ADC scans and retained baseline validity, calibration mask `FFF` and copied mask `FFE`. The live stream also includes unstable-input guard results, which show CHECK WIRING; their cause was not established during this graphics update. The local page was restored in supply-test mode. The rendered preview is generated by the production renderer; it is not a photograph of the physical LCD.

After the user reported CHECK WIRING when applying a supply, display rendering was moved outside the entire eight-scan measurement batch, restoring the sampling schedule used before graphics. A calibration capture draws its banner before the first of its 64 scans. This removes display activity between samples without relaxing the 0.25 V stability limit. The integration test asserts that a normal batch performs no LCD transfers and that the capture banner precedes ADC conversions.

Rejected batches now emit `MEAS_UNSTABLE` with the varying-input mask, followed by `MEAS_MEAN_V`, `MEAS_SPAN_V`, `MEAS_RAW_V` and `MEAS_REF_V` diagnostic lines. Values follow input order 1–12, or reference phase 0–3. Means and spans are referred to the DUT inputs; raw/reference values are ADC node voltages. These diagnostics are emitted after sampling at most once every three seconds and do not turn rejected data into valid measurements. The normal 23-column CSV and stored calibration are unchanged. This follow-up build, tests and reflash evidence are in [the measurement timing update directory](../../output/graphics-measurement-2026-10-19/). A powered physical comparison is needed to establish whether the timing change resolves the reported symptom.

The follow-up application was reflashed after another 64 KiB settings backup, with its flash hash verified. That backup matches the settings region saved before the first graphics installation. The new `MEASUREMENT_MODE: quiet averaging batches` startup marker was observed, saved baseline validity and masks `FFF`/`FFE` were confirmed, and the local UI resumed live no-voltage readings. No new calibration commands were sent.

## Circular typography, October 19, 2026

The connector labels now use rounded Nunito lettering with proportional spacing and antialiased edges. The title and voltage follow the upper rings; status and calibration labels follow upright lower arcs. Outer pin numbers follow the contact circle, while the three central numbers remain beside their contacts. Artwork, contact geometry, polarity colours and measurement behaviour are retained.

`scripts/build_lcd_typography.py` generates `DisplayFont.h` from the pinned [Nunito source](../../assets/fonts/nunito/source.json). The original font and SIL Open Font License are included in `assets/fonts/nunito/`. Three compact glyph atlases retain twice-resolution coverage at four bits per sample; the renderer rotates each glyph along the circular baseline and draws a soft dark edge for contrast against the metal. No extra framebuffer or runtime font engine is needed.

Renderer checks cover atlas bounds, proportional spacing, intermediate edge coverage, rotated glyph clipping and circular placement, in addition to the measurement-state render cases. Actual-sketch integration checks retain the quiet sampling and calibration safeguards. Previews and build/install evidence are in [the typography update directory](../../output/organic-typography-2026-10-19/).

The typography build was application-only flashed at `0x10000` after a settings backup. Its flash hash, `DISPLAY_TYPE: rounded Nunito, circular lettering` startup marker and unchanged quiet-sampling marker were verified. The connected tester retained its valid baseline, calibration mask `FFF` and copied mask `FFE`, and the local page resumed live readings.

## Direct electron animation and rendering budget

The display now draws direct paths from measured negative pins to measured positive pins, with white electron packets, long coloured trails, travelling arrowheads, sparks and expanding contact bursts. `Electrons - to +` identifies the illustrated direction. These paths illustrate polarity; the tester does not measure current or infer which external wires connect individual pairs. For multiple poles, at most eleven selected paths cover every active pin, keeping rendering work bounded.

`scripts/build_electron_paths.py` precomputes all 66 pin-pair paths and a drawing stencil that protects contact symbols and pin numbers. The paths and stencil occupy 6,272 bytes in flash. The 4.2-second animation cycle and broad trails are designed for the board's measurement-paced refresh; the preview deliberately uses 600 ms frames. The previously installed typography build was observed updating about every 710 ms; this is a measured baseline, not a promised frame rate for the new build.

When available, PSRAM holds one 115,200-byte stationary scene cache. Voltage digits, packets and bursts are drawn over a fresh copy; changes to state, masks or status flags rebuild the cache. Numerical voltage changes reuse it. If PSRAM allocation fails, the renderer falls back to a complete render. The same internal framebuffer and LCD driver are retained. Display work remains outside complete ADC averaging batches; acquisition, calibration math and the stability threshold are unchanged.

Startup runs two explicitly labelled off-screen render fixtures (one pair and eleven routes) while the backlight is off. They never reach the LCD or measurement CSV, and the real scene rebuilds afterward. `DISPLAY_BENCH` reports their MCU render times. `DISPLAY_PERF` periodically reports real render and transfer times. Tests cover all 531,441 pin assignments, negative-to-positive endpoints, cache equality through state changes, protected labels, cache fallback and the existing measurement safeguards. Build, preview and installation evidence are in [the electron animation update directory](../../output/electron-flow-2026-10-19/).

The application-only update was flashed and hash verified after a settings backup that matches the preceding backup. The actual ESP32 off-screen fixtures measured 46.267 ms for one pair and 58.610 ms for eleven routes. Real full-frame LCD transfers took about 15.25 ms. A cached no-voltage render measured about 4.2 ms; initial and changed scenes take longer to rebuild. The device confirmed the PSRAM cache, quiet averaging, saved baseline and masks `FFF`/`FFE`. USB disconnected from the host after these checks; the local service remains available for automatic reconnect. The synthetic render fixtures are not physical voltage validation.

## First calibration

For the guided local UI, run `firmware/.venv/bin/python tools/calibration-ui/launch.py` from the repository root and open `http://127.0.0.1:8765`. The launcher keeps the server running independently of the launching terminal. The two-pass workflow captures inputs 1–12 at 0 V first, then inputs 1–12 at approximately 12 V. Stop other serial monitors before launching. See the [local UI instructions](../../tools/calibration-ui/README.txt). The voltage preview is approximate; firmware calibration uses the entered multimeter reading.

Use a stable, current-limited 12 V source and a trusted multimeter. Warm the assembled tester for several minutes. Open its USB serial port at 115200 baud with newline termination. The current display shows NOT READY until the baseline and all twelve gains are stored; calibration details remain available over serial and in the local UI.

1. For first-time setup only, disconnect all twelve input wires and send `zero`. Expect `ZERO_SAVED`. An existing valid open-input baseline is preserved when starting another calibration pass.
2. Send `calbegin <8-digit hex pass ID>` to begin a new two-pass calibration. This clears the batch's zero points while retaining the open-input baseline and existing gains. `calstatus` reports protocol version 2, the pass ID, low-point mask, batch completion mask, gain calibration mask and baseline validity.
3. Keep source negative on **TP19, AGND**. With output OFF, connect positive to input 1, leave the other eleven inputs open, set 0.00 V, then enable output. Verify near-zero voltage on the multimeter and send `cal0 1`. Wait for `CAL_LOW_SAVED`. Turn output OFF before moving to the next input; repeat `cal0` for inputs 2–12 at the same 0 V setpoint.
4. Return to input 1 with output OFF, set approximately 12 V, then enable output. Measure the actual voltage and send, for example, `calv 1 12.013`. The reference must be strictly above 10 V and below 14 V. Wait for `CAL_SAVED`, turn output OFF before moving, and repeat for inputs 2–12 using each actual multimeter reading.
5. Remove the calibration source and AGND wire. Connect a floating 12 V source across two numbered inputs and compare voltage and polarity with the meter.

Each input's 0 V point is stored in a versioned NVS batch record, with its own validity bit. Device reconnects retain these points. The UI checks the matching pass and mask before resuming; a missing capture acknowledgement must be resolved by checking and repeating the displayed point. `zero` invalidates batch low points because it changes their baseline. Existing `cal0`/`calv` per-input workflows remain supported.

Only AGND is used as the calibration reference. USB_GND is on the other side of the isolation barrier. Avoid attaching grounded test equipment across both domains. In normal use the calibration AGND wire must be removed.

`zero` updates the open-input baseline and retains completed gains. `defaults` clears all calibration. The Preferences namespace is `tester12vd`; old calibration cannot be loaded accidentally. Interrupted partial calibration survives restart, but no measurement is shown until all twelve channels are complete.

## Output and limitations

The display shows source voltage and twelve numbered pin states. `+` is positive, `−` is return, and `?` is open or unknown. A live result requires at least one connection to each pole of one common supply. Any count of positive, return and open pins is allowed. Full-assignment identification targets 9–18 V, including nominal 12 V; lower voltages with heavily unbalanced groups may be ambiguous.

U8 reads a dedicated reference during each of the four mux phases. The firmware uses that reference rather than assuming any DUT input is open. `zero` stores each channel's open-input/reference ratio; two-point gain calibration uses the same normalized signal. Earlier calibration formats are not loaded.

Serial CSV contains sequence, acquisition-valid flag, twelve raw ADC node voltages, four reference voltages, result state, positive mask, return mask, unknown mask, and source voltage. Masks are three hexadecimal digits; bit 0 corresponds to pin 1 and bit 11 to pin 12. Raw ADC values near 0.58 V are not DUT terminal voltages. Normal readings average eight scans; calibration averages 64.

The firmware rejects a scan batch if any input changes by more than 0.25 V referred to the DUT input during averaging. The serial result remains invalid, with NaN values, instead of reporting the average of changing connections. The LCD briefly keeps its last confirmed powered image to avoid restarting the animation on a rejected batch; after six seconds without another valid powered reading it withdraws. Missing or faulty ADC acquisition also invalidates the result. Device configuration is read back and checked on every conversion. These are software checks, not a guarantee of catching every hardware failure.

All-open, supply-off and only-one-pole-connected conditions are deliberately indistinguishable. No continuity test or controlled continuity stimulus is included. Multiple independent supplies or arbitrary intermediate rails are outside the supported connection model. Compatible voltage readings do not prove external wiring topology.
