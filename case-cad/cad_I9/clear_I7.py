"""I7 mesh clearance check (python-fcl BVH on the exported STLs): real PCBA, conductors/ferrules, 1-pin housings, real display module."""
import trimesh, fcl, numpy as np, json, glob, os, itertools, sys
ST = "/workspace/psu-tester-case/cad_I9/stl"
M = {os.path.basename(f)[:-4]: trimesh.load(f) for f in glob.glob(f"{ST}/*.stl") + glob.glob(f"{ST}/render/display_*.stl")}
def obj(m):
    b = fcl.BVHModel(); b.beginModel(len(m.vertices), len(m.faces)); b.addSubModel(m.vertices.astype(float), m.faces.astype(np.int32)); b.endModel()
    return fcl.CollisionObject(b, fcl.Transform())
O = {}
def o(k):
    if k not in O: O[k] = obj(M[k])
    return O[k]
def dist(a, b):
    r = fcl.DistanceResult(); fcl.distance(o(a), o(b), fcl.DistanceRequest(enable_nearest_points=True), r)
    c = fcl.CollisionResult(); n = fcl.collide(o(a), o(b), fcl.CollisionRequest(num_max_contacts=1), c)
    return 0.0 if n else round(float(r.min_distance), 3)
PCB = [k for k in M if k.startswith("REF_PCB")]
pairs = [(p, q) for p in ("I9_top_world", "I9_base_world") for q in PCB]
NEW = ["REF_cable_12pin_conductors_x12", "REF_ferrule_pins_0.314in_x12", "REF_ferrule_collars_green_x12", "REF_harness_5x_1pin_housing_d1.2",
       "REF_harness_5_wires_to_J4", "REF_J4_XH5_plug", "REF_USB_male_plug_tip", "REF_cable_12pin_7mm", "REF_zip_tie_2.5mm_centre"]
for n in NEW:
    for q in ["I9_top_world", "I9_base_world", "I9_retainer_world"] + PCB:
        pairs.append((n, q))
pairs += [("REF_zip_tie_2.5mm_centre", "REF_cable_12pin_conductors_x12"), ("REF_cable_12pin_conductors_x12", "REF_cable_12pin_7mm"), ("REF_ferrule_collars_green_x12", "REF_cable_12pin_conductors_x12"),
          ("REF_harness_5_wires_to_J4", "REF_USB_flat_cable_51mm"), ("REF_harness_5_wires_to_J4", "REF_USB_male_90deg_overmold"),
          ("REF_harness_5x_1pin_housing_d1.2", "REF_USB_male_90deg_overmold"), ("REF_harness_5x_1pin_housing_d1.2", "display_parts"),
          ("REF_USB_flat_cable_51mm", "REF_PCB_tall_part"), ("REF_USB_flat_cable_51mm", "REF_PCB_SMD_parts"), ("REF_USB_male_90deg_overmold", "REF_PCB_RevD2_board"),
          ("REF_screw_M2.5x12_PCB_x4", "REF_PCB_SMD_parts"), ("REF_screw_M2.5x12_PCB_x4", "REF_PCB_J4_JST_XH5"),
          ("display_PCB", "I9_top_world"), ("display_LCM", "I9_top_world"), ("display_parts", "I9_top_world"), ("display_PCB", "I9_retainer_world"),
          ("display_parts", "I9_retainer_world"), ("display_LCM", "I9_crown_world"), ("display_PCB", "I9_crown_world")]
R = {}
for a, b in pairs:
    if a in M and b in M: R[f"{a} - {b}"] = dist(a, b)
json.dump(R, open("/workspace/psu-tester-case/cad_I9/clearance_mesh.json", "w"), indent=1)
for k, v in sorted(R.items(), key=lambda kv: kv[1]):
    if v < 3: print(v, k)
