"""Module-plane sections (a = -2.6 through the module PCB, a = -0.85 through the LCM) of the I6 and I7 top shells with the real module."""
from common import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import parts as PARTS
VA = PARTS.vendor_all(); INV = PIPE_PLANE.location.inverse()
def sec(solid_world, a):
    loc = INV * solid_world
    s = loc & Box(120, 120, 0.02).moved(Location((0, 0, a)))
    out = []
    for f in (s.faces() if s else []):
        if abs(f.normal_at().Z) < 0.9: continue
        loops = [f.outer_wire()] + list(f.inner_wires())
        out.append([np.array([[e.position_at(t).X, e.position_at(t).Y] for e in w.edges() for t in np.linspace(0, 1, 40)]) for w in loops])
    return out
def draw(ax, polys, fc, ec, lw=0.6, alpha=1.0):
    for loops in polys:
        verts, codes = [], []
        for L in loops: verts += L.tolist() + [L[0].tolist()]; codes += [Path.MOVETO] + [Path.LINETO]*(len(L) - 1) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, alpha=alpha))
T6 = import_step("/workspace/psu-tester-case/cad_I6/step/I6_top.step").solids()[0]; T7 = import_step(f"{OUT}/step/I9_top.step").solids()[0]
PCBw, LCMw = PIPE_PLANE.location*VA[0], PIPE_PLANE.location*VA[1]
fig, axs = plt.subplots(2, 2, figsize=(13, 12.5), dpi=140)
for row, (a, mod, nm) in enumerate(((-2.6, PCBw, "module PCB (a = -2.6)"), (-0.85, LCMw, "LCM / glass (a = -0.85)"))):
    ms = sec(mod, a)
    for col, (T, tn, I6) in enumerate(((T6, "I6 top shell", True), (T7, "I7 top shell", False))):
        ax = axs[row, col]
        draw(ax, sec(T, a), "#E3DED0", "#7a7466")
        draw(ax, ms, "#1d3a7a", "#0b1b40", alpha=0.75)
        clash = sec(mod & T, a) if (mod & T) else []
        draw(ax, clash, "#ff0000", "#ff0000", lw=1.2)
        vol = (mod & T).volume if (mod & T) else 0.0
        ax.set_title(f"{tn}: section through the {nm}\nreal vendor outline (blue); clash with shell (red) = {vol:.2f} mm3", fontsize=9)
        ax.set_aspect("equal"); ax.set_xlim(-26, 26); ax.set_ylim(-27, 24); ax.grid(alpha=0.25)
        ax.set_xlabel("x (mm)"); ax.set_ylabel("u (mm)")
fig.suptitle("ESP32-S3-LCD-1.28 in the module bay: real perimeter vs shell (view onto the glass, module frame)\nI7: bore d37.0 (was 36.7), seat/tab cut = real PCB+LCM outline + 0.2", fontsize=11)
plt.tight_layout(); plt.savefig("/workspace/psu-tester-case/renders/I9_module_bay_section.png"); print("ok")
