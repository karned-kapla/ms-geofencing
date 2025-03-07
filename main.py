import cv2
import numpy as np

from src.video_capture import VideoCapture
from src.intrusion_detection import IntrusionDetector
from src.capture_management import CaptureManager
from src.user_interface import UserInterface

def main():
    video_source = 'rtsp://192.168.1.107/live1.sdp'
    api_url = 'http://your_api_endpoint'
    polygon_points = np.array([[50, 100], [200, 100], [450, 300], [150, 350]], np.int32)
    polygon_points = polygon_points.reshape((-1, 1, 2))

    video_capture = VideoCapture(video_source)
    intrusion_detector = IntrusionDetector(polygon_points)
    capture_manager = CaptureManager(api_url)
    user_interface = UserInterface()

    while True:
        frame = video_capture.read_frame()
        if frame is None:
            break

        intrusion, capture = intrusion_detector.detect(frame)
        """ 
        if intrusion:
            status_code = capture_manager.send_capture(capture)
            print(f'Capture sent. Status code: {status_code}')
        """
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if not user_interface.display(frame, intrusion_detector.bg_subtractor.apply(frame), intrusion):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
