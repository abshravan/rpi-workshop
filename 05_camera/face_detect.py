#!/usr/bin/env python3
"""
face_detect.py — Real-time face detection with a live GUI window.
Uses libcamera-vid (MJPEG) + OpenCV Haar Cascade — no picamera2 needed.

A background thread reads the camera stream so the GUI window stays
smooth and responsive. Green bounding boxes and a face counter are
drawn on every frame. Press Q in the window or Ctrl-C to quit.

Install dependency:
  pip install opencv-python

Verify camera is detected first:
  libcamera-hello --list-cameras
"""

import subprocess
import sys
import threading
import queue
import cv2
import numpy as np

# ── Settings ────────────────────────────────────────────────────────────────
WIDTH         = 640
HEIGHT        = 480
FRAMERATE     = 15
SAVE_SNAPSHOT = True   # save face_snapshot.jpg on first detection
MIN_FACE_PX   = 60     # ignore detections smaller than this (noise filter)
WINDOW_TITLE  = "Pi Face Detection  |  Q to quit"

# ── Load Haar Cascade (bundled with OpenCV, no download needed) ──────────────
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

if face_cascade.empty():
    print("ERROR: Could not load Haar cascade — is opencv-python installed?")
    sys.exit(1)

# ── Start libcamera-vid streaming MJPEG on stdout ───────────────────────────
proc = subprocess.Popen(
    [
        "libcamera-vid",
        "--nopreview",
        "--codec",     "mjpeg",
        "--width",     str(WIDTH),
        "--height",    str(HEIGHT),
        "--framerate", str(FRAMERATE),
        "--timeout",   "0",   # run indefinitely
        "--output",    "-",   # stdout
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)

# ── Background thread: reads the MJPEG byte stream and queues decoded frames ─
frame_queue = queue.Queue(maxsize=2)  # small buffer keeps latency low

def mjpeg_reader():
    buf = b""
    while True:
        chunk = proc.stdout.read(8192)
        if not chunk:
            break
        buf += chunk

        # extract every complete JPEG in the buffer before moving on
        while True:
            start = buf.find(b"\xff\xd8")
            end   = buf.find(b"\xff\xd9", start + 2) if start != -1 else -1
            if start == -1 or end == -1:
                break

            jpeg  = buf[start : end + 2]
            buf   = buf[end + 2:]

            frame = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # drop the oldest frame if the queue is full (keeps display live)
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except queue.Empty:
                    pass
            frame_queue.put(frame)

reader_thread = threading.Thread(target=mjpeg_reader, daemon=True)
reader_thread.start()

# ── Main thread: detection + GUI ─────────────────────────────────────────────
cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_AUTOSIZE)

print(f"Live window open — {WIDTH}×{HEIGHT} @ {FRAMERATE} fps")
print("Press Q in the window to quit.")

snapshot_saved = False

try:
    while True:
        try:
            frame = frame_queue.get(timeout=2.0)
        except queue.Empty:
            # camera may have stalled; check if the process is still alive
            if proc.poll() is not None:
                print("Camera process ended unexpectedly.")
                break
            continue

        # ── Face detection ───────────────────────────────────────────────────
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray  = cv2.equalizeHist(gray)  # helps in dim lighting

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_PX, MIN_FACE_PX),
        )

        # ── Draw bounding boxes ──────────────────────────────────────────────
        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame, f"Face {i + 1}",
                (x, y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )

        # ── HUD: face count top-left ─────────────────────────────────────────
        hud = f"Faces detected: {len(faces)}"
        cv2.putText(
            frame, hud,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2,
        )

        # ── Show the frame ───────────────────────────────────────────────────
        cv2.imshow(WINDOW_TITLE, frame)

        # ── Auto-save first detection ────────────────────────────────────────
        if len(faces) > 0 and SAVE_SNAPSHOT and not snapshot_saved:
            cv2.imwrite("face_snapshot.jpg", frame)
            print("Snapshot saved → face_snapshot.jpg")
            snapshot_saved = True

        # Q key or window close button quits
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
            break

except KeyboardInterrupt:
    pass
finally:
    print("Shutting down…")
    cv2.destroyAllWindows()
    proc.terminate()
    proc.wait()
