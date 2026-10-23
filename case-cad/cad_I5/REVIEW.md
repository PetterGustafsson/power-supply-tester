# PSU tester case — I5 review CAD (2026-10-20)

**I5 = I4 + the 5-wire display harness on "connector 2".** Outer skin, 2.0 pipe wall, base, crown: unchanged from I4 (top volume identical, 75.508 cm3).
- **Connector 2 = H2**, the RIGHT 2x10 1.27 mm header when the module is viewed from the BACK with the USB tab down (Waveshare mechanical drawing back view).
  In the vendor STEP (`ref/ESP32-S3-LCD-1_28.stp`, frame == module frame x,u,a) it is the header at x -15..-12, u -6.37..6.73, a -7.9..-3.4.
  Because the module sits in its native orientation in I4/I5 (USB tab down-slope, = the 180 deg flip vs H2), H2 lands at **world x = -13.5** — the user's LEFT when looking at the glass, same side as J4.
  Waveshare pin table puts every harness signal on H2: H2.1/2 GND, H2.3 VSYS, H2.4 3V3, H2.5 GPIO6 (SDA), H2.7 GPIO7 (SCL).
- **Reference bodies added:** 5 breadboard pins 0.64 sq x 11.5 (3.0 in H2, 8.5 in the Dupont; pin 1 assumed at the button end), 1x5 female Dupont envelope 12.7 x 2.5 x 14 incl. crimps on the H2 back face (a -7.9..-21.9), 5 leads OD 1.4 (26 AWG) with 6 mm straight + R>=5 bends to a JST-XH5 plug on J4 (plug top z 26.6). Display reference now = 36.4 disc (glass..PCB back, a -3.4..0) + tab + all 205 back-side vendor STEP solids.
- **Retainer re-designed:** the I4 C-ring stopped on the header backs (a -7.9) — H2's back is now occupied by the Dupont. I5 retainer is a press-in **sleeve** OD 36.8 (0.10 dia press) / ID 34.4, a -10.9..-3.4, that seats on the **PCB back rim** (r 17.2..18.2). ID 34.4 clears both headers and the Dupont (1.07 radial). 1.5 mm back flange (ID 29) with a window over H2 (u ±9, x < -11.25) for the housing + leads; tab-side notch as I4; 6 automatic reliefs (0.35 clear) round the BOOT/RESET buttons and rim passives -> ~204 deg of rim contact in 5 feet. Prints flange-down, support-free.
- **Ceiling ribs:** harness keep-out (housing +1.0 & finger room, each lead +1.0) subtracted; it only trims ~0.015 mm3 — ribs were already clear.
- **Sheet views:** the closed-case ortho images in `review/v_*.png` are reused from I4 (exterior is identical); sections are re-cut from I5 meshes.
- **Assembly:** plug the Dupont on H2 first, push the module up the bore from inside, thread the sleeve over the leads + XH plug (fits through ID 34.4) and press it home, then plug J4.

Rebuild: `../.venv/bin/python build_all.py && ../.venv/bin/python make_3mf.py && ../.venv/bin/python validate.py && ../.venv/bin/python sheet.py` (about 1 min).
All parameters come from `src/i5_params.py` (and I2, I, H2 underneath). The CAD scripts in this folder hold only the geometry recipes.

## Files
- `PSU_case_I5_assembly.step`: two named groups. `printed_parts` holds I5_base, I5_top, I5_crown and I5_retainer, each coloured. `reference_bodies_NOT_PRINTED` holds 16 bodies: the Rev D2 board, J1–J3, J4, the tall part, ICs, the display, the male and female USB overmolds, the flat cable and the 12-pin cable.
- `step/I5_{base,top,crown,retainer}.step`: one solid per part, world frame.
- `stl/*_print.stl`: print orientation. `stl/*_world.stl`: assembly frame. `stl/REF_*.stl`: the reference bodies.
- `PSU_case_I5_print.3mf`: core-spec 3MF, 4 named objects on one plate, each with a display colour. Assign filaments/AMS slots in Bambu Studio.
- `review/PSU_case_I5_review.{png,pdf}`: A3 sheet with views, sections A-A, B-B and detail C, key dimensions, parts list, validation and open items.
- `validation.json`: the full check results.

## B-rep status
Every body is true B-rep; nothing is faceted.
- The outer skin of the top is an R12/R4 rounded box plus a pipe cylinder and a tunnel cylinder, with fillets:
  - pipe-tunnel R6.7;
  - tunnel-deck R6.7;
  - pipe-deck variable, from R1.2 at the front generatrix (where the pipe stands only 0.7 mm proud) up to R5 at the flanks.
- Deviation from the I5 SDF skin (60k surface samples): mean 0.18, p95 1.5, max 4.8 mm. The crown-seat cut at the front is included in that figure. The worst case is in the side valley where pipe, tunnel and deck meet: the B-rep fillets are tighter than the SDF smooth-min. The tunnel crest is 1 mm lower than in the SDF so the fillet builds reliably.

## Design changes vs the I3 preview (carried into I5)
- **Module loads from inside.** The USB tab (13.3 wide, out to r 21.1) is wider than both the 36.7 bore and, at the front, the 40.7 pipe, so it cannot go in from the front.
  - The bore runs through to the cavity, with a tab channel on the front (under-deck) side.
  - The glass rim stops on the crown spigot.
  - A new hidden press-in C-ring retainer (part 4) holds the module back face at 7.9 mm depth, in place of the fins.
- **The I3 SDF had a hidden error.** Its 2.4 mm wall behind the 3 mm guide annulus ran into the module body. The CAD fixes this.
- **Ceiling ribs:** 1.6 x 6 mm at x ±21/±39 and y −30/−12/6/24, kept clear of the bore, plug, flat cable and socket.

## Print orientation
- **Base:** flat on its underside. No supports: the keel is 45°, the tie slots are 4.8 mm bridges and the foot has a chamfer.
- **Top:** upright on its split edge. The pipe and mound rise above the deck, so it cannot print deck-down. Upright, the deck, pipe, mound and crown seat are all top or side surfaces, and the bore is only 40° from vertical. The ceiling cells bridge ≤18 mm between ribs. The rib bottoms, the bore-side ceiling ring and the inside crest of the tunnel need tree supports from the plate. These supports are all hidden and come out through the open bottom.
- **Crown:** flange face down. No supports; the R0.4 bed edge is trivial.
- **Retainer:** flat.
