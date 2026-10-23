"""Shared params + helpers for the I6 review CAD (exact build123d B-rep). Units mm, world frame = H2/I frame (base origin centre, z up, -y = user)."""
import sys, math, numpy as np
from build123d import *
sys.path.insert(0, "/workspace/psu-tester-case/src")
from i7_params import *
from i7_params import SHELL, GROM, PCBS, SCR, SD, ANT, RET_OLD_WIN            # noqa  (I6 <- I2 <- I <- H2)
from h2_params import CAB, CRADLE, TIES, LEDGE, FLOOR, HOLES, SCREWS, PCB, PCB_Y, PCB_Z
from i7_params import SCREWS6 as SCREWS        # I6: shell screws moved 1.35 toward the corner centres
XV = np.array([1.0, 0, 0])
OUT = "/workspace/psu-tester-case/cad_I7"
TAB = dict(w=13.32, u_out=21.12, a0=-6.6, a1=-0.13)    # USB tab envelope from the E_display reference model (module frame)
def V(p): return Vector(*map(float, p))
def rrect_prism(hx, hy, r, z0, z1):
    return extrude(RectangleRounded(2*hx, 2*hy, r), amount=z1 - z0).moved(Location((0, 0, z0)))
def box(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float); c = (lo + hi)/2; s = hi - lo
    return Box(*s).moved(Location(tuple(c)))
def cylz(x, y, r, z0, z1): return Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, z0)))
def cyl_axis(origin, direction, r, a0, a1):
    """cylinder along unit direction from origin + a0*dir to origin + a1*dir"""
    d = np.array(direction, float); d /= np.linalg.norm(d); o = np.array(origin, float) + a0*d
    pl = Plane(origin=V(o), z_dir=V(d))
    return Solid.make_cylinder(r, a1 - a0, pl)
PIPE_PLANE = Plane(origin=V(G), x_dir=V(XV), z_dir=V(AF))        # module frame: x, u (=UF), a (=AF)
def mod_box(x0, x1, u0, u1, a0, a1):
    """box in the module frame (x, u, a)"""
    b = Box(x1 - x0, u1 - u0, a1 - a0).moved(Location(((x0 + x1)/2, (u0 + u1)/2, (a0 + a1)/2)))
    return PIPE_PLANE.location * b
def vol(s): return s.volume
