# PSU tester case — I6 review CAD (2026-10-20)

**I6 = I5 + Petter's changes.** Exact B-rep. The outer skin and the 2.0 mm pipe wall are unchanged.

1. **Shell screws:** no inserts.
   - **Base:** Ø3.5 clearance hole, plus a Ø5.5 × 8.0 counterbore from below (depth confirmed by Petter).
   - **Screw positions** moved 1.35 mm toward the corner-radius centres, to (±46.41, ±38.36), in both base and top. This keeps ≥ 1.6 mm wall round the 8 mm pocket inside the lip line.
   - **Base screw columns:** Ø9 below the split, then Ø8.7 (clipped to the lip's outer face) up to z 10.5. That gives a 2.5 mm PLA floor under the head. Walls: 1.75 mm low, 1.6 mm in the raised part (inner and outer).
   - **Old base features removed:** the 6.4 × 3.2 counterbore and the 10 × 0.8 foot recess.
   - **Top bosses:** Ø7.2, starting at z 11.0 (0.5 split gap kept). Pilot Ø2.0 × 10.5, wall 2.6 mm. The bosses are 1.2 mm clear of the PCB corners in y.
2. **Rubber grommet feet (assumed):** hip Ø5.5 × 8.0 fills the pocket; flange Ø9.5 × 2.0 stands 2.0 mm below the base as the foot; through-bore Ø5.0.
   - The screw head (Ø4.5 × 1.7) sits inside the grommet bore and bears flat on the PLA floor at z 8.0. No countersink needed.
3. **All 8 screws: M2.5 × 12 plastic thread-forming, flat (pan/cheese) head.**
   - **Shell:** engagement 9.0 mm (3.6 × d), 1.5 mm spare pilot depth.
   - **PCB:** pilot Ø2.0 × 12, engagement 10.4 mm, 1.6 mm spare, wall 2.0 mm.
   - **Head type:** if the screws are countersunk, the floor would need a 90° countersink. Ø2.0 pilot is tight for M2.5 in PLA (open to 2.1–2.2 if needed).
4. **H2 location corrected:** the vendor STEP tree names `PCB/H2` at x +12..+15 and `PCB/H1` at x −15..−12, in the module frame.
   - So "connector 2" = H2 = the RIGHT header viewed from the FRONT (glass side, USB down), and the left one viewed from the back. That matches the H2 pin table and Petter's "right".
   - I5 had the harness on the −x header, which is H1. I6 moves the 5 pins, the Dupont and the window to +x (world x +13.5).
   - The wires now cross over the flat cable at z ≈ 38.6 (2.55 mm clear).
5. **Retainer window:** reduced to the H2 header + Dupont footprint + 0.75 mm.
   - New: u −7.12..7.48 (14.6 wide), |x| > 11.25.
   - Old: u −8.82..9.18 (18.0 wide), with the same x limit.
6. **Antenna:** C3-001 (5.8 × 2.0 × 1.0 ceramic chip antenna).
   - Position (module frame): x −2.9..2.9, u 14.79..16.79, a −4.4..−3.4.
   - It is at the top edge, about 90° away from the window, and only reaches 4.4 mm deep; the flange sits at 9.4–10.9 mm. So there is no collision.
   - It sits in the sleeve relief at 77.7–102.3° (1.35 deep). Clearance from the retainer is 0.385 mm. Every vendor back-side part is ≥ 0.35 mm from the retainer.
7. **Vents removed:** the deck is solid (no 6×6 grill).
- **Sheet views:** `review/v_*.png` were re-rendered for the I6 exterior (no vents, grommet feet).

Rebuild: `../.venv/bin/python build_all.py && ../.venv/bin/python make_3mf.py && ../.venv/bin/python validate.py && ../.venv/bin/python sheet.py` (about 1 min).
All parameters come from `src/i6_params.py` (and I2, I, H2 underneath). The CAD scripts in this folder hold only the geometry recipes.

## Files
- `PSU_case_I6_assembly.step`: two named groups. `printed_parts` holds I6_base, I6_top, I6_crown and I6_retainer, each coloured. `reference_bodies_NOT_PRINTED` holds 16 bodies: the Rev D2 board, J1–J3, J4, the tall part, ICs, the display, the male and female USB overmolds, the flat cable and the 12-pin cable.
- `step/I6_{base,top,crown,retainer}.step`: one solid per part, world frame.
- `stl/*_print.stl`: print orientation. `stl/*_world.stl`: assembly frame. `stl/REF_*.stl`: the reference bodies.
- `PSU_case_I6_print.3mf`: core-spec 3MF, 4 named objects on one plate, each with a display colour. Assign filaments/AMS slots in Bambu Studio.
- `review/PSU_case_I6_review.{png,pdf}`: A3 sheet with views, sections A-A, B-B and detail C, key dimensions, parts list, validation and open items.
- `validation.json`: the full check results.

## B-rep status
Every body is true B-rep; nothing is faceted.
- The outer skin of the top is an R12/R4 rounded box plus a pipe cylinder and a tunnel cylinder, with fillets:
  - pipe-tunnel R6.7;
  - tunnel-deck R6.7;
  - pipe-deck variable, from R1.2 at the front generatrix (where the pipe stands only 0.7 mm proud) up to R5 at the flanks.
- Deviation from the I6 SDF skin (60k surface samples): mean 0.18, p95 1.5, max 4.8 mm. The crown-seat cut at the front is included in that figure. The worst case is in the side valley where pipe, tunnel and deck meet: the B-rep fillets are tighter than the SDF smooth-min. The tunnel crest is 1 mm lower than in the SDF so the fillet builds reliably.

## Design changes vs the I3 preview (carried into I6)
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

## I6 add-on: HR10A-10P-12S(73) cable plug (reference only, not printed)
- `REF_cable_12pin_7mm_external` (continues the 7 mm stub from y = -63, ~126 mm outside the case in a gentle curve onto the bench) + `REF_HR10A-10P-12S(73)_female_plug`.
- Plug model: `ref/HR10A-10P-12S73_derived.step`, derived (ref/make_hr10a_12s.py) from Hirose's HR10A-10P-12P.stp shell (L 43, d14.7, rear bushing d9.25-9.5) with a socket insert + 12 socket holes (approximate layout) and a d7 cable entry. The official 12S STEP is login-gated on hirose.com.
- Printed parts unchanged.
