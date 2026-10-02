"""Compile without flashing and record reproducible source/binary hashes."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent
CLI='/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli'
fqbn='esp32:esp32:esp32s3:FlashSize=16M,PSRAM=enabled,CDCOnBoot=default,PartitionScheme=app3M_fat9M_16MB'
args=[CLI,'compile','--fqbn',fqbn,'--build-path','/private/tmp/tester12vc-build','--output-dir',str(ROOT/'build'),str(ROOT)]
r=subprocess.run(args,capture_output=True,text=True)
log=ROOT.parents[1]/'hardware/rev-c/validation/firmware-build.log'
log.write_text('Command: '+repr(args)+'\nExit code: '+str(r.returncode)+'\n'+r.stdout+r.stderr)
assert r.returncode==0,log
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data={'compile_exit_code':r.returncode,'fqbn':fqbn,'core_version':'3.3.7','flashed':False,
 'source_sha256':{p.name:sha(p) for p in sorted(ROOT.iterdir()) if p.suffix in ('.ino','.h','.cpp','.c')},
 'binary_sha256':{p.name:sha(p) for p in sorted((ROOT/'build').glob('*.bin'))}}
assert len(data['binary_sha256'])>=4
(ROOT/'build-evidence.json').write_text(json.dumps(data,indent=2)+'\n')
print('PASS: firmware compiled; source and binary hashes saved. No hardware flashed.')
