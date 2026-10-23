"""Capture a bounded, command-free Rev D/D2 startup and summarize raw ADCs."""
from pathlib import Path
import csv
import io
import json
import statistics
import time
from collections import Counter
import serial

root = Path(__file__).resolve().parent
s = serial.Serial(port=None, baudrate=115200, timeout=.2)
s.port = '/dev/cu.usbmodem58760426031'
s.dtr = False
s.rts = False
s.open()
# Release boot strap and reset only the ESP32 application.
s.rts = True
time.sleep(.15)
s.rts = False
data = bytearray()
end = time.monotonic() + 20
try:
    while time.monotonic() < end:
        data.extend(s.read(4096))
finally:
    s.close()
log = data.decode('utf-8', errors='replace')
(root/'release-recheck.log').write_text(log)
rows = []
for row in csv.reader(io.StringIO(log)):
    if len(row) != 23:
        continue
    try:
        seq, valid = int(row[0]), int(row[1])
        adc = [float(v) for v in row[2:14]]
        reference = [float(v) for v in row[14:18]]
        state = int(row[18])
        positive, negative, unknown = [int(v, 16) for v in row[19:22]]
        volts = float(row[22])
    except ValueError:
        continue
    rows.append(dict(sequence=seq, valid=valid, adc=adc, reference=reference,
                     state=state, positive_mask=positive, return_mask=negative,
                     unknown_mask=unknown, supply_volts=volts))
good = [r for r in rows if r['valid']]
states = {0: 'NO_LIVE_VOLTAGE', 1: 'SUPPLY', 2: 'AMBIGUOUS', 3: 'OVER_RANGE',
          4: 'ADC_FAULT', 5: 'FINISH_CAL'}
summary = dict(port=s.port, seconds=20, sample_count=len(rows),
               valid_samples=len(good), invalid_samples=len(rows)-len(good),
               states=dict(Counter(states.get(r['state'], str(r['state'])) for r in rows)),
               calibration_performed=False)
if good:
    summary['raw_adc_channels_V'] = [
        dict(channel=i+1, mean=statistics.mean(r['adc'][i] for r in good),
             minimum=min(r['adc'][i] for r in good), maximum=max(r['adc'][i] for r in good))
        for i in range(12)]
    summary['last_valid_sample'] = good[-1]
    summary['raw_reference_V'] = [
        dict(phase=i, mean=statistics.mean(r['reference'][i] for r in good),
             minimum=min(r['reference'][i] for r in good),
             maximum=max(r['reference'][i] for r in good))
        for i in range(4)]
(root/'release-recheck-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(log[:1600])
print(json.dumps(summary, indent=2))
