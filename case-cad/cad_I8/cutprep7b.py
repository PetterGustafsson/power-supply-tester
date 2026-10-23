"""I7b trench section meshes at the tie plane: body + cap (section face) separately, for colour-coded section renders"""
import trimesh, numpy as np, tie7b
def cut(src, dst):
    m = trimesh.load(src); c = m.slice_plane([0, tie7b.TY, 0], [0, 1, 0], cap=True)
    cap = np.all(np.abs(c.vertices[c.faces][:, :, 1] - tie7b.TY) < 1e-4, axis=1)
    c.submesh([np.where(~cap)[0]], append=True).export(dst + ".stl"); c.submesh([np.where(cap)[0]], append=True).export(dst + "_cap.stl")
cut("stl/I8_base_world.stl", "stl/render/I8_base_cutTY"); cut("stl/REF_cable_12pin_7mm.stl", "stl/render/cable_cutTY"); cut("stl/REF_zip_tie_2.5mm_centre.stl", "stl/render/tie_cutTY")
print("ok")
