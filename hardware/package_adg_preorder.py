"""Package the released Rev B board with its existing ADG4612 preorder BOM."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import io
import json
import shutil
import zipfile

BASE = Path(__file__).resolve().parent
REV = BASE / 'rev-b'
MFG = REV / 'manufacturing'
VAL = REV / 'validation'
NAME = 'tester12v-REV-B-ADG-PREORDER'
OUT = BASE / NAME
FILES = {
    'gerbers': NAME + '-Gerbers.zip',
    'bom': NAME + '-BOM.csv',
    'cpl': NAME + '-CPL.csv',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(path.read_bytes())


def read_json(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open(newline='') as file:
        return list(csv.DictReader(file))


def expand(bom):
    refs = [ref for row in bom for ref in row['Designator'].split(',')]
    assert len(refs) == len(set(refs)) == 114
    return {ref: row for row in bom for ref in row['Designator'].split(',')}


# Check provenance before copying anything. Do not regenerate the PCB.
release = read_json(VAL / 'order-package-checks.json')
assert release['status'] == 'PASS'
released_hashes = release['source_file_hashes']
sources = {
    'PCB-Gerbers.zip': MFG / 'tester12v-rev-b-fabrication.zip',
    'BOM.csv': MFG / 'jlc-bom.csv',
    'CPL.csv': MFG / 'jlc-cpl.csv',
    'reference/assembly.pdf': REV / 'previews/assembly.pdf',
    'reference/schematic.pdf': REV / 'previews/schematic.pdf',
    'reference/front-paste.gtp': MFG / 'stencil/tester12v-F_Paste.gtp',
}
for name, path in sources.items():
    assert digest(path) == released_hashes[name], name
audit = read_json(VAL / 'board-audit.json')
assert audit['status'] == 'PASS'
assert digest(REV / 'tester12v.kicad_pcb') == audit['board_sha256']
assert digest(VAL / 'schematic.net') == audit['schematic_netlist_sha256']
erc = read_json(VAL / 'erc.json')
drc = read_json(VAL / 'drc-final.json')
assert all(not sheet['violations'] for sheet in erc['sheets'])
assert all(not drc[key] for key in ('violations', 'unconnected_items', 'schematic_parity'))

primary = rows(MFG / 'jlc-bom.csv')
preorder = rows(MFG / 'jlc-bom-preorder-switches.csv')
assert len(primary) == len(preorder) == 24
before, after = expand(primary), expand(preorder)
assert before.keys() == after.keys()
changed = {ref for ref in before if before[ref] != after[ref]}
assert changed == {'U4', 'U5', 'U6'}
for ref in changed:
    old, new = before[ref], after[ref]
    assert old['LCSC Part #'] == 'C207399'
    assert old['Manufacturer Part Number'] == 'ADG4612BRUZ-REEL7'
    assert new['LCSC Part #'] == 'C657391'
    assert new['Manufacturer Part Number'] == 'ADG4612BRUZ'
    assert old['Footprint'] == new['Footprint'] == 'TSSOP-16'
    differences = {key for key in old if old[key] != new[key]}
    assert differences == {'Comment', 'LCSC Part #', 'Manufacturer Part Number'}

cpl = rows(MFG / 'jlc-cpl.csv')
assert len(cpl) == 114
assert Counter(row['Designator'] for row in cpl) == Counter({ref: 1 for ref in after})
assert all(row['Layer'] == 'Top' for row in cpl)
assert not {'R43', 'R44'} & after.keys()
assert after['U7']['LCSC Part #'] == 'C22419841'
assert after['U7']['Manufacturer Part Number'] == 'MIE1W0505BGLVH-3R-Z'
u7 = next(row for row in cpl if row['Designator'] == 'U7')
assert (float(u7['Mid X']), float(u7['Mid Y']), float(u7['Rotation'])) == (16, -11, 90)

OUT.mkdir(exist_ok=True)
(OUT / 'reference').mkdir(exist_ok=True)
shutil.copyfile(MFG / 'jlc-bom-preorder-switches.csv', OUT / FILES['bom'])
shutil.copyfile(MFG / 'jlc-cpl.csv', OUT / FILES['cpl'])
for name in ('reference/assembly.pdf', 'reference/schematic.pdf', 'reference/front-paste.gtp'):
    shutil.copyfile(sources[name], OUT / name)

# Keep all fabrication commands byte-identical. Replace only stale purchasing
# guidance in the nested ZIP, which otherwise points to the stocked-switch BOM.
fabrication_notes = (MFG / 'fabrication-notes.txt').read_text().split('Assembly information in the complete design package:')[0]
fabrication_notes += f'''Assembly sourcing variant: ADG4612 PREORDER, prepared 2026-09-30.
Use only the matched BOM and CPL from the containing {NAME} package.
U4/U5/U6: ADG4612BRUZ / C657391, TSSOP-16. Requires procurement confirmation.
U7: MIE1W0505BGLVH-3R-Z / C22419841, LGA-12 4x5mm; must be fitted.
JLC lists U7 as STANDARD PCBA ONLY, with X-ray inspection required.
Select Standard PCBA, top side. Economic PCBA cannot assemble this BOM.
R43/R44: do not populate. 110 SMD parts and four through-hole connectors.
Read ORDER-INSTRUCTIONS.txt in the outer package for procurement and placement.
The seven Gerber layers and two drill files are unchanged from released Rev B.
This is an unbuilt prototype; JLC DFM/placement review and bench tests remain.
'''
with zipfile.ZipFile(sources['PCB-Gerbers.zip']) as original:
    assert original.testzip() is None
    expected = set(original.namelist())
    assert len(expected) == 10 and 'fabrication-notes.txt' in expected
    layer_hashes = {}
    with zipfile.ZipFile(OUT / FILES['gerbers'], 'w', zipfile.ZIP_DEFLATED) as target:
        for name in sorted(expected):
            data = original.read(name)
            if name == 'fabrication-notes.txt':
                data = fabrication_notes.encode('utf-8')
            else:
                assert data == (MFG / 'gerbers' / name).read_bytes(), name
                layer_hashes[name] = sha(data)
            target.writestr(name, data)

instructions = f'''12 V TESTER REV B - ADG4612 PREORDER MANUFACTURING PACKAGE
Prepared 2026-09-30. Target assembly quantity: 2 boards.

EXTRACT THE OUTER PACKAGE FIRST. Upload these three files separately to JLC:
1. {FILES['gerbers']} - PCB fabrication upload.
2. {FILES['bom']} - assembly BOM upload.
3. {FILES['cpl']} - assembly placement upload.
The outer ZIP contains documentation as well and is not the Gerber upload.
Use all three from this folder. Replace all three files in any existing draft.
Do not combine these with the older generic Downloads/PCB-Gerbers.zip files.

REQUIRED ASSEMBLY SERVICE - CORRECTION CONFIRMED 2026-09-30
Select STANDARD PCBA, TOP SIDE. U7 / C22419841 is Standard Only and requires
X-ray inspection. Economic PCBA cannot place U7. Do not omit U7: it powers
the isolated measurement electronics and the tester will not work without it.
This corrects the earlier Economic-service cost assumption. The BOM and
component prices alone do not establish the lowest total assembly cost.
JLC's current order dialog displays USD 25 setup per assembly side; this is
not the full assembly charge. Standard also charges feeder loading for Basic
and Extended parts, plus its stencil/placement/X-ray and other applicable fees.
Obtain the actual Standard quote; previous Economic loading estimates do not
apply. No final Standard assembly total has been verified.
Source: https://jlcpcb.com/partdetail/24043483-MIE1W0505BGLVH_3RZ/C22419841
Fees: https://jlcpcb.com/help/article/pcb-assembly-price

The supplied finished-board outline remains 90 x 80 mm. The order dialog
offers two 5 mm handling rails, resulting in a 90 x 90 mm assembly panel.
Let JLC add the rails/fiducials; do not stretch or scale the supplied Gerbers.
Review panelization and whether the boards will arrive with rails attached.
JLC normally ships rails attached; requested removal may add a charge.
Source: https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order

CHEAPER SWITCH PROCUREMENT
U4/U5/U6 select ADG4612BRUZ / C657391, three per PCB, six fitted for two boards.
This is the same ADG4612 in the same TSSOP-16 package as the stocked
ADG4612BRUZ-REEL7 / C207399; only shipment packaging and purchasing code differ.
No circuit, footprint, routing, placement or firmware change was made.
The schematic reference and original native purchasing fields may retain the
reel suffix. The single BOM in this package defines the requested procurement.

JLC lookup on 2026-09-30: C657391 stock 0, preorder minimum 4,
estimated USD 2.7916 each and estimated 9-day procurement lead time.
These are estimates, not a confirmed offer or total delivery time.
Preorder/confirm C657391 and allocate it to assembly before releasing the order.
Six is the fitted quantity only: buy the quantity JLC requires including attrition.
No components have been reserved or purchased. Do not accept an automatic
switch substitution; the selected ADG4612 power-off protection is required.
Source: https://jlcpcb.com/partdetail/AnalogDevices-ADG4612BRUZ/C657391

At the observed prices, six switches total USD 16.7496 versus USD 40.4700
for C207399. Estimated saving: USD 23.7204 for two boards before attrition.
Nominal total fitted parts: USD 52.0368 for two boards using the earlier
Rev B prices for all other items. This is not a final assembly quote.
PCB, setup, stencil, placement, feeder charges, through-hole work, attrition,
required U7 X-ray, shipping, tax, display/controller and harness are additional.
The switch remains Extended. BOM: 9 Basic, 1 Promotional Extended, 14 Extended
types at the last lookup; JLC categories, other stock and prices can change.

PCB AND ASSEMBLY
90 x 80 mm, 2 layers, FR-4, 1.6 mm thickness, 1 oz copper, ENIG,
green solder mask, white silkscreen. Four 2.7 mm nonplated mounting holes.
Request bare-board electrical testing and manufacturer DFM review.
Top assembly: 114 fitted parts = 110 SMD + four through-hole connectors.
Set assembled quantity to 2. Include through-hole assembly for J1/J2/J3/J4.
Display/controller Waveshare ESP32-S3-LCD-1.28 and harness are separate.
The PCB senses 12 V inputs; J4 powers its electronics from the separate
5 V/3.3 V controller domain. Do not feed 12 V into J4.

PART AND PLACEMENT REVIEW
U7 MUST be fitted: MIE1W0505BGLVH-3R-Z / C22419841, LGA-12 4x5mm.
It is included in both BOM and CPL. X=16.0000, Y=-11.0000, Top, rotation 90.
Its physical pin 1 is X=13.9125, Y=-12.6375 mm; confirm against JLC's preview.
U8: ISO1640BDR / C5122339, eight-pin version.
D1-D12: BZT52C12 / C19077410, SOD-123, cathode pin 1.
C1-C12/C28: 470pF / C1743. C21/C24: 22uF / C45783.
R43/R44 are the only DNP BOM components and are absent from BOM, CPL and paste.
CPL units are mm; X right, Y up. Negative Y is intentional. Do not mirror.
J1-J4 coordinates are body centres. All coordinates share the Gerber origin.
Check all polarized parts and connectors against reference/assembly.pdf.
JLC library rotations, part matching, LGA lands/paste and DFM remain to be
confirmed in the actual order. A missing 3D body alone does not prove omission.

PACKAGE CHECKS AND HARDWARE STATUS
Package checks confirm the only BOM differences affect U4/U5/U6 purchasing
code, packaging suffix and comment. All 114 BOM references have CPL entries.
All seven Gerber layers and two drill files match released Rev B byte-for-byte.
The CPL and reference drawings are also byte-identical to released Rev B.
Only the fabrication ZIP's text instructions changed to match this sourcing.
The board SHA256 matches the existing clean ERC/DRC and 352-pad net audit.
Prior Rev B computer checks passed 1,188 DC cases, 64 resistor corners,
20,000 sensitivity trials, 12 behavioral transients and firmware host tests.
Those electronics tests were not rerun for this packaging-only substitution.
No assembled board has been tested. First-article supply, noise, sequencing,
calibration and all 132 ordered pin-pair tests remain before larger production.

CONTENTS
The three named uploads above, this instruction file and SHA256SUMS.txt.
reference/: assembly and schematic PDFs, front paste layer, package checks,
and the prior Rev B board audit, ERC and DRC reports.
The SHA256 file covers every other file in this folder.
Editable design, firmware and bench procedure remain in the original
tester12v-rev-b-complete.zip. This preorder BOM supersedes its stocked-switch
BOM for this order; retain the Rev B circuit and firmware.
'''
(OUT / 'ORDER-INSTRUCTIONS.txt').write_text(instructions)
for src, name in [
    ('board-audit.json', 'rev-b-board-audit.json'),
    ('erc.json', 'rev-b-erc.json'),
    ('drc-final.json', 'rev-b-drc.json'),
]:
    shutil.copyfile(VAL / src, OUT / 'reference' / name)

checks = {
    'status': 'PASS',
    'prepared_date': '2026-09-30',
    'circuit_revision': 'B',
    'sourcing_variant': 'ADG4612BRUZ C657391 preorder',
    'upload_files': FILES,
    'unique_bom_rows': len(preorder),
    'fitted_parts_per_board': len(after),
    'cpl_rows': len(cpl),
    'bom_cpl_reference_sets_identical': True,
    'bom_changed_references': sorted(changed),
    'bom_changed_fields': ['Comment', 'LCSC Part #', 'Manufacturer Part Number'],
    'bom_all_other_rows_unchanged': True,
    'u7_populated': True,
    'u7_part': after['U7']['Manufacturer Part Number'],
    'u7_lcsc': after['U7']['LCSC Part #'],
    'assembly_service': {
        'required_service': 'Standard PCBA',
        'assembly_side': 'Top',
        'economic_compatible': False,
        'restricting_reference': 'U7',
        'lcsc_part': 'C22419841',
        'u7_xray_required': True,
        'verified_date': '2026-09-30',
        'source': 'https://jlcpcb.com/partdetail/24043483-MIE1W0505BGLVH_3RZ/C22419841',
        'cost_correction': 'Prior Economic fee estimates do not apply. Actual Standard quote remains unverified.',
    },
    'dnp_excluded': ['R43', 'R44'],
    'cpl_byte_identical_to_released_rev_b': True,
    'gerber_and_drill_files_byte_identical_to_released_rev_b': True,
    'fabrication_zip_notes_updated': True,
    'fabrication_member_sha256': layer_hashes,
    'board_sha256': audit['board_sha256'],
    'schematic_netlist_sha256': audit['schematic_netlist_sha256'],
    'existing_erc_violations': 0,
    'existing_drc_violations': 0,
    'existing_unconnected_items': 0,
    'existing_schematic_parity_errors': 0,
    'existing_pad_nets_compared': audit['physical_pad_nets_compared'],
    'procurement': {
        'confirmed': False,
        'lookup_date': '2026-09-30',
        'source': 'https://jlcpcb.com/partdetail/AnalogDevices-ADG4612BRUZ/C657391',
        'lcsc_part': 'C657391',
        'observed_stock': 0,
        'estimated_price_usd_each': 2.7916,
        'estimated_procurement_days': 9,
        'observed_minimum_order': 4,
        'nominal_fitted_quantity_for_two_boards': 6,
        'attrition_quantity': 'Must be confirmed by JLC',
    },
    'limitations': 'Packaging/file consistency checks only. Prior circuit tests reused for identical silicon and PCB. JLC matching, placement, DFM, procurement and physical first-article testing remain.',
}
(OUT / 'reference/package-checks.json').write_text(json.dumps(checks, indent=2) + '\n')

# Verify the exact upload files and both ZIP levels before delivery.
assert digest(OUT / FILES['bom']) == digest(MFG / 'jlc-bom-preorder-switches.csv')
assert digest(OUT / FILES['cpl']) == released_hashes['CPL.csv']
with zipfile.ZipFile(OUT / FILES['gerbers']) as fab:
    assert fab.testzip() is None and set(fab.namelist()) == expected
    for name, checksum in layer_hashes.items():
        assert sha(fab.read(name)) == checksum
    assert 'C207399' not in fab.read('fabrication-notes.txt').decode()

contents = sorted(path for path in OUT.rglob('*') if path.is_file() and path.name != 'SHA256SUMS.txt')
assert len(contents) == 11, [str(path) for path in contents]
hashes = {str(path.relative_to(OUT)): digest(path) for path in contents}
(OUT / 'SHA256SUMS.txt').write_text(''.join(f'{checksum}  {name}\n' for name, checksum in hashes.items()))
archive = BASE / (NAME + '.zip')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as target:
    for path in contents + [OUT / 'SHA256SUMS.txt']:
        target.write(path, str(path.relative_to(OUT)))
with zipfile.ZipFile(archive) as final:
    assert final.testzip() is None
    assert set(final.namelist()) == set(hashes) | {'SHA256SUMS.txt'}
    for name, checksum in hashes.items():
        assert sha(final.read(name)) == checksum
    archive_bom = list(csv.DictReader(io.StringIO(final.read(FILES['bom']).decode())))
    assert expand(archive_bom) == after
    with zipfile.ZipFile(io.BytesIO(final.read(FILES['gerbers']))) as nested:
        assert nested.testzip() is None
        for name, checksum in layer_hashes.items():
            assert sha(nested.read(name)) == checksum

print(json.dumps({
    'status': 'PASS', 'archive': str(archive), 'folder': str(OUT),
    'archive_bytes': archive.stat().st_size, 'archive_sha256': digest(archive),
    'archive_files': len(hashes) + 1, 'bom_rows': len(preorder),
    'placed_references': len(cpl), 'changed_references': sorted(changed),
    'unchanged_gerber_and_drill_files': len(layer_hashes), 'u7_included': True,
}, indent=2))
