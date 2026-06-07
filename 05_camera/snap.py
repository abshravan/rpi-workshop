#!/usr/bin/env python3
"""
snap.py — Capture a single still image with the Pi Camera module.
Saves the image as snap.jpg in the current directory.

Hardware:
  Pi Camera Module connected to the CSI ribbon port.
  Ribbon cable connector faces AWAY from the Ethernet port.

Enable camera:
  sudo raspi-config  →  Interface Options  →  Camera  →  Enable

picamera2 is pre-installed on Raspberry Pi OS (Bookworm+).
"""

from picamera2 import Picamera2
from time import sleep

cam = Picamera2()
cam.configure(cam.create_still_configuration())
cam.start()
sleep(2)             # allow auto-exposure to settle
cam.capture_file("snap.jpg")
cam.stop()

print("Image saved as snap.jpg")
