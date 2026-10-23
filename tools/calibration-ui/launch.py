"""Start the local calibration service independently of a terminal or Codex turn."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
URL='http://127.0.0.1:8765/'

def running():
    try:
        with urlopen(URL+'api/state',timeout=1) as response:
            state=json.load(response)
        return state.get('workflow')=='two-pass-v2'
    except (URLError,TimeoutError,ValueError):return False

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart-pass',action='store_true')
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    if not running():
        data=ROOT/'output/calibration-ui';data.mkdir(parents=True,exist_ok=True)
        cmd=[sys.executable,'-u',str(HERE/'server.py')]
        if args.restart_pass:cmd.append('--restart-pass')
        with (data/'server.log').open('ab',buffering=0) as log:
            process=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        for _ in range(40):
            if running():break
            if process.poll() is not None:raise SystemExit('Server stopped. See output/calibration-ui/server.log.')
            time.sleep(.1)
        else:raise SystemExit('Server did not start. See output/calibration-ui/server.log.')
    print(URL)
    if args.open:webbrowser.open(URL)

if __name__=='__main__':main()
