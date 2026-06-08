#!/usr/bin/env python3
"""
snap.py — Capture a single still image using libcamera-still.
Saves the image as snap.jpg in the current directory.

Hardware:
  Pi Camera Module connected to the CSI ribbon port.
  Ribbon cable connector faces AWAY from the Ethernet port.

No extra Python libraries needed — uses libcamera-still (pre-installed
on Raspberry Pi OS Bullseye / Bookworm).

Verify camera is detected:
  libcamera-hello --list-cameras
"""

import subprocess
import sys
from pathlib import Path

OUTPUT = "snap.jpg"

result = subprocess.run(
    [
        "libcamera-still",
        "--nopreview",
        "--timeout", "2000",   # 2 s auto-exposure settle time (ms)
        "--output", OUTPUT,
    ],
    capture_output=True,
    text=True,
)

if result.returncode != 0:
    print("ERROR: libcamera-still failed")
    print(result.stderr)
    sys.exit(1)

size = Path(OUTPUT).stat().st_size
print(f"Image saved as {OUTPUT}  ({size / 1024:.1f} KB)")
