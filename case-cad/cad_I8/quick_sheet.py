"""I8 quick look: underside render (left) + vertical sections through the pipe root along two rib planes (right). usage: quick_sheet.py render.png top.stl out.png"""
import sys, math, numpy as np, trimesh, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
rp, ts, out = sys.argv[1:4]
m = trimesh.load(ts); m7 = trimesh.load('../cad_I7/stl/I7_top_world.stl'); cy0 = 1.982
fig = plt.figure(figsize=(16, 7.2)); g = fig.add_gridspec(2, 2, width_ratios=[1.25, 1])
a0 = fig.add_subplot(g[:, 0]); a0.imshow(Image.open(rp)); a0.axis('off'); a0.set_title('I8 top underside, iso from below (grey, low-res)', fontsize=10)
for i, phi in enumerate((67.5, 292.5)):
    ax = fig.add_subplot(g[i, 1]); p = math.radians(phi); d = np.array([math.cos(p), math.sin(p), 0]); n = np.array([-math.sin(p), math.cos(p), 0]); o = np.array([0, cy0, 0])
    for mm, c, lw in ((m7, '#bbbbbb', 0.8), (m, 'k', 1.0)):
        s = mm.section(plane_origin=o, plane_normal=n)
        if s is None: continue
        for e in s.discrete: ax.plot((e - o) @ d, e[:, 2], color=c, lw=lw)
    ax.axhline(45.6, color='#3070c0', lw=0.6, ls='--'); ax.set_xlim(10, 45); ax.set_ylim(33, 58); ax.set_aspect('equal'); ax.grid(alpha=.3)
    ax.set_title('section through pipe root along rib plane phi=%.1f deg (s from pipe-root centre, mm); grey = I7 grid, blue = deck underside z 45.6' % phi, fontsize=8)
plt.tight_layout(); plt.savefig(out, dpi=90)
