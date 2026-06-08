#!/usr/bin/env python3
"""
watch.py — Motion detection using libcamera-vid + OpenCV.
Captures frames via libcamera-vid piped as MJPEG, detects motion by
comparing consecutive grayscale frames.

No picamera2 needed — uses libcamera-vid (pre-installed on Pi OS).

Install dependency:
  pip install opencv-python

Verify camera is detected first:
  libcamera-hello --list-cameras
"""

import subprocess
import sys
import cv2
import numpy as np

THRESHOLD  = 8      # mean pixel difference that counts as motion
WIDTH      = 640
HEIGHT     = 480
FRAMERATE  = 10

# libcamera-vid streams MJPEG on stdout; OpenCV decodes each JPEG frame.
cmd = [
    "libcamera-vid",
    "--nopreview",
    "--codec",    "mjpeg",
    "--width",    str(WIDTH),
    "--height",   str(HEIGHT),
    "--framerate", str(FRAMERATE),
    "--timeout",  "0",      # run indefinitely
    "--output",   "-",      # write to stdout
]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

print("Watching for motion — Ctrl-C to stop")

buf  = b""
prev = None

try:
    while True:
        chunk = proc.stdout.read(4096)
        if not chunk:
            break
        buf += chunk

        # scan for JPEG start (FFD8) and end (FFD9) markers
        start = buf.find(b"\xff\xd8")
        end   = buf.find(b"\xff\xd9")

        if start == -1 or end == -1 or end < start:
            continue

        jpeg = buf[start : end + 2]
        buf  = buf[end + 2:]

        frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_GRAYSCALE)
        if frame is None:
            continue

        if prev is not None:
            diff = cv2.absdiff(frame, prev).mean()
            if diff > THRESHOLD:
                print(f"Movement detected! (diff={diff:.1f})")

        prev = frame

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    proc.terminate()
    proc.wait()
