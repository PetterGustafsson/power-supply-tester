"""Retainer ring (print part) + named reference (non-print) bodies, all in the world frame."""
from common import *
import json
import os, math as _m
from i6_params import VENDOR_STEP, H2, H1, PCB_BACK_A, SIG, h2_pin_xu, PIN, DUP, WIRE, J4PLUG, CLEAR, RET, SD, ANT, SHELL, GROM, PCBS, SCR
_VB = "/workspace/psu-tester-case/ref/vendor_back_components.brep"
def vendor_back():
    """all vendor STEP solids behind the PCB back face (headers, USB-C, buttons, ICs, passives), module frame"""
    if os.path.exists(_VB): return import_brep(_VB)
    s = import_step(VENDOR_STEP)
    keep = [x for x in s.solids() if x.bounding_box().max.Z < -1.79 and x.volume < 1000]
    c = Compound(keep); export_brep(c, _VB); return c
RELIEFS = []
def retainer_local():
    """I6 retainer = press-in SLEEVE that seats on the PCB back rim (a = -3.4, r 17.1..18.2) instead of the I4 C-ring on the header backs.
    ID 34.2 clears both 2x10 headers (corner r 16.4) and the Dupont housing (corner r 16.1, >= 1.0 mm). Back flange (a -10.9..-9.4, ID 29)
    for stiffness/push face, with a window over H2 for the housing + leads. Tab-side notch as I4. Reliefs (0.35) round every PCB-back
    component that reaches into the sleeve annulus (buttons, passives). Module frame: z = a."""
    ro, ri = RET['od']/2, RET['id']/2; L = RET['a_front'] - RET['a_back']
    s = Solid.make_cylinder(ro, L).moved(Location((0, 0, RET['a_back']))) - Solid.make_cylinder(ri, L).moved(Location((0, 0, RET['a_back'])))
    s = s + (Solid.make_cylinder(ri + 0.01, RET['flange_t']) - Solid.make_cylinder(RET['flange_id']/2, RET['flange_t'])).moved(Location((0, 0, RET['a_back'])))
    s = s - Box(RET['notch'], 40, 20, align=(Align.CENTER, Align.MAX, Align.CENTER)).moved(Location((0, 0, RET['a_back'] + L/2)))     # tab side (u < 0)
    s = s - (Box(20, RET['win_u1'] - RET['win_u0'], 2*RET['flange_t'] + 0.2, align=(Align.MIN if SD > 0 else Align.MAX, Align.CENTER, Align.CENTER)).moved(Location((RET['win_x'], (RET['win_u0'] + RET['win_u1'])/2, RET['a_back'])))
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
        if SD > 0:     # I6: H2 on +x -> cross over the flat cable (x 0, z <= 33.4) at z ~38.5, then down to J4
            m1 = np.array([2.0, 3.0 + 1.6*(i - 2), 38.6]); m2 = np.array([-24.0, -3.0 + 1.6*(i - 2), 35.0])
            out.append((name, [s0, s1, m1, m2, e1, e0]))
        else:
            mid = np.array([-27.0, -2.0 + 1.6*(i - 2), 35.5])
            out.append((name, [s0, s1, mid, e1, e0]))
    return out
def wire_solid(pts, r):
    p = [V(q) for q in pts]
    t0 = V(-np.array(AF)); t1 = V((0, 0, -1))
    path = Wire([Edge.make_line(p[0], p[1]), Edge.make_spline(p[1:-1], tangents=[t0, t1]), Edge.make_line(p[-2], p[-1])])
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
HR10_STEP = "/workspace/psu-tester-case/ref/HR10A-10P-12S73_derived.step"
def hr10_refs():
    """I6: external 12-core 7 mm cable from the stub end (front, y = -D/2 - 15) with a gentle curve onto the bench (grommet feet -> bench z = -2),
    ending in the Hirose HR10A-10P-12S(73) female plug lying on the bench (derived model, see ref/make_hr10a_12s.py)."""
    zb = -GROM['flange_t']; rP = 7.35; r = CAB['od']/2
    d = np.array([0.55, -0.835, 0.0]); d /= np.linalg.norm(d)
    p0 = np.array([CAB['x'], -D/2 - 15.0, CAB['zc']]); p1 = np.array([CAB['x'], -D/2 - 45.0, zb + r + 0.6])
    p2 = np.array([CAB['x'] + 16.0, -D/2 - 82.0, zb + r]); p3 = np.array([CAB['x'] + 34.0, -D/2 - 108.0, zb + rP]); p4 = p3 + 8.0*d
    path = Wire([Edge.make_spline([V(p0), V(p1), V(p2), V(p3)], tangents=[V((0, -1, 0)), V(d)]), Edge.make_line(V(p3), V(p4))])
    cab = sweep(Circle(r).moved(Location(Plane(origin=V(p0), z_dir=V((0, -1, 0))).location)).face() if hasattr(Circle(r), 'face') else Circle(r), path=path, transition=Transition.ROUND)
    plug = import_step(HR10_STEP).solids()[0]
    xv = np.cross(-d, [0, 0, 1.0]); O = p4 + 43.0*d
    plug = Plane(origin=V(O), x_dir=V(xv), z_dir=V((0, 0, 1))).location * plug
    HR10_INFO.update(cable_len_outside_mm=round(15.0 + path.length, 1), plug_front=[round(float(v), 1) for v in O], plug_axis=[round(float(v), 3) for v in -d])
    return {"REF_cable_12pin_7mm_external": cab, "REF_HR10A-10P-12S(73)_female_plug": plug}
HR10_INFO = {}
def hardware_refs():
    """I6: 4 rubber grommet feet (ASSUMED geometry), 4 shell screws M2.5x12 from below (head inside the grommet), 4 PCB screws M2.5x12"""
    R = {}; g = s1 = s2 = None
    for sx, sy in SCREWS:
        gg = cylz(sx, sy, GROM['flange_d']/2, -GROM['flange_t'], 0) + cylz(sx, sy, GROM['hip_d']/2, -0.01, GROM['hip_l'])
        gg = gg - cylz(sx, sy, GROM['bore_d']/2, -GROM['flange_t'] - 1, GROM['hip_l'] + 1)
        g = gg if g is None else g + gg
        zf = SHELL['cb_depth']
        sc = cylz(sx, sy, SCR['head_d']/2, zf - SCR['head_h'], zf) + cylz(sx, sy, SCR['d']/2, zf - 0.01, zf + SHELL['L'])
        s1 = sc if s1 is None else s1 + sc
    for hx, hy in HOLES:
        zt = PCB_Z + PCB['t']
        sc = cylz(hx, hy, SCR['head_d']/2, zt, zt + SCR['head_h']) + cylz(hx, hy, SCR['d']/2, zt - PCBS['L'], zt + 0.01)
        s2 = sc if s2 is None else s2 + sc
    R["REF_grommet_foot_x4"] = g; R["REF_screw_M2.5x12_shell_x4"] = s1; R["REF_screw_M2.5x12_PCB_x4"] = s2
    return R
def harness_keepout(c=CLEAR):
    """housing + wires grown by c (for the ceiling-rib cut); housing also gets finger room (+3 in u, open toward the axis)"""
    fx0, fx1 = (6.0, 0.0) if SD > 0 else (0.0, 6.0)            # finger room toward the axis
    k = mod_box(H2['xc'] - DUP['x']/2 - c - fx0, H2['xc'] + DUP['x']/2 + c + fx1, H2['uc'] - DUP['u']/2 - c - 3, H2['uc'] + DUP['u']/2 + c + 3, H2['a0'] - DUP['l'] - c, H2['a0'])
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
    R["REF_display_ESP32-S3-LCD-1.28"] = PIPE_PLANE.location * Compound([disp] + list(vendor_back().solids()))   # I6: real back side from vendor STEP
    R["REF_USB_male_90deg_overmold"] = PIPE_PLANE.location * Box(MALE['w'], MALE['u1'] - MALE['u0'], MALE['a1'] - MALE['a0']).moved(
        Location((0, (MALE['u0'] + MALE['u1'])/2, (MALE['a0'] + MALE['a1'])/2)))
    m = json.load(open("/workspace/psu-tester-case/src/meta_I6.json")); P = [np.array(p) for p in m["path"]]
    P = [p for i, p in enumerate(P) if i == 0 or np.linalg.norm(p - P[i-1]) > 0.3]
    fc = None
    for a, b in zip(P[:-1], P[1:]):
        d = b - a; L = np.linalg.norm(d); ang = math.degrees(math.atan2(d[2], d[1]))
        s = Box(8.5, L + 0.2, 2.0).moved(Location(tuple((a + b)/2), (1, 0, 0), ang))
        fc = s if fc is None else fc + s
    R["REF_USB_flat_cable_51mm"] = fc
    R["REF_USB_female_overmold"] = box((-POCKET['w']/2, D/2 - POCKET['l'], ZF - POCKET['t']/2), (POCKET['w']/2, D/2, ZF + POCKET['t']/2))
    R["REF_cable_12pin_7mm"] = Solid.make_cylinder(CAB['od']/2, 6.0 + D/2 + 15, Plane(origin=(CAB['x'], -D/2 - 15, CAB['zc']), z_dir=(0, 1, 0)))
    R.update(harness_refs()); R.update(hardware_refs()); R.update(hr10_refs())
    return R
if __name__ == "__main__":
    r = retainer_local(); print("retainer valid", r.is_valid, "vol %.3f" % (r.volume/1000))
    for k, v in refs().items(): print(k, v.is_valid, round(v.volume, 1))
