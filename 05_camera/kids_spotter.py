#!/usr/bin/env python3
"""
kids_spotter.py — "What Do I See?" — a fun object-spotting game for kids.

Point the camera at things around the room. Every time it spots a new
object it flashes a big colourful label and adds it to your collection.
How many different objects can you find?

Install dependency:
  pip install opencv-python

Model files (~25 MB) are downloaded automatically on first run.
Run:  python3 kids_spotter.py
"""

import subprocess, sys, threading, queue, urllib.request, time
from pathlib import Path
import cv2, numpy as np

# ── Tunables ─────────────────────────────────────────────────────────────────
WIDTH          = 640
HEIGHT         = 480
FRAMERATE      = 20
CONFIDENCE_MIN = 0.55
CELEBRATE_SEC  = 2.0   # how long the celebration banner stays on screen
WINDOW_TITLE   = "What Do I See?  🔍  (Q to quit)"

# ── Friendly labels with emojis ───────────────────────────────────────────────
EMOJI = {
    "person":       "🧍 Person",
    "aeroplane":    "✈️  Aeroplane",
    "bicycle":      "🚲 Bicycle",
    "bird":         "🐦 Bird",
    "boat":         "⛵ Boat",
    "bottle":       "🍼 Bottle",
    "bus":          "🚌 Bus",
    "car":          "🚗 Car",
    "cat":          "🐱 Cat",
    "chair":        "🪑 Chair",
    "cow":          "🐄 Cow",
    "diningtable":  "🍽️  Table",
    "dog":          "🐶 Dog",
    "horse":        "🐴 Horse",
    "motorbike":    "🏍️  Motorbike",
    "pottedplant":  "🪴 Plant",
    "sheep":        "🐑 Sheep",
    "sofa":         "🛋️  Sofa",
    "train":        "🚂 Train",
    "tvmonitor":    "📺 TV",
}

CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow",
    "diningtable", "dog", "horse", "motorbike", "person",
    "pottedplant", "sheep", "sofa", "train", "tvmonitor",
]

# Bright kid-friendly colours per class (BGR)
PALETTE = [
    (0,0,0),       # background — unused
    (255,80,80),   (80,255,80),   (80,80,255),   (255,200,0),
    (0,200,255),   (200,0,255),   (255,128,0),   (0,255,180),
    (255,0,128),   (128,255,0),   (0,128,255),   (255,255,0),
    (0,255,255),   (255,0,255),   (180,255,100), (100,180,255),
    (255,100,180), (180,100,255), (100,255,180), (255,180,100),
]

# ── Model download ────────────────────────────────────────────────────────────
MODEL_DIR  = Path(__file__).parent / "models"
PROTO      = MODEL_DIR / "MobileNetSSD_deploy.prototxt"
WEIGHTS    = MODEL_DIR / "MobileNetSSD_deploy.caffemodel"
PROTO_URL  = ("https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/"
              "master/deploy.prototxt")
MODEL_URL  = ("https://github.com/chuanqi305/MobileNet-SSD/raw/master/"
              "MobileNetSSD_deploy.caffemodel")

def download_models():
    MODEL_DIR.mkdir(exist_ok=True)
    for path, url in [(PROTO, PROTO_URL), (WEIGHTS, MODEL_URL)]:
        if not path.exists():
            print(f"Downloading {path.name} …")
            try:
                urllib.request.urlretrieve(url, path)
            except Exception as e:
                print(f"ERROR: {e}"); sys.exit(1)

download_models()
net = cv2.dnn.readNetFromCaffe(str(PROTO), str(WEIGHTS))
print("Model ready — point the camera at something!")

# ── Camera stream ─────────────────────────────────────────────────────────────
proc = subprocess.Popen(
    ["libcamera-vid", "--nopreview", "--codec", "mjpeg",
     "--width", str(WIDTH), "--height", str(HEIGHT),
     "--framerate", str(FRAMERATE), "--timeout", "0", "--output", "-"],
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
)

frame_q = queue.Queue(maxsize=2)

def reader():
    buf = b""
    while True:
        chunk = proc.stdout.read(8192)
        if not chunk: break
        buf += chunk
        while True:
            s = buf.find(b"\xff\xd8")
            e = buf.find(b"\xff\xd9", s + 2) if s != -1 else -1
            if s == -1 or e == -1: break
            frame = cv2.imdecode(
                np.frombuffer(buf[s:e+2], np.uint8), cv2.IMREAD_COLOR)
            buf = buf[e+2:]
            if frame is None: continue
            if frame_q.full():
                try: frame_q.get_nowait()
                except queue.Empty: pass
            frame_q.put(frame)

threading.Thread(target=reader, daemon=True).start()

# ── Game state ────────────────────────────────────────────────────────────────
found_objects: set  = set()       # unique objects collected so far
celebrate_label     = ""          # label shown during celebration
celebrate_until     = 0.0         # time.monotonic() deadline

def big_text(img, text, cy, scale, color, thickness=3):
    """Draw centred text with a dark shadow for readability."""
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    x = (img.shape[1] - tw) // 2
    y = cy
    cv2.putText(img, text, (x+2, y+2), cv2.FONT_HERSHEY_SIMPLEX,
                scale, (0, 0, 0), thickness + 2)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness)

# ── Main loop ─────────────────────────────────────────────────────────────────
cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_AUTOSIZE)

try:
    while True:
        try:
            frame = frame_q.get(timeout=2.0)
        except queue.Empty:
            if proc.poll() is not None: break
            continue

        h, w = frame.shape[:2]

        # ── Run detection ─────────────────────────────────────────────────────
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            0.007843, (300, 300), 127.5,
        )
        net.setInput(blob)
        dets = net.forward()

        seen_this_frame = set()
        boxes = []

        for i in range(dets.shape[2]):
            conf = float(dets[0, 0, i, 2])
            if conf < CONFIDENCE_MIN: continue
            cid = int(dets[0, 0, i, 1])
            if cid <= 0 or cid >= len(CLASSES): continue
            name = CLASSES[cid]
            x1 = max(0, int(dets[0, 0, i, 3] * w))
            y1 = max(0, int(dets[0, 0, i, 4] * h))
            x2 = min(w-1, int(dets[0, 0, i, 5] * w))
            y2 = min(h-1, int(dets[0, 0, i, 6] * h))
            boxes.append((name, conf, cid, x1, y1, x2, y2))
            seen_this_frame.add(name)

        # ── New object found? ─────────────────────────────────────────────────
        for name in seen_this_frame:
            if name not in found_objects:
                found_objects.add(name)
                celebrate_label = EMOJI.get(name, name.upper())
                celebrate_until = time.monotonic() + CELEBRATE_SEC
                print(f"NEW FIND: {celebrate_label}  (total: {len(found_objects)})")

        # ── Draw bounding boxes ───────────────────────────────────────────────
        for name, conf, cid, x1, y1, x2, y2 in boxes:
            color = PALETTE[cid % len(PALETTE)]
            label = EMOJI.get(name, name)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            (lw, lh), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            cv2.rectangle(frame,
                          (x1, y1 - lh - 10), (x1 + lw + 6, y1),
                          color, -1)
            cv2.putText(frame, label, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)

        # ── Score banner (top) ────────────────────────────────────────────────
        score_txt = f"Found: {len(found_objects)} / {len(EMOJI)}"
        big_text(frame, score_txt, 38, 1.0, (0, 230, 255), 2)

        # ── Celebration flash (centre) ────────────────────────────────────────
        if time.monotonic() < celebrate_until:
            # semi-transparent dark overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, h//2 - 70), (w, h//2 + 70),
                          (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

            big_text(frame, "NEW FIND!", h//2 - 15, 1.4, (0, 255, 100), 3)
            big_text(frame, celebrate_label,  h//2 + 48, 1.0, (255, 230, 0), 2)

        # ── Collected list (bottom strip) ─────────────────────────────────────
        if found_objects:
            strip = "  ".join(
                EMOJI.get(o, o) for o in sorted(found_objects)
            )
            # truncate if too long for the screen
            max_chars = w // 11
            if len(strip) > max_chars:
                strip = strip[:max_chars - 1] + "…"
            cv2.rectangle(frame, (0, h - 34), (w, h), (30, 30, 30), -1)
            cv2.putText(frame, strip, (6, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

        cv2.imshow(WINDOW_TITLE, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or \
           cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
            break

except KeyboardInterrupt:
    pass
finally:
    print(f"\nGame over! You found {len(found_objects)} object(s): "
          + ", ".join(sorted(found_objects)))
    cv2.destroyAllWindows()
    proc.terminate()
    proc.wait()
