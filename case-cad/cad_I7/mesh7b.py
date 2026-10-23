"""I7b breakout meshes for renders/STL from _b7/asm_paths.npz (+ tie)"""
import numpy as np, trimesh, math, os
import breakout as B
ST = "stl"; RD = "stl/render"; JE, ZC = 8.0, 6.25
def load_paths():
    Z = np.load("_b7/asm_paths.npz"); return [Z[f"arr_{i}"] for i in range(12)], Z["term"]
def smooth_poly(p, ds=0.35):
    from scipy.interpolate import splprep, splev
    q = B.resample(p, 0.5); tck, u = splprep(q.T, s=len(q)*0.0004, k=3)
    L = np.linalg.norm(np.diff(q, axis=0), axis=1).sum(); t = np.linspace(0, 1, int(L/ds))
    return np.array(splev(t, tck)).T
def foil_and_filler(seed=3):
    rng = np.random.default_rng(seed); n = 72; a = np.linspace(0, 2*np.pi, n, endpoint=False)
    ext = 0.5 + 0.9*np.abs(np.sin(3*a + 1.0))*rng.uniform(0.6, 1.0, n)       # ragged foil edge, 0.5 .. 1.4 out of the jacket
    ri, ro = 3.16, 3.24; V = []; F = []
    for k in range(n):
        c, s = math.cos(a[k]), math.sin(a[k])
        for r in (ri, ro):
            V += [(r*c, JE - 1.0, ZC + r*s), (r*c, JE + ext[k], ZC + r*s)]
    V = np.array(V)
    for k in range(n):
        i0, j0 = 4*k, 4*((k + 1) % n)
        for (p, q) in ((0, 1), (2, 3)):
            F += [(i0 + p, j0 + p, j0 + q), (i0 + p, j0 + q, i0 + q)]
        F += [(i0 + 1, j0 + 1, j0 + 3), (i0 + 1, j0 + 3, i0 + 3)]
    foil = trimesh.Trimesh(V, np.array(F)); foil.fix_normals()
    fil = []
    for j in range(3):
        t = np.linspace(0, 1, 30); ph = rng.uniform(0, 6.28)
        P = np.c_[0.08*np.cos(ph + 2*j) + 0.35*t**2*np.cos(ph + j), JE - 1.0 + (3.2 + 0.6*j)*t, ZC + 0.08*np.sin(ph + 2*j) + 0.35*t**2*np.sin(ph + 1.3*j)]
        fil.append(B.tube(P, 0.09, 8))
    return foil, trimesh.util.concatenate(fil)
def main():
    os.makedirs(RD, exist_ok=True); P, term = load_paths()
    from route7b import ENT, YMOUTH
    for k, p in enumerate(P):
        q = np.vstack([p[:5], smooth_poly(p[3:-3])[1:-1], p[-5:]]) if False else smooth_poly(p)
        B.tube(q, B.RW, 18).export(f"{RD}/conductor_{k:02d}.stl")
    C, Pn, S = [], [], []
    for xt, yf, zt in ENT:
        c, pn, s = B.ferrule_meshes([xt, YMOUTH, zt], [0, 1, 0]); C.append(c); Pn.append(pn); S.append(s)
    trimesh.util.concatenate(C).export(f"{ST}/REF_ferrule_collars_green_x12.stl")
    trimesh.util.concatenate(Pn).export(f"{ST}/REF_ferrule_pins_0.314in_x12.stl")
    trimesh.util.concatenate(S).export(f"{RD}/ferrule_strands.stl")
    foil, fil = foil_and_filler(); foil.export(f"{RD}/cable_foil.stl"); fil.export(f"{RD}/cable_filler.stl")
    trimesh.util.concatenate([trimesh.load(f"{RD}/conductor_{k:02d}.stl") for k in range(12)]).export(f"{ST}/REF_cable_12pin_conductors_x12.stl")
    print("meshes ok")
if __name__ == "__main__": main()
