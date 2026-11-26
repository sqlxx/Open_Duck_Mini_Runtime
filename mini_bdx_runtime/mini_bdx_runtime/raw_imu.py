import time
from queue import Queue
from threading import Thread

import adafruit_bno08x
import numpy as np

from mini_bdx_runtime.zero3 import open_bno085, remap_vector


class Imu:
    def __init__(
        self, sampling_freq, user_pitch_bias=0, calibrate=False, upside_down=True
    ):
        self.sampling_freq = sampling_freq
        self.user_pitch_bias = user_pitch_bias
        self.calibrate = calibrate
        self.upside_down = upside_down

        self.imu = open_bno085()
        self.imu.enable_feature(adafruit_bno08x.BNO_REPORT_GYROSCOPE)
        self.imu.enable_feature(adafruit_bno08x.BNO_REPORT_ACCELEROMETER)

        if self.calibrate:
            print("BNO085 calibrates inside the chip. imu_calib_data.pkl is not used.")

        self.x_offset = 0

        self.last_imu_data = {
            "gyro": [0, 0, 0],
            "accelero": [0, 0, 0],
        }
        self.imu_queue = Queue(maxsize=1)
        Thread(target=self.imu_worker, daemon=True).start()

    def tare_x(self):
        print("Taring x ...")
        x_values = []
        num_values = 100
        ok = False
        while not ok:
            accel = self.imu.acceleration
            if accel is None:
                time.sleep(0.01)
                continue
            x_values.append(remap_vector(accel, self.upside_down)[0])

            x_values = x_values[-num_values:]

            if len(x_values) == num_values:
                mean = np.mean(x_values)
                std = np.std(x_values)
                if std < 0.05:
                    ok = True
                    self.x_offset = mean
                    print("Tare x done")
                else:
                    print(std)

            time.sleep(0.01)

    def imu_worker(self):
        while True:
            s = time.time()
            try:
                gyro = self.imu.gyro
                accelero = self.imu.acceleration
            except Exception as e:
                print("[IMU]:", e)
                continue

            if gyro is None or accelero is None:
                continue

            gyro = remap_vector(gyro, self.upside_down)
            accelero = remap_vector(accelero, self.upside_down)
            accelero[0] -= self.x_offset

            data = {
                "gyro": gyro,
                "accelero": accelero,
            }

            self.imu_queue.put(data)
            took = time.time() - s
            time.sleep(max(0, 1 / self.sampling_freq - took))

    def get_data(self):
        try:
            self.last_imu_data = self.imu_queue.get(False)  # non blocking
        except Exception:
            pass

        return self.last_imu_data


if __name__ == "__main__":
    imu = Imu(50, upside_down=False)
    while True:
        data = imu.get_data()
        print("gyro", np.around(data["gyro"], 3))
        print("accelero", np.around(data["accelero"], 3))
        print("---")
        time.sleep(1 / 25)
