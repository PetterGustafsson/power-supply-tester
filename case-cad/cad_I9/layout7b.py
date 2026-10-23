"""I7b flat-lay breakout of the 12-core cable: helical bundle out of the jacket, combed but organic fan on the table, ferrules resting on
their flare rim + collar end (no gaps, continuous crimped pins). Returns meshes in the layout frame (cable along +x, table z = 0)."""
import numpy as np, math, trimesh
import breakout as B
def build(xj, rc, seed=11, iters=1100):
    rng = np.random.default_rng(seed); F = B.FER
    xs = np.arange(xj - 3.0, xj + 1.5 + 1e-6, 0.5); S = []
    for r, a0 in B.BUND:
        a = a0 + 2*np.pi*(xs - xj)/B.LAY; S.append(np.c_[xs, r*np.cos(a), rc + r*np.sin(a)])
    ys = np.array([s[-1][1] for s in S]); order = np.argsort(ys)          # bundle y order -> comb order (no plan-view crossings)
    m = 0.2/(F['flare_l'] + F['col_l'])                                    # axis slope: rests on the flare rim and the collar end
    T = []
    for j in range(12):
        yf = (j - 5.5)*3.9 + rng.normal(0, 0.28); xo = xj + 35.0 + rng.normal(0, 0.9) + 1.2*(1 - abs(j - 5.5)/5.5)
        al = 0.55*math.atan2(yf, xo - xj) + rng.normal(0, 0.02); u = np.array([math.cos(al), math.sin(al), -m]); u /= np.linalg.norm(u)
        T.append((np.array([xo, yf, F['flare_r']]), u))
    paths, f0, f1, tgt = [None]*12, [0]*12, [0]*12, [None]*12
    for j, k in enumerate(order):
        o, u = T[j]; tail = np.array([o + s*u for s in np.arange(-3.0, F['wire_in'] + 1e-6, 0.5)])
        s0 = S[k][-1]; P = []
        bend = rng.uniform(0.35, 0.65); wob = rng.uniform(-1.2, 1.2)
        for t in np.linspace(0, 1, 80)[1:-1]:
            x = s0[0] + (tail[0][0] - s0[0])*t
            y = s0[1] + (tail[0][1] - s0[1])*(3*t**2 - 2*t**3)**(0.8 + 0.4*bend) + wob*math.sin(math.pi*t)
            z = max(B.RW, s0[2] + (B.RW - s0[2])*min(1, t*4))
            P.append((x, y, z))
        mid = B.resample(np.vstack([s0, P, tail[0]]), 0.5)[1:-1]
        paths[k] = np.vstack([S[k], mid, tail]); f0[k] = len(S[k]); f1[k] = len(tail); tgt[k] = (o, u)
    def sdf(P):
        P = np.asarray(P); x, y, z = P[:, 0], P[:, 1], P[:, 2]
        rr = np.hypot(y, z - rc) - rc
        dj = np.where(x <= xj, rr, np.hypot(np.maximum(rr, 0), x - xj))
        return np.minimum(z, dj)
    def grad(P, h=0.05):
        P = np.asarray(P); G = np.zeros_like(P)
        for c in range(3):
            e = np.zeros(3); e[c] = h; G[:, c] = (sdf(P + e) - sdf(P - e))/(2*h)
        return G/(np.linalg.norm(G, axis=1, keepdims=True) + 1e-9)
    P = B.relax(paths, f0, f1, sdf, grad, iters=iters, gravity=0.006, clr=0.0, gap=0.12, smooth=0.12, stiff=0.06)
    gap = B.min_wire_gap(P)
    out = []
    from mesh7b import smooth_poly
    for k, p in enumerate(P):
        out.append((B.tube(smooth_poly(p, 0.35), B.RW, 18), B.WC12[k], 0.34, 0))
    for o, u in tgt:
        c, pn, st = B.ferrule_meshes(o, u)
        out += [(c, "1E9E3A", 0.33, 0), (pn, "D3CFC6", 0.27, 1), (st, "B87333", 0.35, 1)]
    # foil + filler at the jacket end (the assembly meshes are along +y about (0, 8, 6.25) -> rotate to +x about (xj, 0, rc))
    from mesh7b import foil_and_filler
    fo, fi = foil_and_filler()
    M = trimesh.transformations.rotation_matrix(-math.pi/2, [0, 0, 1])
    for mm, col, ro, me in ((fo, "D0D2D6", 0.22, 1), (fi, "EEEADF", 0.9, 0)):
        mm = mm.copy(); mm.apply_translation((0, -8.0, -6.25)); mm.apply_transform(M); mm.apply_translation((xj, 0, rc)); out.append((mm, col, ro, me))
    # other-ferrule clearance (wire vs foreign collars)
    dmin = 9.9
    for k, p in enumerate(P):
        for j, (o, u) in enumerate(tgt):
            if tgt[k][0] is o: continue
            s = np.clip((p - o) @ u, 0, 6.0); d = np.linalg.norm(p - (o + s[:, None]*u), axis=1) - 1.5 - B.RW
            dmin = min(dmin, float(d.min()))
    return out, dict(min_wire_gap=gap, min_wire_to_other_ferrule=dmin)
