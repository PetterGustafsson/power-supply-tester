"""I6 top shell (= I4 + harness keep-out in the ceiling ribs; outer skin and 2.0 wall unchanged): exact B-rep outer (top_outer.py) hollowed with an explicit cavity + all internals.
Module loads from INSIDE (the USB tab, r 21.1, is wider than the 36.7 bore and the 38.4 pipe), glass rim stops on the crown spigot;
held from behind by the press-in retainer ring (retainer.py)."""
from common import *
import top_outer, base as BASE, time
import parts as PARTS
RIB = dict(t=1.6, depth=6.0, xs=(-39.0, -21.0, 21.0, 39.0), ys=(-30.0, -12.0, 6.0, 24.0))
def tab_channel():
    return mod_box(-(TAB['w']/2 + 0.4), TAB['w']/2 + 0.4, -(TAB['u_out'] + 0.5), -(BORE - 3.0), -60.0, TAB['a1'] + 0.15)
def plug_window():
    return mod_box(-(MALE['w']/2 + 0.3), MALE['w']/2 + 0.3, MALE['u0'] - 6.5, MALE['u1'] + 0.3, MALE['a0'] - 0.3, MALE['a1'] + 0.3)
def bore():
    b = cyl_axis(G, AF, BORE, -60.0, PIPE_END + 3.0)
    return b & rrect_prism(W/2 - T, D/2 - T, RP - T, 0, 200)
def cavity():
    bi = rrect_prism(W/2 - T, D/2 - T, RP - T, 0, HI - T)
    bi = fillet(bi.edges().group_by(Axis.Z)[-1], 1.6)
    bt = math.radians(TUN['beta']); dirv = np.array([0, math.cos(bt), -math.sin(bt)])
    A0 = np.array([0.0, TUN['y_top'], TUN['z_top'] - top_outer.TZ_DROP - TUN['r']/math.cos(bt)])
    ti = cyl_axis(A0, dirv, TUN['r'] - T, -40.0, 45.0)
    ti = ti & (PIPE_PLANE.location * Box(200, 200, 200).moved(Location((0, 0, top_outer.A_CUT - 100)))) & rrect_prism(W/2 - T, D/2 - T, RP - T, 0, 200)
    return bi + ti + bore()
def ceiling_ribs():
    z0, z1 = HI - T - RIB['depth'], HI - T + 0.5
    r = None
    for x in RIB['xs']:
        s = box((x - RIB['t']/2, -D/2, z0), (x + RIB['t']/2, D/2, z1)); r = s if r is None else r + s
    for y in RIB['ys']:
        r = r + box((-W/2, y - RIB['t']/2, z0), (W/2, y + RIB['t']/2, z1))
    r = r & rrect_prism(W/2 - T + 0.2, D/2 - T + 0.2, RP - T, 0, 200)
    # keep-outs: module + plug + flat cable + socket pad zone, with 1 mm clearance
    ko = cyl_axis(G, AF, BORE + 1.0, -60.0, 5.0) + mod_box(-(MALE['w']/2 + 1.3), MALE['w']/2 + 1.3, MALE['u0'] - 7.5, MALE['u1'] + 1.3, MALE['a0'] - 1.3, MALE['a1'] + 1.3) \
        + tab_channel() + box((-(FW + LEDGE['wall'] + 1), D/2 - POCKET['l'] - 1, 0), ((FW + LEDGE['wall'] + 1), D/2, 60))
    r = r - ko
    for k in PARTS.harness_keepout(): r = r - k          # I6: Dupont housing + 5 leads to J4, 1.0 mm clear (+ finger room)
    return r
def build(verbose=True):
    t0 = time.time()
    out = top_outer.build(verbose=False)
    s = out - cavity()
    if verbose: print("shell ok %.1f" % (time.time() - t0), s.is_valid)
    # bosses (M3 heat-set, hole 4.0 x 7)
    for sx, sy in SCREWS: s = s + (cylz(sx, sy, SHELL['boss_r'], SHELL['boss_z0'], HI - 1) & out)     # I6: boss starts above the extended base column
    # 12-pin clamp block with the arched tunnel (0.3 squeeze on the 7 mm jacket) and the chamfered entry
    cx, zc = CAB['x'], CAB['zc']
    s = s + (box((cx - 7.0, -D/2 + 1.0, ZS + GAP), (cx + 7.0, -D/2 + T + 5.0, CRADLE['top'] + 5.0)) & out)
    arch = box((cx - (CRADLE['w']/2 + CRADLE['wall'] + 0.3), -D/2 + T, 0), (cx + (CRADLE['w']/2 + CRADLE['wall'] + 0.3), -D/2 + T + 5.5, CRADLE['top'] + 0.3)) \
        + Solid.make_cylinder(3.2, 5.5, Plane(origin=(cx, -D/2 + T, zc), z_dir=(0, 1, 0)))
    s = s - arch
    s = s - Solid.make_cylinder(3.6, T + 1.2, Plane(origin=(cx, -D/2 - 1, zc), z_dir=(0, 1, 0)))
    s = s - Solid.make_cone(3.6 + 2.6, 3.6, 2.6, Plane(origin=(cx, -D/2 - 0.6, zc), z_dir=(0, 1, 0)))
    # USB socket: pad from the ceiling, pocket roof (upper half), skirts, crush ribs
    fw, wo = FW, FW + LEDGE['wall']
    pad = box((-wo, D/2 - POCKET['l'] + 0.2, ZF + POCKET['t']/2 - 0.15), (wo, D/2 - T + 0.1, HI - 1)) & out
    s = s + pad
    y0, y1 = D/2 - POCKET['l'] + 0.2, D/2 - T + 0.1
    s = s - box((-fw, y0 - 0.5, ZT), (fw, y1, ROOF_Z))
    for sx in (-1, 1):
        sk = box((min(sx*wo, sx*fw), y0, ZT + TONGUE['gap']), (max(sx*wo, sx*fw), y1, ROOF_Z + 1)) & out
        s = s + sk
    if POCKET['shim'] <= 0:
        for ry in POCKET['ribs']:
            s = s + box((-fw + 0.6, ry - POCKET['rib_w']/2, RIB_Z), (fw - 0.6, ry + POCKET['rib_w']/2, ROOF_Z + 0.2))
    # ceiling ribs
    s = s + ceiling_ribs()
    if verbose: print("internals ok %.1f" % (time.time() - t0))
    # tongue notch (0.5 gap), rear window + chamfer
    prof = BASE.flare_profile(TW + TONGUE['gap'], ZT + TONGUE['gap'], TONGUE['r_flare'] - TONGUE['gap'], ZS + TONGUE['gap'])
    s = s - BASE.prism_xz(prof, D/2 - T - 0.3, D/2 + 1)
    s = s - box((-FW, D/2 - T - 1.2, ZF - FT), (FW, D/2 + 1, ZF + FT))
    s = s - extrude(Plane(origin=(0, D/2 + 0.001, ZF), x_dir=(1, 0, 0), z_dir=(0, -1, 0)) * Rectangle(2*(FW + WIN_CH), 2*(FT + WIN_CH)), amount=WIN_CH, taper=45)
    # module: tab channel + plug window (bore is in the cavity)
    s = s - tab_channel() - plug_window()
    # boss holes
    for sx, sy in SCREWS: s = s - cylz(sx, sy, SHELL['pilot_d']/2, SHELL['boss_z0'] - 1, SHELL['boss_z0'] + SHELL['pilot_depth'])   # I6: Ø2.0 pilot, no insert
    # deck details: thumb dish (rear right); I6: vents removed
    # I6: 6x6 vent field removed (Petter: no extra airflow needed) -> solid deck
    s = s - Sphere(40).moved(Location((41.5, 30.0, HI + 40 - 1.0)))
    if verbose: print("cuts ok %.1f" % (time.time() - t0))
    return s, out
if __name__ == "__main__":
    s, out = build()
    print("top valid", s.is_valid, "solids", len(s.solids()), "vol %.2f cm3" % (s.volume/1000))
    pass  # exports live in build_all.py
    pass  # exports live in build_all.py
