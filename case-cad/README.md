# Enclosure CAD

## Current: I15 as built

Open [current/PSU_case_I15_as_built.3mf](current/PSU_case_I15_as_built.3mf)
in a 3MF-capable slicer. It contains the four current printed parts, in their
preserved print orientations and millimetre units:

| Part | Individual mesh | Finish |
| --- | --- | --- |
| Base | [I15_base_print.stl](current/I15_base_print.stl) | Charcoal |
| Top shell | [I15_top_print.stl](current/I15_top_print.stl) | Marble / ivory |
| Crown | [I15_crown_print.stl](current/I15_crown_print.stl) | Orange |
| Display retainer | [I15_retainer_print.stl](current/I15_retainer_print.stl) | Charcoal |

The original [I15 print package](cad_I15/PSU_case_I15_print.3mf) is preserved.
The as-built plate removes its `I15_shim` object because assembly uses a **2 mm
foam pad**. The other four meshes are unchanged. Individual STL exports only
translate each part to centre XY and place its lowest surface at Z=0.
[The manifest](current/manifest.json) records dimensions, triangle counts and
source/output hashes.

Recreate these exports from the repository root:

```sh
python3 scripts/export_current_enclosure.py
```

## Earlier CAD and component references

The revision directories retain available print plates, source scripts and
review records. I9 also includes individual STEP parts and the component meshes
used by the final poster. Large historical assembly STEP files are stored as
losslessly compressed `.step.gz` files. Decompress a copy before opening it:

```sh
gzip -dk case-cad/cad_I9/PSU_case_I9_assembly.step.gz
```

I15's preserved source is the final 3MF mesh package. Historical STEP and
build123d sources describe their named revisions. Some older generators refer
to the original `/workspace/psu-tester-case` environment; the exported STEP,
3MF and STL files are self-contained. The current print exporter and final
poster renderer use repository-relative paths.

Reference display/connector/PCB geometry is under [ref/](ref/) and
[cad_I9/stl/](cad_I9/stl/). The assembled poster is a layout illustration; its
parts are arranged independently and its labels identify the actual hardware.

## As-built fasteners and USB support

- Six M2 × 6 mm black flat Phillips self-tapping screws: four PCB, two display.
- Four M2.5 × 10 mm black flat Phillips self-tapping screws: case.
- One 2 mm foam pad and one 4-inch, 90° USB-C male-to-female soft flat extension.

The [assembly poster](../output/pdf/power-supply-tester-final-layout.pdf) and
[parts manifest](../output/final-layout-poster/parts-manifest.json) are the
current assembly references. Earlier CAD reference screw and USB models retain
their historical names and dimensions.
