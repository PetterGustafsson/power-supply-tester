"""Retainer ring (print part) + named reference (non-print) bodies, all in the world frame."""
from common import *
import json
import os, math as _m
from i5_params import VENDOR_STEP, H2, H1, PCB_BACK_A, SIG, h2_pin_xu, PIN, DUP, WIRE, J4PLUG, CLEAR, RET
_VB = "/workspace/psu-tester-case/ref/vendor_back_components.brep"
def vendor_back():
    """all vendor STEP solids behind the PCB back face (headers, USB-C, buttons, ICs, passives), module frame"""
    if os.path.exists(_VB): return import_brep(_VB)
    s = import_step(VENDOR_STEP)
    keep = [x for x in s.solids() if x.bounding_box().max.Z < -1.79 and x.volume < 1000]
    c = Compound(keep); export_brep(c, _VB); return c
RELIEFS = []
def retainer_local():
    """I5 retainer = press-in SLEEVE that seats on the PCB back rim (a = -3.4, r 17.1..18.2) instead of the I4 C-ring on the header backs.
    ID 34.2 clears both 2x10 headers (corner r 16.4) and the Dupont housing (corner r 16.1, >= 1.0 mm). Back flange (a -10.9..-9.4, ID 29)
    for stiffness/push face, with a window over H2 for the housing + leads. Tab-side notch as I4. Reliefs (0.35) round every PCB-back
    component that reaches into the sleeve annulus (buttons, passives). Module frame: z = a."""
    ro, ri = RET['od']/2, RET['id']/2; L = RET['a_front'] - RET['a_back']
    s = Solid.make_cylinder(ro, L).moved(Location((0, 0, RET['a_back']))) - Solid.make_cylinder(ri, L).moved(Location((0, 0, RET['a_back'])))
    s = s + (Solid.make_cylinder(ri + 0.01, RET['flange_t']) - Solid.make_cylinder(RET['flange_id']/2, RET['flange_t'])).moved(Location((0, 0, RET['a_back'])))
    s = s - Box(RET['notch'], 40, 20, align=(Align.CENTER, Align.MAX, Align.CENTER)).moved(Location((0, 0, RET['a_back'] + L/2)))     # tab side (u < 0)
    s = s - (Box(20, 2*RET['win_u'], 2*RET['flange_t'] + 0.2, align=(Align.MAX, Align.CENTER, Align.CENTER)).moved(Location((RET['win_x'], H2['uc'], RET['a_back'])))
             & Solid.make_cylinder(ri, 10).moved(Location((0, 0, RET['a_back'] - 5))))          # H2 window in the flange only (sleeve wall kept)
    env = (Solid.make_cylinder(ro + 1, 8) - Solid.make_cylinder(ri - 0.5, 8)).moved(Location((0, 0, -11.5)))
    iv = []
    for c in vendor_back().solids():
        b = c.bounding_box()
        if b.min.Z > PCB_BACK_A - 0.01: continue
        if max(_m.hypot(px, py) for px in (b.min.X, b.max.X) for py in (b.min.Y, b.max.Y)) < ri - RET['relief'] - 0.05: continue
        if (c & env).volume < 1e-6: continue
        angs = [_m.atan2(py, px) for px in (b.min.X, b.max.X) for py in (b.min.Y, b.max.Y)]
        if max(angs) - min(angs) > _m.pi: angs = [a + 2*_m.pi if a < 0 else a for a in angs]
        d = RET['relief']/ri; iv.append([min(angs) - d, max(angs) + d, b.min.Z - RET['relief']])
    iv.sort(); merged = []
    for a0, a1, z0 in iv:                       # merge overlapping angular intervals, keep the deepest relief
        if merged and a0 <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], a1); merged[-1][2] = min(merged[-1][2], z0)
        else: merged.append([a0, a1, z0])
    RELIEFS.clear()
    for a0, a1, z0 in merged:
        R = ro + 2; n = 8; k = 1/_m.cos((a1 - a0)/(2*n))
        pts = [(0, 0)] + [(R*k*_m.cos(a0 + (a1 - a0)*t/n), R*k*_m.sin(a0 + (a1 - a0)*t/n)) for t in range(n + 1)]
        w = extrude(Polygon(*pts, align=None), amount=PCB_BACK_A + 1 - z0).moved(Location((0, 0, z0)))
        s = s - w
        RELIEFS.append(dict(deg=(round(_m.degrees(a0), 1), round(_m.degrees(a1), 1)), depth=round(PCB_BACK_A - z0, 2)))
    s = chamfer(s.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1].filter_by(lambda e: e.radius > ro - 0.01), 0.4)   # lead-in on the leading (front) outer edge
    return s
def retainer_world(): return PIPE_PLANE.location * retainer_local()
def retainer_print(): return retainer_local().moved(Location((0, 0, -RET['a_back'])))     # flange down on the plate, no supports
def mod_pt(x, u, a): return np.array(G) + x*XV + u*np.array(UF) + a*np.array(AF)
def harness_paths():
    """wire centre-line control points per signal (world). Housing slot i at 2.54 pitch along u; J4 pin 1 at the front (-y) end."""
    out = []
    a_end = H2['a0'] - DUP['l']
    for i, (name, hp, jp) in enumerate(SIG):
        u = H2['uc'] + (i - 2)*2.54
        s0 = mod_pt(H2['xc'], u, a_end); s1 = s0 - WIRE['straight']*np.array(AF)
        yj = (J4PLUG['y0'] + J4PLUG['y1'])/2 + (jp - 3)*J4PLUG['pitch']
        xj = (J4PLUG['x0'] + J4PLUG['x1'])/2
        e0 = np.array([xj, yj, J4PLUG['z1']]); e1 = e0 + np.array([0, 0, 5.0])
        mid = np.array([-27.0, -2.0 + 1.6*(i - 2), 35.5])
        out.append((name, [s0, s1, mid, e1, e0]))
    return out
def wire_solid(pts, r):
    p = [V(q) for q in pts]
    t0 = V(-np.array(AF)); t1 = V((0, 0, -1))
    path = Wire([Edge.make_line(p[0], p[1]), Edge.make_spline([p[1], p[2], p[3]], tangents=[t0, t1]), Edge.make_line(p[3], p[4])])
    prof = Circle(r).moved(Location(Plane(origin=p[0], z_dir=t0).location))
    return sweep(prof.face() if hasattr(prof, 'face') else prof, path=path, transition=Transition.ROUND)
def harness_refs():
    R = {}
    pins = None
    for name, hp, jp in SIG:
        x, u = h2_pin_xu(hp)
        b = mod_box(x - PIN['sq']/2, x + PIN['sq']/2, u - PIN['sq']/2, u + PIN['sq']/2, PIN['a_out'], PIN['a_in'])
        pins = b if pins is None else pins + b
    R["REF_harness_5x_breadboard_pins_0.64sq"] = pins
    R["REF_harness_Dupont_1x5_female"] = mod_box(H2['xc'] - DUP['x']/2, H2['xc'] + DUP['x']/2, H2['uc'] - DUP['u']/2, H2['uc'] + DUP['u']/2, H2['a0'] - DUP['l'], H2['a0'])
    w = None
    for name, pts in harness_paths():
        s = wire_solid(pts, WIRE['d']/2); w = s if w is None else w + s
    R["REF_harness_5_wires_to_J4"] = w
    R["REF_J4_XH5_plug"] = box((J4PLUG['x0'], J4PLUG['y0'], J4PLUG['z0']), (J4PLUG['x1'], J4PLUG['y1'], J4PLUG['z1']))
    return R
def harness_keepout(c=CLEAR):
    """housing + wires grown by c (for the ceiling-rib cut); housing also gets finger room (+3 in u, open toward the axis)"""
    k = mod_box(H2['xc'] - DUP['x']/2 - c, H2['xc'] + DUP['x']/2 + c + 6, H2['uc'] - DUP['u']/2 - c - 3, H2['uc'] + DUP['u']/2 + c + 3, H2['a0'] - DUP['l'] - c, H2['a0'])
    return [k] + [wire_solid(pts, WIRE['d']/2 + c) for name, pts in harness_paths()]     # list: subtract one by one (fused fat sweeps break OCC)
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
    disp = Solid.make_cylinder(MOD['d']/2, -PCB_BACK_A).moved(Location((0, 0, PCB_BACK_A))) + \
        Box(TAB['w'], TAB['u_out'], TAB['a1'] - TAB['a0'], align=(Align.CENTER, Align.MAX, Align.MIN)).moved(Location((0, 0, TAB['a0'])))
    R["REF_display_ESP32-S3-LCD-1.28"] = PIPE_PLANE.location * Compound([disp] + list(vendor_back().solids()))   # I5: real back side from vendor STEP
    R["REF_USB_male_90deg_overmold"] = PIPE_PLANE.location * Box(MALE['w'], MALE['u1'] - MALE['u0'], MALE['a1'] - MALE['a0']).moved(
        Location((0, (MALE['u0'] + MALE['u1'])/2, (MALE['a0'] + MALE['a1'])/2)))
    m = json.load(open("/workspace/psu-tester-case/src/meta_I5.json")); P = [np.array(p) for p in m["path"]]
    P = [p for i, p in enumerate(P) if i == 0 or np.linalg.norm(p - P[i-1]) > 0.3]
    fc = None
    for a, b in zip(P[:-1], P[1:]):
        d = b - a; L = np.linalg.norm(d); ang = math.degrees(math.atan2(d[2], d[1]))
        s = Box(8.5, L + 0.2, 2.0).moved(Location(tuple((a + b)/2), (1, 0, 0), ang))
        fc = s if fc is None else fc + s
    R["REF_USB_flat_cable_51mm"] = fc
    R["REF_USB_female_overmold"] = box((-POCKET['w']/2, D/2 - POCKET['l'], ZF - POCKET['t']/2), (POCKET['w']/2, D/2, ZF + POCKET['t']/2))
    R["REF_cable_12pin_7mm"] = Solid.make_cylinder(CAB['od']/2, 6.0 + D/2 + 15, Plane(origin=(CAB['x'], -D/2 - 15, CAB['zc']), z_dir=(0, 1, 0)))
    R.update(harness_refs())
    return R
if __name__ == "__main__":
    r = retainer_local(); print("retainer valid", r.is_valid, "vol %.3f" % (r.volume/1000))
    for k, v in refs().items(): print(k, v.is_valid, round(v.volume, 1))
