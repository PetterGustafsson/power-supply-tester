import time
from pathlib import Path
import serial
s=serial.Serial(port=None, baudrate=115200, timeout=.5)
s.port='/dev/cu.usbmodem58760426031'
s.dtr=False
s.rts=False
s.open()
# Reset into the application while leaving GPIO0 (DTR) released.
s.rts=True
time.sleep(.15)
s.rts=False
end=time.monotonic()+12
out=bytearray()
while time.monotonic()<end:
    out.extend(s.read(4096))
s.close()
text=out.decode('utf-8',errors='replace')
Path('firmware/boot-log.txt').write_text(text)
print(text)
if any(token not in text for token in ['DISPLAY_READY', 'DISPLAY_ALIVE', 'ANIMATION_STATE: GREEN_SUCCESS', 'ANIMATION_STATE: RED_FAILURE', 'millivolts=24000 stage=HOLD', 'millivolts=0 stage=DROP']) or 'ANIMATION_ERROR' in text:
    raise SystemExit('Animation startup and alternating states were not confirmed')
