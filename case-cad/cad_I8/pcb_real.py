"""Real Rev D2 PCBA from Petter's KiCad VRML export (ref/tester-d2.wrl): per-footprint meshes in the world frame, plus faceted
B-rep (closed shapes -> solids, open ones -> shells) for the assembly STEP. Board frame (centre, mid-thickness) + PCB_OFF -> world."""
import sys, os, pickle, numpy as np, trimesh, collections
sys.path.insert(0, "/workspace/psu-tester-case/src"); sys.path.insert(0, os.path.dirname(__file__))
import wrl
from i7_params import PCB_WRL, PCB_OFF
CACHE = "/workspace/psu-tester-case/ref/tester-d2_parsed.pkl"
LAYERS = {"TXFM_161": "board", "TXFM_162": "copper_top", "TXFM_163": "pads_top", "TXFM_164": "mask_top", "TXFM_165": "copper_bot",
          "TXFM_166": "mask_bot", "TXFM_167": "silk_top", "TXFM_168": "silk_bot"}
def shapes():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    S = wrl.load(PCB_WRL)
    for s in S: s['verts'] = s['verts'] + np.array(PCB_OFF)
    pickle.dump(S, open(CACHE, "wb")); return S
def groups():
    """name -> list of shapes. Footprints named from geometry (designators are not in the VRML)."""
    S = shapes(); g = collections.OrderedDict()
    for s in S:
        k = s['path'][1]; g.setdefault(k, []).append(s)
    info = {}
    for k, ss in g.items():
        v = np.vstack([s['verts'] for s in ss]); info[k] = (v.min(0), v.max(0))
    out = collections.OrderedDict()
    out["REF_PCB_RevD2_board"] = g["TXFM_161"]
    terms = sorted([k for k in g if (info[k][1] - info[k][0])[0] > 13 and info[k][1][2] > 23 and k not in LAYERS and info[k][1][2] < 25], key=lambda k: info[k][0][0])
    for i, k in enumerate(terms): out[f"REF_PCB_J{i+1}_XY350V_4p"] = g[k]
    j4 = [k for k in g if k not in LAYERS and abs(info[k][1][2] - 22.6) < 0.05 and (info[k][1] - info[k][0])[1] > 14][0]
    out["REF_PCB_J4_JST_XH5"] = g[j4]
    tall = [k for k in g if k not in LAYERS and info[k][1][2] > 25.5][0]
    out["REF_PCB_tall_part"] = g[tall]
    used = {"TXFM_161", j4, tall, *terms}
    out["REF_PCB_SMD_parts"] = [s for k in g if k not in used and k not in LAYERS for s in g[k]]
    out["_layers"] = [s for k in g if k in LAYERS and k != "TXFM_161" for s in g[k]]
    return out
def mesh_of(ss):
    ms = []
    for s in ss:
        if len(s['faces']) == 0: continue
        m = trimesh.Trimesh(s['verts'], s['faces'], process=False)
        m.visual.face_colors = (np.r_[np.clip(s['rgb'], 0, 1), 1.0]*255).astype(np.uint8); ms.append(m)
    return trimesh.util.concatenate(ms)
def brep_of(ss, tol=1e-3):
    """faceted OCC shape: one solid per closed VRML shape, sewn shell otherwise"""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.gp import gp_Pnt
    from OCP.TopoDS import TopoDS
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.BRepCheck import BRepCheck_Analyzer
    from build123d import Shape, Compound, Solid, Shell
    parts = []
    mm = mesh_of(ss); mm.merge_vertices()
    items = [mm] if mm.is_watertight else [trimesh.Trimesh(s['verts'], s['faces'], process=True) for s in ss]
    for m in items:
        if len(m.faces) == 0: continue
        sew = BRepBuilderAPI_Sewing(tol)
        for f in m.faces:
            p = [m.vertices[i] for i in f]
            if np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) < 1e-9: continue
            poly = BRepBuilderAPI_MakePolygon(*[gp_Pnt(*map(float, q)) for q in p], True)
            fa = BRepBuilderAPI_MakeFace(poly.Wire(), True)
            if fa.IsDone(): sew.Add(fa.Face())
        sew.Perform(); sh = sew.SewedShape()
        ex = TopExp_Explorer(sh, TopAbs_SHELL); done = False
        while ex.More():
            shell = TopoDS.Shell(ex.Current()) if hasattr(TopoDS, "Shell") else TopoDS.Shell_s(ex.Current()); ex.Next()
            if m.is_watertight:
                ms = BRepBuilderAPI_MakeSolid(shell)
                if ms.IsDone():
                    so = Solid(ms.Solid())
                    if so.volume < 0: so = Solid(ms.Solid().Reversed())
                    parts.append(so); done = True; continue
            parts.append(Shell(shell)); done = True
        if not done: parts.append(Shape.cast(sh))
    return Compound(parts)
if __name__ == "__main__":
    G = groups()
    for k, ss in G.items():
        m = mesh_of(ss); print(k, len(ss), len(m.faces), np.round(m.bounds, 2).tolist())
def term_entries():
    """(x, y_face, z) of the 12 wire-entry holes (black discs) of J1..J3, sorted by x; y_face = front face of the terminal body"""
    G = groups(); E = []
    for k in ("REF_PCB_J1_XY350V_4p", "REF_PCB_J2_XY350V_4p", "REF_PCB_J3_XY350V_4p"):
        ss = G[k]; yface = min(s['verts'][:, 1].min() for s in ss)
        for s in ss:
            if len(s['faces']) > 100 and s['rgb'][0] < 0.075 and np.ptp(s['verts'][:, 1]) < 0.1:
                c = s['verts'].mean(0); E.append((round(float(c[0]), 3), round(float(yface), 3), round(float(c[2]), 3)))
    return sorted(E)
