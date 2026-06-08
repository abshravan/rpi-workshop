#!/usr/bin/env python3
"""
face_detect.py — Real-time face detection from the Pi Camera live feed.
Uses libcamera-vid (MJPEG) + OpenCV Haar Cascade — no picamera2 needed.

Displays a live window with green bounding boxes around detected faces.
Prints bounding-box coordinates to the terminal and optionally saves a
snapshot on first detection. Press Q in the window (or Ctrl-C) to quit.

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

        # Draw bounding boxes and label on the live frame
        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Face {i+1}", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Overlay face count in the top-left corner
        label = f"Faces: {len(faces)}"
        cv2.putText(frame, label, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

        cv2.imshow("Face Detection — press Q to quit", frame)

        if len(faces) > 0:
            for i, (x, y, w, h) in enumerate(faces):
                print(f"[frame {frame_count:05d}] Face {i+1}: "
                      f"x={x} y={y} w={w} h={h}")

            # Save a snapshot the first time a face appears
            if SAVE_SNAPSHOT and not snapshot_saved:
                cv2.imwrite("face_snapshot.jpg", frame)
                print("  → Snapshot saved as face_snapshot.jpg")
                snapshot_saved = True

        # Q key quits the window
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    cv2.destroyAllWindows()
    proc.terminate()
    proc.wait()
