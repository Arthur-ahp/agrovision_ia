import os
import cv2
import time
import uuid
import threading
from datetime import datetime
from collections import defaultdict

from ultralytics import YOLO

from services.config import (
    CAMERA_SOURCE,
    CAMERA_RECONNECT_SECONDS,
    MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    MIN_CONSECUTIVE_FRAMES,
    ALERT_COOLDOWN_SECONDS,
    TARGET_CLASSES,
    SAVE_DIR,
)
from services.event_repository import save_event

_last_frame = None
_last_frame_lock = threading.Lock()
_camera_connected = False
_camera_online = False
_source_type = "unknown"

_detection_state: dict[str, int] = defaultdict(int)
_last_alert_time: dict[str, float] = defaultdict(lambda: 0.0)

model = YOLO(MODEL_PATH)


def _detect_source_type(source) -> str:
    if isinstance(source, int):
        return "webcam"
    s = str(source).lower()
    if s.startswith("rtsp://"):
        return "rtsp"
    if s.endswith(".m3u8"):
        return "hls"
    if "mjpg" in s or "mjpeg" in s:
        return "mjpeg"
    if s.endswith(".mp4") or s.endswith(".avi"):
        return "file"
    return "stream"


def _draw_box(frame, x1: int, y1: int, x2: int, y2: int, label: str, conf: float):
    text = f"{label} {conf:.2f}"
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(
        frame, text,
        (x1, max(20, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2,
    )


def _should_alert(label: str) -> bool:
    return (time.time() - _last_alert_time[label]) > ALERT_COOLDOWN_SECONDS


def process_stream() -> None:
    global _last_frame, _camera_connected, _camera_online, _source_type

    _source_type = _detect_source_type(CAMERA_SOURCE)

    while True:
        print(f"[Camera] Conectando a: {CAMERA_SOURCE}")
        cap = cv2.VideoCapture(CAMERA_SOURCE)

        if not cap.isOpened():
            print(f"[Camera] Falha ao abrir. Tentando novamente em {CAMERA_RECONNECT_SECONDS}s...")
            _camera_connected = False
            _camera_online = False
            time.sleep(CAMERA_RECONNECT_SECONDS)
            continue

        _camera_connected = True
        _camera_online = True
        print("[Camera] Conectada com sucesso.")

        while True:
            ok, frame = cap.read()
            if not ok:
                print("[Camera] Frame perdido. Reconectando...")
                _camera_online = False
                break

            results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

            found_in_frame: set[str] = set()
            best_conf: dict[str, float] = {}

            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    label = model.names[cls_id]
                    if label not in TARGET_CLASSES:
                        continue

                    found_in_frame.add(label)
                    if label not in best_conf or conf > best_conf[label]:
                        best_conf[label] = conf

                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    _draw_box(frame, x1, y1, x2, y2, label, conf)

            for label in TARGET_CLASSES:
                if label in found_in_frame:
                    _detection_state[label] += 1
                else:
                    _detection_state[label] = 0

            for label in found_in_frame:
                if _detection_state[label] >= MIN_CONSECUTIVE_FRAMES and _should_alert(label):
                    event_id = str(uuid.uuid4())[:8]
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{ts}_{label}_{event_id}.jpg"
                    filepath = os.path.join(SAVE_DIR, filename)
                    cv2.imwrite(filepath, frame)
                    image_path = f"/static/captures/{filename}"
                    confidence = best_conf.get(label, 0.0)
                    save_event(event_id, label, confidence, image_path)
                    _last_alert_time[label] = time.time()
                    print(f"[Alerta] {label} | conf={confidence:.2f} | {filepath}")

            with _last_frame_lock:
                _last_frame = frame.copy()

            time.sleep(0.05)

        cap.release()
        _camera_connected = False
        _camera_online = False
        time.sleep(CAMERA_RECONNECT_SECONDS)


def get_last_frame():
    with _last_frame_lock:
        return _last_frame.copy() if _last_frame is not None else None


def get_camera_status() -> dict:
    with _last_frame_lock:
        has_frame = _last_frame is not None
    return {
        "online": _camera_online,
        "connected": _camera_connected,
        "has_live_frame": has_frame,
        "source_type": _source_type,
    }


def generate_mjpeg():
    """Gerador para o endpoint /video_feed (multipart/x-mixed-replace)."""
    while True:
        frame = get_last_frame()
        if frame is None:
            time.sleep(0.1)
            continue
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not success:
            time.sleep(0.05)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )
        time.sleep(0.05)
