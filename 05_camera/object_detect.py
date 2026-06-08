#!/usr/bin/env python3
"""
object_detect.py — Real-time object detection with a live GUI window.
Uses libcamera-vid (MJPEG) + MobileNet SSD via OpenCV DNN.

Detects 20 object classes from the PASCAL VOC dataset:
  person, car, bicycle, dog, cat, bird, bottle, chair, sofa,
  bus, motorbike, aeroplane, train, boat, horse, cow, sheep,
  diningtable, pottedplant, tvmonitor

Model files (~25 MB total) are downloaded automatically on first run.

Install dependency:
  pip install opencv-python

Verify camera:
  libcamera-hello --list-cameras
"""

import subprocess
import sys
import threading
import queue
import urllib.request
from pathlib import Path

import cv2
import numpy as np

# ── Settings ─────────────────────────────────────────────────────────────────
WIDTH          = 640
HEIGHT         = 480
FRAMERATE      = 15
CONFIDENCE_MIN = 0.50   # detections below this are discarded
WINDOW_TITLE   = "Pi Object Detection  |  Q to quit"
SAVE_SNAPSHOT  = True   # save object_snapshot.jpg on first detection

# ── PASCAL VOC class labels ───────────────────────────────────────────────────
CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow",
    "diningtable", "dog", "horse", "motorbike", "person",
    "pottedplant", "sheep", "sofa", "train", "tvmonitor",
]

# One distinct colour per class (BGR)
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(CLASSES), 3), dtype=np.uint8)

# ── Model files ───────────────────────────────────────────────────────────────
MODEL_DIR   = Path(__file__).parent / "models"
PROTO_PATH  = MODEL_DIR / "MobileNetSSD_deploy.prototxt"
MODEL_PATH  = MODEL_DIR / "MobileNetSSD_deploy.caffemodel"

PROTO_URL  = ("https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/"
              "master/deploy.prototxt")
MODEL_URL  = ("https://github.com/chuanqi305/MobileNet-SSD/raw/master/"
              "MobileNetSSD_deploy.caffemodel")

def download_models():
    MODEL_DIR.mkdir(exist_ok=True)
    for path, url in [(PROTO_PATH, PROTO_URL), (MODEL_PATH, MODEL_URL)]:
        if not path.exists():
            print(f"Downloading {path.name} …")
            try:
                urllib.request.urlretrieve(url, path)
                print(f"  Saved → {path}")
            except Exception as e:
                print(f"ERROR downloading {path.name}: {e}")
                print("Check your internet connection and try again.")
                sys.exit(1)

download_models()

# ── Load MobileNet SSD ────────────────────────────────────────────────────────
print("Loading model …")
net = cv2.dnn.readNetFromCaffe(str(PROTO_PATH), str(MODEL_PATH))
print("Model ready.")

# ── Start libcamera-vid ───────────────────────────────────────────────────────
proc = subprocess.Popen(
    [
        "libcamera-vid",
        "--nopreview",
        "--codec",     "mjpeg",
        "--width",     str(WIDTH),
        "--height",    str(HEIGHT),
        "--framerate", str(FRAMERATE),
        "--timeout",   "0",
        "--output",    "-",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)

# ── Background thread: MJPEG reader ──────────────────────────────────────────
frame_queue = queue.Queue(maxsize=2)

def mjpeg_reader():
    buf = b""
    while True:
        chunk = proc.stdout.read(8192)
        if not chunk:
            break
        buf += chunk
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
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except queue.Empty:
                    pass
            frame_queue.put(frame)

threading.Thread(target=mjpeg_reader, daemon=True).start()

# ── Main loop: detection + GUI ────────────────────────────────────────────────
cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_AUTOSIZE)
print(f"Live window open — {WIDTH}×{HEIGHT} @ {FRAMERATE} fps")
print(f"Confidence threshold: {CONFIDENCE_MIN:.0%}  |  Press Q to quit")

snapshot_saved = False

try:
    while True:
        try:
            frame = frame_queue.get(timeout=2.0)
        except queue.Empty:
            if proc.poll() is not None:
                print("Camera process ended unexpectedly.")
                break
            continue

        # ── Run MobileNet SSD ─────────────────────────────────────────────────
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            scalefactor=0.007843,
            size=(300, 300),
            mean=127.5,
        )
        net.setInput(blob)
        detections = net.forward()   # shape: (1, 1, N, 7)

        h, w = frame.shape[:2]
        found = []

        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < CONFIDENCE_MIN:
                continue

            class_id = int(detections[0, 0, i, 1])
            if class_id >= len(CLASSES):
                continue

            # Bounding box in pixel coords
            x1 = int(detections[0, 0, i, 3] * w)
            y1 = int(detections[0, 0, i, 4] * h)
            x2 = int(detections[0, 0, i, 5] * w)
            y2 = int(detections[0, 0, i, 6] * h)

            # Clamp to frame bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

            found.append((class_id, confidence, x1, y1, x2, y2))

        # ── Draw detections ───────────────────────────────────────────────────
        for class_id, confidence, x1, y1, x2, y2 in found:
            color = tuple(int(c) for c in COLORS[class_id])
            label = f"{CLASSES[class_id]}: {confidence:.0%}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Label background pill
            (lw, lh), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
            )
            cv2.rectangle(
                frame,
                (x1, y1 - lh - 6), (x1 + lw + 4, y1),
                color, -1,
            )
            cv2.putText(
                frame, label,
                (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1,
            )

        # ── HUD ───────────────────────────────────────────────────────────────
        cv2.putText(
            frame, f"Objects: {len(found)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2,
        )

        cv2.imshow(WINDOW_TITLE, frame)

        # ── Snapshot ──────────────────────────────────────────────────────────
        if found and SAVE_SNAPSHOT and not snapshot_saved:
            cv2.imwrite("object_snapshot.jpg", frame)
            print("Snapshot saved → object_snapshot.jpg")
            snapshot_saved = True

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
