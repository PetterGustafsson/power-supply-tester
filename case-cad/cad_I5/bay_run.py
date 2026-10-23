"""I5 bay renders: inside view + section through H2 (x = -13.5) showing the 5 breadboard pins, Dupont housing, retainer sleeve cut-out and the lead route to J4."""
import sys; sys.argv = ['x']
from common import *
import parts as PARTS
from i5_params import H2, DUP, RET, J4PLUG
import json, subprocess, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.image as mpimg
BL = "/workspace/blender-4.2.3-linux-x64/blender"; R = "/workspace/psu-tester-case/renders"
ST = f"{OUT}/stl"
TOPc, CRc, REc, DIc, MAc, FLc = "CFCFCF", "F2C200", "2A2A2C", "1B2238", "7A3B3B", "9B6B3B"
WIc, DUc, PIc, PCc = "D02A1E", "151515", "E0B030", "3F7A3F"
def run(cfg, name):
    p = f"/tmp/bay_{name}.json"; cfg["AF"] = list(map(float, AF)); json.dump(cfg, open(p, "w"))
    r = subprocess.run([BL, "-b", "-P", f"{OUT}/bay.py", "--", p], capture_output=True, text=True)
    if "Saved" not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:])
G_ = np.array(G)
HARN = [dict(f=f"{ST}/REF_harness_Dupont_1x5_female.stl", col=DUc, capcol="404040"), dict(f=f"{ST}/REF_harness_5x_breadboard_pins_0.64sq.stl", col=PIc, capcol="F0C040"),
        dict(f=f"{ST}/REF_harness_5_wires_to_J4.stl", col=WIc, capcol="F04030"), dict(f=f"{ST}/REF_J4_XH5_plug.stl", col="EDEDE0", capcol="CFCFC0"),
        dict(f=f"{ST}/REF_PCB_J4_JST_XH5.stl", col="F5F5EA", capcol="DADACC")]
# 1. inside view: from below/behind along the bore axis, offset toward -x so H2 + housing + leads read
look1 = G_ - 14*AF + np.array([-8, 0, 0])
cam1 = G_ - 90*AF + np.array([-30, 0, -10])
run(dict(out=f"{R}/quick_I5_bay_inside.png", res=(1000, 650), samples=32, cam=dict(loc=cam1.tolist(), look=look1.tolist(), lens=30),
         objs=[dict(f=f"{ST}/I5_top_world.stl", col=TOPc), dict(f=f"{ST}/I5_crown_world.stl", col=CRc), dict(f=f"{ST}/I5_retainer_world.stl", col=REc),
               dict(f=f"{ST}/REF_display_ESP32-S3-LCD-1.28.stl", col=DIc), dict(f=f"{ST}/REF_USB_male_90deg_overmold.stl", col=MAc),
               dict(f=f"{ST}/REF_USB_flat_cable_51mm.stl", col=FLc, alpha=0.25)] + [dict(f=o["f"], col=o["col"]) for o in HARN]), "inside")
im = mpimg.imread(f"{R}/quick_I5_bay_inside.png")
fig = plt.figure(figsize=(10, 6.5), dpi=100); ax = fig.add_axes((0, 0, 1, 1)); ax.imshow(im); ax.set_axis_off()
ax.text(12, 640, "I5 bay from inside (base removed). H2 = RIGHT header seen from the back (USB down) -> world -x side.\n"
        "Black = 1x5 Dupont on 5 breadboard pins in H2 (H2.3 VSYS, .1 GND, .4 3V3, .5 GPIO6, .7 GPIO7); red = 5 leads to J4 (XH plug, white).\n"
        "Retainer is now a sleeve (ID 34.4) seating on the PCB rim; flange window over H2.", fontsize=8.5, va="bottom", bbox=dict(fc="white", ec="#888", alpha=0.9))
fig.savefig(f"{R}/quick_I5_bay_inside.png", dpi=100); plt.close(fig)
# 2. section through the H2 centre line x = -13.5 (keep x < -13.5), ortho from +x
CX = H2['xc']
look2 = np.array([0.0, -6.0, 42.0]); OS = 84.0
run(dict(out="/tmp/bay5_section_raw.png", res=(1000, 650), samples=32, cut=True, cut_x=CX, cam=dict(loc=(look2 + np.array([300, 0, 0])).tolist(), look=look2.tolist(), ortho=OS),
         objs=[dict(f=f"{ST}/I5_top_world.stl", col=TOPc, capcol="B9A98A"), dict(f=f"{ST}/I5_crown_world.stl", col=CRc, capcol="C99A00"),
               dict(f=f"{ST}/I5_retainer_world.stl", col=REc, capcol="707074"), dict(f="/tmp/REF_display_clip_xlt-13.5.stl", col=DIc, cut=False),
               dict(f=f"{ST}/REF_USB_male_90deg_overmold.stl", col=MAc, capcol="9A4B4B"), dict(f=f"{ST}/REF_PCB_RevD2_board.stl", col=PCc, capcol="5A9A5A"),
               dict(f=f"{ST}/I5_base_world.stl", col="2A2A2C", capcol="4A4A4C"),
               dict(f=f"{ST}/REF_harness_Dupont_1x5_female.stl", col="303030", alpha=0.35), dict(f=f"{ST}/REF_harness_5x_breadboard_pins_0.64sq.stl", col=PIc, cut=False)] + HARN[2:]), "section")
im = mpimg.imread("/tmp/bay5_section_raw.png"); Hh = OS*650/1000
ext = [look2[1] - OS/2, look2[1] + OS/2, look2[2] - Hh/2, look2[2] + Hh/2]
fig = plt.figure(figsize=(10, 6.5), dpi=100); ax = fig.add_axes((0, 0, 1, 1)); ax.imshow(im, extent=ext); ax.set_xlim(ext[:2]); ax.set_ylim(ext[2:]); ax.set_axis_off()
def P(u, a): q = G_ + u*np.array(UF) + a*np.array(AF); return q[1], q[2]
def lab(xy, txt, dxy, col="#a00000"):
    tx = min(max(xy[0] + dxy[0], ext[0] + 1), ext[1] - 32); ty = min(max(xy[1] + dxy[1], ext[2] + 2), ext[3] - 5)
    ax.annotate(txt, xy=xy, xytext=(tx, ty), fontsize=8, color=col, arrowprops=dict(arrowstyle="-", lw=0.7, color=col),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, lw=0.5, alpha=0.92))
lab(P(H2['uc'] - 4, -5.6), "H2 2x10 1.27 header (vendor STEP)\nx -15..-12, u -6.4..6.7, a -7.9..-3.4", (-36, 6))
lab(P(4.6, -12.0), "5 breadboard pins 0.64 sq (gold)\n(3.0 in H2, 8.5 in Dupont)", (12, 6))
lab(P(H2['uc'] - 3, -18.0), "1x5 female Dupont 12.7 x 2.5 x 14\n(incl. crimps) on H2 back face", (-40, -4))
lab(P(11.6, -6.0), "retainer SLEEVE ID 34.4 / OD 36.8 (0.10 press),\nseats on PCB rim at a=-3.4; 1.07 radial to housing", (4, 9))
lab(P(-11.6, -9.5), "sleeve + flange (a -10.9..-9.4);\nflange window over H2 (u +/-9, x < -11.25)", (-34, -12))
lab(P(-1.0, -25.0), "6 mm straight lead, R>=5 bends", (-36, -8))
lab((-2.0, 35.5), "5 leads (26 AWG, OD 1.4) -> J4\n>= 1.0 to top/ribs, 8.6 to flat cable,\n17.6 to 90 deg plug", (10, -14))
lab(((J4PLUG['y0'] + J4PLUG['y1'])/2, 24.6), "J4 JST-XH5 + plug (top z 26.6)", (8, -8))
lab(P(math.sqrt((BORE + 1.0)**2 - CX**2), 1.0), "pipe wall 2.0 (unchanged)", (8, 3))
ax.text(ext[0] + 1, ext[3] - 3, "I5 section x = -13.5 (H2 centre line), looking -x", fontsize=9, va="top", bbox=dict(fc="white", ec="#888", alpha=0.9))
fig.savefig(f"{R}/quick_I5_bay_section.png", dpi=100); plt.close(fig)
print("done")
