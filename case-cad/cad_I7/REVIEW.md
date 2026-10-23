# PSU tester case - I7b revision (2026-10-21)

I7b = I7 + the two changes below. Same folder (cad_I7). The I7a archive is kept as ../cad_I7a_review_snapshot.tgz.

1. **Zip tie moved to the middle of the trench** (tie7b.py, base.py). The two floor-level stations at y -8 / +4 are replaced by ONE station at the trench mid-length, y = -18.65 (cradle walls run y -45.3..+8.0). A single tie fits there, so no symmetric pair is needed.
   - 3.0 x 1.6 slots go through both trench walls at wall mid-height (z 4.4..6.0; tray floor 2.4, wall top 8.0).
   - 1.2 deep inner-wall grooves run from the slots down to a blind 3.4 bed pocket under the jacket (z 1.2).
   - There is a blind 6.0 x 5.8 head pocket on the tray floor right of the +x wall (z 1.2).
   - Floor left under every pocket is 1.2, and the underside is still one flat face.
   - It is support-free: the only new overhangs are the two 3.0 mm slot-roof bridges (down-facing horizontal area 68.6 mm2, was 83.7).
   - New reference body REF_zip_tie_2.5mm_centre (band 2.5 x 1.0 + head). Clearances:
     - tie to PCBA (J1/J2 THT pin tips at y -18.8..-18.0, z 12.1): 2.15
     - tie to cores: 0.38
     - tie to jacket: hugs it (contact)
   - The station is clear of the standoffs (x +/-40) and of the jacket end (y 8).
   - Base volume is 43.27 cm3 (was 43.18).
2. **Natural 12-core breakout** (breakout.py, route7b.py, mesh7b.py, layout7b.py).
   - The cores leave the jacket as the 9 + 3 bundle with a right-hand helical lay (45 mm lay length), with a ragged foil screen edge and 3 filler threads.
   - The splay comes from a relaxation: smoothing, bending stiffness, light gravity, wire/wire contact and an obstacle field of the real assembly.
   - In the case:
     - 4 cores (J1) U-turn to -x and 8 (J2/J3) to +x behind the jacket end.
     - They lie on the tray floor beside the trench, pass the tie, and rise in front of the board into J1-J3 at z 17.95.
     - Assignment is monotonic, so there are no crossings.
   - Results:
     - minimum core-to-core 0.03 (inside the tight bundle), 0.05+ after the splay
     - core to base 0.08 (resting on the floor)
     - core to PCBA 1.72
     - core to top 6.99
     - lengths 66..103
   - Ferrules: a flare (d3.0) and green collar (d2.6 x 4.5) surround the insulation end (1.2 mm overlap, no gap). The pin (d1.1 x 8.0 exposed) starts 0.8 mm inside the collar, so it is continuous. Pins have square crimp flats (0.88 across flats) and tinned strand ends.
   - Flat-lay layout: the cores are combed in bundle order (no plan-view crossings) with slight irregular curves. Ferrules rest on their flare rim and collar end.
   - STEP: the cores are exact sweeps along the relaxed splines (REF_cable_12pin_conductors_x12). The pins with flats, collars and strand ends are exact solids. The foil and filler are render-only.

Renders (I7b): renders/I7b_zip_trench.png, renders/I7b_breakout_closeup.png, renders/I7b_bay_routing.png (PCB ghosted). Updated: renders/I7_bay_inside.png and renders/I7_parts_layout{,_labels,_wes,_wes_labels}.png.

---

# PSU tester case - I7 review CAD (2026-10-20)

I7 = I6 + the changes below. Printed parts: exact B-rep (step/I7_*.step, solid, 0 free edges). Reference bodies are in
PSU_case_I7_assembly.step under `reference_bodies_NOT_PRINTED`. The real PCBA and the full vendor module are faceted or vendor solids,
so the assembly STEP is large (~160 MB).

## Changes
1. **Real PCBA.** `REF_PCB_*` bodies come from Petter's KiCad VRML export `ref/tester-d2.wrl`, parsed by `wrl.py` and `pcb_real.py`.
   - Board frame + (0, 2.6, 14.8) maps to world.
   - Board, J1-J3 (3.5 mm 4p terminals), J4 (JST B5B-XH), the tall part and all SMD parts are included. Closed meshes become faceted solids; SMD parts are shells.
   - Placeholder errors fixed: the terminals actually sit at x -18..-4 / 2..16 / 22..36 (the I6 boxes were 5.25 mm off), J4 is 4 mm further toward +y, and the tall part is 25.8 high.
2. **Real module perimeter.** The `REF_display` body is the complete Waveshare vendor STEP.
   - Outline (= Waveshare drawing): PCB OD 36.5, with its circle centre +0.13 in u; 39.5 tall; trapezoid USB tab 12.8 wide at the bottom; LCM 35.6.
   - I6 clashed with the real module: PCB x top 9.19 mm3 (tab flanks + top point), LCM x top 4.57 mm3.
   - I7: bore 36.70 -> 37.00 (pipe OD kept, wall 1.85). The shell cut follows the real PCB+LCM outline + 0.2, as a seat at a -3.6..0.15, and the tab region is open to the back for loading from inside. Retainer OD 37.10.
   - Result: 0 mm3 clash; mesh gaps PCB-top 0.20, LCM-top 0.19.
   - Figures: renders/I7_module_outline_overlay.png, renders/I7_module_bay_section.png.
3. **Base tie stations.** The floor through-slots and underside groove are removed; the underside is flat.
   - Per tie: blind band pocket 3.4 wide x 1.2 deep across the cradle (1.2 floor left); 3.0 x 1.6 slots through both trench walls at floor level; blind head pocket 5.6 x 5.4 x 1.2 beside the +x wall.
   - The cradle walls are now continuous. Support-free: slot bridges 3.0.
4. **12-pin fan-out.** The jacket ends at y 8 (past both ties). 12 conductors (d1.4, 0.34 mm2 ASSUMED) leave in an upward U-arc, run forward under the board at z 10.95, rise in a R3.5 U-arc in the front zone and enter the J1-J3 entries (z 17.95).
   - Each conductor has an insulated ferrule: 8.0 mm (0.314") pin d1.1, 6 mm inserted; green collar d2.6 x 4.5 + flare d3.0.
   - Lengths 56-74 mm. Wire -> terminal order is J1.1..J3.4 in x order (to confirm).
5. **H2 lead.** The 1x5 Dupont is replaced by 5 round single-pin housings d1.2 x 12 (gap 0.07 at the 1.27 pitch) on H2.1/.3/.4/.5/.7, with 28 AWG (d0.8) leads to the J4 XH plug (moved +4 y to the real J4).
   - The retainer window is unchanged; it already covers the housings, with 0.99 to the sleeve.
6. **USB extender "flip" (not done).** A 180 deg turn about the plug axis (a -4.52) puts the overmold at a -7.54..+8.46, i.e. 8.5 mm in front of the glass and through the deck (380 mm3 into the top). The extender is kept in the I6 orientation, with a USB-C tip now modelled (`REF_USB_male_plug_tip`). Open question: what "flip" means.

## Renders
- renders/I7_usb_cutaway_hero.png
- renders/I7_usb_extender_closeup.png
- renders/I7_bay_inside.png
- renders/I7_hero_connector.png
- renders/I7_parts_layout_labels.png, renders/I7_parts_layout.png
- renders/I7_module_outline_overlay.png
- renders/I7_module_bay_section.png

## Validation
See validation.json. OCC checks cover the printed parts and the exact refs; `clearance_mesh_fcl_mm` holds python-fcl mesh distances for the PCBA, vendor module and new refs.
