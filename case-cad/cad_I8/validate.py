"""Validation of the I7 review CAD: STEP re-import validity/closure, interference + clearance matrix, overhangs in print orientation,
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
for k in ("I8_base", "I8_top", "I8_crown", "I8_retainer"):
    s = import_step(f"{OUT}/step/{k}.step"); sol = s.solids()
    P[k] = sol[0]
    R.setdefault("step", {})[k] = dict(solids=len(sol), valid=bool(BRepCheck_Analyzer(sol[0].wrapped).IsValid()), free_edges=free_edges(sol[0]),
                                      volume_cm3=round(sol[0].volume/1000, 3), faces=len(sol[0].faces()),
                                      surface_types=sorted({f.geom_type.name for f in sol[0].faces()}))
asm = import_step(f"{OUT}/PSU_case_I8_assembly.step")
R["assembly"] = dict(solids=len(asm.solids()), labels=[c.label for c in asm.descendants if c.label][:40] if hasattr(asm, "descendants") else None)
print("step checks %.1f" % (time.time() - t0))
import parts as PARTS
REF_ALL = PARTS.refs()
REF = {k: v for k, v in REF_ALL.items() if 'PCB' not in k and 'display' not in k}   # I7: faceted PCBA + full vendor module -> mesh (fcl) checks
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
CL = [("I8_top", "REF_PCB_J1_XY350V_4p"), ("I8_top", "REF_PCB_J2_XY350V_4p"), ("I8_top", "REF_PCB_J3_XY350V_4p"), ("I8_top", "REF_PCB_tall_part"),
      ("I8_top", "REF_PCB_J4_JST_XH5"), ("I8_top", "REF_PCB_RevD2_board"), ("I8_base", "REF_PCB_RevD2_board"), ("I8_top", "REF_USB_male_90deg_overmold"),
      ("I8_top", "REF_USB_flat_cable_51mm"), ("I8_base", "REF_USB_flat_cable_51mm"), ("I8_top", "REF_display_ESP32-S3-LCD-1.28"),
      ("I8_retainer", "REF_USB_male_90deg_overmold"), ("I8_base", "REF_USB_female_overmold"), ("I8_base", "REF_cable_12pin_7mm"), ("I8_top", "REF_cable_12pin_7mm"),
      ("I8_top", "REF_harness_5x_1pin_housing_d1.2"), ("I8_base", "REF_cable_12pin_conductors_x12"), ("I8_top", "REF_cable_12pin_conductors_x12"), ("I8_top", "REF_ferrule_collars_green_x12"), ("I8_top", "REF_harness_5_wires_to_J4"), ("I8_retainer", "REF_harness_5x_1pin_housing_d1.2"),
      ("I8_retainer", "REF_harness_5_wires_to_J4"), ("I8_retainer", "REF_harness_5x_breadboard_pins_0.64sq"), ("I8_retainer", "REF_display_ESP32-S3-LCD-1.28"),
      ("I8_base", "REF_harness_5_wires_to_J4"), ("REF_harness_5_wires_to_J4", "REF_USB_male_90deg_overmold"), ("REF_harness_5_wires_to_J4", "REF_USB_flat_cable_51mm"),
      ("REF_harness_5x_1pin_housing_d1.2", "REF_USB_male_90deg_overmold"), ("REF_harness_5x_1pin_housing_d1.2", "REF_USB_flat_cable_51mm"),
      ("REF_harness_5_wires_to_J4", "REF_PCB_tall_part"), ("REF_harness_5_wires_to_J4", "REF_PCB_RevD2_board"),
      ("REF_USB_male_90deg_overmold", "REF_PCB_RevD2_board"), ("I8_base", "REF_grommet_foot_x4"), ("I8_base", "REF_cable_12pin_7mm_external"), ("I8_top", "REF_cable_12pin_7mm_external"),
      ("I8_base", "REF_HR10A-10P-12S(73)_female_plug"), ("I8_top", "REF_HR10A-10P-12S(73)_female_plug"), ("REF_grommet_foot_x4", "REF_cable_12pin_7mm_external"), ("I8_top", "REF_grommet_foot_x4"),
      ("I8_base", "REF_screw_M2.5x12_shell_x4"), ("I8_top", "REF_screw_M2.5x12_shell_x4"), ("REF_screw_M2.5x12_shell_x4", "REF_grommet_foot_x4"),
      ("REF_screw_M2.5x12_PCB_x4", "REF_PCB_J4_JST_XH5"), ("REF_harness_5_wires_to_J4", "REF_PCB_J4_JST_XH5"), ("REF_display_ESP32-S3-LCD-1.28", "REF_PCB_RevD2_board")]
ALL = dict(P, **REF); clr = {}
CL = [(a, b) for a, b in CL if a in ALL and b in ALL]
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
# outer skin deviation vs I4 SDF (outer skin unchanged in I6) (smooth-min) : sample the B-rep outer tessellation, evaluate the SDF
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
R["retainer_reliefs"] = PARTS.RELIEFS if PARTS.RELIEFS else (PARTS.retainer_local(), PARTS.RELIEFS)[1]
R["housing_radial_gap_to_sleeve_mm"] = round(PARTS.RET['id']/2 - max(np.hypot(x, u) for x in (PARTS.H2['xc'] - PARTS.DUP['x']/2, PARTS.H2['xc'] + PARTS.DUP['x']/2) for u in (PARTS.H2['uc'] - PARTS.DUP['u']/2, PARTS.H2['uc'] + PARTS.DUP['u']/2)), 3)
# I6: retainer vs every vendor back-side part (world), antenna, screws/grommets
rw = PARTS.retainer_world(); vb = [PIPE_PLANE.location * s for s in PARTS.vendor_back().solids()]
dd = sorted((round(rw.distance_to(s), 3), [round(v, 2) for v in (lambda b: (b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z))(PARTS.vendor_back().solids()[i].bounding_box())]) for i, s in enumerate(vb))
ant = PIPE_PLANE.location * mod_box(ANT['x0'], ANT['x1'], ANT['u0'], ANT['u1'], ANT['a0'], ANT['a1']).moved(Location()) if False else mod_box(ANT['x0'], ANT['x1'], ANT['u0'], ANT['u1'], ANT['a0'], ANT['a1'])
R["retainer_vs_vendor_parts"] = dict(min_distance_any_part=dd[0][0], nearest5_module_frame_bbox=dd[:5], antenna=dict(name=ANT['name'], module_frame=ANT,
    world_centre=[round(v, 2) for v in ant.center()], retainer_distance=round(rw.distance_to(ant), 3)),
    window_new_u=[round(RET['win_u0'], 2), round(RET['win_u1'], 2)], window_new_x=f"{'>' if SD > 0 else '<'} {RET['win_x']:+.2f}", window_old=RET_OLD_WIN)
R["HR10A_plug"] = dict(PARTS.HR10_INFO, model="derived from Hirose HR10A-10P-12P.stp + socket insert", A=43.0, dB=14.7, dC=9.5, cable_od=7.0)
R["screws_I6"] = dict(all_8="M2.5 x 12 plastic thread-forming, flat(pan)-head d 4.5 x 1.7 (assumed)",
    shell=dict(counterbore=f"d{SHELL['cb_d']} x {SHELL['cb_depth']} from below", clearance=SHELL['clear_d'], base_floor_under_head=round(SHELL['col_top'] - SHELL['cb_depth'], 2),
               top_pilot=f"d{SHELL['pilot_d']} x {SHELL['pilot_depth']} from z {SHELL['boss_z0']}", engagement=round(SHELL['cb_depth'] + SHELL['L'] - SHELL['boss_z0'], 2),
               engagement_xd=round((SHELL['cb_depth'] + SHELL['L'] - SHELL['boss_z0'])/SCR['d'], 2), tip_to_pilot_bottom=round(SHELL['boss_z0'] + SHELL['pilot_depth'] - SHELL['cb_depth'] - SHELL['L'], 2),
               top_boss_wall=round(SHELL['boss_r'] - SHELL['pilot_d']/2, 2), base_column_wall_low=round(SHELL['col_r_low'] - SHELL['cb_d']/2, 2),
               base_column_wall_ext_inner=round(SHELL['col_r_up'] - SHELL['cb_d']/2, 2), base_column_wall_ext_outer_min=round((RP - T - 0.25) - np.hypot(W/2 - RP - abs(SCREWS[0][0]), D/2 - RP - abs(SCREWS[0][1])) - SHELL['cb_d']/2, 2), screw_xy=[round(abs(SCREWS[0][0]), 2), round(abs(SCREWS[0][1]), 2)]),
    pcb=dict(pilot=f"d{PCBS['pilot_d']} x {PCBS['pilot_depth']} from z {PCB_Z}", engagement=round(PCBS['L'] - PCB['t'], 2), engagement_xd=round((PCBS['L'] - PCB['t'])/SCR['d'], 2),
             tip_to_pilot_bottom=round(PCBS['pilot_depth'] - (PCBS['L'] - PCB['t']), 2), standoff_wall=round(PCBS['standoff_r'] - PCBS['pilot_d']/2, 2)),
    grommet=dict(GROM, protrusion_below_base=GROM['flange_t'], head_recess_below_counterbore_floor=SCR['head_h']))
# I7 additions
import subprocess
subprocess.run([sys.executable, f"{OUT}/clear_I7.py"], capture_output=True)
R["clearance_mesh_fcl_mm"] = json.load(open(f"{OUT}/clearance_mesh.json"))
VA = PARTS.vendor_all(); top_s, ret_s, crn = P["I8_top"], P["I8_retainer"], P["I8_crown"]
def iv(a, b):
    c = a & b; return round(c.volume, 3) if c else 0.0
R["module_real_vendor"] = dict(pcb_x_top_mm3=iv(PIPE_PLANE.location*VA[0], top_s), lcm_x_top_mm3=iv(PIPE_PLANE.location*VA[1], top_s),
    pcb_x_retainer_mm3=iv(PIPE_PLANE.location*VA[0], ret_s), lcm_x_crown_mm3=iv(PIPE_PLANE.location*VA[1], crn),
    I6_values=dict(pcb_x_top_mm3=9.19, lcm_x_top_mm3=4.57), bore_d=2*BORE, retainer_od=RET['od'], pipe_wall=round(RS_O - BORE, 2), outline_clearance=MOD_OUTLINE_CLR)
hs = REF_ALL["REF_harness_5x_1pin_housing_d1.2"].solids()
R["h2_housings"] = dict(d=PARTS.HOUS['d'], l=PARTS.HOUS['l'], min_gap_between=round(min(a.distance_to(b) for a, b in itertools.combinations(hs, 2)), 3),
    pins=[hp for _, hp, _ in SIG], wire_od=PARTS.HWIRE_D)
ap = -4.52
mb = Box(MALE['w'], MALE['u1'] - MALE['u0'], MALE['a1'] - MALE['a0']).moved(Location((0, (MALE['u0'] + MALE['u1'])/2, (MALE['a0'] + MALE['a1'])/2)))
fl = PIPE_PLANE.location * mb.rotate(Axis(Vector(0, 0, ap), Vector(0, 1, 0)), 180)
R["usb_flip_check"] = dict(plug_axis_a=ap, flipped_overmold_a_range=[-7.54, 8.46], flipped_x_top_mm3=iv(fl, top_s), current_x_top_mm3=iv(PIPE_PLANE.location*mb, top_s),
    note="180 deg about the plug axis puts the overmold 8.5 mm in front of the glass plane (through the deck) -> not buildable; I7 keeps the I6 orientation")
import breakout as _BK, tie7b as _T
R["conductors"] = dict(n=12, insulation_od=2*_BK.RW, jacket_end_y=PARTS.JACKET_END, helical_lay_mm=_BK.LAY, ferrule=_BK.FER, entries=PARTS.term_entries(),
    route=json.load(open("_b7/asm_route.json")), note="I7b: relaxed natural breakout (route7b.py); pin starts 0.8 inside the collar (no gap), crimp flats 0.88 A/F")
R["zip_tie_I7b"] = dict(n=1, y=_T.TY, trench_walls_y=[CRADLE['y0'] + 0.3, CRADLE['y1']], slot_z=_T.SLOT_Z, slot_w=_T.TIE['slot_w'], head_x=_T.HEAD_X,
    pocket_floor_z=_T.TIE['z0'], floor_left_mm=_T.TIE['z0'], note="one central tie (fits at the exact middle); slots at wall mid-height")
json.dump(R, open(f"{OUT}/validation.json", "w"), indent=1)
print(json.dumps(R, indent=1))
