"""Build all I5 review CAD: per-part STEPs (world frame), assembly STEP (named + coloured), print-oriented STLs, Bambu-importable 3MF."""
from common import *
import base as BASE, top as TOP, crown as CROWNM, parts as PARTS, time, json, os
t0 = time.time()
os.makedirs(f"{OUT}/stl", exist_ok=True); os.makedirs(f"{OUT}/step", exist_ok=True)
base = BASE.build(); top, outer = TOP.build(verbose=False); crown = CROWNM.world(CROWNM.build()); ret = PARTS.retainer_world()
print("built %.1f s" % (time.time() - t0))
COL = {"I5_base": ("Matte Charcoal", (0.10, 0.10, 0.11)), "I5_top": ("Matte Ivory White (or Marble)", (0.88, 0.87, 0.82)),
       "I5_crown": ("Basic Sunflower Yellow", (0.99, 0.78, 0.0)), "I5_retainer": ("Matte Charcoal", (0.10, 0.10, 0.11))}
PRINT = {"I5_base": base, "I5_top": top, "I5_crown": crown, "I5_retainer": ret}
for k, s in PRINT.items():
    s.label = k; s.color = Color(*COL[k][1])
    export_step(s, f"{OUT}/step/{k}.step")
refs = PARTS.refs(); RC = []
for k, s in refs.items():
    s.label = k; s.color = Color(0.85, 0.15, 0.1) if "harness_5_wires" in k else Color(0.1, 0.1, 0.1) if "Dupont" in k or "XH5_plug" in k else Color(0.8, 0.7, 0.3) if "pins" in k else Color(0.25, 0.45, 0.25) if "PCB" in k else Color(0.15, 0.15, 0.17) if "display" in k else Color(0.05, 0.05, 0.05) if "12pin" in k or "overmold" in k else Color(0.35, 0.35, 0.38)
    RC.append(s)
prints = Compound(children=list(PRINT.values()), label="printed_parts")
reference = Compound(children=RC, label="reference_bodies_NOT_PRINTED")
asm = Compound(children=[prints, reference], label="PSU_case_I5_assembly")
export_step(asm, f"{OUT}/PSU_case_I5_assembly.step")
print("steps %.1f s" % (time.time() - t0))
# print orientations (justification in REVIEW.md)
def to_print(k, s):
    if k == "I5_crown":   # flange down: local frame flipped so the visible flange face sits on the plate
        return CROWNM.build().rotate(Axis.X, 180).moved(Location((0, 0, CROWN['t'])))
    if k == "I5_retainer": return PARTS.retainer_print()
    if k == "I5_top": return s.moved(Location((0, 0, -(ZS + GAP))))        # upright on its split edge
    return s
for k, s in PRINT.items():
    export_stl(to_print(k, s), f"{OUT}/stl/{k}_print.stl", tolerance=0.01, angular_tolerance=0.08)
    export_stl(s, f"{OUT}/stl/{k}_world.stl", tolerance=0.02, angular_tolerance=0.1)
for s in RC: export_stl(s, f"{OUT}/stl/{s.label}.stl", tolerance=0.05)
export_stl(outer, f"{OUT}/stl/_top_outer_world.stl", tolerance=0.01, angular_tolerance=0.05)
print("stls %.1f s" % (time.time() - t0))
json.dump({k: dict(filament=v[0], rgb=v[1]) for k, v in COL.items()}, open(f"{OUT}/colours.json", "w"), indent=1)
