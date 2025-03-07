import cv2
import requests

class CaptureManager:
    def __init__(self, api_url):
        self.api_url = api_url

    def send_capture(self, capture):
        _, buffer = cv2.imencode('.jpg', capture)
        response = requests.post(self.api_url, files={'capture': buffer.tobytes()})
        return response.status_code
