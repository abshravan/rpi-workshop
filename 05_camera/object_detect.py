#!/usr/bin/env python3
"""
object_detect.py — Real-time object detection with a live GUI window.
Uses libcamera-vid (MJPEG) + YOLOv8n ONNX via OpenCV DNN.

Detects 80 COCO object classes. Model (~6 MB) is downloaded automatically
on first run from the official Ultralytics release.

Install dependency:
  pip install opencv-python

Verify camera:
  libcamera-hello --list-cameras

Run:
  python3 object_detect.py
"""

import sys, queue
import cv2
from _camera_utils import (
    COCO_CLASSES, COCO_COLORS,
    load_model, detect, start_camera_stream,
)

# ── Settings ──────────────────────────────────────────────────────────────────
WIDTH          = 640
HEIGHT         = 480
FRAMERATE      = 15
CONFIDENCE_MIN = 0.45
WINDOW_TITLE   = "Object Detection  |  Q to quit"
SAVE_SNAPSHOT  = True

print("Loading YOLOv8n …")
net = load_model()
print("Model ready.")

proc, frame_q = start_camera_stream(WIDTH, HEIGHT, FRAMERATE)
cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_AUTOSIZE)
print(f"Live window open — {WIDTH}×{HEIGHT} @ {FRAMERATE} fps  |  press Q to quit")

snapshot_saved = False

try:
    while True:
        try:
            frame = frame_q.get(timeout=2.0)
        except queue.Empty:
            if proc.poll() is not None:
                print("Camera process ended.")
                break
            continue

        detections = detect(net, frame, CONFIDENCE_MIN)

        for cid, conf, x1, y1, x2, y2 in detections:
            color = tuple(int(c) for c in COCO_COLORS[cid])
            label = f"{COCO_CLASSES[cid]}: {conf:.0%}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            (lw, lh), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(frame,
                          (x1, y1 - lh - 6), (x1 + lw + 4, y1),
                          color, -1)
            cv2.putText(frame, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        cv2.putText(frame, f"Objects: {len(detections)}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

        cv2.imshow(WINDOW_TITLE, frame)

        if detections and SAVE_SNAPSHOT and not snapshot_saved:
            cv2.imwrite("object_snapshot.jpg", frame)
            print("Snapshot saved → object_snapshot.jpg")
            snapshot_saved = True

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or \
           cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
            break

except KeyboardInterrupt:
    pass
finally:
    cv2.destroyAllWindows()
    proc.terminate()
    proc.wait()
