#!/bin/bash
cd "$(dirname "$0")/../.." || exit 1
exec firmware/.venv/bin/python tools/calibration-ui/launch.py --open
