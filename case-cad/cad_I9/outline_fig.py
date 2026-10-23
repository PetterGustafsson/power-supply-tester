"""Top view (looking at the glass, module frame x,u) : real vendor outline vs the I6 model, bore, retainer, tab channel."""
from common import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import parts as PARTS, top as TOP
VA = PARTS.vendor_all()
def sec_xy(sol, z):
    f = (sol & Box(80, 80, 0.01).moved(Location((0, 0, z)))).faces()[0]
    return np.array([[v.X, v.Y] for v in f.outer_wire().positions(np.linspace(0, 1, 600).tolist())]) if hasattr(f.outer_wire(), "positions") else \
           np.array([[e.position_at(t).X, e.position_at(t).Y] for e in f.outer_wire().edges() for t in np.linspace(0, 1, 12)])
pcb, lcm = sec_xy(VA[0], -2.6), sec_xy(VA[1], -0.85)
mo = TOP.module_outline(); mop = np.array([[e.position_at(t).X, e.position_at(t).Y] for e in mo.faces()[0].outer_wire().edges() for t in np.linspace(0, 1, 12)])
fig, ax = plt.subplots(figsize=(11, 10.5), dpi=150)
th = np.linspace(0, 2*np.pi, 400); C = lambda r, **k: ax.plot(r*np.cos(th), r*np.sin(th), **k)
# I6 model: disc 36.4 + rectangular tab 13.32 to u -21.12
r6 = 36.4/2; a = np.arcsin(6.66/r6); t6 = np.linspace(-np.pi/2 + a, 3*np.pi/2 - a, 300)
old = np.r_[np.c_[r6*np.cos(t6), r6*np.sin(t6)], [[-6.66, -r6*np.cos(a)], [-6.66, -21.12], [6.66, -21.12], [6.66, -r6*np.cos(a)]], [[r6*np.cos(t6[0]), r6*np.sin(t6[0])]]]
ax.fill(pcb[:, 0], pcb[:, 1], color="#1d3a7a", alpha=0.25, label="REAL PCB outline (vendor STEP; Waveshare: OD 36.5, 39.5 tall)")
ax.plot(pcb[:, 0], pcb[:, 1], color="#1d3a7a", lw=1.6)
ax.plot(lcm[:, 0], lcm[:, 1], color="#0a7a3a", lw=1.2, label="REAL LCM outline (35.6 + FPC tail)")
ax.plot(old[:, 0], old[:, 1], "--", color="#c0392b", lw=1.4, label="I6 model: disc 36.4 + 13.32 rect tab")
C(18.35, color="#888888", lw=1.0, ls=":", label="I6 bore d36.70")
C(BORE, color="#000000", lw=1.2, label="I7 bore d%.2f" % (2*BORE))
C(RET['od']/2, color="#e67e22", lw=1.0, label="I7 retainer sleeve OD %.2f / ID %.1f (behind the PCB)" % (RET['od'], RET['id'])); C(RET['id']/2, color="#e67e22", lw=1.0)
ax.plot(mop[:, 0], mop[:, 1], color="#8e44ad", lw=1.0, label="I7 shell cut = real PCB+LCM outline + 0.2 (seat a -3.6..0.15; tab region u<-12 open to the back)")
ax.add_patch(plt.Rectangle((-7.06, -21.62), 14.12, 21.62 - 15.35, fill=False, ec="#c0392b", lw=0.8, ls="-.", label="I6 tab channel 14.1 wide"))
ax.annotate("I6: real tab flanks outside the old channel\n(PCB 9.2 mm3 + LCM 4.6 mm3 clash with the I6 top)", (8.6, -17.0), (14, -26), arrowprops=dict(arrowstyle="->"), fontsize=8)
ax.annotate("PCB circle centre +0.13 in u:\nPCB top r 18.39 > I6 bore 18.35", (0, 18.39), (-23, 22.5), arrowprops=dict(arrowstyle="->"), fontsize=8)
ax.set_aspect("equal"); ax.set_xlim(-24, 30); ax.set_ylim(-28, 26); ax.grid(alpha=0.3); ax.set_xlabel("x (mm)"); ax.set_ylabel("u (mm, + = up the display)")
ax.set_title("ESP32-S3-LCD-1.28 perimeter: real vendor outline vs I6 model vs I7 bore / retainer / shell cut (view onto the glass)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=2, fontsize=7.5, framealpha=0.9)
ins = ax.inset_axes([0.62, 0.62, 0.36, 0.36])
for arr, kw in ((pcb, dict(color="#1d3a7a", lw=1.6)), (lcm, dict(color="#0a7a3a", lw=1.2)), (old, dict(color="#c0392b", lw=1.4, ls="--")), (mop, dict(color="#8e44ad", lw=1.0))):
    ins.plot(arr[:, 0], arr[:, 1], **kw)
ins.plot(BORE*np.cos(th), BORE*np.sin(th), color="k", lw=1.0); ins.plot(18.35*np.cos(th), 18.35*np.sin(th), color="#888", lw=1.0, ls=":")
ins.add_patch(plt.Rectangle((-7.06, -21.62), 14.12, 21.62 - 15.35, fill=False, ec="#c0392b", lw=0.8, ls="-."))
ins.set_xlim(3, 12); ins.set_ylim(-22.5, -13.5); ins.set_aspect("equal"); ins.set_title("tab flank (zoom)", fontsize=7); ins.tick_params(labelsize=6); ins.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("/workspace/psu-tester-case/renders/I9_module_outline_overlay.png")
print("ok")
