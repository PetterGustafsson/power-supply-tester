"""Section meshes for the I7 renders: (1) x = 0 half-cut of the printed parts (keep x > 0) for the USB cutaway, (2) module-plane cut (a = -2.6,
keep the front a > -2.6) of top/crown/retainer + the module parts for the module-bay view."""
from common import *
import parts as PARTS, os
O = f"{OUT}/stl/render"; os.makedirs(O, exist_ok=True)
P = {k: import_step(f"{OUT}/step/{k}.step").solids()[0] for k in ("I8_base", "I8_top", "I8_crown", "I8_retainer")}
half = box((0.0, -200, -50), (200, 200, 200))
for k, s in P.items():
    export_stl(s & half, f"{O}/{k}_cutx0.stl", tolerance=0.01, angular_tolerance=0.08)
front = PIPE_PLANE.location * Box(200, 200, 100, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -2.6)))
for k in ("I8_top", "I8_crown", "I8_retainer"):
    c = P[k] & front
    if c: export_stl(c, f"{O}/{k}_cutmod.stl", tolerance=0.01, angular_tolerance=0.08)
VA = PARTS.vendor_all()
export_stl(PIPE_PLANE.location * (VA[0] & Box(200, 200, 100, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -2.6)))), f"{O}/display_PCB_cutmod.stl", tolerance=0.02)
print("ok")
