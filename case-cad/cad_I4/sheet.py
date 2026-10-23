"""Review sheet (A3 landscape PNG + PDF): ortho views, key dimensions, sections (display+mound, USB clamp, crown detail), parts list, open items."""
import sys; sys.argv = ['x']
from common import *
import trimesh, json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.image as mpimg
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import polygonize, unary_union
VAL = json.load(open(f"{OUT}/validation.json"))
BODIES = [("I4_base", "stl/I4_base_world.stl", "#2a2a2c"), ("I4_top", "stl/I4_top_world.stl", "#d9d3c3"), ("I4_crown", "stl/I4_crown_world.stl", "#f2c200"),
          ("I4_retainer", "stl/I4_retainer_world.stl", "#555558"), ("display", "stl/REF_display_ESP32-S3-LCD-1.28.stl", "#3b4a6b"),
          ("male", "stl/REF_USB_male_90deg_overmold.stl", "#7a3b3b"), ("flat", "stl/REF_USB_flat_cable_51mm.stl", "#9b6b3b"),
          ("female", "stl/REF_USB_female_overmold.stl", "#7a3b3b"), ("pcb", "stl/REF_PCB_RevD2_board.stl", "#3f7a3f"),
          ("J1", "stl/REF_PCB_J1_XY350V_4p.stl", "#4f9a5f"), ("cable", "stl/REF_cable_12pin_7mm.stl", "#111111")]
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
    for p in polys: res = p if res is None else res.symmetric_difference(p)
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
        g = section(MESH[k], origin, normal, proj); draw(ax, g, c, alpha=1.0 if k.startswith("I4") else 0.75)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.set_title(title, fontsize=9, loc="left"); ax.grid(alpha=0.25, lw=0.4)
    ax.tick_params(labelsize=6)
fig = plt.figure(figsize=(16.54, 11.69), dpi=150)
fig.suptitle("PSU tester case - concept I4 - review CAD (exact B-rep)   |   2026-10-20   |   all dims mm", fontsize=13, x=0.01, ha="left", y=0.99)
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
ax.text(-58, 72, "pipe OD 40.7 / bore 36.7 / wall 2.0 (5 perimeters)\ncrown ID 32.4 OD 40.7 t 2.5 (spigot 1.5)\n80 / 20 above / below deck (module height)", fontsize=6)
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
ax.text(top_pt[1] - 4.8, top_pt[2] + 3.2, "spigot OD 36.80 in bore 36.70\n= 0.10 interference (0.15 safe, 2.0 wall)\nlead-in 0.4 x 45, flange 1.0", fontsize=6)
# ---- text blocks
st = VAL["step"]; cl = VAL["min_distance_mm"]; inter = VAL["interference_mm3"]; dev = VAL["outer_skin_deviation_vs_SDF_mm"]; ov = VAL["overhangs_print_orientation"]
PTOP = ZG + PIPE_END*math.cos(ph) + RS_O*math.sin(ph)
txt1 = ("KEY DIMENSIONS\n"
 f"Footprint 108 x 96, R12 plan corners; deck z 48 (R4 edge); pipe top z {PTOP:.1f}\n"
 f"Base 0-6 (black band) + 0.5 shadow gap; top from 6.5\n"
 f"Wall 2.4; floor 2.4; pipe wall 2.0 = 5 x 0.4 perimeters, solid (bore 36.7, OD 40.7)\n"
 f"Display: 36.4 round, art 31.3, 40 deg tilt, glass centre (0, -10, 59.88)\n"
 f"Crown ID 32.4 / OD 40.7 (2 in, flush with pipe), art margin 0.55/side\n"
 f"Crown sinks into a 0.2-gap seat at the front (pipe end 0.05 below deck)\n"
 f"PCB Rev D2 86x62x1.6 on 4 standoffs (z 14), M2.5 heat-set holes 3.6\n"
 f"4x M3 from below: dia 3.4 thru, c'bore 6.4x3.2, foot recess 10x0.8\n"
 f"Top bosses dia 7.2, M3 heat-set hole 4.0 x 7\n"
 f"12-pin cradle 7.3 wide, ridged bed (0.35 ridges @2.5), ties at y -8 / +4\n"
 f"USB-C socket centre z {ZF:.2f}, tongue 16.9 wide, R6 flares\n"
 f"Ceiling ribs 1.6 x 6 at x +-21/+-39, y -30/-12/6/24")
txt2 = ("PARTS LIST\n"
 "I4_base      Bambu PLA Matte Charcoal      prints flat, no supports\n"
 "I4_top       PLA Matte Ivory White*        upright on split edge, tree supports inside only\n"
 "I4_crown     PLA Basic Sunflower Yellow*   flange down, no supports\n"
 "I4_retainer  PLA Matte Charcoal (hidden)   flat, no supports\n"
 "4x M3 x 40 socket/button head screw (from below, into top bosses; length TBC)\n"
 "4x M3 heat-set insert (OD ~4.0-4.2, L 5.7) in top bosses\n"
 "4x M2.5 heat-set insert (hole 3.6) in base standoffs + 4x M2.5 x 6 screws\n"
 "4x 10 mm rubber/cork feet; 2x zip tie 2.5 mm; glue (optional backup)\n"
 "Waveshare ESP32-S3-LCD-1.28; YANBORONSN USB4 90 deg ext. 51 mm\n"
 "Pipe wall 2.0 = 5 perimeters x 0.4 (0.4 nozzle): set walls >= 5, solid, no infill gaps\n"
 "* colour names from the Bambu catalogue - verify spool names")
txt3 = ("VALIDATION\n"
 f"All 4 print solids valid, closed (0 free edges) after STEP re-import\n"
 f"Volumes cm3: base {st['I4_base']['volume_cm3']}, top {st['I4_top']['volume_cm3']}, crown {st['I4_crown']['volume_cm3']}, retainer {st['I4_retainer']['volume_cm3']}\n"
 f"Base x top 0 mm3 (gap 0.25 lip, 0.5 shadow gap); intended: top x crown {inter['I4_top x I4_crown']} (press fit),\n"
 f"   top x retainer {inter['I4_top x I4_retainer']} (press fit), top x female {inter['I4_top x REF_USB_female_overmold']} (crush ribs), top x 12-pin {inter['I4_top x REF_cable_12pin_7mm']} (0.3 clamp)\n"
 f"Min clearances: top-PCB {cl['I4_top - REF_PCB_RevD2_board']}, top-terminals {min(cl['I4_top - REF_PCB_J%d_XY350V_4p' % i] for i in (1,2,3))}, top-male plug {cl['I4_top - REF_USB_male_90deg_overmold']}, top-flat cable {cl['I4_top - REF_USB_flat_cable_51mm']}, base-flat cable {cl['I4_base - REF_USB_flat_cable_51mm']}, top-display {cl['I4_top - REF_display_ESP32-S3-LCD-1.28']}\n"
 f"Skin over tab channel {VAL['skins_mm']['tab_channel_to_outer']}, over plug window {VAL['skins_mm']['plug_window_to_outer']}\n"
 f"Outer skin vs I4 SDF: mean {dev['all_mean']}, p95 {dev['all_p95']}, max {dev['all_max']} (B-rep fillets tighter than smooth-min in the pipe/tunnel/deck valleys)\n"
 f"Overhangs: base support-free (45 deg keel, 4.8 tie-slot bridges); crown/retainer none; top: ceiling cells bridge <=18 between ribs,\n"
 f"   rib bottoms + tunnel crest inside + bore-side ceiling need tree supports (all hidden, removable through the open bottom)")
txt4 = ("OPEN ITEMS\n"
 "1. USB extender overmold dims are ESTIMATES (female 12.5x6.5x20, male 12x9x16) - caliper, then tune POCKET\n"
 "2. USB tab position/size taken from the old display model (13.3 wide, to r 21.1) - verify on the real module\n"
 "3. 51 mm free cable length assumed between the overmolds (route 46.9 + bow)\n"
 "4. Rev D2 component heights under the USB keel (y 25.6-45, |x|<15) - confirm nothing > 0.5 below the 45 deg line\n"
 "5. Ceiling ribs: check supports in Bambu Studio; consider pitched ribs if supports are a pain\n"
 "6. Colour/filament names unverified\n"
 "7. Crown + retainer press fit 0.10 dia interference: test print, tune 0.10-0.15 (PF['interf'])\n"
 "8. Module loads from INSIDE (tab wider than bore); retainer ring holds it - check 7.9 module depth\n"
 "9. Front: crown sits in a 0.2 gap seat in the deck (pipe end 0.05 below deck); check the look of that gap line\n"
 "10. M3 screw length / insert brand to confirm; tongue/notch rear-face 0.5 chamfers not modelled in CAD")
import textwrap
def wrap(t, n): return "\n".join("\n   ".join(textwrap.wrap(l, n)) if len(l) > n else l for l in t.split("\n"))
for (x, t, n) in ((0.005, txt1, 70), (0.25, txt2, 68), (0.50, txt3, 68), (0.75, txt4, 70)):
    fig.text(x, 0.235, wrap(t, n), fontsize=6.4, va="top", family="monospace")
leg = fig.add_axes((0.86, 0.30, 0.13, 0.3)); leg.set_axis_off()
for i, (k, f, c) in enumerate(BODIES):
    leg.add_patch(plt.Rectangle((0, 1 - (i+1)*0.085), 0.12, 0.06, color=c)); leg.text(0.16, 1 - (i+1)*0.085 + 0.01, k + ("" if k.startswith("I4") else "  (ref)"), fontsize=7)
leg.set_xlim(0, 1); leg.set_ylim(0, 1); leg.set_title("Section colours", fontsize=8, loc="left")
fig.savefig(f"{OUT}/review/PSU_case_I4_review.png", dpi=150); fig.savefig(f"{OUT}/review/PSU_case_I4_review.pdf")
print("ok")
