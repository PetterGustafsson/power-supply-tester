"""I6 detail renders: (1) section through a shell screw + grommet foot, (2) retainer H2 window vs antenna, seen from behind the module."""
import sys; sys.argv = ['x']
from common import *
import json, subprocess, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.image as mpimg
BL = "/workspace/blender-4.2.3-linux-x64/blender"; R = "/workspace/psu-tester-case/renders"; ST = f"{OUT}/stl"
def run(cfg, name):
    p = f"/tmp/det_{name}.json"; cfg["AF"] = list(map(float, AF)); json.dump(cfg, open(p, "w"))
    r = subprocess.run([BL, "-b", "-P", f"{OUT}/bay.py", "--", p], capture_output=True, text=True)
    if "Saved" not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:])
# 1. screw section: front-right screw (47.6, -39), plane x = 47.6, keep x < 47.6, ortho from +x
sx, sy = SCREWS[1] if SCREWS[1][1] < 0 and SCREWS[1][0] > 0 else [s for s in SCREWS if s[0] > 0 and s[1] < 0][0]
look = np.array([0.0, sy + 1.0, 11.0]); OS = 38.0; Wd, Ht = 1000, 900
run(dict(out="/tmp/det_screw_raw.png", res=(Wd, Ht), samples=32, cut=True, cut_x=sx, cam=dict(loc=(look + np.array([300, 0, 0])).tolist(), look=look.tolist(), ortho=OS),
         objs=[dict(f=f"{ST}/I8_top_world.stl", col="CFCFCF", capcol="B9A98A"), dict(f=f"{ST}/I8_base_world.stl", col="2A2A2C", capcol="5A5A5E"),
               dict(f=f"{ST}/REF_grommet_foot_x4.stl", col="151515", capcol="303030"), dict(f=f"{ST}/REF_screw_M2.5x12_shell_x4.stl", col="9A9DA2", capcol="C0C3C8")]), "screw")
im = mpimg.imread("/tmp/det_screw_raw.png"); Hh = OS*Ht/Wd
ext = [look[1] - OS/2, look[1] + OS/2, look[2] - Hh/2, look[2] + Hh/2]
fig = plt.figure(figsize=(10, 9), dpi=100); ax = fig.add_axes((0, 0, 1, 1)); ax.imshow(im, extent=ext); ax.set_xlim(ext[:2]); ax.set_ylim(ext[2:]); ax.set_axis_off()
def lab(xy, txt, dxy, col="#a00000"):
    ax.annotate(txt, xy=xy, xytext=(xy[0] + dxy[0], xy[1] + dxy[1]), fontsize=10, color=col, arrowprops=dict(arrowstyle="-", lw=0.8, color=col),
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, lw=0.6, alpha=0.93))
lab((sy - GROM['flange_d']/2 + 0.5, -1.0), f"rubber grommet foot (ASSUMED): flange d{GROM['flange_d']} x {GROM['flange_t']}\n= {GROM['flange_t']} mm below the base, hip d{GROM['hip_d']} x {GROM['hip_l']}, bore d{GROM['bore_d']}", (-6, -4.5))
lab((sy + GROM['hip_d']/2, 3.0), f"counterbore d{SHELL['cb_d']} x {SHELL['cb_depth']} deep (from below)", (4.5, -3.2))
lab((sy + 0.6, SHELL['cb_depth'] - 0.8), f"M2.5 x {SHELL['L']:.0f} pan/flat head d{SCR['head_d']} x {SCR['head_h']}\nseats flat on the PLA floor, inside the grommet", (5.5, -2.2))
lab((sy + SHELL['clear_d']/2, 7.2), f"base clearance d{SHELL['clear_d']}, floor {SHELL['col_top'] - SHELL['cb_depth']:.1f} under the head\n(base column extended to z {SHELL['col_top']})", (4.5, 2.6))
lab((sy + 1.0, SHELL['boss_z0'] + 6), f"top boss d{2*SHELL['boss_r']:.1f}, pilot d{SHELL['pilot_d']} x {SHELL['pilot_depth']:.1f}\nengagement {SHELL['cb_depth'] + SHELL['L'] - SHELL['boss_z0']:.1f} = {(SHELL['cb_depth'] + SHELL['L'] - SHELL['boss_z0'])/SCR['d']:.1f} x d, wall {SHELL['boss_r'] - SHELL['pilot_d']/2:.1f}", (4.0, 3.0))
lab((sy - 2.0, SHELL['col_top'] + 0.25), "0.5 gap base column / top boss", (-11, 3.0))
ax.text(ext[0] + 0.5, ext[3] - 0.5, f"I6 shell screw section, plane x = {sx:.2f}, looking -x", fontsize=11, va="top", bbox=dict(fc="white", ec="#888", alpha=0.9))
fig.savefig(f"{R}/I8_screw_grommet_section.png", dpi=100); plt.close(fig)
# 2. retainer window vs antenna, from behind along +AF (image right = world -x), top shell hidden
G_ = np.array(G); OS2 = 46.0; W2, H2_ = 1000, 900
cam = G_ - 150*np.array(AF); lookp = G_ - 5*np.array(AF)
run(dict(out="/tmp/det_win_raw.png", res=(W2, H2_), samples=32, cam=dict(loc=cam.tolist(), look=lookp.tolist(), ortho=OS2),
         objs=[dict(f=f"{ST}/REF_display_ESP32-S3-LCD-1.28.stl", col="2B3A60"), dict(f=f"{ST}/I8_retainer_world.stl", col="3A3A3E", alpha=0.45),
               dict(f=f"{ST}/REF_harness_5x_1pin_housing_d1.2.stl", col="151515", alpha=0.55), dict(f=f"{ST}/REF_harness_5x_breadboard_pins_0.64sq.stl", col="E0B030")]), "win")
im = mpimg.imread("/tmp/det_win_raw.png"); k = W2/OS2
fig = plt.figure(figsize=(15, 10), dpi=100); ax = fig.add_axes((0, 0, 1, 1)); ax.imshow(im); ax.set_xlim(-250, W2 + 250); ax.set_ylim(H2_ + 50, -50); ax.set_axis_off()
def P(x, u): return (W2/2 - x*k, H2_/2 - u*k)
def labp(x, u, txt, dxy, col="#a00000"):
    p = P(x, u); ax.annotate(txt, xy=p, xytext=(p[0] + dxy[0], p[1] + dxy[1]), fontsize=10, color=col, arrowprops=dict(arrowstyle="-", lw=0.8, color=col),
                             bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, lw=0.6, alpha=0.93))
def rect(x0, x1, u0, u1, col, ls="-"):
    a = P(x0, u0); b = P(x1, u1); ax.add_patch(plt.Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fill=False, ec=col, lw=1.6, ls=ls))
xw = RET['win_x']; RO = RET['id']/2
rect(xw, SD*RO, RET['win_u0'], RET['win_u1'], "#00a050"); rect(SD*11.25, SD*RO, RET_OLD_WIN['u'][0], RET_OLD_WIN['u'][1], "#d02020", "--")
rect(ANT['x0'], ANT['x1'], ANT['u0'], ANT['u1'], "#ff8800")
labp((ANT['x0'] + ANT['x1'])/2, ANT['u1'], f"ceramic antenna C3-001 (vendor STEP)\nx {ANT['x0']}..{ANT['x1']}, u {ANT['u0']}..{ANT['u1']}, a {ANT['a0']}..{ANT['a1']}\nsleeve relief 77.7-102.3 deg, 1.35 deep", (230, -20))
labp(xw + SD*1.5, RET['win_u1'], f"NEW flange window: u {RET['win_u0']:.2f}..{RET['win_u1']:.2f} ({RET['win_u1'] - RET['win_u0']:.1f}),\n|x| > {abs(xw):.2f} (H2 + Dupont + {0.75})", (-340, -200), "#00803c")
labp(xw + SD*3, RET_OLD_WIN['u'][0], f"OLD (I5) window: u {RET_OLD_WIN['u'][0]:.2f}..{RET_OLD_WIN['u'][1]:.2f} (18.0)", (-330, 170), "#d02020")
labp(H2['xc'], H2['u0'] + 1, "H2 header + Dupont 1x5 + 5 pins (H2 = +x per vendor STEP)", (-360, 60), "#333333")
ax.text(-240, -40, "I6 retainer (translucent) vs module back, seen from behind (USB tab down; image right = world -x)", fontsize=11, va="top", bbox=dict(fc="white", ec="#888", alpha=0.9))
fig.savefig(f"{R}/I8_retainer_window_vs_antenna.png", dpi=100); plt.close(fig)
print("done")
