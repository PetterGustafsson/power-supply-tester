"""Top shell OUTER solid as exact B-rep: R12 rounded box (R4 top edge, 0.5 foot chamfer) + slim pipe + trailing tunnel, fillet blends.
B-rep deviations from the I5 SDF (smooth-min) are measured in validate.py."""
from common import *
import time
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.collections import Array1_gp_Pnt2d as TColgp_Array1OfPnt2d
from OCP.gp import gp_Pnt2d
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS
PIPE_EXT = 5.0     # I5: the 40.7 pipe end dips 0.05 below the deck at the front -> build long, blend, then cut the crown recess
TZ_DROP = 1.0       # tunnel crest 1 mm lower than the SDF so it meets the pipe crossing (not tangent) -> robust fillet
A_CUT = -5.0        # tunnel front cut plane (module frame), hidden inside the pipe
def var_fillet(shape, items):
    """items: list of (edge, radius | callable(point)->radius)"""
    mk = BRepFilletAPI_MakeFillet(shape.wrapped)
    for e, r in items:
        if callable(r):
            n = 13; arr = TColgp_Array1OfPnt2d(1, n)
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
def build(verbose=True, r_pt=None, r_side=None, r_front=1.2, r_tun=None):
    t0 = time.time(); z0 = ZS + GAP
    bx = rrect_prism(W/2, D/2, RP, z0, HI)
    bx = fillet(bx.edges().group_by(Axis.Z)[-1], 4.0)
    bx = chamfer(bx.edges().group_by(Axis.Z)[0], 0.5)
    pipe = cyl_axis(G, AF, RS_O, -45.0, PIPE_END + PIPE_EXT)   # extended, trimmed back by the crown recess below
    bt = math.radians(TUN['beta']); dirv = np.array([0, math.cos(bt), -math.sin(bt)])
    A0 = np.array([0.0, TUN['y_top'], TUN['z_top'] - TZ_DROP - TUN['r']/math.cos(bt)])
    tun = cyl_axis(A0, dirv, TUN['r'], -40.0, 45.0)
    tun = tun & (PIPE_PLANE.location * Box(200, 200, 200).moved(Location((0, 0, A_CUT - 100))))
    clip = rrect_prism(W/2 - 6, D/2 - 6, RP - 6, HI - 12.0, 200)
    stub = (pipe + tun) & clip
    r1 = r_pt or TUN['k']
    es = [e for e in stub.edges() if e.center().Z > HI + 1 and e.geom_type == GeomType.BSPLINE]
    stub = var_fillet(stub, [(e, r1) for e in es])
    if verbose: print("pipe-tunnel blend R%.1f on %d edges, t %.1f" % (r1, len(es), time.time() - t0))
    body = bx + stub
    # deck blends: tunnel/deck R(KR); pipe/deck variable: r_front at the front generatrix -> r_side at the flanks
    rs = r_side or KF; rt = r_tun or KR
    items = []
    for e in body.edges():
        c = e.center()
        if abs(c.Z - HI) > 0.6 or not all(abs(v.Z - HI) < 0.6 for v in e.vertices()) or abs(c.X) > 30 or not (-40 < c.Y < 40): continue
        if e.geom_type == GeomType.LINE: continue
        if c.Y > 15:  items.append((e, rt))
        else:
            def rf(p, rs=rs):
                q = np.array([p.X, p.Y, p.Z]) - G; u = q @ UF
                th = math.asin(max(-1, min(1, u/RS_O)))        # -90 deg at the front generatrix
                h = ZG + (PIPE_END + PIPE_EXT)*math.cos(ph) + RS_O*math.sin(ph)*math.sin(th) - HI     # (extended) rim height above the deck
                h0 = ZG + (PIPE_END + PIPE_EXT)*math.cos(ph) - RS_O*math.sin(ph) - HI
                return min(rs, max(r_front, r_front + (rs - r_front)*((h - h0)/6.0)))
            items.append((e, rf))
    if verbose: print("deck blend edges", len(items), [(round(e.center().Y,1), round(e.length,1)) for e, _ in items])
    body = var_fillet(body, items)
    if verbose: print("deck blends ok, t %.1f" % (time.time() - t0))
    body = body - cyl_axis(G, AF, RS_O + CRECESS, PIPE_END, 40.0)      # crown seat: trims the pipe to a = 1.5 and sinks the crown into the deck at the front
    return body
if __name__ == "__main__":
    b = build()
    print("valid", b.is_valid, "solids", len(b.solids()), "faces", len(b.faces()), "vol %.1f" % (b.volume/1000))
    pass  # exports live in build_all.py
