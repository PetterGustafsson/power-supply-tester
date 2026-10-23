"""Knolling layout for I5: orient every part for viewing, build simple hardware/flat-lay cable meshes, place on a grid, write placed STLs + items.json"""
import sys, json, numpy as np, trimesh
sys.path.insert(0, "/workspace/psu-tester-case/src")
from i7_params import *
from h2_params import CAB
ST = "/workspace/psu-tester-case/cad_I7/stl"; OUTD = "/workspace/psu-tester-case/layout_I7/mesh_wes"
import os; os.makedirs(OUTD, exist_ok=True)
L = lambda f: trimesh.load(f"{ST}/{f}")
def rot(m, ax, deg):
    m = m.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), ax)); return m
def boxm(sx, sy, sz, c=(0, 0, 0)):
    b = trimesh.creation.box((sx, sy, sz)); b.apply_translation(c); return b
def cyl(r, h, c=(0, 0, 0), ax=None, sec=48):
    m = trimesh.creation.cylinder(r, h, sections=sec)
    if ax == 'x': m = rot(m, [0, 1, 0], 90)
    if ax == 'y': m = rot(m, [1, 0, 0], 90)
    m.apply_translation(c); return m
def ring(ro, ri, h, c=(0, 0, 0)):
    m = trimesh.creation.annulus(ri, ro, h, sections=48); m.apply_translation(c); return m
IV, CH, YE = "E3DED0", "2A2A2C", "FF6A13"
# module frame -> local (glass up)
X = np.array([1.0, 0, 0]); Rm = np.array([X, UF, AF])           # rows
Tm = np.eye(4); Tm[:3, :3] = Rm; Tm[:3, 3] = -Rm @ np.array(G)
disp = [trimesh.load(f"{ST}/render/display_{n}.stl") for n in ("PCB", "LCM", "parts")]
for _d in disp: _d.apply_transform(Tm)
crown = rot(L("I7_crown_print.stl"), [1, 0, 0], 180)
items = []
def item(name, parts, label, row):
    items.append(dict(name=name, parts=parts, label=label, row=row))
item("top", [(L("I7_top_world.stl"), IV, 0.55, 0)], "Top shell  x1\nPLA Matte Ivory White", 0)
item("base", [(L("I7_base_world.stl"), CH, 0.6, 0)], "Base  x1\nPLA Matte Charcoal", 0)
import glob as _g
RD = f"{ST}/render"
PCOL = dict(dark=("161616", 0.45, 0), metal=("C8C8C8", 0.25, 1), green=("0E6A2A", 0.42, 0), white=("EFEDE2", 0.5, 0), brown=("6B4A3A", 0.5, 0))
pcb = [(L("REF_PCB_RevD2_board.stl"), "0E0F10", 0.32, 0), (trimesh.load(f"{RD}/PCB_silk.stl"), "EDEDE6", 0.6, 0), (trimesh.load(f"{RD}/PCB_pads.stl"), "C9C9C4", 0.25, 1)] + \
      [(trimesh.load(f), *PCOL[f.split("__")[1][:-4]]) for f in sorted(_g.glob(f"{RD}/REF_PCB_*__*.stl"))]
item("pcba", pcb, "Rev D2 PCBA  x1 (KiCad model)\nJ1-J3 3.5 mm terminals, J4 JST-XH5", 0)
item("display", [(disp[0], "1B2238", 0.4, 0), (disp[1], "07080A", 0.22, 0), (disp[2], "2A2A2E", 0.4, 0)], "Display module  x1\nWaveshare ESP32-S3-LCD-1.28", 1)
item("crown", [(crown, YE, 0.45, 0)], "Crown  x1\nPLA Basic Orange", 1)
item("retainer", [(L("I7_retainer_print.stl"), CH, 0.6, 0)], "Retainer sleeve  x1\nPLA Matte Charcoal", 1)
# USB-C 90 deg extender, laid flat: male (90 deg) - 51 mm flat cable - female
# I6 fix (Petter): 90 deg plug bends the other way relative to the flat cable -> tip points DOWN (to the table side of the ribbon);
# the male end rests on its tip, the ribbon leaves the overmold underside and drops to the table
# I7 wes: extender turned over (belly <-> back) vs the I6/I7 layout: overmold lies on the table, plug tip points UP,
# ribbon leaves the overmold near its (now upper) tip side and drops to the table
from shapely.geometry import Point as _P2, box as _bx
def stadium(w, h): return _bx(-(w - h)/2, -1e-3, (w - h)/2, 1e-3).buffer(h/2, 16)
H = 6.5; MH = 9.0
male = boxm(16, 12, MH, (0, 0, MH/2))
tip = trimesh.creation.extrude_polygon(stadium(8.25, 2.45), H); tip = rot(tip, [0, 0, 1], 90); tip.apply_translation((-5.2, 0, MH))
hole = trimesh.creation.extrude_polygon(stadium(7.0, 1.3), 0.05); hole = rot(hole, [0, 0, 1], 90); hole.apply_translation((-5.2, 0, MH + H))
tong = boxm(0.6, 5.6, 0.06, (-5.2, 0, MH + H + 0.06))
x0, x1 = 8.0, 20.0; zt = MH - 1.0; ang = np.degrees(np.arctan2(zt, x1 - x0)); Ls = np.hypot(zt, x1 - x0)
slope = rot(boxm(Ls + 0.6, 8.5, 1.0), [0, 1, 0], ang); slope.apply_translation(((x0 + x1)/2, 0, zt/2 + 0.5))
flat = trimesh.util.concatenate([slope, boxm(51 - Ls, 8.5, 1.0, (x1 + (51 - Ls)/2, 0, 0.5))])
xe = x1 + 51 - Ls
fem = boxm(20, 12.5, 6.5, (xe + 10, 0, 3.25)); femh = boxm(0.6, 8.6, 2.8, (xe + 20.2, 0, 3.25))
item("usb", [(male, "1A1A1A", 0.4, 0), (tip, "C8C8C8", 0.25, 1), (hole, "0A0A0A", 0.6, 0), (tong, "2A2A2A", 0.5, 0), (flat, "2B2B2B", 0.5, 0), (fem, "1A1A1A", 0.4, 0), (femh, "6A6A6A", 0.3, 1)],
     "USB-C 90° extender  x1\nmale + 51 mm flat cable + female (turned over)", 1)
# I6: 12-core 7 mm cable with the Hirose HR10A-10P-12S(73) female plug (derived model, ref/HR10A-10P-12S73_derived.step) lying on the table
rc = CAB['od']/2; RP10 = 7.35
plug = trimesh.load("/workspace/psu-tester-case/layout_I7/hr10_local.stl"); plug = rot(plug, [0, 0, 1], -90)   # local +y (front->rear) -> +x
plug.apply_translation((0, 0, RP10))
xs, xr = 43.0, 43.0 + 16.0; ang = np.degrees(np.arctan2(RP10 - rc, xr - xs)); Lr = np.hypot(RP10 - rc, xr - xs)
rise = rot(cyl(rc, Lr + 1.0, (0, 0, 0), 'x'), [0, 1, 0], ang); rise.apply_translation(((xs + xr)/2, 0, (RP10 + rc)/2))
CL = 95.0; cab = cyl(rc, CL, (xr + CL/2, 0, rc), 'x')
from shapely.geometry import Point as _Pt
WC12 = ["C0392B", "1A1A1A", "E67E22", "F1C40F", "27AE60", "2980B9", "8E44AD", "7F8C8D", "ECF0F1", "8B4513", "E91E63", "16A085"]
xj = xr + CL; fan = []; rw = 0.7
for i in range(12):
    yo = (i - 5.5)*3.8; t = np.linspace(0, 1, 40)
    P0, P1, P2, P3 = np.array([xj, (i % 4 - 1.5)*1.2, rw]), np.array([xj + 14, (i % 4 - 1.5)*1.2, rw]), np.array([xj + 22, yo, rw]), np.array([xj + 40, yo, rw])
    pts = ((1 - t)**3)[:, None]*P0 + (3*(1 - t)**2*t)[:, None]*P1 + (3*(1 - t)*t**2)[:, None]*P2 + (t**3)[:, None]*P3
    w = trimesh.creation.sweep_polygon(_Pt(0, 0).buffer(rw, 8), pts)
    col = cyl(1.3, 4.5, (xj + 40 + 2.25, yo, 1.3), 'x', 24); fl = cyl(1.5, 1.5, (xj + 40 - 0.0, yo, 1.5), 'x', 24); pin = cyl(0.55, 8.0, (xj + 46 + 4.0, yo, 1.3), 'x', 16)
    fan += [(w, WC12[i], 0.45, 0), (col, "1E9E3A", 0.38, 0), (fl, "1E9E3A", 0.38, 0), (pin, "DADADA", 0.22, 1)]
item("cab12", [(plug, "C9CCD1", 0.28, 1), (rise, "111111", 0.5, 0), (cab, "111111", 0.5, 0)] + fan,
     "HR10A-10P-12S(73) female plug x1\n7 mm 12-core cable, 12 ferrules 0.314\" (green)", 2)
# 1x5 Dupont lead -> JST-XH5, flat
# I7: JST-XH5 -> 5 single round 1-pin housings d1.2 (H2 pins 1,3,4,5,7 are not one 1x5 row), 28 AWG
from shapely.geometry import Point as _Pt
xh = boxm(9, 13.0, 5.8, (90 - 4.5, 0, 2.9)); WC = ["C0392B", "1A1A1A", "E67E22", "2980B9", "F1C40F"]; hl = []
for i in range(5):
    y0, y1 = (i - 2)*4.0, (i - 2)*2.5; t = np.linspace(0, 1, 30)
    P0, P1, P2, P3 = np.array([12.0, y0, 0.6]), np.array([30.0, y0, 0.6]), np.array([50.0, y1, 0.6]), np.array([81.0, y1, 0.6])
    pts = ((1 - t)**3)[:, None]*P0 + (3*(1 - t)**2*t)[:, None]*P1 + (3*(1 - t)*t**2)[:, None]*P2 + (t**3)[:, None]*P3
    hl += [(trimesh.creation.sweep_polygon(_Pt(0, 0).buffer(0.4, 8), pts), WC[i], 0.4, 0), (cyl(0.6, 12.0, (6.0, y0, 0.6), 'x', 24), "141414", 0.45, 0),
           (boxm(8.5, 0.64, 0.64, (-0.25 + 0.0, y0, 0.6)), "D4AF37", 0.25, 1)]
item("lead", [(xh, "F2F0E6", 0.5, 0)] + hl, "JST-XH5 to 5 single 1-pin leads  x1\nround housings d1.2 on H2.1/.3/.4/.5/.7", 3)
# hardware (I6): 8x M2.5 x 12 plastic flat/pan-head screws (4 shell + 4 PCB), 4 rubber grommet feet, 2 zip ties. No inserts.
from i7_params import GROM, SCR, SHELL
def m25screw(c, L=12.0):
    return [cyl(1.25, L, (c[0] + SCR['head_h'] + L/2, c[1], 2.25), 'x', 24), cyl(SCR['head_d']/2, SCR['head_h'], (c[0] + SCR['head_h']/2, c[1], 2.25), 'x', 32)]
hw = []
for i in range(8): hw += [(m, "2B2B2E", 0.55, 0) for m in m25screw(((i % 2)*18, (i//2)*7))]
item("m25s", hw, "M2.5x12 plastic flat-head screw  x8\n4 shell (into top bosses) + 4 PCB", 3)
hw = []
for i in range(4):
    c = ((i % 2)*13, (i//2)*13)
    g = trimesh.boolean.difference([trimesh.util.concatenate([cyl(GROM['flange_d']/2, GROM['flange_t'], (c[0], c[1], GROM['flange_t']/2)),
                                    cyl(GROM['hip_d']/2, GROM['hip_l'], (c[0], c[1], GROM['flange_t'] + GROM['hip_l']/2 - 0.01))]),
                                    cyl(GROM['bore_d']/2, 20, (c[0], c[1], 5))], engine="manifold") if False else None
    hw += [(ring(GROM['flange_d']/2, GROM['bore_d']/2, GROM['flange_t'], (c[0], c[1], GROM['flange_t']/2)), "1C1C1C", 0.85, 0),
           (ring(GROM['hip_d']/2, GROM['bore_d']/2, GROM['hip_l'], (c[0], c[1], GROM['flange_t'] + GROM['hip_l']/2)), "1C1C1C", 0.85, 0)]
item("grom", hw, "Rubber grommet foot  x4\nhip d5.5 x 8.0, flange d9.5 x 2", 3)
hw = []
for i in range(2):
    hw += [(boxm(100, 2.5, 1.1, (50 + 3, i*10, 0.55)), "F4F4F0", 0.5, 0), (boxm(5, 4.5, 4.0, (0, i*10, 2.0)), "F4F4F0", 0.5, 0)]
item("ties", hw, "Zip tie  x2\n2.5 mm", 3)
# layout: rows (back -> front), even gaps
GAP, RGAP = 18.0, 34.0
rows = {}
for it in items:
    m = trimesh.util.concatenate([p[0] for p in it["parts"]]); b = m.bounds
    it["size"] = (b[1] - b[0]).tolist(); it["b0"] = b[0].tolist(); rows.setdefault(it["row"], []).append(it)
for r in rows:
    for i in rows[r]:
        ls = i["label"].split("\n"); i["w"] = max(i["size"][0], max(0.62*6.0*len(ls[0]), 0.58*4.8*max([len(t) for t in ls[1:]] or [0])))
CW = max(i["w"] for r in rows if len(rows[r]) > 1 for i in rows[r])
y = 0.0; out = []
for r in sorted(rows):
    its = rows[r]; depth = max(i["size"][1] for i in its)
    cw = CW if len(its) > 1 else its[0]["w"]
    for i in its: i["w"] = cw
    width = sum(i["w"] for i in its) + GAP*(len(its) - 1)
    x = -width/2
    for it in its:
        sx, sy, sz = it["size"]; cx = x + it["w"]/2; cy = y - depth/2
        sh = np.array([cx - (it["b0"][0] + sx/2), cy - (it["b0"][1] + sy/2), -it["b0"][2]])
        files = []
        for k, (m, col, rough, met) in enumerate(it["parts"]):
            mm = m.copy(); mm.apply_translation(sh); f = f"{OUTD}/{it['name']}_{k}.stl"; mm.export(f); files.append(dict(f=f, col=col, rough=rough, metal=met))
        out.append(dict(name=it["name"], label=it["label"], parts=files, center=[cx, cy], label_xy=[cx, y - depth - 5.0], size=it["size"]))
        x += it["w"] + GAP
    y -= depth + RGAP + 10
allb = np.array([[o["center"][0] - o["size"][0]/2 - 25, o["label_xy"][1] - 10, o["center"][0] + o["size"][0]/2 + 25, o["center"][1] + o["size"][1]/2] for o in out])
ext = [allb[:, 0].min(), allb[:, 1].min(), allb[:, 2].max(), allb[:, 3].max()]
json.dump(dict(items=out, extent=ext), open("/workspace/psu-tester-case/layout_I7/items_wes.json", "w"), indent=1)
for o in out: print(o["name"], np.round(o["size"], 1), np.round(o["center"], 1))
print("extent", np.round(ext, 1))
