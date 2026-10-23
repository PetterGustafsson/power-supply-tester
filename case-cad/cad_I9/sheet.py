"""Review sheet (A3 landscape PNG + PDF): ortho views, key dimensions, sections (display+mound, USB clamp, crown detail), parts list, open items."""
import sys; sys.argv = ['x']
from common import *
import trimesh, json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.image as mpimg
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import polygonize, unary_union
VAL = json.load(open(f"{OUT}/validation.json"))
BODIES = [("I9_base", "stl/I9_base_world.stl", "#2a2a2c"), ("I9_top", "stl/I9_top_world.stl", "#d9d3c3"), ("I9_crown", "stl/I9_crown_world.stl", "#ff6a13"),
          ("I9_retainer", "stl/I9_retainer_world.stl", "#555558"), ("display", "stl/render/display_PCB.stl", "#3b4a6b"), ("LCM", "stl/render/display_LCM.stl", "#20283a"),
          ("male", "stl/REF_USB_male_90deg_overmold.stl", "#7a3b3b"), ("flat", "stl/REF_USB_flat_cable_51mm.stl", "#9b6b3b"),
          ("female", "stl/REF_USB_female_overmold.stl", "#7a3b3b"), ("pcb", "stl/REF_PCB_RevD2_board.stl", "#3f7a3f"),
          ("J1", "stl/REF_PCB_J1_XY350V_4p.stl", "#4f9a5f"), ("grommet", "stl/REF_grommet_foot_x4.stl", "#151515"), ("screw", "stl/REF_screw_M2.5x12_shell_x4.stl", "#9a9da2"), ("cable", "stl/REF_cable_12pin_7mm.stl", "#111111")]
MESH = {k: trimesh.load(f"{OUT}/{f}") for k, f, c in BODIES}
def section(mesh, origin, normal, proj):
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    if s is None: return None
    lines = []
    for d in s.discrete:
        p = proj(d)
        if len(p) > 2: lines.append(p)
    polys = list(polygonize([tuple(map(tuple, l)) for l in lines]))
    if not polys: return None
    res = None
    for p in polys:
        try: res = p if res is None else res.symmetric_difference(p)
        except Exception:          # I6: the display ref is a compound of overlapping vendor solids -> clean + skip bad loops
            try: res = res.buffer(0).symmetric_difference(p.buffer(0))
            except Exception: pass
    return res
def draw(ax, geom, col, alpha=1.0, hatch=None):
    if geom is None or geom.is_empty: return
    gs = geom.geoms if hasattr(geom, "geoms") else [geom]
    for g in gs:
        if not isinstance(g, Polygon): continue
        ext = np.array(g.exterior.coords); ax.fill(ext[:,0], ext[:,1], color=col, alpha=alpha, lw=0.3, ec="k", hatch=hatch)
        for h in g.interiors:
            hh = np.array(h.coords); ax.fill(hh[:,0], hh[:,1], color="white", lw=0.3, ec="k")
def sec_plot(ax, origin, normal, proj, xlim, ylim, title):
    for k, f, c in BODIES:
        g = section(MESH[k], origin, normal, proj); draw(ax, g, c, alpha=1.0 if k.startswith("I7") else 0.75)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.set_title(title, fontsize=9, loc="left"); ax.grid(alpha=0.25, lw=0.4)
    ax.tick_params(labelsize=6)
fig = plt.figure(figsize=(16.54, 11.69), dpi=150)
fig.suptitle("PSU tester case - concept I9 (one straight 40 deg pipe, rounded root, no trailing tunnel; I8 ring ribs) - review CAD (exact B-rep)   |   2026-10-21   |   all dims mm", fontsize=13, x=0.01, ha="left", y=0.99)
# ---- ortho + iso images
imgs = [("v_iso.png", "Isometric"), ("v_front.png", "Front (user side)"), ("v_side.png", "Side (from right)"), ("v_rear.png", "Rear (USB-C)"), ("v_top.png", "Top")]
pos = [(0.005, 0.66, 0.2, 0.3), (0.205, 0.66, 0.2, 0.3), (0.405, 0.66, 0.2, 0.3), (0.605, 0.66, 0.2, 0.3), (0.805, 0.66, 0.19, 0.3)]
for (f, t), p in zip(imgs, pos):
    ax = fig.add_axes(p); im = mpimg.imread(f"{OUT}/review/{f}"); ax.imshow(im[60:-60, 60:-60]); ax.set_axis_off(); ax.set_title(t, fontsize=9)
# ortho scale 0.14 m over 1000 px -> 7.14 px/mm, centre (0, 0, 40 mm)
def dimline(ax, p0, p1, txt, off=(0, 0)):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<->", lw=0.7, color="#c00")); ax.text((p0[0]+p1[0])/2 + off[0], (p0[1]+p1[1])/2 + off[1], txt, fontsize=7, color="#c00", ha="center")
# ---- section A: x = 0 (display + mound + USB clamp + 12-pin cradle)
ax = fig.add_axes((0.03, 0.27, 0.42, 0.37))
projA = lambda d: d[:, [1, 2]]
sec_plot(ax, (0, 0, 0), (1, 0, 0), projA, (-60, 60), (-3, 80), "Section A-A  (x = 0): display, pipe, tunnel mound, USB-C clamp, 12-pin cradle")
dimline(ax, (-52, 0), (-52, HI), "48 deck", off=(-3.5, 0)); dimline(ax, (-50, 0), (-50, ZS), "6", off=(-2, 0))
ax.axhline(ZS + GAP/2, color="#888", lw=0.5, ls="--"); ax.text(52, ZS + 1, "split 6.0 / 6.5", fontsize=6)
gz = G; ax.plot([gz[1], gz[1] - 30*AF[1]], [gz[2], gz[2] - 30*AF[2]], color="#06c", lw=0.6, ls="-.")
ax.text(gz[1] - 8, gz[2] - 30, "axis 40 deg from vertical\nglass centre y %.1f z %.2f" % (G[1], G[2]), fontsize=6, color="#06c")
ax.text(-58, 72, "pipe OD 40.7 / bore 37.0 / wall 1.85 (I7)\ncrown ID 32.4 OD 40.7 t 2.5 (spigot 1.5)\n80 / 20 above / below deck (module height)", fontsize=6)
ax.text(30, ZF + 5, "USB-C clamp\nsplit z %.2f" % ZT, fontsize=6); ax.text(-46, 12, "12-pin 7 mm\ncradle + clamp", fontsize=6)
# ---- section B: y = 40 (USB clamp, crush rib)
ax = fig.add_axes((0.46, 0.27, 0.2, 0.37))
projB = lambda d: d[:, [0, 2]]
sec_plot(ax, (0, 40, 0), (0, 1, 0), projB, (-22, 22), (-2, 50), "Section B-B (y = 40): USB-C clamp")
ax.text(-21, 46, "tongue (base) + notch (top), 0.5 gap\nsocket pocket 12.9 x 6.9 (+0.2 / 0.1)\ncrush rib 0.3 into overmold (y 33, 40)", fontsize=6)
dimline(ax, (-FW, 22), (FW, 22), "12.9")
# ---- section C: crown detail (x = 0, zoom on the upper crown edge)
ax = fig.add_axes((0.69, 0.27, 0.15, 0.37))
top_pt = G + RS_O*UF
sec_plot(ax, (0, 0, 0), (1, 0, 0), projA, (top_pt[1] - 5, top_pt[1] + 4), (top_pt[2] - 6, top_pt[2] + 4), "Detail C: crown press fit")
ax.text(top_pt[1] - 4.8, top_pt[2] + 3.2, "spigot OD 37.10 in bore 37.00\n= 0.10 interference (1.85 wall)\nlead-in 0.4 x 45, flange 1.0", fontsize=6)
# ---- text blocks
st = VAL["step"]; cl = VAL["min_distance_mm"]; inter = VAL["interference_mm3"]; dev = VAL["outer_skin_deviation_vs_SDF_mm"]; ov = VAL["overhangs_print_orientation"]
PTOP = ZG + PIPE_END*math.cos(ph) + RS_O*math.sin(ph)
cm = VAL["clearance_mesh_fcl_mm"]; mv = VAL["module_real_vendor"]; cd = VAL["conductors"]; hh = VAL["h2_housings"]
txt1 = ("KEY DIMENSIONS (I7 changes marked *)\n"
 f"Footprint 108 x 96, R12 plan corners; deck z 48 (R4 edge); pipe top z {PTOP:.1f}\n"
 f"Base 0-6 (black band) + 0.5 shadow gap; top from 6.5; wall 2.4; floor 2.4\n"
 f"*Bore d{2*BORE:.2f} (was 36.70), pipe OD 40.7 -> wall {RS_O - BORE:.2f}; module seat/tab cut = real PCB+LCM outline + 0.2\n"
 f"*Display = Waveshare vendor STEP: PCB OD 36.5 (+0.13 u offset), 39.5 tall, trapezoid USB tab 12.8 at the bottom; LCM 35.6; 40 deg tilt, glass centre (0, -10, 59.88)\n"
 f"Crown ID 32.4 / OD 40.7, spigot into the bore; *retainer sleeve OD {RET['od']:.2f} / ID {RET['id']}\n"
 f"*PCB = Rev D2 KiCad model (tester-d2.wrl) 86x62x1.6 on 4 standoffs d6 (z 14), pilot d2.0 x 12; holes (+-40, PCB_Y+-28) match\n"
 f"4x shell screws from below at (+/-{abs(SCREWS[0][0]):.2f}, +/-{abs(SCREWS[0][1]):.2f}): d3.5 thru, c'bore d5.5 x 8.0 (grommet), floor 2.5\n"
 f"Top bosses d7.2 from z 11.0, pilot d2.0 x 10.5; deck solid (no vents)\n"
 f"*I7b: 12-pin cradle 7.3 wide, ONE tie at the trench middle y -18.65: 3.0 x 1.6 wall slots at mid-height (z 4.4-6.0),\n   inner grooves + blind bed pocket (floor 1.2 left), blind head pocket 6.0 x 5.8 right of +x wall; underside flat\n"
 f"*Jacket to y {cd['jacket_end_y']}; 12 conductors d{cd['insulation_od']} fan to J1-J3 (U-arc under the board at z 10.95, R3.5 up in the front zone)\n"
 f"USB-C socket centre z {ZF:.2f}, tongue 16.9 wide, R6 flares")
txt2 = ("PARTS LIST\n"
 "I9_base      Bambu PLA Matte Charcoal      prints flat, no supports\n"
 "I9_top       PLA Matte Ivory White*        upright on split edge, tree supports inside only\n"
 "I9_crown     PLA Basic Orange* (#FF6A13)   flange down, no supports\n"
 "I9_retainer  PLA Matte Charcoal (hidden)   sleeve, flange down, no supports\n"
 "8x M2.5 x 12 plastic thread-forming flat(pan)-head screw (4 shell + 4 PCB); 4x rubber grommet foot (hip 5.5 x 8 ASSUMED)\n"
 "1x Hirose HR10A-10P-12S(73) female plug on 7 mm 12-core cable (12 x 0.34 mm2 ASSUMED)\n"
 "12x insulated ferrule, 8.0 mm (0.314\") pin d1.1, green collar d2.6 (type/size to confirm vs conductor gauge)\n"
 "1x lead JST-XHP-5 (J4) -> 5 x 28 AWG -> 5 single round 1-pin housings d1.2 x 12 on H2.1/.3/.4/.5/.7 (0.64 sq pins)\n"
 "1x zip tie 2.5 mm at the trench middle (I7b; through both wall slots, under the jacket); no heat-set inserts\n"
 "Waveshare ESP32-S3-LCD-1.28; YANBORONSN USB4 90 deg ext. 51 mm\n"
 "* colour names from the Bambu catalogue - verify spool names")
txt3 = ("VALIDATION\n"
 f"All 4 print solids valid, closed after STEP re-import; vol cm3 base {st['I9_base']['volume_cm3']}, top {st['I9_top']['volume_cm3']}, crown {st['I9_crown']['volume_cm3']}, retainer {st['I9_retainer']['volume_cm3']}\n"
 f"Intended: top x crown {inter['I9_top x I9_crown']}, top x retainer {inter['I9_top x I9_retainer']} (press fits), top x female {inter['I9_top x REF_USB_female_overmold']} (crush ribs), 12-pin clamp\n"
 f"*Real module: PCB x top {mv['pcb_x_top_mm3']} (I6 {mv['I6_values']['pcb_x_top_mm3']}), LCM x top {mv['lcm_x_top_mm3']} (I6 {mv['I6_values']['lcm_x_top_mm3']}) mm3; gaps PCB-top {cm.get('display_PCB - I9_top_world')}, LCM-top {cm.get('display_LCM - I9_top_world')}\n"
 f"*Real PCBA (fcl mesh): top-board {cm['I9_top_world - REF_PCB_RevD2_board']}, top-components >= {min(v for k, v in cm.items() if k.startswith('I9_top_world - REF_PCB_') and 'board' not in k)}, base-SMD {cm['I9_base_world - REF_PCB_SMD_parts']}\n"
 f"*Conductors: to THT terminal pins/bodies {min(cm['REF_cable_12pin_conductors_x12 - REF_PCB_J%d_XY350V_4p' % i] for i in (1, 2, 3))}, base {cm['REF_cable_12pin_conductors_x12 - I9_base_world']}, top {cm['REF_cable_12pin_conductors_x12 - I9_top_world']}, board {cm['REF_cable_12pin_conductors_x12 - REF_PCB_RevD2_board']}; collars-board {cm['REF_ferrule_collars_green_x12 - REF_PCB_RevD2_board']}\n"
 f"*H2 housings d{hh['d']}: gap between {hh['min_gap_between']}, to sleeve {cm['REF_harness_5x_1pin_housing_d1.2 - I9_retainer_world']}, to top {cm['REF_harness_5x_1pin_housing_d1.2 - I9_top_world']}; leads-top {cm['REF_harness_5_wires_to_J4 - I9_top_world']}\n"
 f"USB: top-male plug {cl.get('I9_top - REF_USB_male_90deg_overmold')}, top-flat {cl.get('I9_top - REF_USB_flat_cable_51mm')}, base-flat {cl.get('I9_base - REF_USB_flat_cable_51mm')}; flip check: 180 deg -> {VAL['usb_flip_check']['flipped_x_top_mm3']} mm3 into the top (not buildable)\n"
 f"Overhangs: base support-free (tie slots = 3.0 bridges); crown/retainer none; top: tree supports inside only")
txt4 = ("OPEN ITEMS\n"
 "1. USB 'flip': 180 deg about the plug axis puts the 90 deg overmold 8.5 mm in front of the glass (through the deck) -> kept as I6; confirm what 'flip' means\n"
 "2. Conductor -> terminal mapping, gauge (0.34 mm2 assumed, d1.4) and ferrule type (0.314\" pin, green collar) to confirm\n"
 "3. H2 pin numbering (pin 1 at +u, odd pins outer row) unverified; d1.2 housings leave 0.07 between neighbours at 1.27 pitch; 0.64 pins in a 1.27 socket: check\n"
 "4. Module: Petter's 36.4 vs Waveshare/STEP 36.5; art 31.3 vs LCD AA 32.4 - crown ID 32.4 kept; bore 37.0 gives 0.11 at the PCB top point\n"
 "5. USB overmold dims are ESTIMATES - caliper, then tune POCKET\n"
 "6. Crown + retainer press fit 0.10 dia interference: test print, tune 0.10-0.15\n"
 "7. Grommet geometry (hip 8.0) assumed; colour/filament names unverified\n"
 "8. Faceted PCBA/vendor bodies make the assembly STEP large (~160 MB); per-part STEPs are small exact B-rep")
import textwrap
def wrap(t, n): return "\n".join("\n   ".join(textwrap.wrap(l, n)) if len(l) > n else l for l in t.split("\n"))
for (x, t, n) in ((0.005, txt1, 70), (0.25, txt2, 68), (0.50, txt3, 68), (0.75, txt4, 70)):
    fig.text(x, 0.235, wrap(t, n), fontsize=6.4, va="top", family="monospace")
leg = fig.add_axes((0.86, 0.30, 0.13, 0.3)); leg.set_axis_off()
for i, (k, f, c) in enumerate(BODIES):
    leg.add_patch(plt.Rectangle((0, 1 - (i+1)*0.085), 0.12, 0.06, color=c)); leg.text(0.16, 1 - (i+1)*0.085 + 0.01, k + ("" if k.startswith("I7") else "  (ref)"), fontsize=7)
leg.set_xlim(0, 1); leg.set_ylim(0, 1); leg.set_title("Section colours", fontsize=8, loc="left")
fig.savefig(f"{OUT}/review/PSU_case_I9_review.png", dpi=150); fig.savefig(f"{OUT}/review/PSU_case_I9_review.pdf")
print("ok")
