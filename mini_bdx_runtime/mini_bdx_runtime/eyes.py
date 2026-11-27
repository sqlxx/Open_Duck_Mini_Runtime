import random
import time
from threading import Thread, Event

from mini_bdx_runtime.zero3 import GpioLine, LEFT_EYE, RIGHT_EYE


class Eyes:
    def __init__(self, blink_duration=0.1, min_interval=1.0, max_interval=4.0):
        self.left_eye = GpioLine(*LEFT_EYE, consumer="duck-eye-left", output=True)
        self.right_eye = GpioLine(*RIGHT_EYE, consumer="duck-eye-right", output=True)

        self.blink_duration = blink_duration
        self.min_interval = min_interval
        self.max_interval = max_interval

        self._stop_event = Event()
        self._thread = Thread(target=self.run, daemon=True)
        self._thread.start()

    def _set_eyes(self, state):
        self.left_eye.value = state
        self.right_eye.value = state

    def run(self):
        try:
            while not self._stop_event.is_set():
                self._set_eyes(False)
                if self._stop_event.wait(self.blink_duration):
                    break
                self._set_eyes(True)
                next_blink = random.uniform(self.min_interval, self.max_interval)
                if self._stop_event.wait(next_blink):
                    break
        except Exception as err:
            print(f"Error in eye thread: {err}")
            self._stop_event.set()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self._set_eyes(False)
        self.left_eye.close()
        self.right_eye.close()


if __name__ == "__main__":
    e = Eyes()
    try:
        while True:
            time.sleep(1)
    finally:
        e.stop()
