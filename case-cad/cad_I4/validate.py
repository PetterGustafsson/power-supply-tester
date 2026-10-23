"""Validation of the I4 review CAD: STEP re-import validity/closure, interference + clearance matrix, overhangs in print orientation,
B-rep vs SDF deviation of the blended outer skin. Writes validation.json + prints a summary."""
from common import *
import json, trimesh, itertools, time
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepCheck import BRepCheck_Analyzer
R = {}
t0 = time.time()
def free_edges(shape):
    fb = ShapeAnalysis_FreeBounds(shape.wrapped, 1e-4, False, False)
    from OCP.TopExp import TopExp_Explorer; from OCP.TopAbs import TopAbs_EDGE
    n = 0; ex = TopExp_Explorer(fb.GetOpenWires(), TopAbs_EDGE)
    while ex.More(): n += 1; ex.Next()
    return n
P = {}
for k in ("I4_base", "I4_top", "I4_crown", "I4_retainer"):
    s = import_step(f"{OUT}/step/{k}.step"); sol = s.solids()
    P[k] = sol[0]
    R.setdefault("step", {})[k] = dict(solids=len(sol), valid=bool(BRepCheck_Analyzer(sol[0].wrapped).IsValid()), free_edges=free_edges(sol[0]),
                                      volume_cm3=round(sol[0].volume/1000, 3), faces=len(sol[0].faces()),
                                      surface_types=sorted({f.geom_type.name for f in sol[0].faces()}))
asm = import_step(f"{OUT}/PSU_case_I4_assembly.step")
R["assembly"] = dict(solids=len(asm.solids()), labels=[c.label for c in asm.descendants if c.label][:40] if hasattr(asm, "descendants") else None)
print("step checks %.1f" % (time.time() - t0))
import parts as PARTS
REF = PARTS.refs()
def common_vol(a, b):
    try:
        bb1, bb2 = a.bounding_box(), b.bounding_box()
        if (bb1.min.X > bb2.max.X or bb2.min.X > bb1.max.X or bb1.min.Y > bb2.max.Y or bb2.min.Y > bb1.max.Y or bb1.min.Z > bb2.max.Z or bb2.min.Z > bb1.max.Z): return 0.0
        c = a & b; return c.volume if c is not None else 0.0
    except Exception as e: return float('nan')
inter = {}
for (ka, a), (kb, b) in itertools.combinations(P.items(), 2):
    inter[f"{ka} x {kb}"] = round(common_vol(a, b), 3)
for ka, a in P.items():
    for kb, b in REF.items():
        v = common_vol(a, b)
        if v > 1e-4: inter[f"{ka} x {kb}"] = round(v, 3)
for (ka, a), (kb, b) in itertools.combinations(REF.items(), 2):
    if "PCB" in ka and "PCB" in kb: continue
    v = common_vol(a, b)
    if v > 1e-4: inter[f"{ka} x {kb}"] = round(v, 3)
R["interference_mm3"] = inter
print("interference %.1f" % (time.time() - t0))
CL = [("I4_top", "REF_PCB_J1_XY350V_4p"), ("I4_top", "REF_PCB_J2_XY350V_4p"), ("I4_top", "REF_PCB_J3_XY350V_4p"), ("I4_top", "REF_PCB_tall_part"),
      ("I4_top", "REF_PCB_J4_JST_XH5"), ("I4_top", "REF_PCB_RevD2_board"), ("I4_base", "REF_PCB_RevD2_board"), ("I4_top", "REF_USB_male_90deg_overmold"),
      ("I4_top", "REF_USB_flat_cable_51mm"), ("I4_base", "REF_USB_flat_cable_51mm"), ("I4_top", "REF_display_ESP32-S3-LCD-1.28"),
      ("I4_retainer", "REF_USB_male_90deg_overmold"), ("I4_base", "REF_USB_female_overmold"), ("I4_base", "REF_cable_12pin_7mm"), ("I4_top", "REF_cable_12pin_7mm"),
      ("REF_USB_male_90deg_overmold", "REF_PCB_RevD2_board"), ("REF_display_ESP32-S3-LCD-1.28", "REF_PCB_RevD2_board")]
ALL = dict(P, **REF); clr = {}
for a, b in CL:
    try: clr[f"{a} - {b}"] = round(ALL[a].distance_to(ALL[b]), 2)
    except Exception as e: clr[f"{a} - {b}"] = str(e)[:60]
for (ka, a), (kb, b) in itertools.combinations(P.items(), 2):
    try: clr[f"{ka} - {kb}"] = round(a.distance_to(b), 3)
    except Exception: pass
R["min_distance_mm"] = clr
print("clearances %.1f" % (time.time() - t0))
# overhangs (> 45 deg from vertical, i.e. normal.z < -0.7071), excluding the bed layer and horizontal "bridge" faces listed separately
ov = {}
for k in P:
    m = trimesh.load(f"{OUT}/stl/{k}_print.stl"); z0 = m.bounds[0, 2]
    nz = m.face_normals[:, 2]; zc = m.triangles_center[:, 2]
    off_bed = zc > z0 + 0.05
    steep = off_bed & (nz < -0.7071) & (nz > -0.999)
    flat = off_bed & (nz <= -0.999)
    groups = []
    sub = m.submesh([np.where(steep | flat)[0]], append=True) if (steep | flat).any() else None
    if sub is not None:
        for g in sub.split(only_watertight=False):
            if g.area > 2.0: groups.append(dict(area_mm2=round(g.area, 1), bbox=g.bounds.round(1).tolist()))
    groups.sort(key=lambda g: -g["area_mm2"])
    ov[k] = dict(steep_overhang_mm2=round(m.area_faces[steep].sum(), 1), horizontal_downfacing_mm2=round(m.area_faces[flat].sum(), 1), regions=groups[:12])
R["overhangs_print_orientation"] = ov
print("overhangs %.1f" % (time.time() - t0))
# outer skin deviation vs I4 SDF (smooth-min) : sample the B-rep outer tessellation, evaluate the SDF
import importlib.util, sys as _s
_s.argv = ["x"]; import i4_sdf as S3
m = trimesh.load(f"{OUT}/stl/_top_outer_world.stl")
pts, _ = trimesh.sample.sample_surface_even(m, 60000)
d, *_ = S3.core.top_outer(pts)
ad = np.abs(d); hi = pts[:, 2] > HI + 0.3
iw = np.argmax(ad)
R["outer_skin_deviation_vs_SDF_mm"] = dict(all_max=round(float(ad.max()), 2), all_p95=round(float(np.percentile(ad, 95)), 2), all_mean=round(float(ad.mean()), 3),
    above_deck_max=round(float(ad[hi].max()), 2), above_deck_p95=round(float(np.percentile(ad[hi], 95)), 2), worst_point=pts[iw].round(1).tolist())
print("deviation %.1f" % (time.time() - t0))
import top as TOPM, top_outer as TO
outer = TO.build(verbose=False); skin = Compound([f for f in outer.faces() if f.center().Z > HI - 6])   # top skin only (deck, blends, pipe, crown seat)
R["skins_mm"] = dict(tab_channel_to_outer=round(skin.distance_to(TOPM.tab_channel()), 2), plug_window_to_outer=round(skin.distance_to(TOPM.plug_window()), 2),
                     pipe_wall=round(RS_O - BORE, 2))
json.dump(R, open(f"{OUT}/validation.json", "w"), indent=1)
print(json.dumps(R, indent=1))
