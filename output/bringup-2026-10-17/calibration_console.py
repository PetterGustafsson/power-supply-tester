"""Keep the ESP32 serial connection open between the two calibration points.

Input commands: status, cal0 <pin>, calv <pin> <measured volts>, quit.
The firmware keeps its pending low point in RAM, so do not reopen/reset the port
between cal0 and calv. Device output and command acknowledgements are logged.
"""
import csv
import datetime
import json
import math
import os
from pathlib import Path
import re
import select
import sys
import time
import serial

root = Path(__file__).resolve().parent
log = (root/'calibration-console.log').open('a', buffering=1)
events = (root/'calibration-events.jsonl').open('a', buffering=1)
latest_path = root/'calibration-console-latest.json'
latest = dict(pid=os.getpid(), port='/dev/cu.usbmodem58760426031',
              pending_pin=None, pending_low_point_valid=False,
              console_closed=False, last_ack=None, sample=None)
pending_command = None
last_snapshot = 0

def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def snapshot():
    latest['updated_at_utc'] = timestamp()
    temporary = latest_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(latest, indent=2)+'\n')
    temporary.replace(latest_path)

def event(kind, text):
    events.write(json.dumps(dict(at_utc=timestamp(), kind=kind, text=text))+'\n')

def device_line(line):
    global last_snapshot, pending_command
    log.write(line+'\n')
    row = next(csv.reader([line]), [])
    if len(row) == 23:
        try:
            sample = dict(sequence=int(row[0]), valid=int(row[1]),
                          raw_V=list(map(float, row[2:14])),
                          reference_V=list(map(float, row[14:18])),
                          state=int(row[18]), positive_mask=int(row[19],16),
                          return_mask=int(row[20],16), unknown_mask=int(row[21],16),
                          supply_V=float(row[22]))
        except ValueError:
            pass
        else:
            latest['sample'] = sample
            if time.monotonic()-last_snapshot > 1:
                snapshot(); last_snapshot = time.monotonic()
            return
    if not line:
        return
    print(line, flush=True)
    if line.startswith('ESP-ROM:') or line.startswith('TESTER12V Rev D:'):
        latest['pending_pin'] = None
        latest['pending_low_point_valid'] = False
        event('boot', line)
    if line.startswith(('CAL_', 'ZERO_SAVED', 'COMMANDS:')):
        latest['last_ack'] = line
        latest['last_ack_at_utc'] = timestamp()
        event('ack', line)
        low = re.match(r'CAL_LOW_SAVED pin=(\d+)', line)
        saved = re.match(r'CAL_SAVED pin=(\d+) gain=([\d.]+) mask=([0-9A-Fa-f]+)', line)
        if low:
            latest['pending_pin'] = int(low[1])
            latest['pending_low_point_valid'] = True
        if saved:
            latest['pending_pin'] = None
            latest['pending_low_point_valid'] = False
            latest['calibration_mask'] = int(saved[3],16)
            point = dict(pin=int(saved[1]), gain=float(saved[2]),
                         command=pending_command, acknowledgement=line,
                         saved_at_utc=timestamp())
            (root/f'input-{saved[1]}-calibration.json').write_text(json.dumps(point,indent=2)+'\n')
        snapshot()

s = serial.Serial(port=None, baudrate=115200, timeout=0)
s.port = latest['port']; s.dtr = False; s.rts = False; s.open()
snapshot()
print('CONSOLE_READY: no commands sent; serial stays open. Commands: status, cal0 N, calv N measured_V, quit', flush=True)
buffer = bytearray()
try:
    running = True
    while running:
        ready, _, _ = select.select([s, sys.stdin], [], [], .25)
        if s in ready:
            buffer.extend(s.read(max(1,s.in_waiting)))
            while b'\n' in buffer:
                raw, _, rest = buffer.partition(b'\n'); buffer = bytearray(rest)
                device_line(raw.decode('utf-8', errors='replace').rstrip('\r'))
        if sys.stdin in ready:
            command = sys.stdin.readline()
            if not command:
                break
            command = command.strip()
            if command == 'quit':
                running = False; continue
            if command == 'status':
                snapshot(); print(json.dumps(latest),flush=True); continue
            low = re.fullmatch(r'cal0 ([1-9]|1[0-2])',command)
            high = re.fullmatch(r'calv ([1-9]|1[0-2]) ([0-9]+(?:\.[0-9]+)?)',command)
            if not low and not high:
                print('HOST_REJECTED: expected cal0 N or calv N measured_V',flush=True); continue
            if high:
                voltage = float(high[2])
                if not math.isfinite(voltage) or not 10 < voltage < 14:
                    print('HOST_REJECTED: measured voltage must be above 10 V and below 14 V',flush=True); continue
                if latest['pending_pin'] != int(high[1]) or not latest['pending_low_point_valid']:
                    print('HOST_REJECTED: matching cal0 acknowledgement is required in this uninterrupted session',flush=True); continue
            pending_command = command
            latest['last_command'] = command
            event('command',command);log.write('HOST_COMMAND: '+command+'\n')
            s.write((command+'\n').encode());s.flush()
            print('HOST_SENT: '+command,flush=True)
except (serial.SerialException, OSError) as error:
    latest['disconnected'] = str(error)
    latest['pending_pin'] = None
    latest['pending_low_point_valid'] = False
    event('disconnect',str(error))
    print('SERIAL_DISCONNECTED: '+str(error),flush=True)
finally:
    s.close();latest['console_closed'] = True;latest['pending_pin'] = None
    latest['pending_low_point_valid'] = False
    snapshot();log.close();events.close()
