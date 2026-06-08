#!/usr/bin/env python3
"""
kids_spotter.py — "What Do I See?" — a fun object-spotting game for kids.

Point the camera at things around the room. Every time it spots a new
object it flashes a big colourful celebration banner and adds it to your
collection. How many different objects can you find out of 80?

Install dependency:
  pip install opencv-python

Model (~6 MB) is downloaded automatically on first run.
Run:  python3 kids_spotter.py
"""

import queue, time
import cv2
from _camera_utils import (
    COCO_CLASSES,
    load_model, detect, start_camera_stream,
)

# ── Settings ──────────────────────────────────────────────────────────────────
WIDTH          = 640
HEIGHT         = 480
FRAMERATE      = 20
CONFIDENCE_MIN = 0.50
CELEBRATE_SEC  = 2.0
WINDOW_TITLE   = "What Do I See?  (Q to quit)"

# ── Friendly emoji labels ─────────────────────────────────────────────────────
EMOJI = {
    "person":        "🧍 Person",       "bicycle":     "🚲 Bicycle",
    "car":           "🚗 Car",           "motorbike":   "🏍️  Motorbike",
    "aeroplane":     "✈️  Aeroplane",    "bus":         "🚌 Bus",
    "train":         "🚂 Train",         "truck":       "🚚 Truck",
    "boat":          "⛵ Boat",           "bird":        "🐦 Bird",
    "cat":           "🐱 Cat",           "dog":         "🐶 Dog",
    "horse":         "🐴 Horse",         "sheep":       "🐑 Sheep",
    "cow":           "🐄 Cow",           "elephant":    "🐘 Elephant",
    "bear":          "🐻 Bear",          "zebra":       "🦓 Zebra",
    "giraffe":       "🦒 Giraffe",       "backpack":    "🎒 Backpack",
    "umbrella":      "☂️  Umbrella",     "bottle":      "🍼 Bottle",
    "cup":           "☕ Cup",            "bowl":        "🥣 Bowl",
    "banana":        "🍌 Banana",        "apple":       "🍎 Apple",
    "sandwich":      "🥪 Sandwich",      "orange":      "🍊 Orange",
    "pizza":         "🍕 Pizza",         "donut":       "🍩 Donut",
    "cake":          "🎂 Cake",          "chair":       "🪑 Chair",
    "sofa":          "🛋️  Sofa",         "pottedplant": "🪴 Plant",
    "bed":           "🛏️  Bed",          "diningtable": "🍽️  Table",
    "toilet":        "🚽 Toilet",        "tvmonitor":   "📺 TV",
    "laptop":        "💻 Laptop",        "mouse":       "🖱️  Mouse",
    "keyboard":      "⌨️  Keyboard",     "cell phone":  "📱 Phone",
    "book":          "📚 Book",          "clock":       "🕐 Clock",
    "scissors":      "✂️  Scissors",     "teddy bear":  "🧸 Teddy Bear",
    "toothbrush":    "🪥 Toothbrush",
}

# ── Bright colour palette (BGR) ───────────────────────────────────────────────
PALETTE = [
    (255,80,80),  (80,255,80),  (80,80,255),  (255,200,0),
    (0,200,255),  (200,0,255),  (255,128,0),  (0,255,180),
    (255,0,128),  (128,255,0),  (0,128,255),  (255,255,0),
    (0,255,255),  (255,0,255),  (180,255,100),(100,180,255),
]

def class_color(cid):
    return PALETTE[cid % len(PALETTE)]

def big_text(img, text, cy, scale, color, thickness=3):
    (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    x = (img.shape[1] - tw) // 2
    cv2.putText(img, text, (x+2, cy+2),
                cv2.FONT_HERSHEY_SIMPLEX, scale, (0,0,0), thickness+2)
    cv2.putText(img, text, (x, cy),
                cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

# ── Load model + start camera ─────────────────────────────────────────────────
print("Loading YOLOv8n …")
net = load_model()
print("Model ready — point the camera at something!")

proc, frame_q = start_camera_stream(WIDTH, HEIGHT, FRAMERATE)
cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_AUTOSIZE)

# ── Game state ────────────────────────────────────────────────────────────────
found_objects:   set  = set()
celebrate_label: str  = ""
celebrate_until: float = 0.0

try:
    while True:
        try:
            frame = frame_q.get(timeout=2.0)
        except Exception:
            if proc.poll() is not None:
                break
            continue

        h, w = frame.shape[:2]
        detections = detect(net, frame, CONFIDENCE_MIN)

        # ── Check for new finds ───────────────────────────────────────────────
        for cid, conf, *_ in detections:
            name = COCO_CLASSES[cid]
            if name not in found_objects:
                found_objects.add(name)
                celebrate_label = EMOJI.get(name, name.upper())
                celebrate_until = time.monotonic() + CELEBRATE_SEC
                print(f"NEW FIND: {celebrate_label}  "
                      f"(total: {len(found_objects)})")

        # ── Draw bounding boxes ───────────────────────────────────────────────
        for cid, conf, x1, y1, x2, y2 in detections:
            name  = COCO_CLASSES[cid]
            color = class_color(cid)
            label = EMOJI.get(name, name)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            (lw, lh), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            cv2.rectangle(frame,
                          (x1, y1 - lh - 10), (x1 + lw + 6, y1),
                          color, -1)
            cv2.putText(frame, label, (x1+3, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)

        # ── Score banner (top) ────────────────────────────────────────────────
        big_text(frame, f"Found: {len(found_objects)} / {len(EMOJI)}",
                 38, 1.0, (0, 230, 255), 2)

        # ── Celebration flash (centre) ────────────────────────────────────────
        if time.monotonic() < celebrate_until:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, h//2-70), (w, h//2+70), (20,20,20), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            big_text(frame, "NEW FIND!", h//2-15, 1.4, (0, 255, 100), 3)
            big_text(frame, celebrate_label,  h//2+48, 1.0, (255, 230, 0), 2)

        # ── Collected strip (bottom) ──────────────────────────────────────────
        if found_objects:
            strip = "  ".join(
                EMOJI.get(o, o) for o in sorted(found_objects))
            max_chars = w // 11
            if len(strip) > max_chars:
                strip = strip[:max_chars-1] + "…"
            cv2.rectangle(frame, (0, h-34), (w, h), (30,30,30), -1)
            cv2.putText(frame, strip, (6, h-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220,220,220), 1)

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
