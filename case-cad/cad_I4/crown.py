"""I4 press-fit crown, exact revolve. Local frame: z = module axis a (glass plane z=0), print flange-down (local z flipped)."""
from common import *
def build(interf=None):
    i = PF['interf'] if interf is None else interf
    ri, ro, rs = CROWN['id']/2, RS_O, BORE + i/2
    h, t, ld = PF['spigot_h'], CROWN['t'], PF['lead']
    pts = [(ri, 0), (rs - ld, 0), (rs, ld), (rs, h), (ro - 0.4, h), (ro, h + 0.0)]   # profile (r, z), outer top edge rounded after
    prof = Polyline((ri, 0), (rs - ld, 0), (rs, ld), (rs, h), (ro, h), (ro, t), (ri + 0.6, t), (ri, t - 0.6), close=True)
    fc = Plane.XZ * make_face(prof)
    c = revolve(fc, Axis.Z, 360)
    top_outer = [e for e in c.edges() if e.geom_type == GeomType.CIRCLE and abs(e.center().Z - t) < 1e-3 and abs(e.radius - ro) < 1e-3] if False else \
        [e for e in c.edges().filter_by(GeomType.CIRCLE) if abs(e.arc_center.Z - t) < 1e-3 and abs(e.radius - ro) < 1e-3]
    c = fillet(top_outer, 0.4)
    return c
def world(c):
    return PIPE_PLANE.location * c
if __name__ == "__main__":
    c = build(); print("crown valid", c.is_valid, "vol %.3f cm3" % (c.volume/1000), "spigot OD %.2f vs bore %.2f" % (2*(BORE + PF['interf']/2), 2*BORE))
    pass  # exports live in build_all.py
