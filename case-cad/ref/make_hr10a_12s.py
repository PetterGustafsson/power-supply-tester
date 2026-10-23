"""Derive a reference model of the Hirose HR10A-10P-12S(73) (12-pos SOCKET-contact cable plug, solder type) from the official Hirose
HR10A-10P-12P.stp (same HR10A-10P plug shell: A 43, dB 14.7, dC 9.5 per the HR10 catalog). The 12P model's front cavity (y 0..~6, r 6.9) is
filled with a socket insert (r 5.0, face recessed 1.2 mm) carrying 12 socket holes d0.9 (9 on r 3.2 + 3 on r 1.3, approximate layout),
plus a d7 cable entry at the rear. Local frame: axis = +y, mating face at y = 0, cable end at y = 43. Exterior envelope = Hirose data."""
from build123d import *
import math
src = import_step("/workspace/psu-tester-case/ref/HR10A-10P-12P.stp").solids()[0]
ax = Plane(origin=(0, 0, 0), z_dir=(0, 1, 0))
def cyl_y(r, y0, y1, x=0.0, z=0.0): return Solid.make_cylinder(r, y1 - y0, Plane(origin=(x, y0, z), z_dir=(0, 1, 0)))
body = src + cyl_y(5.0, 1.2, 6.3)
for i in range(9):
    a = 2*math.pi*i/9; body = body - cyl_y(0.45, 1.0, 4.2, 3.2*math.cos(a), 3.2*math.sin(a))
for i in range(3):
    a = 2*math.pi*i/3 + math.pi/6; body = body - cyl_y(0.45, 1.0, 4.2, 1.3*math.cos(a), 1.3*math.sin(a))
body = body - cyl_y(3.5, 40.0, 43.1)        # cable entry (d7 cable, catalog dD = 7.0)
body = body.solids()[0]; body.label = "HR10A-10P-12S(73)_derived"
print("valid", body.is_valid, "vol %.1f" % body.volume, body.bounding_box().min, body.bounding_box().max)
export_step(body, "/workspace/psu-tester-case/ref/HR10A-10P-12S73_derived.step")
