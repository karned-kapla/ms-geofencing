import cv2
import numpy as np

class IntrusionDetector:
    def __init__(self, polygon_points):
        self.polygon_points = polygon_points
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True
        )

    def detect(self, frame):
        frame = cv2.resize(frame, (640, 360))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        mask = self.bg_subtractor.apply(blurred)

        # Afficher le masque avant le seuillage pour diagnostic
        cv2.imshow("Raw Mask", mask)

        # Ajuster le seuil pour améliorer la détection
        _, mask = cv2.threshold(mask, 25, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                if self.is_inside_polygon(x, y, w, h):
                    return True, frame
        return False, None

    def is_inside_polygon(self, x, y, w, h):
        rect_center = (x + w // 2, y + h // 2)
        return cv2.pointPolygonTest(self.polygon_points, rect_center, False) >= 0
