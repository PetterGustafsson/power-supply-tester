"""I7b base (I6 base + I7 real-PCB fixes + I7b central tie station),
I6 base (I2 base + I6 screw columns/grommet counterbores, PCB pilots) as exact build123d B-rep. Matte Charcoal, prints flat on its underside, support-free."""
from common import *
L = LEDGE
TIE = dict(w=3.4, slot_w=3.0, slot_h=1.6, z0=FLOOR - 1.2, band_out=2.5, head_x=5.6, head_y=5.4)   # I7: 2.5 mm tie; floor 2.4 -> 1.2 left under pockets
def flare_profile(hw, ztop, rf, zband):
    """x-z face: strip |x|<=hw up to ztop + concave R rf flares into the band top z=zband (region below band included down to z=-1)"""
    s = Rectangle(2*hw, ztop + 1, align=(Align.CENTER, Align.MIN)).moved(Location((0, -1)))
    for sx in (-1, 1):
        sq = Rectangle(rf, rf + 1, align=(Align.MIN, Align.MIN)).moved(Location((sx*hw if sx > 0 else -hw - rf, zband - 1)))
        dk = Circle(rf).moved(Location((sx*(hw + rf), zband + rf)))
        s = s + (sq - dk)
    s = s + Rectangle(2*(hw + rf + 2), zband + 1, align=(Align.CENTER, Align.MIN)).moved(Location((0, -1)))
    return s
def xz_extrude(face2d, y0, y1):
    """face drawn in (x, z) -> solid spanning y0..y1"""
    pl = Plane(origin=(0, y0, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))       # local y' = world -z? -> check: z_dir=+y, x=+x => local y = z_dir x x_dir = (0,0,-1)?
    return extrude(pl * face2d, amount=y1 - y0)
def XZ(y0): return Plane(origin=(0, y0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))   # local (x, y) -> world (x, z); extrude toward -y
def prism_xz(face2d, y0, y1):
    """extrude an (x,z) sketch between y0 < y1"""
    return extrude(XZ(y1) * face2d, amount=y1 - y0)
def build():
    cx, hw = CAB['x'], CRADLE['w']/2
    sh = rrect_prism(W/2, D/2, RP, 0, ZS)
    sh = chamfer(sh.edges().group_by(Axis.Z)[0], 0.5); sh = chamfer(sh.edges().group_by(Axis.Z)[-1], 0.5)
    b = sh - rrect_prism(W/2 - T, D/2 - T, RP - T, FLOOR, ZS + 1)
    lip = rrect_prism(W/2 - T - 0.25, D/2 - T - 0.25, RP - T - 0.25, 0, ZS + 4) - rrect_prism(W/2 - T - 1.85, D/2 - T - 1.85, RP - T - 1.85, -1, ZS + 5)
    b = b + lip
    for hx, hy in HOLES: b = b + cylz(hx, hy, 3.0, 0, PCB_Z)                           # PCB standoffs
    for sx, sy in SCREWS: b = b + cylz(sx, sy, SHELL['col_r_low'], 0, ZS)              # I6 screw columns (Ø9 round the Ø5.5 counterbore)
    # 12-pin cradle walls with tie-station gaps, bed ridges
    y0, y1 = CRADLE['y0'], CRADLE['y1']
    for sx in (-1, 1):
        wl = box((cx + sx*hw if sx > 0 else cx - hw - CRADLE['wall'], y0 + 0.3, 0), (cx + hw + CRADLE['wall'] if sx > 0 else cx - hw, y1, CRADLE['top']))
        b = b + wl
    k = 0
    while True:
        yc = y0 + 1.25 + 2.5*k
        if yc + 0.35 > y1: break
        b = b + box((cx - hw, yc - 0.35, FLOOR - 0.1), (cx + hw, yc + 0.35, CRADLE['floor'])); k += 1
    # front entry: U-saddle through wall + lip, lip notch for the clamp block, 2 mm entry cone
    zc = CAB['zc']; yw = -D/2 + T + 2.4
    sad = (Cylinder(3.6, 20, rotation=(90, 0, 0)).moved(Location((cx, -D/2 + yw/1 if False else (-D/2 - 5 + yw)/2, zc)))) if False else None
    saddle = Solid.make_cylinder(3.6, yw + D/2 + 5, Plane(origin=(cx, -D/2 - 5, zc), z_dir=(0, 1, 0))) + box((cx - 3.6, -D/2 - 5, zc), (cx + 3.6, yw, 30))
    b = b - saddle
    b = b - box((cx - 7.3, -D/2 + T - 0.1, ZS), (cx + 7.3, -D/2 + T + 2.4, ZS + 5))
    cone = Solid.make_cone(3.6 + 2.0 + 0.6, 3.6 - 0.0, 2.6, Plane(origin=(cx, -D/2 - 0.6, zc), z_dir=(0, 1, 0)))
    b = b - cone
    # I7b: ONE zip-tie station at the middle of the trench (tie7b.py): wall slots at mid-height, inner-wall grooves down to a blind
    # bed pocket under the jacket, blind head pocket right of the +x wall. Floor >= 1.2 everywhere, underside untouched.
    import tie7b
    for c in tie7b.base_cuts(): b = b - c
    # USB-C ledge: keel above a 45 deg line from the board edge + 45 deg flared foot; walls stop at the split ZT (I2)
    FWb, WOb = FW, FW + L['wall']
    fb = ZF - POCKET['t']/2 - POCKET['clr_bed']; yin = D/2 - T - 0.25
    ys = (D/2 - POCKET['l']) - POCKET['clr_side']; yb = PCB_Y + PCB['d']/2 + L['board_clr']; zb = PCB_Z + PCB['t'] + L['board_clr']
    body = box((-WOb, ys - L['stop'], 0), (WOb, yin, ZF + 1.5))
    # forbid zone: y < yb and z < zb + (yb - y): a 45-deg wedge, removed with an (y,z) polygon prism along x
    wedge = Polyline((yb, zb), (yb - 60, zb + 60), (yb - 60, -5), (yb, -5), close=True)
    wedge = extrude(Plane(origin=(-30, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * make_face(wedge), amount=60)
    keel = body - wedge
    flank = extrude(Plane(origin=(0, yb, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0)) * make_face(Polyline((-WOb - 14, 0), (WOb + 14, 0), (WOb, 14), (-WOb, 14), close=True)), amount=yin - yb)
    # Plane above: local y = z_dir x x_dir = (0,1,0)x(1,0,0) = (0,0,-1) -> flip sign of the sketch y
    flank = extrude(Plane(origin=(0, yb, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0)) * make_face(Polyline((-WOb - 14, 0), (WOb + 14, 0), (WOb, -14), (-WOb, -14), close=True)), amount=yin - yb)
    led = keel + flank
    led = led - box((-WOb - 0.6, ys - L['stop'] - 1.5, ZT), (WOb + 0.6, D/2 - T - 0.24, ZF + 8))
    led = led - box((-FWb, ys, fb), (FWb, yin + 1, ZF + 8))
    led = led - box((-L['slot_w']/2, ys - L['stop'] - 1, fb + L['stop_z']), (L['slot_w']/2, ys + 0.1, ZF + 8))
    led = led - box((-(FWb - 1.5), ys + 6, fb - 1.2), (FWb - 1.5, ys + 12, fb + 0.1))
    b = b + led
    # rear tongue: lower half of the socket clamp, R6 flares into the base band
    prof = flare_profile(TW, ZT, TONGUE['r_flare'], ZS)
    tg = prism_xz(prof, D/2 - T - 0.3, D/2) & rrect_prism(W/2, D/2, RP, 0, 60)
    tg = tg - box((-60, -60, -2), (60, 60, FLOOR))          # keep the tray floor as is
    b = b + tg
    # window through the tongue + 1 mm x 45 chamfer at the rear face, pocket opened to the top
    b = b - box((-FW, D/2 - T - 1.2, ZF - FT), (FW, D/2 + 1, ZF + FT)) - box((-FW, D/2 - T - 1.2, fb), (FW, D/2 + 1, ZF + 8))
    ch = extrude(Plane(origin=(0, D/2 + 0.001, ZF), x_dir=(1, 0, 0), z_dir=(0, -1, 0)) * Rectangle(2*(FW + WIN_CH), 2*(FT + WIN_CH)), amount=WIN_CH, taper=45)
    b = b - ch
    # screws: M3 clearance, counterbore 6.4 x 3.2 from below, 10 x 0.8 foot recess; PCB insert holes; lip relief round top bosses
    # I6: no inserts, no foot recess. Lip relief round the top boss, column extended 2.5 above the split (clipped to the lip's outer
    # boundary so it clears the top wall), Ø3.5 clearance, Ø5.5 x 5.8 counterbore from below for the grommet foot; PCB standoffs Ø2.0 pilot x 12
    lipout = rrect_prism(W/2 - T - 0.25, D/2 - T - 0.25, RP - T - 0.25, ZS - 0.1, SHELL['col_top'] + 0.1)
    for sx, sy in SCREWS:
        b = b - cylz(sx, sy, 4.0, ZS, ZS + 5)
        b = b + (cylz(sx, sy, SHELL['col_r_up'], ZS - 0.05, SHELL['col_top']) & lipout)
        b = b - cylz(sx, sy, SHELL['clear_d']/2, -1, SHELL['col_top'] + 1) - cylz(sx, sy, SHELL['cb_d']/2, -1, SHELL['cb_depth'])
    for hx, hy in HOLES: b = b - cylz(hx, hy, PCBS['pilot_d']/2, PCB_Z - PCBS['pilot_depth'], PCB_Z + 1)
    return b
if __name__ == "__main__":
    import time; t = time.time(); b = build()
    print("base valid", b.is_valid, "solids", len(b.solids()), "vol %.2f cm3" % (b.volume/1000), "t %.1f" % (time.time() - t))
    bb = b.bounding_box(); print(bb.min, bb.max)
    pass  # exports live in build_all.py
