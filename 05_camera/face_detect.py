#!/usr/bin/env python3
"""
face_detect.py — Real-time face detection from the Pi Camera live feed.
Uses libcamera-vid (MJPEG) + OpenCV Haar Cascade — no picamera2 needed.

Detected faces are printed to the terminal with their bounding box.
Optionally saves a snapshot when a face is first detected.

Install dependency:
  pip install opencv-python

Verify camera is detected first:
  libcamera-hello --list-cameras
"""

import subprocess
import sys
import cv2
import numpy as np

# ── Settings ────────────────────────────────────────────────────────────────
WIDTH         = 640
HEIGHT        = 480
FRAMERATE     = 15
SAVE_SNAPSHOT = True    # save face_snapshot.jpg on first detection
MIN_FACE_PX   = 60      # ignore faces smaller than this (filters noise)

# ── Load Haar Cascade (bundled with OpenCV, no download needed) ──────────────
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("ERROR: Could not load Haar cascade — is opencv-python installed?")
    sys.exit(1)

# ── Start libcamera-vid streaming MJPEG on stdout ───────────────────────────
cmd = [
    "libcamera-vid",
    "--nopreview",
    "--codec",     "mjpeg",
    "--width",     str(WIDTH),
    "--height",    str(HEIGHT),
    "--framerate", str(FRAMERATE),
    "--timeout",   "0",    # run indefinitely
    "--output",    "-",    # stdout
]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

print("Face detection running — Ctrl-C to stop")
print(f"Resolution: {WIDTH}×{HEIGHT}  |  FPS: {FRAMERATE}")
print("-" * 50)

buf           = b""
snapshot_saved = False
frame_count   = 0

try:
    while True:
        chunk = proc.stdout.read(4096)
        if not chunk:
            break
        buf += chunk

        # Parse one complete JPEG frame from the MJPEG stream
        start = buf.find(b"\xff\xd8")
        end   = buf.find(b"\xff\xd9")
        if start == -1 or end == -1 or end < start:
            continue

        jpeg = buf[start : end + 2]
        buf  = buf[end + 2:]
        frame_count += 1

        frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            continue

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray  = cv2.equalizeHist(gray)   # improve detection in dim light

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_PX, MIN_FACE_PX),
        )

        if len(faces) > 0:
            for i, (x, y, w, h) in enumerate(faces):
                print(f"[frame {frame_count:05d}] Face {i+1}: "
                      f"x={x} y={y} w={w} h={h}")

            # Save a snapshot the first time a face appears
            if SAVE_SNAPSHOT and not snapshot_saved:
                # Draw bounding boxes on the saved image
                annotated = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imwrite("face_snapshot.jpg", annotated)
                print(f"  → Snapshot saved as face_snapshot.jpg")
                snapshot_saved = True
        else:
            # Print a dot every 30 frames so you know it's running
            if frame_count % 30 == 0:
                print(".", end="", flush=True)

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    proc.terminate()
    proc.wait()
