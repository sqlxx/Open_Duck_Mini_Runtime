"""Bring-up check for the Radxa Zero 3W wiring.

Lights each eye, prints the foot switches, moves both ear servos through
1.2 ms / 1.5 ms / 1.8 ms, then prints one gyro and accelerometer sample.
"""

import time

from mini_bdx_runtime.antennas import Antennas
from mini_bdx_runtime.feet_contacts import FeetContacts
from mini_bdx_runtime.raw_imu import Imu
from mini_bdx_runtime.zero3 import GpioLine, LEFT_EYE, RIGHT_EYE, value_to_pulse_ns


def run(name, fn):
    print(f"\n== {name} ==")
    try:
        fn()
    except Exception as err:
        print(f"FAIL: {err}")


def eyes():
    left = GpioLine(*LEFT_EYE, consumer="check-eye-left", output=True)
    right = GpioLine(*RIGHT_EYE, consumer="check-eye-right", output=True)
    try:
        print("left eye on")
        left.value = True
        time.sleep(0.6)
        left.value = False
        print("right eye on")
        right.value = True
        time.sleep(0.6)
        right.value = False
    finally:
        left.close()
        right.close()


def feet():
    contacts = FeetContacts()
    try:
        print("press each foot switch; printed pair is [left, right]")
        for _ in range(20):
            print(contacts.get())
            time.sleep(0.1)
    finally:
        contacts.stop()


def ears():
    antennas = Antennas()
    try:
        for value in (0.0, -0.6, 0.6, 0.0):
            pulse_ms = value_to_pulse_ns(value) / 1_000_000
            print(f"pulse {pulse_ms:.1f} ms")
            antennas.set_position(antennas.pwm_left, value, sign=1)
            antennas.set_position(antennas.pwm_right, value, sign=1)
            time.sleep(0.5)
    finally:
        antennas.stop()


def imu():
    sensor = Imu(50, upside_down=False)
    time.sleep(0.3)
    print(sensor.get_data())


if __name__ == "__main__":
    run("eyes", eyes)
    run("feet", feet)
    run("ears", ears)
    run("imu", imu)
