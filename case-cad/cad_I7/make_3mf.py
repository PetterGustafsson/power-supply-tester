"""Generic 3MF core-spec file (Bambu Studio imports it as 4 named objects on one plate, each with a display colour via basematerials).
Filament/AMS slot assignment is then done in Studio (one filament per object)."""
import trimesh, json, numpy as np, zipfile, io
OUT = "/workspace/psu-tester-case/cad_I7"
COL = json.load(open(f"{OUT}/colours.json"))
PLACE = {"I7_base": (68, 185), "I7_top": (188, 185), "I7_crown": (60, 62), "I7_retainer": (125, 62)}
objs, mats, items = [], [], []
for i, (k, (px, py)) in enumerate(PLACE.items()):
    m = trimesh.load(f"{OUT}/stl/{k}_print.stl"); m.merge_vertices(); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
    c = m.bounds.mean(0); v = m.vertices - np.array([c[0], c[1], m.bounds[0, 2]]) + np.array([px, py, 0])
    r, g, b = [int(255*x) for x in COL[k]["rgb"]]
    mats.append(f'<base name="{COL[k]["filament"]}" displaycolor="#{r:02X}{g:02X}{b:02X}FF"/>')
    vs = "".join(f'<vertex x="{p[0]:.4f}" y="{p[1]:.4f}" z="{p[2]:.4f}"/>' for p in v)
    ts = "".join(f'<triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in m.faces)
    objs.append(f'<object id="{i+2}" name="{k}" type="model" pid="1" pindex="{i}"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
    items.append(f'<item objectid="{i+2}"/>')
    print(k, len(v), len(m.faces), "watertight", m.is_watertight, "size", (m.bounds[1] - m.bounds[0]).round(1))
model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
         '<metadata name="Title">PSU tester case I6</metadata><resources><basematerials id="1">' + "".join(mats) + '</basematerials>' + "".join(objs) +
         '</resources><build>' + "".join(items) + '</build></model>')
ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
with zipfile.ZipFile(f"{OUT}/PSU_case_I7_print.3mf", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)
import lib3mf; w = lib3mf.get_wrapper(); md = w.CreateModel(); md.QueryReader("3mf").ReadFromFile(f"{OUT}/PSU_case_I7_print.3mf"); it = md.GetMeshObjects(); n = []
while it.MoveNext(): o = it.GetCurrentMeshObject(); n.append((o.GetName(), o.GetTriangleCount(), o.IsManifoldAndOriented()))
print("lib3mf re-read:", n)
