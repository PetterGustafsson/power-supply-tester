"""Build all I7 review CAD: per-part STEPs (world frame), assembly STEP (named + coloured), print-oriented STLs, Bambu-importable 3MF."""
from common import *
import base as BASE, top as TOP, crown as CROWNM, parts as PARTS, time, json, os
t0 = time.time()
os.makedirs(f"{OUT}/stl", exist_ok=True); os.makedirs(f"{OUT}/step", exist_ok=True)
base = BASE.build(); top, outer = TOP.build(verbose=False); crown = CROWNM.world(CROWNM.build()); ret = PARTS.retainer_world()
print("built %.1f s" % (time.time() - t0))
COL = {"I9_base": ("Matte Charcoal", (0.10, 0.10, 0.11)), "I9_top": ("Matte Ivory White (or Marble)", (0.88, 0.87, 0.82)),
       "I9_crown": ("Basic Orange (suggested, name unverified)", (1.0, 0.416, 0.075)), "I9_retainer": ("Matte Charcoal", (0.10, 0.10, 0.11))}
PRINT = {"I9_base": base, "I9_top": top, "I9_crown": crown, "I9_retainer": ret}
for k, s in PRINT.items():
    s.label = k; s.color = Color(*COL[k][1])
    export_step(s, f"{OUT}/step/{k}.step")
RULES = [("HR10A", (0.75, 0.76, 0.78)), ("external", (0.05, 0.05, 0.05)), ("grommet", (0.12, 0.12, 0.12)), ("screw", (0.6, 0.6, 0.62)),
         ("harness_5_wires", (0.85, 0.15, 0.1)), ("housing", (0.1, 0.1, 0.1)), ("XH5_plug", (0.93, 0.93, 0.88)), ("breadboard_pins", (0.8, 0.7, 0.3)),
         ("ferrule_pins", (0.78, 0.78, 0.8)), ("strand_ends", (0.72, 0.45, 0.2)), ("zip_tie", (0.95, 0.95, 0.92)), ("collars_green", (0.1, 0.6, 0.2)), ("conductors", (0.75, 0.3, 0.1)),
         ("PCB_RevD2_board", (0.04, 0.04, 0.04)), ("XY350V", (0.04, 0.35, 0.12)), ("J4_JST", (0.93, 0.93, 0.88)), ("PCB", (0.12, 0.12, 0.12)),
         ("display", (0.15, 0.15, 0.17)), ("plug_tip", (0.8, 0.8, 0.82)), ("12pin", (0.05, 0.05, 0.05)), ("overmold", (0.05, 0.05, 0.05))]
def refcol(k): return next((c for key, c in RULES if key in k), (0.35, 0.35, 0.38))
refs = PARTS.refs(); RC = []
for k, s in refs.items():
    s.label = k; s.color = Color(*refcol(k))
    RC.append(s)
prints = Compound(children=list(PRINT.values()), label="printed_parts")
reference = Compound(children=RC, label="reference_bodies_NOT_PRINTED")
asm = Compound(children=[prints, reference], label="PSU_case_I9_assembly")
export_step(asm, f"{OUT}/PSU_case_I9_assembly.step")
print("steps %.1f s" % (time.time() - t0))
# print orientations (justification in REVIEW.md)
def to_print(k, s):
    if k == "I9_crown":   # flange down: local frame flipped so the visible flange face sits on the plate
        return CROWNM.build().rotate(Axis.X, 180).moved(Location((0, 0, CROWN['t'])))
    if k == "I9_retainer": return PARTS.retainer_print()
    if k == "I9_top": return s.moved(Location((0, 0, -(ZS + GAP))))        # upright on its split edge
    return s
for k, s in PRINT.items():
    export_stl(to_print(k, s), f"{OUT}/stl/{k}_print.stl", tolerance=0.01, angular_tolerance=0.08)
    export_stl(s, f"{OUT}/stl/{k}_world.stl", tolerance=0.02, angular_tolerance=0.1)
import pcb_real, trimesh
PCBG = pcb_real.groups()
for s in RC:
    if s.label in PCBG: pcb_real.mesh_of(PCBG[s.label]).export(f"{OUT}/stl/{s.label}.stl"); continue     # PCB: the KiCad mesh itself
    export_stl(s, f"{OUT}/stl/{s.label}.stl", tolerance=0.05)
# render-only meshes: PCB layers by colour, display sub-parts, single conductors
os.makedirs(f"{OUT}/stl/render", exist_ok=True)
lay = PCBG["_layers"]
for nm, test in (("silk", lambda c: c[0] > 0.9), ("copper", lambda c: c[0] > 0.6 and c[2] < 0.4), ("pads", lambda c: abs(c[0] - 0.5) < 0.05)):
    ss = [s for s in lay if test(s['rgb'])]
    if ss: pcb_real.mesh_of(ss).export(f"{OUT}/stl/render/PCB_{nm}.stl")
for k in ("REF_PCB_SMD_parts", "REF_PCB_J1_XY350V_4p", "REF_PCB_J2_XY350V_4p", "REF_PCB_J3_XY350V_4p", "REF_PCB_J4_JST_XH5", "REF_PCB_tall_part"):
    for nm, test in (("dark", lambda c: max(c) < 0.2), ("metal", lambda c: min(c) > 0.55 and max(c) - min(c) < 0.15), ("green", lambda c: c[1] > 0.3 and c[0] < 0.1),
                     ("white", lambda c: min(c) > 0.75), ("brown", lambda c: c[0] > 0.3 and c[2] < 0.25 and c[0] - c[2] > 0.1)):
        ss = [s for s in PCBG[k] if test(s['rgb'])]
        if ss: pcb_real.mesh_of(ss).export(f"{OUT}/stl/render/{k}__{nm}.stl")
VA = PARTS.vendor_all()
export_stl(PIPE_PLANE.location * VA[0], f"{OUT}/stl/render/display_PCB.stl", tolerance=0.02)
export_stl(PIPE_PLANE.location * VA[1], f"{OUT}/stl/render/display_LCM.stl", tolerance=0.02)
export_stl(PIPE_PLANE.location * Compound(VA[2:]), f"{OUT}/stl/render/display_parts.stl", tolerance=0.02)
import subprocess; subprocess.run(["../.venv/bin/python", "mesh7b.py"], check=True)     # I7b: render meshes of the breakout (tubes, ferrules, foil, filler)
export_stl(outer, f"{OUT}/stl/_top_outer_world.stl", tolerance=0.01, angular_tolerance=0.05)
print("stls %.1f s" % (time.time() - t0))
json.dump({k: dict(filament=v[0], rgb=v[1]) for k, v in COL.items()}, open(f"{OUT}/colours.json", "w"), indent=1)
