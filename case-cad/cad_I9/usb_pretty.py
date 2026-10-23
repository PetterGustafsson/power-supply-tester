"""Render-quality USB-C extender meshes (same envelopes as the REF bodies): filleted overmolds, metal plug/receptacle shells, swept ribbon."""
from common import *
import json, os
O = f"{OUT}/stl/render"
m = json.load(open("/workspace/psu-tester-case/src/meta_I7.json")); Pth = [np.array(p) for p in m["path"]]
Pth = [p for i, p in enumerate(Pth) if i == 0 or np.linalg.norm(p - Pth[i-1]) > 0.8]
# male: overmold (module frame) filleted, with a short boot where the ribbon leaves (a0 end)
mb = Box(MALE['w'], MALE['u1'] - MALE['u0'], MALE['a1'] - MALE['a0']).moved(Location((0, (MALE['u0'] + MALE['u1'])/2, (MALE['a0'] + MALE['a1'])/2)))
mb = fillet(mb.edges(), 1.6)
export_stl(PIPE_PLANE.location * mb, f"{O}/usb_male_body.stl", tolerance=0.01, angular_tolerance=0.05)
ap = -4.52; tw, tt, tl = 8.25, 2.4, 6.6
sh = Box(tw - tt, tl, tt).moved(Location((0, -20.94 + tl/2, ap)))
for sx in (-1, 1): sh = sh + Solid.make_cylinder(tt/2, tl, Plane(origin=(sx*(tw - tt)/2, -20.94, ap), z_dir=(0, 1, 0)))
collar = Box(tw + 0.9 - tt - 0.9, 1.2, tt + 0.9).moved(Location((0, -20.94 - 0.6, ap)))
for sx in (-1, 1): collar = collar + Solid.make_cylinder((tt + 0.9)/2, 1.2, Plane(origin=(sx*(tw - tt)/2, -20.94 - 1.2, ap), z_dir=(0, 1, 0)))
export_stl(PIPE_PLANE.location * (sh + collar), f"{O}/usb_male_shell.stl", tolerance=0.005, angular_tolerance=0.05)
# ribbon: 8.5 x 1.1 rounded section swept along the solved path (y-z plane, x = 0)
pts = [V(p) for p in Pth]
path = Edge.make_spline(pts)
t0 = path.tangent_at(0)
prof = Plane(origin=pts[0], x_dir=V((1, 0, 0)), z_dir=t0) * RectangleRounded(8.5, 1.1, 0.5)
rib = sweep(prof, path=Wire([path]))
export_stl(rib, f"{O}/usb_ribbon.stl", tolerance=0.01, angular_tolerance=0.05)
# female overmold in the rear clamp + metal receptacle at the rear face
fb = box((-POCKET['w']/2, D/2 - POCKET['l'], ZF - POCKET['t']/2), (POCKET['w']/2, D/2, ZF + POCKET['t']/2))
fb = fillet(fb.edges(), 1.2)
rec = Box(8.94 - 3.26, 2.0, 3.26).moved(Location((0, D/2 + 0.3 - 1.0, ZF)))
for sx in (-1, 1): rec = rec + Solid.make_cylinder(3.26/2, 2.0, Plane(origin=(sx*(8.94 - 3.26)/2, D/2 - 1.7, ZF), z_dir=(0, 1, 0)))
hole = Box(8.34 - 2.56, 2.2, 2.56).moved(Location((0, D/2 + 0.31 - 1.0, ZF)))
for sx in (-1, 1): hole = hole + Solid.make_cylinder(2.56/2, 2.2, Plane(origin=(sx*(8.34 - 2.56)/2, D/2 - 1.8, ZF), z_dir=(0, 1, 0)))
export_stl(fb - rec, f"{O}/usb_female_body.stl", tolerance=0.01, angular_tolerance=0.05)
export_stl(rec - hole, f"{O}/usb_female_shell.stl", tolerance=0.005, angular_tolerance=0.05)
export_stl(Box(6.6, 0.3, 0.7).moved(Location((0, D/2 - 1.2, ZF))), f"{O}/usb_female_tongue.stl", tolerance=0.01)
print("ok", rib.is_valid, round(path.length, 1))
