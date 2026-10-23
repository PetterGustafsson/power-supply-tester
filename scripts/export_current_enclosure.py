"""Export the four as-built enclosure meshes from the preserved I15 3MF.

The original file is retained unchanged. The obsolete printed USB shim is
omitted from the as-built plate because the prototype uses a 2 mm foam pad.
No printed-part geometry is modified. Uses only the Python standard library.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib, json, math, struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'case-cad/cad_I15/PSU_case_I15_print.3mf'
OUT = ROOT / 'case-cad/current'
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with ZipFile(SOURCE) as archive:
        entries = {item.filename: archive.read(item.filename) for item in archive.infolist()}
    model = ET.fromstring(entries['3D/3dmodel.model'])
    assert model.get('unit') == 'millimeter'
    resources, build = model.find('m:resources', NS), model.find('m:build', NS)
    objects = resources.findall('m:object', NS)
    parts = []
    for obj in objects:
        name = obj.get('name')
        if name == 'I15_shim':
            resources.remove(obj)
            for item in list(build):
                if item.get('objectid') == obj.get('id'): build.remove(item)
            continue
        assert name in ('I15_base', 'I15_top', 'I15_crown', 'I15_retainer')
        verts = [tuple(float(v.get(c)) for c in ('x','y','z')) for v in obj.findall('m:mesh/m:vertices/m:vertex', NS)]
        triangles = [tuple(int(t.get(c)) for c in ('v1','v2','v3')) for t in obj.findall('m:mesh/m:triangles/m:triangle', NS)]
        low = [min(v[i] for v in verts) for i in range(3)]
        high = [max(v[i] for v in verts) for i in range(3)]
        shift = ((low[0]+high[0])/2, (low[1]+high[1])/2, low[2])
        centered = [tuple(v[i]-shift[i] for i in range(3)) for v in verts]
        path = OUT / f'{name}_print.stl'
        with path.open('wb') as f:
            f.write(f'{name}: I15 source mesh, millimeters, print orientation'.encode().ljust(80,b'\0'))
            f.write(struct.pack('<I', len(triangles)))
            for tri in triangles:
                a,b,c = [centered[i] for i in tri]
                u,v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
                n = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                length = math.sqrt(sum(x*x for x in n))
                normal = tuple(x/length for x in n) if length else (0,0,0)
                f.write(struct.pack('<12fH', *normal,*a,*b,*c,0))
        parts.append(dict(name=name, file=path.name, triangles=len(triangles),
                          size_mm=[round(high[i]-low[i],4) for i in range(3)],
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    ET.register_namespace('', NS['m'])
    entries['3D/3dmodel.model'] = ET.tostring(model, encoding='utf-8', xml_declaration=True)
    plate = OUT / 'PSU_case_I15_as_built.3mf'
    with ZipFile(plate,'w',ZIP_DEFLATED) as archive:
        for name,data in entries.items(): archive.writestr(name,data)
    (OUT/'manifest.json').write_text(json.dumps(dict(
        source=str(SOURCE.relative_to(ROOT)), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        units='mm', geometry='unchanged I15 meshes; individual STLs centered on XY and placed at Z=0',
        omitted_object='I15_shim', replacement='2 mm foam pad', parts=parts),indent=2)+'\n')
    print(f'Exported {len(parts)} unchanged print meshes and the as-built 3MF to {OUT}')

if __name__ == '__main__': main()
