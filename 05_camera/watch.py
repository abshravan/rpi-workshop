#!/usr/bin/env python3
"""
watch.py — Simple motion detection using the Pi Camera + OpenCV.
Prints "movement" whenever consecutive frames differ significantly.

Hardware: same Pi Camera setup as snap.py.

Install dependency:
  pip install opencv-python
"""

from picamera2 import Picamera2
import cv2

THRESHOLD = 8   # mean pixel difference that counts as motion

cam = Picamera2()
cam.configure(cam.create_video_configuration())
cam.start()

prev = None

print("Watching for motion — Ctrl-C to stop")

while True:
    frame = cam.capture_array()
    gray  = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    if prev is not None:
        diff = cv2.absdiff(gray, prev).mean()
        if diff > THRESHOLD:
            print(f"Movement detected! (diff={diff:.1f})")

    prev = gray
