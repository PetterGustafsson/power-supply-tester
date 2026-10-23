"""Top shell OUTER solid as exact B-rep. I9: R12 rounded box (R4 top edge, 0.5 foot chamfer) + ONE straight tilted pipe, constant-R root fillet (trailing tunnel removed).
B-rep deviations from the I6 SDF (smooth-min) are measured in validate.py."""
from common import *
import time
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.collections import Array1_gp_Pnt2d as TColgp_Array1OfPnt2d
from OCP.gp import gp_Pnt2d
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS
PIPE_EXT = 5.0     # I6: the 40.7 pipe end dips 0.05 below the deck at the front -> build long, blend, then cut the crown recess
TZ_DROP = 1.0       # tunnel crest 1 mm lower than the SDF so it meets the pipe crossing (not tangent) -> robust fillet
A_CUT = -5.0        # tunnel front cut plane (module frame), hidden inside the pipe
def var_fillet(shape, items):
    """items: list of (edge, radius | callable(point)->radius)"""
    mk = BRepFilletAPI_MakeFillet(shape.wrapped)
    for e, r in items:
        if callable(r):
            n = 13 if not hasattr(r, 'n') else r.n; arr = TColgp_Array1OfPnt2d(1, n)
            for i in range(n):
                u = i/(n - 1); p = e.position_at(u)
                arr.SetValue(i + 1, gp_Pnt2d(u, float(r(p))))
            mk.Add(arr, e.wrapped)
        else:
            mk.Add(float(r), e.wrapped)
    mk.Build()
    if not mk.IsDone(): raise RuntimeError("fillet failed")
    from OCP.TopExp import TopExp_Explorer; from OCP.TopAbs import TopAbs_SOLID
    ex = TopExp_Explorer(mk.Shape(), TopAbs_SOLID); sols = []
    while ex.More(): sols.append(Solid(TopoDS.Solid(ex.Current()))); ex.Next()
    assert len(sols) == 1, len(sols)
    return sols[0]
R_ROOT = 5.0       # I9: rounded joint line where the single tilted pipe leaves the flat deck (rear + flanks)
R_FRONT = 0.8      # I9: at the front generatrix the crown seat (a = 1.5) sits flush with the deck -> any constant R leaves a knife lip in front of the crown
LIP_M = 1.0        # fillet tangent line kept >= 1 mm below the crown seat plane
def root_radius(R=None, rf=None, m=None):
    """radius law on the pipe/deck edge: R where the crown seat is high enough above the deck to take the whole fillet, smoothly (C1 smoothstep) down to
    R_FRONT at the front. Fillet tangent height on the pipe = r (1 - n_z), n_z = sin(ph) sin(theta) (pipe normal z); seat height
    h(theta) = ZG + PIPE_END cos(ph) + RS_O sin(ph) sin(theta) - HI; r_max = (h - m)/(1 - n_z)."""
    R = R or R_ROOT; rf = R_FRONT if rf is None else rf; m = LIP_M if m is None else m
    def f(p):
        q = np.array([p.X, p.Y, p.Z]) - G; st = max(-1.0, min(1.0, (q @ UF)/RS_O))
        h = ZG + PIPE_END*math.cos(ph) + RS_O*math.sin(ph)*st - HI; rmax = (h - m)/(1 - math.sin(ph)*st)
        x = max(0.0, min(1.0, (rmax - rf)/(R - rf))); x = x*x*(3 - 2*x)
        return rf + (R - rf)*x
    f.n = 73
    return f
def root_edges(body):
    """pipe/deck intersection edges: on the deck plane z = HI, inside the deck (not the R4 perimeter)"""
    out = []
    for e in body.edges():
        c = e.center()
        if abs(c.Z - HI) > 0.6 or not all(abs(v.Z - HI) < 0.6 for v in e.vertices()) or abs(c.X) > 30 or not (-45 < c.Y < 45): continue
        if e.geom_type == GeomType.LINE: continue
        out.append(e)
    return out
def build(verbose=True, r_root=None, constant=False):
    """I9 (Petter: 'one angle, with a rounded joint line'): R12 rounded box (R4 top edge, 0.5 foot chamfer) + ONE straight tilted pipe
    (OD 40.7 about G/AF, 40 deg), no trailing tunnel; constant fillet r_root along the whole pipe/deck intersection; crown recess."""
    t0 = time.time(); z0 = ZS + GAP; rr = r_root or R_ROOT
    bx = rrect_prism(W/2, D/2, RP, z0, HI)
    bx = fillet(bx.edges().group_by(Axis.Z)[-1], 4.0)
    bx = chamfer(bx.edges().group_by(Axis.Z)[0], 0.5)
    pipe = cyl_axis(G, AF, RS_O, -45.0, PIPE_END + PIPE_EXT) & rrect_prism(W/2 - 6, D/2 - 6, RP - 6, HI - 12.0, 200)
    body = bx + pipe
    es = root_edges(body)
    if verbose: print("root edges", len(es), [(round(e.center().Y, 1), round(e.length, 1), e.geom_type) for e in es])
    body = var_fillet(body, [(e, rr if constant else root_radius(rr)) for e in es])
    if verbose: print("root fillet R%.1f ok, t %.1f" % (rr, time.time() - t0))
    body = body - cyl_axis(G, AF, RS_O + CRECESS, PIPE_END, 40.0)      # crown seat: trims the pipe to a = 1.5 and sinks the crown into the deck at the front
    return body
if __name__ == "__main__":
    b = build()
    print("valid", b.is_valid, "solids", len(b.solids()), "faces", len(b.faces()), "vol %.1f" % (b.volume/1000))
    pass  # exports live in build_all.py
