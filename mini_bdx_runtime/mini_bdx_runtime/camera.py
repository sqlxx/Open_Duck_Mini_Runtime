import base64
import os

import cv2


class Cam:
    def __init__(self, device=0):
        self.cam = cv2.VideoCapture(device, cv2.CAP_V4L2)
        if not self.cam.isOpened():
            raise RuntimeError(f"Could not open camera device {device}")

    def capture_array(self):
        ok, frame = self.cam.read()
        if not ok or frame is None:
            raise RuntimeError("Camera read failed")
        return frame

    def get_encoded_image(self):
        im = self.capture_array()
        im = cv2.resize(im, (512, 512))
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)

        path = os.path.expanduser("~/duck_capture.jpg")
        cv2.imwrite(path, im)

        return self.encode_image(path)

    def encode_image(self, image_path: str):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def close(self):
        self.cam.release()
