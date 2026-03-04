import uuid
import json

import cv2
import numpy as np

from core.entities import Zone
from core.geofencing import GeofencingAnalyzer
from core.throttle import CaptureThrottle

CONFIG_PATH = "config_webcam.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def main() -> None:
    config = load_config()

    zone = Zone(
        polygon=config["polygon"],
        frame_width=config["frame_width"],
        frame_height=config["frame_height"],
        min_object_size=config["min_object_size"],
    )

    analyzer = GeofencingAnalyzer()
    throttle = CaptureThrottle(interval=config["capture_interval"])
    polygon_points = np.array(zone.polygon, np.int32).reshape((-1, 1, 2))
    frame_delay = int(1000 / config["target_fps"])

    cap = cv2.VideoCapture(config["video_source"])

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        resized, mask = analyzer.preprocess_frame(frame, zone)
        events = analyzer.detect_intrusions(mask, zone)

        print(events)

        if config["show_zone"]:
            cv2.polylines(resized, [polygon_points], isClosed=True, color=(0, 255, 0), thickness=2)

        if events:
            if config["show_intrusion"]:
                for event in events:
                    x, y, w, h = event.bbox
                    #cv2.putText(resized, "Intrusion !", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.rectangle(resized, (x, y), (x + w, y + h), (0, 0, 255), 2)

            if throttle.is_ready():
                cv2.imwrite(f"tmp/{uuid.uuid4()}.jpg", resized)
                throttle.mark()

        if config["show_video"]:
            cv2.imshow("Video", resized)

        if config["show_mask"]:
            cv2.imshow("Masque", mask)

        if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
