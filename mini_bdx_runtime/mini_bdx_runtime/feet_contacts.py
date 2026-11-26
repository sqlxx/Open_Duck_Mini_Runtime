import time

from mini_bdx_runtime.zero3 import GpioLine, LEFT_FOOT, RIGHT_FOOT


class FeetContacts:
    def __init__(self):
        self.left_foot = GpioLine(
            *LEFT_FOOT, consumer="duck-foot-left", output=False, pull_up=True
        )
        self.right_foot = GpioLine(
            *RIGHT_FOOT, consumer="duck-foot-right", output=False, pull_up=True
        )

    def get(self):
        left = not self.left_foot.value
        right = not self.right_foot.value
        return [left, right]

    def stop(self):
        self.left_foot.close()
        self.right_foot.close()


if __name__ == "__main__":
    feet_contacts = FeetContacts()
    try:
        while True:
            print(feet_contacts.get())
            time.sleep(0.05)
    finally:
        feet_contacts.stop()
