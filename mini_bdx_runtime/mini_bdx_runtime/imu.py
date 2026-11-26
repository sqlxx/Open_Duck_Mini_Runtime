import time
from queue import Queue
from threading import Thread

import adafruit_bno08x
import numpy as np
from scipy.spatial.transform import Rotation as R

from mini_bdx_runtime.zero3 import open_bno085, remap_matrix


class Imu:
    def __init__(
        self, sampling_freq, user_pitch_bias=0, calibrate=False, upside_down=True
    ):
        self.sampling_freq = sampling_freq
        self.user_pitch_bias = user_pitch_bias
        self.nominal_pitch_bias = 0
        self.calibrate = calibrate
        self.upside_down = upside_down

        self.imu = open_bno085()
        self.imu.enable_feature(adafruit_bno08x.BNO_REPORT_GAME_ROTATION_VECTOR)
        self._remap = R.from_matrix(remap_matrix(upside_down))

        if self.calibrate:
            print("BNO085 calibrates inside the chip. imu_calib_data.pkl is not used.")

        self.pitch_bias = self.nominal_pitch_bias + self.user_pitch_bias

        self.last_imu_data = [0, 0, 0, 0]
        self.imu_queue = Queue(maxsize=1)
        Thread(target=self.imu_worker, daemon=True).start()

    def convert_axes(self, euler):
        euler = [np.pi + euler[1], euler[0], euler[2]]
        return euler

    def imu_worker(self):
        while True:
            s = time.time()
            try:
                # BNO085 game quaternion is (i, j, k, real): scalar last.
                raw_orientation = self.imu.game_quaternion
                if raw_orientation is None:
                    continue
                orientation = R.from_quat(raw_orientation) * self._remap.inv()
                euler = orientation.as_euler("xyz").copy()
            except Exception as e:
                print("[IMU]:", e)
                continue

            euler[1] -= np.deg2rad(self.pitch_bias)

            # scalar last, which is what isaac wants
            final_orientation_quat = R.from_euler("xyz", euler).as_quat()

            self.imu_queue.put(final_orientation_quat.copy())
            took = time.time() - s
            time.sleep(max(0, 1 / self.sampling_freq - took))

    def get_data(self, euler=False, mat=False):
        try:
            self.last_imu_data = self.imu_queue.get(False)  # non blocking
        except Exception:
            pass

        try:
            if not euler and not mat:
                return self.last_imu_data
            elif euler:
                return R.from_quat(self.last_imu_data).as_euler("xyz")
            elif mat:
                return R.from_quat(self.last_imu_data).as_matrix()

        except Exception as e:
            print("[IMU]: ", e)
            return None


if __name__ == "__main__":
    imu = Imu(50, calibrate=True, upside_down=False)
    while True:
        data = imu.get_data()
        print("quat", np.around(data, 3))
        print("---")
        time.sleep(1 / 25)
