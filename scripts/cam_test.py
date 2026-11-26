import os

import cv2

print("Initializing camera ...")
cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cam.isOpened():
    raise SystemExit("Could not open camera device 0")
print("Camera initialized")

ok, im = cam.read()
if not ok or im is None:
    raise SystemExit("Camera read failed")
im = cv2.resize(im, (512, 512))
im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

path = os.path.expanduser("~/duck_capture.jpg")
cv2.imwrite(path, im)
print(f"Wrote {path}")
cam.release()
