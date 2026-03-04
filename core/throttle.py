import time


class CaptureThrottle:
    def __init__(self, interval: float):
        self._interval = interval
        self._last_capture: float = 0

    def is_ready(self) -> bool:
        return time.time() - self._last_capture > self._interval

    def mark(self) -> None:
        self._last_capture = time.time()

