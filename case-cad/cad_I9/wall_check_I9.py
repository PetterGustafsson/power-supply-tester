"""I9: outer-skin wall thickness round the new pipe root. Samples the outer skin (|x| < 36, |y| < 42, z > 47, not down-facing), casts a ray inward
along -normal to the exit face (chunked). The crown-seat zone (r < 23.5 about the pipe axis, a > -4: pipe end face/rim edges and the 0.6 mm
front lip) is reported separately. usage: wall_check_I9.py [top.stl ...] -> wall_check_I9.json"""
import sys, json, numpy as np, trimesh
G = np.array([0, -10, 59.87992521]); AF = np.array([0, -0.64278761, 0.76604444])
R = {}
for f in (sys.argv[1:] or ['stl/I9_top_world.stl', '../cad_I8/stl/I8_top_world.stl']):
    m = trimesh.load(f); p, fi = trimesh.sample.sample_surface_even(m, 100000, seed=3); n = m.face_normals[fi]
    s = (np.abs(p[:, 0]) < 36) & (np.abs(p[:, 1]) < 42) & (p[:, 2] > 47.0) & (n[:, 2] > -0.2); p = p[s]; n = n[s]
    d = np.full(len(p), np.inf)
    for i0 in range(0, len(p), 2500):
        pp = p[i0:i0+2500]; nn = n[i0:i0+2500]
        l, r, t = m.ray.intersects_location(pp - nn*1e-3, -nn, multiple_hits=False); ok = np.einsum('ij,ij->i', m.face_normals[t], -nn[r]) > 0.2
        d[i0 + r[ok]] = np.linalg.norm(l[ok] - pp[r[ok]], axis=1)
    v = p - G; a = v @ AF; rad = np.linalg.norm(v - np.outer(a, AF), axis=1)
    seat = (rad < 23.5) & (a > -4); fin = np.isfinite(d); w = fin & ~seat; i = np.argmin(np.where(w, d, np.inf))
    R[f] = dict(samples=int(fin.sum()), wall_min_outside_seat=round(float(d[w].min()), 2), at=[round(float(x), 1) for x in p[i]], p1=round(float(np.percentile(d[w], 1)), 2),
                below_1p6_outside_seat=int((w & (d < 1.6)).sum()), seat_zone_below_1p6=int((fin & seat & (d < 1.6)).sum()),
                seat_zone_thin_radius_range=[round(float(rad[fin & seat & (d < 1.6)].min()), 2), round(float(rad[fin & seat & (d < 1.6)].max()), 2)] if (fin & seat & (d < 1.6)).any() else None)
print(json.dumps(R, indent=1)); json.dump(R, open('wall_check_I9.json', 'w'), indent=1)
