"""Compile without flashing and record reproducible source/binary hashes."""
from pathlib import Path
import hashlib,json,subprocess,os,shutil,tempfile
ROOT=Path(__file__).resolve().parent
CLI=os.environ.get('ARDUINO_CLI') or shutil.which('arduino-cli')
if not CLI:raise SystemExit('Install arduino-cli or set ARDUINO_CLI to its executable path.')
fqbn='esp32:esp32:esp32s3:FlashSize=16M,PSRAM=enabled,CDCOnBoot=default,PartitionScheme=app3M_fat9M_16MB'
scratch=tempfile.TemporaryDirectory(prefix='tester12vd-build-')
args=[CLI,'compile','--fqbn',fqbn,'--build-path',scratch.name,'--output-dir',str(ROOT/'build'),str(ROOT)]
r=subprocess.run(args,capture_output=True,text=True)
log=ROOT.parents[1]/'hardware/rev-d/validation/firmware-build.log'
log.write_text('Command: '+repr(args)+'\nExit code: '+str(r.returncode)+'\n'+r.stdout+r.stderr)
assert r.returncode==0,log
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data={'compile_exit_code':r.returncode,'fqbn':fqbn,'core_version':'3.3.7','flashed':False,
 'source_sha256':{p.name:sha(p) for p in sorted(ROOT.iterdir()) if p.suffix in ('.ino','.h','.cpp','.c')},
 'binary_sha256':{p.name:sha(p) for p in sorted((ROOT/'build').glob('*.bin'))}}
assert len(data['binary_sha256'])>=4
(ROOT/'build-evidence.json').write_text(json.dumps(data,indent=2)+'\n')
print('PASS: firmware compiled; source and binary hashes saved. No hardware flashed.')
