import cv2
import numpy as np
import json
import time
from kafka import KafkaProducer

CONFIG_PATH = "config.json"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


config = load_config()

producer = KafkaProducer(
    bootstrap_servers=config["kafka_broker"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def is_inside_polygon( x, y, w, h, polygon ):
    """Vérifie si un rectangle est à l'intérieur du polygone."""
    rect_center = (x + w // 2, y + h // 2)
    return cv2.pointPolygonTest(polygon, rect_center, False) >= 0


# Chargement du flux vidéo
cap = cv2.VideoCapture(config["video_source"])
FRAME_WIDTH = config["frame_width"]
FRAME_HEIGHT = config["frame_height"]
TARGET_FPS = config["target_fps"]
frame_delay = int(1000 / TARGET_FPS)
polygon_points = np.array(config["polygon"], np.int32).reshape((-1, 1, 2))
bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    mask = bg_subtractor.apply(blurred)
    mask = cv2.threshold(mask, 25, 255, cv2.THRESH_BINARY)[1]

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.polylines(frame, [polygon_points], isClosed=True, color=(0, 255, 0), thickness=3)

    intrusion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) > config["min_object_size"]:
            x, y, w, h = cv2.boundingRect(contour)
            if is_inside_polygon(x, y, w, h, polygon_points):
                intrusion_detected = True
                cv2.putText(frame, "Intrusion detectee!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    if intrusion_detected:
        producer.send(config["kafka_topic"], {"event": "intrusion", "timestamp": time.time()})

    cv2.imshow("Video", frame)
    cv2.imshow("Masque", mask)

    if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
