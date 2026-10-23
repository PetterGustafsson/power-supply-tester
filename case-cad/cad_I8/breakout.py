"""I7b 12-core breakout: helical bundle out of the jacket, splay with a light physical relaxation (smoothing + gravity + wire/wire and
wire/obstacle contact), green-collar 0.314" ferrules with a continuous crimped pin. Used for the assembly (world) and the flat-lay layout."""
import math, numpy as np, trimesh
from scipy.spatial import cKDTree
RW = 0.7                                   # conductor insulation OD 1.4 (ASSUMED 0.34 mm2)
FER = dict(flare_l=1.5, flare_r=1.5, col_r=1.3, col_l=4.5, pin_r=0.55, pin_l=8.0, pin_in=0.8, flat=0.44, wire_in=1.2)
LAY = 45.0                                 # helical lay length of the 12 cores (mm per turn, right-hand)
BUND = [(2.45, 2*math.pi*k/9) for k in range(9)] + [(0.85, 2*math.pi*k/3 + 0.5) for k in range(3)]
WC12 = ["C0392B", "1A1A1A", "E67E22", "F1C40F", "27AE60", "2980B9", "8E44AD", "7F8C8D", "ECF0F1", "8B4513", "E91E63", "16A085"]
def resample(P, ds):
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    n = max(int(round(L[-1]/ds)), 2); t = np.linspace(0, L[-1], n + 1)
    return np.c_[[np.interp(t, L, P[:, k]) for k in range(3)]].T
def relax(paths, nfix0, nfix1, sdf, grad, iters=600, gravity=0.004, clr=0.12, gap=0.14, seed=1, smooth=0.22, ds=0.5, wobble=None, stiff=0.0):
    """paths: list of (N,3); first nfix0[i] and last nfix1[i] points fixed"""
    P = [p.copy() for p in paths]
    for it in range(iters):
        # smoothing (Laplacian) + gravity on free points
        for i, p in enumerate(P):
            a, b = nfix0[i], len(p) - nfix1[i]
            lap = p[a - 1:b - 1] + p[a + 1:b + 1] - 2*p[a:b]
            p[a:b] += smooth*lap
            if stiff > 0:
                aa, bb = max(a, 2), min(b, len(p) - 2)
                d4 = p[aa - 2:bb - 2] - 4*p[aa - 1:bb - 1] + 6*p[aa:bb] - 4*p[aa + 1:bb + 1] + p[aa + 2:bb + 2]
                p[aa:bb] -= stiff*d4
            p[a:b, 2] -= gravity*np.clip((b - np.arange(a, b))/24.0, 0, 1)      # no sag in the last ~12 mm before the ferrule
        # wire / wire contact
        allp = np.vstack(P); wid = np.concatenate([np.full(len(p), i) for i, p in enumerate(P)])
        idx = np.concatenate([np.arange(len(p)) for p in P])
        free = np.concatenate([np.r_[np.zeros(nfix0[i], bool), np.ones(len(p) - nfix0[i] - nfix1[i], bool), np.zeros(nfix1[i], bool)] for i, p in enumerate(P)])
        tr = cKDTree(allp); pr = tr.query_pairs(2*RW + gap, output_type='ndarray')
        if len(pr):
            pr = pr[wid[pr[:, 0]] != wid[pr[:, 1]]]
            if len(pr):
                v = allp[pr[:, 1]] - allp[pr[:, 0]]; d = np.linalg.norm(v, axis=1) + 1e-9; push = ((2*RW + gap - d)/d)[:, None]*v*0.5
                f0, f1 = free[pr[:, 0]], free[pr[:, 1]]
                w0 = np.where(f0 & ~f1, 2.0, np.where(f0, 1.0, 0.0)); w1 = np.where(f1 & ~f0, 2.0, np.where(f1, 1.0, 0.0))
                D = np.zeros_like(allp)
                np.add.at(D, pr[:, 0], -push*w0[:, None]); np.add.at(D, pr[:, 1], push*w1[:, None])
                allp = allp + D
        # obstacles
        d = sdf(allp); bad = (d < RW + clr) & free
        if bad.any():
            g = grad(allp[bad]); allp[bad] += ((RW + clr) - d[bad])[:, None]*g
        # split back
        k = 0
        for i in range(len(P)): n = len(P[i]); P[i] = allp[k:k + n]; k += n
        if it % 15 == 14 and it < iters - 30:
            for i, p in enumerate(P):
                a, b = nfix0[i], len(p) - nfix1[i]
                mid = resample(p[a - 1:b + 1], ds)
                P[i] = np.vstack([p[:a - 1], mid, p[b + 1:]])
    return P
def min_wire_gap(P):
    allp = np.vstack(P); wid = np.concatenate([np.full(len(p), i) for i, p in enumerate(P)])
    tr = cKDTree(allp); pr = tr.query_pairs(3.0, output_type='ndarray'); pr = pr[wid[pr[:, 0]] != wid[pr[:, 1]]]
    d = np.linalg.norm(allp[pr[:, 0]] - allp[pr[:, 1]], axis=1)
    return float(d.min() - 2*RW) if len(d) else 9.9
# ---------------- meshes ----------------
def frames(P):
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    n = np.cross(T[0], [0, 0, 1.0]);
    if np.linalg.norm(n) < 1e-3: n = np.cross(T[0], [1.0, 0, 0])
    n /= np.linalg.norm(n); N = [n]
    for k in range(1, len(P)):
        v = N[-1] - np.dot(N[-1], T[k])*T[k]; v /= np.linalg.norm(v); N.append(v)
    N = np.array(N); B = np.cross(T, N); return T, N, B
def tube(P, r, nseg=18):
    T, N, B = frames(P); a = np.linspace(0, 2*np.pi, nseg, endpoint=False)
    V = (P[:, None, :] + r*(np.cos(a)[None, :, None]*N[:, None, :] + np.sin(a)[None, :, None]*B[:, None, :])).reshape(-1, 3)
    F = []; n = len(P)
    for k in range(n - 1):
        for j in range(nseg):
            a0, a1, b0, b1 = k*nseg + j, k*nseg + (j + 1) % nseg, (k + 1)*nseg + j, (k + 1)*nseg + (j + 1) % nseg
            F += [(a0, b0, b1), (a0, b1, a1)]
    c0, c1 = len(V), len(V) + 1; V = np.vstack([V, P[0], P[-1]])
    for j in range(nseg):
        F += [(c0, (j + 1) % nseg, j), (c1, (n - 1)*nseg + j, (n - 1)*nseg + (j + 1) % nseg)]
    m = trimesh.Trimesh(V, np.array(F), process=True); m.fix_normals(); return m
def revolve(prof, origin, u, nseg=36, crimp=None):
    """prof: [(s, r)] along axis u from origin; crimp(s) -> half-width of the square flats (None = round)"""
    u = np.asarray(u, float)/np.linalg.norm(u); n = np.cross(u, [0, 0, 1.0])
    if np.linalg.norm(n) < 1e-3: n = np.cross(u, [1.0, 0, 0])
    n /= np.linalg.norm(n); b = np.cross(u, n); a = np.linspace(0, 2*np.pi, nseg, endpoint=False) + np.pi/4
    V = []
    for s, r in prof:
        rr = np.full(nseg, r)
        if crimp is not None:
            h = crimp(s)
            if h < r: rr = np.minimum(r, h/np.maximum(np.abs(np.cos(a - np.pi/4)), np.abs(np.sin(a - np.pi/4))))
        V.append(np.asarray(origin) + s*u + rr[:, None]*(np.cos(a)[:, None]*n + np.sin(a)[:, None]*b))
    V = np.vstack(V); F = []; m = len(prof)
    for k in range(m - 1):
        for j in range(nseg):
            a0, a1, b0, b1 = k*nseg + j, k*nseg + (j + 1) % nseg, (k + 1)*nseg + j, (k + 1)*nseg + (j + 1) % nseg
            F += [(a0, b0, b1), (a0, b1, a1)]
    c0, c1 = len(V), len(V) + 1; V = np.vstack([V, np.asarray(origin) + prof[0][0]*u, np.asarray(origin) + prof[-1][0]*u])
    for j in range(nseg):
        F += [(c0, (j + 1) % nseg, j), (c1, (m - 1)*nseg + j, (m - 1)*nseg + (j + 1) % nseg)]
    mm = trimesh.Trimesh(V, np.array(F), process=True); mm.fix_normals(); return mm
def ferrule_meshes(o, u):
    """o = flare mouth centre, u = axis toward the pin tip. Returns (collar, pin, strands)"""
    F_ = FER; c0 = F_['flare_l']; c1 = c0 + F_['col_l']
    prof = [(0, F_['flare_r']), (0.15, F_['flare_r']), (c0, F_['col_r']), (c1 - 0.25, F_['col_r']), (c1 - 0.05, F_['col_r'] - 0.12), (c1, F_['col_r'] - 0.3)]
    collar = revolve(prof, o, u, 40)
    s0 = c1 - F_['pin_in']; s1 = c1 + F_['pin_l']
    ss = np.linspace(s0, s1, 90)
    def crimp(s):
        a, b = c1 + 1.0, s1 - 0.9                               # square crimp over the pin, 0.5 ramps
        if s < a - 0.5 or s > b + 0.5: return 9.0
        w = min(1.0, (s - (a - 0.5))/0.5, ((b + 0.5) - s)/0.5)
        return F_['pin_r'] - w*(F_['pin_r'] - F_['flat'])
    pin = revolve([(s, F_['pin_r'] if s < s1 - 0.08 else F_['pin_r'] - 0.06) for s in ss], o, u, 32, crimp)
    strands = revolve([(s1 - 0.1, 0.36), (s1 + 0.04, 0.36)], o, u, 24)
    return collar, pin, strands
def ferrule_solids(o, u):
    """exact B-rep versions for the STEP (collar = flare + cylinder; pin = tube with 4 crimp flats; strand ends)"""
    from build123d import Solid, Plane, Box, Location, Vector, Axis
    F_ = FER; u = np.asarray(u, float)/np.linalg.norm(u); o = np.asarray(o, float); c0 = F_['flare_l']; c1 = c0 + F_['col_l']
    pl = lambda s: Plane(origin=tuple(o + s*u), z_dir=tuple(u))
    col = Solid.make_cone(F_['flare_r'], F_['col_r'], c0, pl(0)) + Solid.make_cylinder(F_['col_r'], F_['col_l'] - 0.3, pl(c0)) + \
          Solid.make_cone(F_['col_r'], F_['col_r'] - 0.3, 0.3, pl(c1 - 0.3))
    s0 = c1 - F_['pin_in']; s1 = c1 + F_['pin_l']
    pin = Solid.make_cylinder(F_['pin_r'], s1 - s0, pl(s0))
    a, b = c1 + 1.0, s1 - 0.9; P = pl((a + b)/2)
    for ang in (45, 135, 225, 315):
        d = (F_['flat'] + 1.0)
        bx = Box(2.0, 2.0, b - a)
        bx = P.location * bx.moved(Location((d*math.cos(math.radians(ang)), d*math.sin(math.radians(ang)), 0), (0, 0, 1), ang))
        pin = pin - bx
    st = Solid.make_cylinder(0.36, 0.14, pl(s1 - 0.1))
    return col, pin, st
