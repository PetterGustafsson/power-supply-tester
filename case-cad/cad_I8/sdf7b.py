"""signed distance grid of the I7b assembly obstacles (mm), for routing the 12 conductors"""
import numpy as np, trimesh, os, scipy.ndimage as nd
from scipy.ndimage import map_coordinates
class SDF:
    def __init__(self, meshes, lo, hi, pitch=0.3, cache=None):
        self.lo, self.p = np.array(lo, float), pitch
        n = np.ceil((np.array(hi) - self.lo)/pitch).astype(int) + 1; self.n = n
        if cache and os.path.exists(cache):
            self.d = np.load(cache); return
        occ = np.zeros(n, bool)
        for m in meshes:
            T = m.triangles                                             # (F,3,3)
            ok = np.all(T.max(axis=1) >= self.lo - 1, axis=1) & np.all(T.min(axis=1) <= np.array(hi) + 1, axis=1); T = T[ok]
            e = np.max(np.linalg.norm(T - np.roll(T, 1, axis=1), axis=2), axis=1)
            ns = np.maximum(1, np.ceil(e/(pitch*0.45)).astype(int))
            for k in np.unique(ns):
                Tk = T[ns == k]
                i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); msk = (i + j) <= k
                u, v = (i[msk]/k), (j[msk]/k)
                for c in range(0, len(Tk), 4000):
                    t = Tk[c:c + 4000]
                    P = t[:, None, 0] + u[None, :, None]*(t[:, None, 1] - t[:, None, 0]) + v[None, :, None]*(t[:, None, 2] - t[:, None, 0])
                    ij = np.round((P.reshape(-1, 3) - self.lo)/pitch).astype(int)
                    g = np.all((ij >= 0) & (ij < n), axis=1); ij = ij[g]
                    occ[ij[:, 0], ij[:, 1], ij[:, 2]] = True
        occ = nd.binary_fill_holes(occ)
        dout = nd.distance_transform_edt(~occ)*pitch; din = nd.distance_transform_edt(occ)*pitch
        self.d = (dout - din - 0.5*pitch).astype(np.float32)
        if cache: np.save(cache, self.d)
    def __call__(self, P):
        g = ((np.asarray(P) - self.lo)/self.p).T
        return map_coordinates(self.d, g, order=1, mode='nearest')
    def grad(self, P, h=0.15):
        P = np.asarray(P); G = np.zeros_like(P)
        for k in range(3):
            e = np.zeros(3); e[k] = h; G[:, k] = (self(P + e) - self(P - e))/(2*h)
        n = np.linalg.norm(G, axis=1, keepdims=True) + 1e-9
        return G/n
