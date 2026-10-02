"""Throttle serial writes for this board's USB Single Serial bridge on macOS."""
import time
import serial
import esptool
original_write = serial.Serial.write
def paced_write(self, data):
    sent = 0
    for start in range(0, len(data), 64):
        chunk = data[start:start+64]
        count = original_write(self, chunk)
        if count != len(chunk):
            raise serial.SerialTimeoutException('Short serial write')
        sent += count
        time.sleep(len(chunk) * 10 / self.baudrate + .002)
    return sent
serial.Serial.write = paced_write
esptool._main()
