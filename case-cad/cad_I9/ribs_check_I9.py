"""I8/I9: clearances of the ring ribs + collar (hanging part, below the deck underside) to the internals, plus the module/retainer loading sweep.
Writes ribs_check_I9.json. Reference meshes: this folder's stl/ (rebuilt by build_all.py)."""
import sys, json, math, numpy as np, trimesh, fcl
sys.path.insert(0, '.')
import top
from common import *
def F(m):
    b = fcl.BVHModel(); b.beginModel(len(m.vertices), len(m.faces)); b.addSubModel(m.vertices, m.faces); b.endModel(); return fcl.CollisionObject(b)
def dist(A, B):
    q = fcl.DistanceRequest(); r = fcl.DistanceResult(); return round(float(fcl.distance(A, B, q, r)), 2)
info = {}; r = top.ring_ribs(info); export_stl(r, '_q/ribs_I8.stl', tolerance=0.02)
m = trimesh.load('_q/ribs_I8.stl'); hang = trimesh.intersections.slice_mesh_plane(m, [0, 0, -1], [0, 0, HI - T - 0.1], cap=True); H = F(hang)
v = hang.vertices - G; rad = np.linalg.norm(v - np.outer(v @ AF, AF), axis=1)
out = dict(design=dict(RIB=top.RIB, **info), ribs_and_collar_volume_cm3=round(r.volume/1000, 3), hanging_zmin=round(float(hang.bounds[0][2]), 2),
           hanging_min_radius_to_pipe_axis=round(float(rad.min()), 2), bore_r=BORE, retainer_od=RET['od'] if 'RET' in globals() and isinstance(RET, dict) and 'od' in RET else 37.1)
cl = {}
for k in ("REF_display_ESP32-S3-LCD-1.28", "I9_retainer_world", "REF_USB_male_90deg_overmold", "REF_USB_male_plug_tip", "REF_USB_flat_cable_51mm", "REF_USB_female_overmold",
          "REF_harness_5_wires_to_J4", "REF_harness_5x_1pin_housing_d1.2", "REF_harness_5x_breadboard_pins_0.64sq", "REF_J4_XH5_plug", "REF_PCB_J4_JST_XH5",
          "REF_PCB_SMD_parts", "REF_PCB_tall_part", "REF_PCB_RevD2_board", "REF_PCB_J1_XY350V_4p", "REF_PCB_J2_XY350V_4p", "REF_PCB_J3_XY350V_4p", "REF_cable_12pin_conductors_x12", "REF_zip_tie_2.5mm_centre"):
    cl[k] = dist(H, F(trimesh.load(f'stl/{k}.stl')))
out['clearance_hanging_ribs_mm'] = cl
sw = {}
for k in ("REF_display_ESP32-S3-LCD-1.28", "I9_retainer_world"):
    b = trimesh.load(f'stl/{k}.stl'); best = (1e9, 0)
    for s in np.arange(0.0, 45.1, 1.0):
        bb = b.copy(); bb.apply_translation(-s*AF); best = min(best, (dist(H, F(bb)), float(s)))
    sw[k] = dict(min_mm=best[0], at_withdrawal_mm=best[1])
out['loading_sweep_along_pipe_axis_0_45mm'] = sw
json.dump(out, open('ribs_check_I9.json', 'w'), indent=1); print(json.dumps(out, indent=1))
