"""Retainer ring (print part) + named reference (non-print) bodies, all in the world frame."""
from common import *
import json
RET = dict(h=3.0, id=29.0, notch=TAB['w'] + 1.6)      # press-in C-ring behind the module (stop face at a = -7.9)
def retainer_local():
    ro = BORE + PF['interf']/2
    r = Solid.make_cylinder(ro, RET['h']) - Solid.make_cylinder(RET['id']/2, RET['h'])
    r = r - Box(RET['notch'], 40, 10, align=(Align.CENTER, Align.MAX, Align.MIN)).moved(Location((0, 0, -1)))   # open on the tab side (u < 0)
    r = chamfer(r.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1].filter_by(lambda e: e.radius > ro - 0.01), 0.4)
    return r
def retainer_world(): return PIPE_PLANE.location * retainer_local().moved(Location((0, 0, -MOD['t'] - RET['h'])))
def refs():
    R = {}
    off = np.array([0, PCB_Y, PCB_Z])
    R["REF_PCB_RevD2_board"] = box((-43.0, PCB_Y - 31, PCB_Z), (43.0, PCB_Y + 31, PCB_Z + 1.6))
    for i, (x0, x1) in enumerate(((-12.75, 1.25), (7.25, 21.25), (27.25, 41.25))):
        R[f"REF_PCB_J{i+1}_XY350V_4p"] = box((x0, -22.2, 15.6), (x1, -14.6, 25.6))
    R["REF_PCB_J4_JST_XH5"] = box((-39.88, -18.85, 15.6), (-34.12, -5.95, 22.6))
    R["REF_PCB_tall_part"] = box((-35.61, 14.6, 15.6), (-24.01, 20.6, 25.6))
    for i, (x, y) in enumerate(((-11, 13.6), (9, 13.6), (19, 13.6), (29, 13.6), (-26, 6.6))):
        R[f"REF_PCB_ic{i+1}"] = box((x - 1.6, y - 1.6, 15.6), (x + 1.6, y + 1.6, 16.8))
    disp = Solid.make_cylinder(MOD['d']/2, MOD['t']).moved(Location((0, 0, -MOD['t']))) + \
        Box(TAB['w'], TAB['u_out'], TAB['a1'] - TAB['a0'], align=(Align.CENTER, Align.MAX, Align.MIN)).moved(Location((0, 0, TAB['a0'])))
    R["REF_display_ESP32-S3-LCD-1.28"] = PIPE_PLANE.location * disp
    R["REF_USB_male_90deg_overmold"] = PIPE_PLANE.location * Box(MALE['w'], MALE['u1'] - MALE['u0'], MALE['a1'] - MALE['a0']).moved(
        Location((0, (MALE['u0'] + MALE['u1'])/2, (MALE['a0'] + MALE['a1'])/2)))
    m = json.load(open("/workspace/psu-tester-case/src/meta_I4.json")); P = [np.array(p) for p in m["path"]]
    P = [p for i, p in enumerate(P) if i == 0 or np.linalg.norm(p - P[i-1]) > 0.3]
    fc = None
    for a, b in zip(P[:-1], P[1:]):
        d = b - a; L = np.linalg.norm(d); ang = math.degrees(math.atan2(d[2], d[1]))
        s = Box(8.5, L + 0.2, 2.0).moved(Location(tuple((a + b)/2), (1, 0, 0), ang))
        fc = s if fc is None else fc + s
    R["REF_USB_flat_cable_51mm"] = fc
    R["REF_USB_female_overmold"] = box((-POCKET['w']/2, D/2 - POCKET['l'], ZF - POCKET['t']/2), (POCKET['w']/2, D/2, ZF + POCKET['t']/2))
    R["REF_cable_12pin_7mm"] = Solid.make_cylinder(CAB['od']/2, 6.0 + D/2 + 15, Plane(origin=(CAB['x'], -D/2 - 15, CAB['zc']), z_dir=(0, 1, 0)))
    return R
if __name__ == "__main__":
    r = retainer_local(); print("retainer valid", r.is_valid, "vol %.3f" % (r.volume/1000))
    for k, v in refs().items(): print(k, v.is_valid, round(v.volume, 1))
