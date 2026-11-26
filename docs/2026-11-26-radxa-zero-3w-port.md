# 将运行时移植到 Radxa Zero 3W

走路主循环在 `scripts/v2_rl_walk_mujoco.py`，观测用的是 `mini_bdx_runtime/mini_bdx_runtime/raw_imu.py` 的 `gyro` 和 `accelero`，再加脚开关。眼睛、耳朵、喇叭、投影仪是可选功能。预构建的树莓派镜像（`docs/INSTALL.md`、`docs/RELEASE_GUIDE.md`）不重做，只在文首标明它仍是 Pi Zero 2W 专用。

## 引脚

- 眼睛：19 脚 GPIO4_C3（`gpiochip4` 线 19）左，24 脚 GPIO4_C6（线 22）右，推挽输出
- 脚开关：29 脚 GPIO3_B3（`gpiochip3` 线 11）左，31 脚 GPIO3_B4（线 12）右，输入并打开内部上拉，按下为低
- 左耳：7 脚 PWM14_M0，控制器 `fe700020.pwm`
- 右耳：21 脚 PWM12_M1，控制器 `fe700000.pwm`（必须是 M1，不能是 M0）
- IMU：I2C4（`/dev/i2c-4`，27/28 脚），地址 `0x4B`，BNO085
- 喇叭：I2S3 dummy 声卡 `dummysound`
- 舵机总线：16 脚是板子 RX、18 脚是板子 TX，即 UART4_M1。飞特是单线半双工，软件只打开串口；总线和 3.3V 引脚之间仍要半双工转换，不能把 5V 数据线直接接到 16/18
- 投影仪：默认关闭。`duck_config.json` 里的 `projector_pin` 没写却打开投影仪时直接报错

## 接口

`mini_bdx_runtime/mini_bdx_runtime/zero3.py` 集中放脚位，以及按设备地址查找 `pwmchip`。

- GPIO 用系统里的 libgpiod 1.x（`python3-libgpiod`）
- 耳朵 PWM 用 sysfs：50 Hz，脉宽 1.0–2.0 ms，中位 1.5 ms。`stop()` 时把 `enable` 写成 0
- IMU 用 `adafruit-circuitpython-bno08x`，`adafruit-extended-bus` 打开 I2C 总线 4。加速度计和陀螺仪给走路；`imu.py` 的姿态用 Game Rotation Vector。读数后做和 BNO055 相同的轴变换：`upside_down` 时新坐标为 `(-y, -x, -z)`，否则为 `(-y, +x, +z)`。不再读写 `imu_calib_data.pkl`
- 摄像头用 OpenCV `VideoCapture`（V4L2）
- 手柄继续用 pygame。喇叭初始化前指定 ALSA 声卡 `dummysound`。配置在 `radxa/asoundrc`

`setup.cfg` 去掉 `adafruit-circuitpython-bno055`，加入 `adafruit-circuitpython-bno08x` 和 `adafruit-extended-bus`。不安装 pip 的 `gpiod` 2.x。

## 串口

`duck_config.json` 的 `serial_port` 默认 `/dev/ttyS4`。硬件接口和电机脚本都从这份配置读端口，波特率保持 1_000_000。仍用 USB 总线板时，把配置改成 `/dev/ttyACM0`。

## 自检

`scripts/check_zero3.py` 点亮左右眼、打印脚开关、两只耳朵在 1.2/1.5/1.8 ms 之间小幅摆动后关闭 PWM、打印一次陀螺仪和加速度。
