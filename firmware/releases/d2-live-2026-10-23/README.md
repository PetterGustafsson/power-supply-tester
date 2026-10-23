# Working Rev D2 live firmware — October 23, 2026

This package preserves the exact application installed when the operator
confirmed: **“Yes, about 1–2 seconds and steady”**, then **“Works well, stop.”**
The source is in [`../../Tester12VRevD/`](../../Tester12VRevD/).

| File | Flash address | Purpose |
| --- | --- | --- |
| `app.bin` | `0x10000` | Actual measurement firmware with live optical display |
| `live50.bin` | `0x610000` | Matching 311-frame RGB565 optical asset |
| `bootloader.bin` | `0x0` | ESP32-S3 bootloader, for initial installation |
| `partitions.bin` | `0x8000` | Matching 16 MB / 3 MB app partition table |
| `boot_app0.bin` | `0xe000` | OTA boot data, for initial installation |

[`SHA256SUMS`](SHA256SUMS) verifies the files. The
[`flash manifest`](flash-manifest.json) records exact sizes, hashes, partition
layout and target board. See the [build/flash guide](../../../docs/BUILD.md)
for application-only updates and fresh-board installation.

The application-only update preserves saved NVS calibration and the existing
display asset. This package does not embed the prototype's calibration into a
generic firmware image. Device-specific backups and measured/copied calibration
provenance are retained in the engineering records.

The LCD can use a filtered provisional estimate for noisy readings. The strict
eight-scan measurement CSV retains the 0.25 V stability guard. This release
records an operator-confirmed prototype, with independent accuracy qualification
tracked separately in the [firmware guide](../../Tester12VRevD/README.md).
