"""route the 12 cores in the assembly (world frame) -> _b7/asm_paths.npz"""
import numpy as np, trimesh, glob, math, sys, json
import breakout as B
from sdf7b import SDF
ST = "stl"; rng = np.random.default_rng(7)
JE, ZC = 8.0, 6.25
ENT = [(-16.25, -21.85, 17.95), (-12.75, -21.85, 17.95), (-9.25, -21.85, 17.95), (-5.75, -21.85, 17.95), (3.75, -21.85, 17.95), (7.25, -21.85, 17.95),
       (10.75, -21.85, 17.95), (14.25, -21.85, 17.95), (23.75, -21.85, 17.95), (27.25, -21.85, 17.95), (30.75, -21.85, 17.95), (34.25, -21.85, 17.95)]
FL = B.FER; YMOUTH = ENT[0][1] - 2.0 - FL['col_l'] - FL['flare_l']        # flare mouth y (-29.85): pin 6 mm in the terminal, as I7
BASE_STL = sys.argv[1] if len(sys.argv) > 1 else "/tmp/base7b.stl"; TIE_STL = sys.argv[2] if len(sys.argv) > 2 else "/tmp/tie7b.stl"
def obstacles():
    M = [trimesh.load(BASE_STL), trimesh.load(TIE_STL), trimesh.load(f"{ST}/I8_top_world.stl")]
    for f in sorted(glob.glob(f"{ST}/REF_PCB_*.stl")) + [f"{ST}/REF_cable_12pin_7mm.stl", f"{ST}/REF_harness_5_wires_to_J4.stl", f"{ST}/REF_J4_XH5_plug.stl",
              f"{ST}/REF_screw_M2.5x12_PCB_x4.stl", f"{ST}/REF_USB_female_overmold.stl", f"{ST}/REF_USB_flat_cable_51mm.stl"]:
        M.append(trimesh.load(f))
    return M
def start_points():
    ys = np.arange(3.0, JE + 1.5 + 1e-6, 0.5); S = []
    for r, a0 in B.BUND:
        a = a0 + 2*np.pi*(ys - JE)/B.LAY
        S.append(np.c_[r*np.cos(a), ys, ZC + r*np.sin(a)])
    return S
def guess(S, xf, xt):
    xs, ys, zs = S[-1]; yu = ys + 2.5; R = abs(xf - xs)/2; xc = (xs + xf)/2
    P = [S[-1] + [0.0, 0.5*j, 0.0] for j in range(1, 6)]
    ey = rng.uniform(0.8, 1.1)
    for t in np.linspace(0, np.pi, 40)[1:]:
        P.append((xc + (xs - xc)*np.cos(t), yu + ey*R*np.sin(t), zs + (3.3 - zs)*min(1.0, 1.4*t/np.pi)))
    ph, amp = rng.uniform(0, 6.28), rng.uniform(0.15, 0.4)
    for y in np.arange(yu - 0.5, -27.0, -0.5):
        P.append((xf + amp*np.sin(ph + y/9.0), y, 3.3))
    Rr = 6.5
    for t in np.linspace(0, np.pi, 50)[1:]:
        w = (1 - np.cos(t))/2; ya = -27.0 + (YMOUTH - 3.0 + 27.0)*w
        P.append((xf + (xt - xf)*w, ya - Rr*np.sin(t), 3.3 + (ENT[0][2] - 3.3)*w))
    tail = np.array([(xt, y, ENT[0][2]) for y in np.arange(YMOUTH - 3.0, YMOUTH + FL['wire_in'] + 1e-6, 0.5)])
    return np.array(P), tail
def main():
    S = start_points(); xs = np.array([s[-1][0] for s in S]); order = np.argsort(xs)
    Lg = sorted(order[:4], key=lambda k: xs[k]); Rg = sorted(order[4:], key=lambda k: -xs[k])
    assign = {}
    xl = -8.1 - np.cumsum(np.r_[0, rng.uniform(1.5, 2.0, 3)]); xr = 14.0 + np.cumsum(np.r_[0, rng.uniform(1.5, 2.0, 7)])
    for j, k in enumerate(Lg): assign[k] = (3 - j, xl[j])
    for j, k in enumerate(Rg): assign[k] = (4 + j, xr[j])
    paths, f0, f1, term = [], [], [], []
    for k in range(12):
        ti, xf = assign[k]; xt = ENT[ti][0]
        P, tail = guess(S[k], xf, xt)
        mid = B.resample(np.vstack([S[k][-1], P, tail[0]]), 0.5)[1:-1]
        paths.append(np.vstack([S[k], mid, tail])); f0.append(len(S[k])); f1.append(len(tail)); term.append(ti)
    sdf = SDF(obstacles(), (-47, -47, 0), (47, 34, 22), 0.3, cache=sys.argv[3] if len(sys.argv) > 3 else "_b7/sdf_asm.npy")
    zk = sdf.lo[2] + sdf.p*np.arange(sdf.n[2]); sdf.d = np.minimum(sdf.d, (zk - 2.4)[None, None, :]).astype(np.float32)   # tray floor is solid below z 2.4
    P = B.relax(paths, f0, f1, sdf, sdf.grad, iters=int(sys.argv[4]) if len(sys.argv) > 4 else 700, gravity=0.003)
    gaps = B.min_wire_gap(P); dmin = min(float((sdf(p[f0[i]:len(p) - f1[i]]) - B.RW).min()) for i, p in enumerate(P))
    L = [float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()) for p in P]
    print("min wire-wire gap %.3f  min obstacle gap %.3f  lengths %.0f..%.0f" % (gaps, dmin, min(L), max(L)))
    np.savez("_b7/asm_paths.npz", *P, term=np.array(term), f0=np.array(f0), f1=np.array(f1))
    json.dump(dict(min_wire_gap=gaps, min_obstacle_gap=dmin, lengths=L, term=[int(t) for t in term]), open("_b7/asm_route.json", "w"), indent=1)
if __name__ == "__main__": main()
