import cv2

class VideoCapture:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        self.cap.release()
