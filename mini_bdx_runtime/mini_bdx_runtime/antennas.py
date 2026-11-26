import math
import time

from mini_bdx_runtime.zero3 import (
    LEFT_EAR_PWM,
    PwmServo,
    RIGHT_EAR_PWM,
    value_to_pulse_ns,
)

LEFT_SIGN = 1
RIGHT_SIGN = -1
MIN_UPDATE_INTERVAL = 1 / 50  # 20ms


class Antennas:
    def __init__(self):
        self.pwm_left = PwmServo(LEFT_EAR_PWM)
        self.pwm_right = PwmServo(RIGHT_EAR_PWM)

    def set_position_left(self, position):
        self.set_position(self.pwm_left, position, LEFT_SIGN)

    def set_position_right(self, position):
        self.set_position(self.pwm_right, position, RIGHT_SIGN)

    def set_position(self, pwm, value, sign=1):
        if -1 <= value <= 1:
            pwm.set_pulse_ns(value_to_pulse_ns(value * sign))
        else:
            print("Invalid input! Enter a value between -1 and 1.")

    def stop(self):
        time.sleep(MIN_UPDATE_INTERVAL)
        self.set_position_left(0)
        self.set_position_right(0)
        time.sleep(MIN_UPDATE_INTERVAL)
        self.pwm_left.stop()
        self.pwm_right.stop()


if __name__ == "__main__":
    antennas = Antennas()

    try:
        start_time = time.monotonic()
        current_time = start_time

        while current_time - start_time < 5:
            value = math.sin(2 * math.pi * 1 * current_time)
            antennas.set_position_left(value)
            antennas.set_position_right(value)
            time.sleep(MIN_UPDATE_INTERVAL)
            current_time = time.monotonic()

    finally:
        antennas.stop()
