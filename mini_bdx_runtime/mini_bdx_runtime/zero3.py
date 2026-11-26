"""Radxa Zero 3W pin map and hardware helpers.

Header wiring used on this duck:
  pin 19 GPIO4_C3  left eye LED
  pin 24 GPIO4_C6  right eye LED
  pin 29 GPIO3_B3  left foot switch
  pin 31 GPIO3_B4  right foot switch
  pin 7  PWM14_M0  left ear servo   (fe700020.pwm)
  pin 21 PWM12_M1  right ear servo  (fe700000.pwm)
  pins 27/28 I2C4  BNO085 at 0x4B
  pins 16/18 UART4_M1 Feetech bus (/dev/ttyS4)
"""

from pathlib import Path

import numpy as np

I2C_BUS = 4
IMU_ADDRESS = 0x4B
SERIAL_PORT = "/dev/ttyS4"
ALSA_CARD = "dummysound"

LEFT_EYE = ("gpiochip4", 19)
RIGHT_EYE = ("gpiochip4", 22)
LEFT_FOOT = ("gpiochip3", 11)
RIGHT_FOOT = ("gpiochip3", 12)

LEFT_EAR_PWM = "fe700020"
RIGHT_EAR_PWM = "fe700000"

SERVO_PERIOD_NS = 20_000_000
SERVO_MIN_PULSE_NS = 1_000_000
SERVO_MAX_PULSE_NS = 2_000_000
SERVO_CENTER_PULSE_NS = 1_500_000


def remap_matrix(upside_down: bool) -> np.ndarray:
    """Same axis change the BNO055 driver applied in the chip.

    upside_down: (x, y, z) -> (-y, -x, -z)
    otherwise:   (x, y, z) -> (-y,  x,  z)
    """
    if upside_down:
        return np.array(
            [[0.0, -1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
            dtype=float,
        )
    return np.array(
        [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )


def remap_vector(vec, upside_down: bool) -> np.ndarray:
    return remap_matrix(upside_down) @ np.asarray(vec, dtype=float)


class GpioLine:
    def __init__(
        self,
        chip_name: str,
        offset: int,
        consumer: str,
        output: bool,
        pull_up: bool = False,
    ):
        import gpiod

        self._chip = gpiod.Chip(chip_name)
        self._line = self._chip.get_line(offset)
        if output:
            self._line.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT)
        else:
            flags = gpiod.LINE_REQ_FLAG_BIAS_PULL_UP if pull_up else 0
            self._line.request(
                consumer=consumer, type=gpiod.LINE_REQ_DIR_IN, flags=flags
            )

    @property
    def value(self) -> int:
        return self._line.get_value()

    @value.setter
    def value(self, state: bool):
        self._line.set_value(1 if state else 0)

    def close(self):
        self._line.release()
        self._chip.close()


def parse_projector_pin(pin):
    if pin is None:
        raise RuntimeError(
            "projector is enabled but projector_pin is not set in duck_config.json. "
            'Set it to {"chip": "gpiochip3", "line": 1} for the header pin you wired.'
        )
    if isinstance(pin, str) and ":" in pin:
        chip, line = pin.split(":", 1)
        return chip, int(line)
    if isinstance(pin, dict) and "chip" in pin and "line" in pin:
        return pin["chip"], int(pin["line"])
    raise RuntimeError(
        'projector_pin must be {"chip": "gpiochip3", "line": 1} or "gpiochip3:1"'
    )


def find_pwmchip(address: str) -> Path:
    root = Path("/sys/class/pwm")
    if not root.is_dir():
        raise RuntimeError(
            "PWM sysfs is not available. Enable pwm14-m0 and pwm12-m1 in rsetup, then reboot."
        )
    for chip in sorted(root.glob("pwmchip*")):
        device = (chip / "device").resolve()
        if address in device.name:
            return chip
    raise RuntimeError(
        f"PWM controller {address}.pwm was not found. "
        "Enable pwm14-m0 for the left ear and pwm12-m1 for the right ear, then reboot."
    )


def _write_sysfs(path: Path, text: str):
    payload = text if str(text).endswith("\n") else f"{text}\n"
    try:
        path.write_text(payload)
    except OSError as err:
        raise RuntimeError(f"Cannot write {path}: {err}") from err


class PwmServo:
    def __init__(self, address: str):
        import time

        chip = find_pwmchip(address)
        self._pwm = chip / "pwm0"
        if not self._pwm.is_dir():
            _write_sysfs(chip / "export", "0")
            time.sleep(0.05)
        self._disable()
        polarity = self._pwm / "polarity"
        if polarity.exists():
            _write_sysfs(polarity, "normal")
        _write_sysfs(self._pwm / "period", str(SERVO_PERIOD_NS))
        self.set_pulse_ns(SERVO_CENTER_PULSE_NS)
        _write_sysfs(self._pwm / "enable", "1")

    def set_pulse_ns(self, pulse_ns: int):
        pulse_ns = int(min(max(pulse_ns, SERVO_MIN_PULSE_NS), SERVO_MAX_PULSE_NS))
        _write_sysfs(self._pwm / "duty_cycle", str(pulse_ns))

    def _disable(self):
        enable = self._pwm / "enable"
        if enable.exists():
            _write_sysfs(enable, "0")

    def stop(self):
        self.set_pulse_ns(SERVO_CENTER_PULSE_NS)
        self._disable()


def value_to_pulse_ns(value: float) -> int:
    pulse_ms = 1.5 + (value * 0.5)
    return int(round(pulse_ms * 1_000_000))


def open_bno085():
    from adafruit_bno08x.i2c import BNO08X_I2C
    from adafruit_extended_bus import ExtendedI2C

    i2c = ExtendedI2C(I2C_BUS)
    return BNO08X_I2C(i2c, address=IMU_ADDRESS)
