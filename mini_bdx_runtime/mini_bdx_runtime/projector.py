import time

from mini_bdx_runtime.zero3 import GpioLine, parse_projector_pin


class Projector:
    def __init__(self, pin=None):
        chip, line = parse_projector_pin(pin)
        self.project = GpioLine(chip, line, consumer="duck-projector", output=True)
        self.on = False

    def switch(self):
        self.on = not self.on
        self.project.value = self.on

    def stop(self):
        self.project.value = False
        self.project.close()


if __name__ == "__main__":
    import sys

    pin = sys.argv[1] if len(sys.argv) > 1 else None
    p = Projector(pin)
    try:
        while True:
            p.switch()
            time.sleep(1)
    finally:
        p.stop()
