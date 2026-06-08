"""
_camera_utils.py — shared helpers for camera programs.
Not meant to be run directly.
"""

import subprocess, threading, queue, urllib.request, sys
from pathlib import Path
import cv2, numpy as np

# ── YOLOv8n ONNX — stable versioned URL from Ultralytics ─────────────────────
MODEL_DIR   = Path(__file__).parent / "models"
MODEL_PATH  = MODEL_DIR / "yolov8n.onnx"
MODEL_URL   = ("https://github.com/ultralytics/assets/releases/"
               "download/v8.3.0/yolov8n.onnx")

# 80 COCO class names
COCO_CLASSES = [
    "person","bicycle","car","motorbike","aeroplane","bus","train","truck",
    "boat","traffic light","fire hydrant","stop sign","parking meter","bench",
    "bird","cat","dog","horse","sheep","cow","elephant","bear","zebra","giraffe",
    "backpack","umbrella","handbag","tie","suitcase","frisbee","skis","snowboard",
    "sports ball","kite","baseball bat","baseball glove","skateboard","surfboard",
    "tennis racket","bottle","wine glass","cup","fork","knife","spoon","bowl",
    "banana","apple","sandwich","orange","broccoli","carrot","hot dog","pizza",
    "donut","cake","chair","sofa","pottedplant","bed","diningtable","toilet",
    "tvmonitor","laptop","mouse","remote","keyboard","cell phone","microwave",
    "oven","toaster","sink","refrigerator","book","clock","vase","scissors",
    "teddy bear","hair drier","toothbrush",
]

np.random.seed(7)
COCO_COLORS = np.random.randint(50, 230, size=(len(COCO_CLASSES), 3),
                                dtype=np.uint8)


def ensure_model():
    """Download YOLOv8n ONNX on first run."""
    MODEL_DIR.mkdir(exist_ok=True)
    if not MODEL_PATH.exists():
        print(f"Downloading YOLOv8n model (~6 MB) …")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print(f"  Saved → {MODEL_PATH}")
        except Exception as e:
            print(f"ERROR downloading model: {e}")
            print(f"Manual download:\n  wget -O {MODEL_PATH} \"{MODEL_URL}\"")
            sys.exit(1)


def load_model():
    ensure_model()
    net = cv2.dnn.readNetFromONNX(str(MODEL_PATH))
    return net


def detect(net, frame, conf_threshold=0.45, iou_threshold=0.45):
    """
    Run YOLOv8n inference on a BGR frame.
    Returns list of (class_id, confidence, x1, y1, x2, y2).
    """
    h, w = frame.shape[:2]

    # letterbox resize to 640×640
    scale  = min(640 / w, 640 / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (nw, nh))
    canvas  = np.full((640, 640, 3), 114, dtype=np.uint8)
    pad_x   = (640 - nw) // 2
    pad_y   = (640 - nh) // 2
    canvas[pad_y:pad_y+nh, pad_x:pad_x+nw] = resized

    blob = cv2.dnn.blobFromImage(canvas, 1/255.0, (640, 640),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    out = net.forward()[0]          # shape: (84, 8400)  — 4+80 × anchors

    # YOLOv8 output: rows=84 (cx,cy,w,h + 80 scores), cols=8400 anchors
    out = out.T                     # → (8400, 84)
    boxes_xywh = out[:, :4]
    scores     = out[:, 4:]

    class_ids  = np.argmax(scores, axis=1)
    confs      = scores[np.arange(len(scores)), class_ids]
    mask       = confs >= conf_threshold

    boxes_xywh = boxes_xywh[mask]
    confs      = confs[mask]
    class_ids  = class_ids[mask]

    if len(confs) == 0:
        return []

    # xywh (on 640×640 padded) → xyxy in original frame coords
    cx, cy, bw, bh = (boxes_xywh[:, i] for i in range(4))
    x1 = ((cx - bw / 2) - pad_x) / scale
    y1 = ((cy - bh / 2) - pad_y) / scale
    x2 = ((cx + bw / 2) - pad_x) / scale
    y2 = ((cy + bh / 2) - pad_y) / scale

    x1 = np.clip(x1, 0, w - 1).astype(int)
    y1 = np.clip(y1, 0, h - 1).astype(int)
    x2 = np.clip(x2, 0, w - 1).astype(int)
    y2 = np.clip(y2, 0, h - 1).astype(int)

    # NMS per class
    results = []
    for cid in np.unique(class_ids):
        idx = np.where(class_ids == cid)[0]
        b   = np.stack([x1[idx], y1[idx], x2[idx], y2[idx]], axis=1)
        c   = confs[idx].tolist()
        keep = cv2.dnn.NMSBoxes(
            b.tolist(), c, conf_threshold, iou_threshold
        )
        for k in (keep.flatten() if len(keep) else []):
            results.append((int(cid), float(confs[idx[k]]),
                            int(x1[idx[k]]), int(y1[idx[k]]),
                            int(x2[idx[k]]), int(y2[idx[k]])))

    return results


def start_camera_stream(width, height, framerate):
    """Spawn libcamera-vid and return a Queue that yields BGR frames."""
    proc = subprocess.Popen(
        ["libcamera-vid", "--nopreview", "--codec", "mjpeg",
         "--width", str(width), "--height", str(height),
         "--framerate", str(framerate), "--timeout", "0", "--output", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )

    frame_q = queue.Queue(maxsize=2)

    def _reader():
        buf = b""
        while True:
            chunk = proc.stdout.read(8192)
            if not chunk:
                break
            buf += chunk
            while True:
                s = buf.find(b"\xff\xd8")
                e = buf.find(b"\xff\xd9", s + 2) if s != -1 else -1
                if s == -1 or e == -1:
                    break
                frame = cv2.imdecode(
                    np.frombuffer(buf[s:e+2], np.uint8), cv2.IMREAD_COLOR)
                buf = buf[e+2:]
                if frame is None:
                    continue
                if frame_q.full():
                    try: frame_q.get_nowait()
                    except queue.Empty: pass
                frame_q.put(frame)

    threading.Thread(target=_reader, daemon=True).start()
    return proc, frame_q
