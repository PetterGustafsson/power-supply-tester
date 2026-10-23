"""I9: single straight pipe (no trailing tunnel), rounded root. I6 top shell (= I4 + harness keep-out in the ceiling ribs; outer skin and 2.0 wall unchanged): exact B-rep outer (top_outer.py) hollowed with an explicit cavity + all internals.
Module loads from INSIDE (the USB tab, r 21.1, is wider than the 36.7 bore and the 38.4 pipe), glass rim stops on the crown spigot;
held from behind by the press-in retainer ring (retainer.py)."""
from common import *
import top_outer, base as BASE, time
import parts as PARTS
RIB = dict(t=1.6, depth=6.0, run=6.0, n=8, phi0=22.5, collar_w=2.0, collar_h=2.0)   # I8: ring of radial gussets round the pipe root (was the 4x4 grid)
_MO = None
def module_outline():
    """I7: real PCB + LCM outline (vendor STEP sections, module frame x,u) grown by MOD_OUTLINE_CLR"""
    global _MO
    if _MO is None:
        s = import_step(VENDOR_STEP); big = sorted(s.solids(), key=lambda x: -x.volume)[:2]
        f = [(b & Box(80, 80, 0.01).moved(Location((0, 0, z)))).faces()[0] for b, z in zip(big, (-2.6, -0.85))]
        fs = [Face(ff.outer_wire()).moved(Location((0, 0, -ff.center().Z))) for ff in f]
        u = fs[0].fuse(fs[1]).clean().faces()[0]
        _MO = offset(u, MOD_OUTLINE_CLR, kind=Kind.INTERSECTION)
    return _MO
def tab_channel():
    """I7: real outline: tab region (u < -12) open back to a = -60 for loading from inside, full outline as a local seat a -3.6..+0.15;
    plus the I6 rectangular channel (USB-C receptacle + tab parts)"""
    o = module_outline()
    pr = extrude(o, amount=60.15).moved(Location((0, 0, -60.0)))
    tab = pr & Box(80, 40, 200, align=(Align.CENTER, Align.MAX, Align.CENTER)).moved(Location((0, -12.0, 0)))
    seat = extrude(o, amount=3.75).moved(Location((0, 0, -3.6)))
    rect = mod_box(-(TAB['w']/2 + 0.4), TAB['w']/2 + 0.4, -(TAB['u_out'] + 0.5), -(BORE - 3.0), -60.0, TAB['a1'] + 0.15)
    return PIPE_PLANE.location * (tab + seat) + rect
def plug_window():
    return mod_box(-(MALE['w']/2 + 0.3), MALE['w']/2 + 0.3, MALE['u0'] - 6.5, MALE['u1'] + 0.3, MALE['a0'] - 0.3, MALE['a1'] + 0.3)
def bore():
    b = cyl_axis(G, AF, BORE, -60.0, PIPE_END + 3.0)
    return b & rrect_prism(W/2 - T, D/2 - T, RP - T, 0, 200)
def cavity():
    bi = rrect_prism(W/2 - T, D/2 - T, RP - T, 0, HI - T)
    bi = fillet(bi.edges().group_by(Axis.Z)[-1], 1.6)
    # I9: trailing tunnel removed (outer and cavity) -> flat ceiling behind the pipe
    return bi + bore()
def _ko_ellipse(z):
    """horizontal section of the loading-path keep-out cylinder (BORE + 1 about G/AF) at height z: centre y, semi-axes x, y"""
    a = (z - G[2])/AF[2]
    return G[1] + AF[1]*a, BORE + 1.0, (BORE + 1.0)/AF[2]
def _ray_ellipse(cy0, cy, ax, ay, phi):
    """distance from (0, cy0) along (cos phi, sin phi) to the ellipse centred (0, cy) with semi-axes ax, ay (ray starts inside)"""
    c, s_ = math.cos(phi), math.sin(phi); dy = cy0 - cy
    A = c*c/ax**2 + s_*s_/ay**2; B = 2*s_*dy/ay**2; C = dy*dy/ay**2 - 1
    return (-B + math.sqrt(B*B - 4*A*C))/(2*A)
def ring_ribs(info=None):
    """I8 (Petter: 'keep only a ring of ribs around the pipe'): RIB['n'] radial gussets t 1.6 hanging from the deck underside round the
    pipe root, RIB['depth'] deep at the root and running out to 0 over RIB['run'] (45 deg underside -> no support when printed deck-up),
    plus a 45 deg fillet collar (collar_w x collar_h) round the root. The root follows the loading-path keep-out (BORE + 1), evaluated
    at the rib's full depth, so the rib keeps its full depth on the back side where the tilted path sweeps outward."""
    zc = HI - T; h0, L, t = RIB['depth'], RIB['run'], RIB['t']
    cy0, ax0, ay0 = _ko_ellipse(zc)
    r = None; meta = []
    for k in range(RIB['n']):
        phi = math.radians(RIB['phi0'] + 360.0*k/RIB['n'])
        d = np.array([math.cos(phi), math.sin(phi), 0.0]); n = np.array([-math.sin(phi), math.cos(phi), 0.0])
        s_top = _ray_ellipse(cy0, cy0, ax0, ay0, phi)
        cyh, axh, ayh = _ko_ellipse(zc - h0)
        s0 = max(s_top, _ray_ellipse(cy0, cyh, axh, ayh, phi))
        o = np.array([0.0, cy0, zc]) - n*t/2
        pl = Plane(origin=V(o), x_dir=V(d), z_dir=V(n))          # local y = -world z
        pts = [(s_top - 0.6, -0.5), (s0 + L, -0.5), (s0 + L, 0.0), (s0, h0), (s0 - 0.6, h0)]
        rib = extrude(pl * Polygon(*pts, align=None), amount=t)
        r = rib if r is None else r + rib
        meta.append(dict(phi=round(math.degrees(phi), 1), root_s=round(s0, 2), root_xy=[round(float(x), 2) for x in (np.array([0, cy0]) + d[:2]*s0)]))
    # collar: loft of keep-out-offset ellipses (outer edge 45 deg)
    w, hc = RIB['collar_w'], RIB['collar_h']
    e = []
    for z, grow in ((zc - hc, 0.0), (zc, w), (zc + 0.5, w + 0.5)):
        cy, ax, ay = _ko_ellipse(z)
        e.append(Plane(origin=(0, cy, z)) * Ellipse(ax + grow, ay + grow))
    collar = Solid.make_loft([x.faces()[0].outer_wire() for x in e], ruled=True)
    r = r + collar
    r = r & rrect_prism(W/2 - T + 0.2, D/2 - T + 0.2, RP - T, 0, 200)
    # keep-outs (same as the I7 grid): loading path BORE + 1 to a = -60, plug + flat cable, tab channel, socket pad zone, harness
    ko = cyl_axis(G, AF, BORE + 1.0, -60.0, 5.0) + mod_box(-(MALE['w']/2 + 1.3), MALE['w']/2 + 1.3, MALE['u0'] - 7.5, MALE['u1'] + 1.3, MALE['a0'] - 1.3, MALE['a1'] + 1.3) \
        + tab_channel() + box((-(FW + LEDGE['wall'] + 1), D/2 - POCKET['l'] - 1, 0), ((FW + LEDGE['wall'] + 1), D/2, 60))
    r = r - ko
    tc = tab_channel()                                   # I8: tab path grown ~0.8 mm (4 shifted copies) -> ribs/collar >= 1.0 mm from the tab outline
    for dv in (XV, -np.array(XV), UF, -np.array(UF)): r = r - tc.moved(Location(tuple(0.8*np.array(dv, float))))
    for kk in PARTS.harness_keepout(): r = r - kk
    if info is not None: info.update(ribs=meta, deck_underside_z=zc, root_centre_y=round(float(cy0), 3))
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
    # I8: ring ribs round the pipe root (4x4 ceiling grid removed)
    s = s + ring_ribs()
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
