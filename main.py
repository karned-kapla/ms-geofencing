import json
import os
import time
import uuid

import cv2
import numpy as np

from core.entities import Zone
from core.geofencing import GeofencingAnalyzer
from core.kafka_publisher import KafkaPublisher
from core.throttle import CaptureThrottle

# ── Configuration ─────────────────────────────────────────────────────────────
# Each instance (pod) monitors a single video stream.
# Override these env vars to configure the service without rebuilding the image.

def _bool_env(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")

def _int_env(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))

VIDEO_SOURCE: str | int = os.getenv("VIDEO_SOURCE", "0")
if VIDEO_SOURCE.isdigit():
    VIDEO_SOURCE = int(VIDEO_SOURCE)

FRAME_WIDTH      = _int_env("FRAME_WIDTH", 640)
FRAME_HEIGHT     = _int_env("FRAME_HEIGHT", 360)
TARGET_FPS       = _int_env("TARGET_FPS", 5)
MIN_OBJECT_SIZE  = _int_env("MIN_OBJECT_SIZE", 1000)
CAPTURE_INTERVAL = _int_env("CAPTURE_INTERVAL", 5)
CAPTURE_DIR      = os.getenv("CAPTURE_DIR", "tmp")

# When POLYGON is not set, the zone covers the entire frame by default.
_polygon_env = os.getenv("POLYGON")
POLYGON: list[list[int]] = (
    json.loads(_polygon_env)
    if _polygon_env
    else [[0, 0], [FRAME_WIDTH, 0], [FRAME_WIDTH, FRAME_HEIGHT], [0, FRAME_HEIGHT]]
)

# Display flags — forced to False when running headless (no display server)
HEADLESS       = _bool_env("HEADLESS", True)
SHOW_VIDEO     = _bool_env("SHOW_VIDEO", False) and not HEADLESS
SHOW_MASK      = _bool_env("SHOW_MASK", False) and not HEADLESS
SHOW_ZONE      = _bool_env("SHOW_ZONE", True)
SHOW_INTRUSION = _bool_env("SHOW_INTRUSION", True)

# ── Kafka (optional) ───────────────────────────────────────────────────────────
# If KAFKA_BOOTSTRAP_SERVERS or KAFKA_TOPIC is not set, publishing is disabled.
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC             = os.getenv("KAFKA_TOPIC")
SERVICE_ID              = os.getenv("SERVICE_ID")          # optional pod identifier

# ── Reconnexion ────────────────────────────────────────────────────────────────
RECONNECT_DELAY     = _int_env("RECONNECT_DELAY", 5)       # délai initial en secondes
RECONNECT_MAX_DELAY = _int_env("RECONNECT_MAX_DELAY", 60)  # délai maximum en secondes

# ── Entrypoint ─────────────────────────────────────────────────────────────────

def main() -> None:
    print("🚀 Geofencing service starting")
    print(f"   📹 Source      : {VIDEO_SOURCE}")
    print(f"   📐 Resolution  : {FRAME_WIDTH}x{FRAME_HEIGHT} @ {TARGET_FPS} fps")
    print(f"   📦 Min size    : {MIN_OBJECT_SIZE}px")
    print(f"   🔷 Polygon     : {POLYGON}")
    print(f"   💾 Capture dir : {CAPTURE_DIR} (every {CAPTURE_INTERVAL}s)")
    print(f"   🖥️  Headless    : {HEADLESS}")
    if KAFKA_BOOTSTRAP_SERVERS and KAFKA_TOPIC:
        print(f"   📨 Kafka       : {KAFKA_BOOTSTRAP_SERVERS} → {KAFKA_TOPIC}")
    else:
        print("   📨 Kafka       : disabled")

    zone = Zone(
        polygon=POLYGON,
        frame_width=FRAME_WIDTH,
        frame_height=FRAME_HEIGHT,
        min_object_size=MIN_OBJECT_SIZE,
    )

    analyzer = GeofencingAnalyzer()
    throttle = CaptureThrottle(interval=CAPTURE_INTERVAL)
    polygon_points = np.array(zone.polygon, np.int32).reshape((-1, 1, 2))
    frame_delay = int(1000 / TARGET_FPS)

    kafka = (
        KafkaPublisher(KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC)
        if KAFKA_BOOTSTRAP_SERVERS and KAFKA_TOPIC
        else None
    )

    os.makedirs(CAPTURE_DIR, exist_ok=True)

    delay = RECONNECT_DELAY
    try:
        while True:
            cap = cv2.VideoCapture(VIDEO_SOURCE)

            if not cap.isOpened():
                print(f"⚠️  Cannot open stream — retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, RECONNECT_MAX_DELAY)
                continue

            delay = RECONNECT_DELAY  # reset backoff on success
            print("✅ Stream opened — monitoring started")

            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"⚠️  Stream lost — reconnecting in {delay}s...")
                    cap.release()
                    time.sleep(delay)
                    delay = min(delay * 2, RECONNECT_MAX_DELAY)
                    break

                resized, mask = analyzer.preprocess_frame(frame, zone)
                events = analyzer.detect_intrusions(mask, zone, video_source=str(VIDEO_SOURCE), service_id=SERVICE_ID)

                if SHOW_ZONE:
                    cv2.polylines(resized, [polygon_points], isClosed=True, color=(0, 255, 0), thickness=2)

                if events:
                    for event in events:
                        print(f"🚨 Intrusion detected at {event.timestamp.strftime('%H:%M:%S')} — bbox {event.bbox}")
                        if SHOW_INTRUSION:
                            x, y, w, h = event.bbox
                            cv2.rectangle(resized, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    if throttle.is_ready():
                        filename = f"{CAPTURE_DIR}/{uuid.uuid4()}.jpg"
                        cv2.imwrite(filename, resized)
                        throttle.mark()
                        print(f"📸 Frame captured → {filename}")

                        if kafka:
                            for event in events:
                                event.capture_path = filename
                                kafka.publish(event)
                            print(f"📨 {len(events)} event(s) published to Kafka topic '{KAFKA_TOPIC}'")

                if SHOW_VIDEO:
                    cv2.imshow("Video", resized)

                if SHOW_MASK:
                    cv2.imshow("Masque", mask)

                if (SHOW_VIDEO or SHOW_MASK) and cv2.waitKey(frame_delay) & 0xFF == ord("q"):
                    print("🛑 Stop requested via keyboard")
                    cap.release()
                    return

    finally:
        if kafka:
            kafka.close()
        if SHOW_VIDEO or SHOW_MASK:
            cv2.destroyAllWindows()
        print("🔴 Geofencing service stopped")


if __name__ == "__main__":
    main()
