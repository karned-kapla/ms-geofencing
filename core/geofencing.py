from datetime import datetime

import cv2
import numpy as np

from core.entities import Zone, IntrusionEvent

GAUSSIAN_BLUR_KERNEL = (5, 5)
MASK_THRESHOLD = 25


class GeofencingAnalyzer:
    def __init__(self):
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

    def preprocess_frame(self, frame: np.ndarray, zone: Zone) -> tuple[np.ndarray, np.ndarray]:
        resized = cv2.resize(frame, (zone.frame_width, zone.frame_height))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_KERNEL, 0)
        mask = self._bg_subtractor.apply(blurred)
        mask = cv2.threshold(mask, MASK_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        return resized, mask

    def detect_intrusions(self, mask: np.ndarray, zone: Zone) -> list[IntrusionEvent]:
        polygon = np.array(zone.polygon, np.int32).reshape((-1, 1, 2))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        events = []
        for contour in contours:
            if cv2.contourArea(contour) > zone.min_object_size:
                x, y, w, h = cv2.boundingRect(contour)
                if self._is_inside_polygon(x, y, w, h, polygon):
                    events.append(IntrusionEvent(timestamp=datetime.now(), bbox=(x, y, w, h)))

        return events

    def _is_inside_polygon(self, x: int, y: int, w: int, h: int, polygon: np.ndarray) -> bool:
        center = (x + w // 2, y + h // 2)
        return cv2.pointPolygonTest(polygon, center, False) >= 0

