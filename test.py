import uuid

import cv2
import numpy as np
import json
import time
from kafka import KafkaProducer

CONFIG_PATH = "config.json"

last_capture = 0


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


config = load_config()

def is_inside_polygon( x, y, w, h, polygon ):
    rect_center = (x + w // 2, y + h // 2)
    return cv2.pointPolygonTest(polygon, rect_center, False) >= 0


cap = cv2.VideoCapture(config["video_detection"])
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

    intrusion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) > config["min_object_size"]:
            x, y, w, h = cv2.boundingRect(contour)
            if is_inside_polygon(x, y, w, h, polygon_points):
                intrusion_detected = True

    if intrusion_detected:
        now = time.time()
        if int(now - last_capture) > 5:
            print("Intrusion detected !")
            uuid_img = str(uuid.uuid4())
            cv2.imwrite(f"tmp/{uuid_img}.jpg", frame)
            last_capture = now

    if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
