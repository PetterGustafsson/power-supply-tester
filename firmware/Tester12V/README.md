# Live Rev A firmware

Target: Waveshare ESP32-S3-LCD-1.28 **non-touch**, ESP32-S3, 16 MB flash,
2 MB QSPI PSRAM. This sketch reads the actual Rev A ADS1115 channels;
it does not use simulated voltages. USB-powered, GPIO6 SDA / GPIO7 SCL,
100 kHz I²C, serial console 115200 baud.

The circuit, connector pin numbers, two-point calibration commands, and
first-article procedure are in [the hardware README](../../hardware/rev-a/README.md).
Do not flash this expecting live readings without the assembled measurement board.
The default readings are marked `UNCAL`; partial calibration is marked `FINISH CAL`.
All twelve channels must be calibrated before calibrated results are displayed.

Build from the workspace root with Arduino CLI and the installed ESP32 core 3.3.7:

```sh
arduino-cli compile \
  --fqbn esp32:esp32:esp32s3:FlashSize=16M,PSRAM=enabled,CDCOnBoot=default,PartitionScheme=app3M_fat9M_16MB \
  --build-path /tmp/tester12v-build \
  --output-dir firmware/Tester12V/build firmware/Tester12V
```

The release binaries were compiled for exactly those settings. The merged binary
contains the bootloader, partition table and application and is written at address
0x0 on the specified 16 MB target. Flashing erases/replaces the previous demo.
Select and verify the intended serial port before any upload. This work did not
flash the connected display or claim an on-device measurement test.

`Measurement.h` contains the host-tested classification logic. A scan validates
all three ADCs and all channels before updating the display. I²C/configuration/
conversion failures produce `ADC FAULT`; patterns inconsistent with a single
active pair produce `AMBIGUOUS`. Acquisition is sequential, so changing voltages
are not captured simultaneously. The normal measurement range is 0–18 V.

Display driver files originate from Waveshare's official ESP32-S3-LCD-1.28 demo;
their original license notices remain in the source files.
