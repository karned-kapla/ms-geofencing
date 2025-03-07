import cv2

class UserInterface:
    def __init__(self, frame_delay=10):
        self.frame_delay = frame_delay

    def display(self, frame, mask, intrusion_detected=False):
        if intrusion_detected:
            cv2.putText(frame, "Intrusion detectee!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        cv2.imshow("Video", frame)
        cv2.imshow("Masque", mask)

        if cv2.waitKey(self.frame_delay) & 0xFF == ord('q'):
            return False
        return True

    def close(self):
        cv2.destroyAllWindows()
