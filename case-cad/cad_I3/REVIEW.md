# PSU tester case — I3 review CAD (2026-10-20)

Rebuild: `../.venv/bin/python build_all.py && ../.venv/bin/python make_3mf.py && ../.venv/bin/python validate.py && ../.venv/bin/python sheet.py` (about 1 min).
All parameters come from `src/i3_params.py` (and I2, I, H2 underneath). The CAD scripts in this folder hold only the geometry recipes.

## Files
- `PSU_case_I3_assembly.step`: two named groups. `printed_parts` holds I3_base, I3_top, I3_crown and I3_retainer, each coloured. `reference_bodies_NOT_PRINTED` holds 16 bodies: the Rev D2 board, J1–J3, J4, the tall part, ICs, the display, the male and female USB overmolds, the flat cable and the 12-pin cable.
- `step/I3_{base,top,crown,retainer}.step`: one solid per part, world frame.
- `stl/*_print.stl`: print orientation. `stl/*_world.stl`: assembly frame. `stl/REF_*.stl`: the reference bodies.
- `PSU_case_I3_print.3mf`: core-spec 3MF, 4 named objects on one plate, each with a display colour. Assign filaments/AMS slots in Bambu Studio.
- `review/PSU_case_I3_review.{png,pdf}`: A3 sheet with views, sections A-A, B-B and detail C, key dimensions, parts list, validation and open items.
- `validation.json`: the full check results.

## B-rep status
Every body is true B-rep; nothing is faceted.
- The outer skin of the top is an R12/R4 rounded box plus a pipe cylinder and a tunnel cylinder, with fillets:
  - pipe-tunnel R6.7;
  - tunnel-deck R6.7;
  - pipe-deck variable, from R1.2 at the front generatrix (where the pipe stands only 0.7 mm proud) up to R5 at the flanks.
- Deviation from the I3 SDF skin (60k surface samples): mean 0.15, p95 1.2, max 4.3 mm. The worst case is in the side valley where pipe, tunnel and deck meet: the B-rep fillets are tighter than the SDF smooth-min. The tunnel crest is 1 mm lower than in the SDF so the fillet builds reliably.

## Design changes vs the I3 preview
- **Module loads from inside.** The USB tab (13.3 wide, out to r 21.1) is wider than both the 36.7 bore and the 38.4 pipe, so it cannot go in from the front.
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
