"""I7b zip-tie station: ONE tie at the middle of the 12-pin trench (y = midpoint of the cradle walls), slots at mid-height of the walls.
Loop (x-z at y = TY): head on the tray floor right of the +x wall -> through the +x wall slot -> down an inner-wall groove -> under the
jacket in a blind bed pocket -> up the -x groove -> out the -x slot -> up the -x outer face -> over the jacket top -> down beside the +x
wall into the head. Floor under every pocket >= 1.2 mm; nothing penetrates the underside."""
import math, numpy as np
from common import *
CX, HW, WALL = CAB['x'], CRADLE['w']/2, CRADLE['wall']
XO = HW + WALL                                           # wall outer face |x| (5.65)
TY = round(((CRADLE['y0'] + 0.3) + CRADLE['y1'])/2, 3)   # trench middle (walls y -45.3 .. 8.0) -> -18.65
ZSL = (FLOOR + CRADLE['top'])/2                          # wall mid-height above the tray floor (2.4 .. 8.0) -> 5.2
TIE = dict(band_w=2.5, band_t=1.0, slot_w=3.0, slot_h=1.6, groove_d=1.2, pocket_w=3.4, z0=FLOOR - 1.2,
           head_x=5.6, head_y=5.4, head_h=4.0, head_gap=1.25)
SLOT_Z = (ZSL - TIE['slot_h']/2, ZSL + TIE['slot_h']/2)  # 4.4 .. 6.0
HEAD_X = (XO + TIE['head_gap'], XO + TIE['head_gap'] + TIE['head_x'])   # 6.9 .. 12.5
ZB = ZSL - 0.25                                          # band centre height through the slots (4.95)
def band_centreline(n_arc=24):
    """(x, z) centreline of the band, head -> loop -> head"""
    t, r = TIE['band_t'], CAB['od']/2 + TIE['band_t']/2 + 0.05
    xg = CX + HW + TIE['groove_d'] - t/2                 # band centre in the groove (4.35)
    zb = TIE['z0'] + 0.05 + t/2                          # band centre in the bed pocket (1.75)
    P = [(HEAD_X[0], ZB), (xg, ZB), (xg, zb), (-xg, zb), (-xg, ZB), (-(XO + t/2), ZB), (-(XO + t/2), CRADLE['top'] + 0.5), (-(XO - 0.3), CRADLE['top'] + 0.6)]
    a0, a1 = math.radians(140), math.radians(40)
    for k in range(n_arc + 1):
        a = a0 + (a1 - a0)*k/n_arc; P.append((CX + r*math.cos(a), CAB['zc'] + r*math.sin(a)))
    xt = HEAD_X[0] + 0.6
    P += [(XO, CRADLE['top'] + 0.6), (xt, CRADLE['top'] - 0.4), (xt, FLOOR + TIE['head_h'] - 0.8)]
    return P
def base_cuts():
    """solids to subtract from the base"""
    from build123d import Box as _B
    S = []
    w, gz = TIE['slot_w'], SLOT_Z
    S.append(box((CX - XO - 0.1, TY - w/2, gz[0]), (CX + XO + 0.1, TY + w/2, gz[1])))                                          # wall slots (both walls)
    for sx in (-1, 1):                                                                                                       # inner-wall grooves
        x0, x1 = (CX + HW - 0.05, CX + HW + TIE['groove_d']) if sx > 0 else (CX - HW - TIE['groove_d'], CX - HW + 0.05)
        S.append(box((x0, TY - w/2, TIE['z0']), (x1, TY + w/2, gz[1])))
    S.append(box((CX - HW - 0.05, TY - TIE['pocket_w']/2, TIE['z0']), (CX + HW + 0.05, TY + TIE['pocket_w']/2, CRADLE['floor'] + 0.01)))   # blind bed pocket
    S.append(box((HEAD_X[0] - 0.2, TY - TIE['head_y']/2 - 0.2, TIE['z0']), (HEAD_X[1] + 0.2, TY + TIE['head_y']/2 + 0.2, FLOOR + 0.01)))    # blind head pocket
    return S
def tie_solid():
    from build123d import Polyline, offset, make_face, extrude, Plane, Wire
    P = band_centreline()
    pts = [(x, 0.0, z) for x, z in P]
    import numpy as _n
    # band = union of boxes along the centreline segments (robust), + head
    s = None
    for (xa, za), (xb, zb) in zip(P[:-1], P[1:]):
        L = math.hypot(xb - xa, zb - za)
        if L < 1e-6: continue
        ang = math.degrees(math.atan2(zb - za, xb - xa))
        b = Box(L + TIE['band_t'] - 0.02, TIE['band_w'], TIE['band_t']).rotate(Axis.Y, -ang).moved(Location(((xa + xb)/2, TY, (za + zb)/2)))
        s = b if s is None else s + b
    head = box((HEAD_X[0], TY - TIE['head_y']/2 + 0.2, TIE['z0'] + 0.05), (HEAD_X[1] - 0.2, TY + TIE['head_y']/2 - 0.2, TIE['z0'] + 0.05 + TIE['head_h']))
    return s + head
