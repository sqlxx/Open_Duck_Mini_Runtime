import pygame
from threading import Thread
from queue import Queue
import time
import numpy as np
from mini_bdx_runtime.buttons import Buttons


X_RANGE = [-0.15, 0.15]
Y_RANGE = [-0.2, 0.2]
YAW_RANGE = [-1.0, 1.0]

# rads
NECK_PITCH_RANGE = [-0.34, 1.1]
HEAD_PITCH_RANGE = [-0.78, 0.3]
HEAD_YAW_RANGE = [-0.5, 0.5]
HEAD_ROLL_RANGE = [-0.5, 0.5]

# pygame joystick indices. Linux lists axes and buttons by evdev code.
# This DualShock 4 reports ABS_X, ABS_Y, ABS_Z (L2), ABS_RX, ABS_RY, ABS_RZ (R2).
# Its key bitmap includes the unused BTN_C and BTN_Z gaps, so the face
# buttons are Cross, Circle, Triangle, Square at 0, 1, 3, 4, and L1/R1 at 6/7.
XBOX_LAYOUT = {
    "lx": 0,
    "ly": 1,
    "rx": 2,
    "ry": 3,
    "l2": 5,
    "r2": 4,
    "a": 0,
    "b": 1,
    "x": 3,
    "y": 4,
    "lb": 6,
    "rb": 7,
}
PS4_LAYOUT = {
    "lx": 0,
    "ly": 1,
    "rx": 3,
    "ry": 4,
    "l2": 2,
    "r2": 5,
    "a": 0,  # Cross, pause
    "b": 1,  # Circle, sound
    "y": 3,  # Triangle, head control
    "x": 4,  # Square, projector
    "lb": 6,  # L1, sprint
    "rb": 7,  # R1
}


def _layout_for(joystick):
    name = joystick.get_name().lower()
    hints = ("wireless controller", "dualshock", "dualsense", "sony")
    if any(hint in name for hint in hints):
        return "ps4", PS4_LAYOUT
    return "xbox", XBOX_LAYOUT


class XBoxController:
    def __init__(self, command_freq, only_head_control=False):
        self.command_freq = command_freq
        self.head_control_mode = only_head_control
        self.only_head_control = only_head_control

        self.last_commands = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.last_left_trigger = 0.0
        self.last_right_trigger = 0.0
        pygame.init()
        self.p1 = pygame.joystick.Joystick(0)
        self.p1.init()
        self.pad_name, self.pad = _layout_for(self.p1)
        print(
            f"Loaded {self.pad_name} controller '{self.p1.get_name()}' "
            f"with {self.p1.get_numaxes()} axes."
        )
        self.cmd_queue = Queue(maxsize=1)

        self.A_pressed = False
        self.B_pressed = False
        self.X_pressed = False
        self.Y_pressed = False
        self.LB_pressed = False
        self.RB_pressed = False

        self.buttons = Buttons()

        Thread(target=self.commands_worker, daemon=True).start()

    def commands_worker(self):
        while True:
            self.cmd_queue.put(self.get_commands())
            time.sleep(1 / self.command_freq)

    def get_commands(self):
        last_commands = self.last_commands
        left_trigger = self.last_left_trigger
        right_trigger = self.last_right_trigger

        l_x = -1 * self.p1.get_axis(self.pad["lx"])
        l_y = -1 * self.p1.get_axis(self.pad["ly"])
        r_x = -1 * self.p1.get_axis(self.pad["rx"])
        r_y = -1 * self.p1.get_axis(self.pad["ry"])

        right_trigger = np.around((self.p1.get_axis(self.pad["r2"]) + 1) / 2, 3)
        left_trigger = np.around((self.p1.get_axis(self.pad["l2"]) + 1) / 2, 3)

        if left_trigger < 0.1:
            left_trigger = 0
        if right_trigger < 0.1:
            right_trigger = 0

        if not self.head_control_mode:
            lin_vel_y = l_x
            lin_vel_x = l_y
            ang_vel = r_x
            if lin_vel_x >= 0:
                lin_vel_x *= np.abs(X_RANGE[1])
            else:
                lin_vel_x *= np.abs(X_RANGE[0])

            if lin_vel_y >= 0:
                lin_vel_y *= np.abs(Y_RANGE[1])
            else:
                lin_vel_y *= np.abs(Y_RANGE[0])

            if ang_vel >= 0:
                ang_vel *= np.abs(YAW_RANGE[1])
            else:
                ang_vel *= np.abs(YAW_RANGE[0])

            last_commands[0] = lin_vel_x
            last_commands[1] = lin_vel_y
            last_commands[2] = ang_vel
        else:
            last_commands[0] = 0.0
            last_commands[1] = 0.0
            last_commands[2] = 0.0
            last_commands[3] = 0.0  # neck pitch 0 for now

            head_yaw = l_x
            head_pitch = l_y
            head_roll = r_x

            if head_yaw >= 0:
                head_yaw *= np.abs(HEAD_YAW_RANGE[0])
            else:
                head_yaw *= np.abs(HEAD_YAW_RANGE[1])

            if head_pitch >= 0:
                head_pitch *= np.abs(HEAD_PITCH_RANGE[0])
            else:
                head_pitch *= np.abs(HEAD_PITCH_RANGE[1])

            if head_roll >= 0:
                head_roll *= np.abs(HEAD_ROLL_RANGE[0])
            else:
                head_roll *= np.abs(HEAD_ROLL_RANGE[1])

            last_commands[4] = head_pitch
            last_commands[5] = head_yaw
            last_commands[6] = head_roll

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:

                if self.p1.get_button(self.pad["a"]):  # Cross / A, pause
                    self.A_pressed = True

                if self.p1.get_button(self.pad["b"]):  # Circle / B, sound
                    self.B_pressed = True

                if self.p1.get_button(self.pad["x"]):  # Square / X, projector
                    self.X_pressed = True

                if self.p1.get_button(self.pad["y"]):  # Triangle / Y, head control
                    self.Y_pressed = True
                    if not self.only_head_control:
                        self.head_control_mode = not self.head_control_mode

                if self.p1.get_button(self.pad["lb"]):  # L1 / LB, sprint
                    self.LB_pressed = True

                if self.p1.get_button(self.pad["rb"]):  # R1 / RB
                    self.RB_pressed = True

            if event.type == pygame.JOYBUTTONUP:
                self.A_pressed = False
                self.B_pressed = False
                self.X_pressed = False
                self.Y_pressed = False
                self.LB_pressed = False
                self.RB_pressed = False

            # for i in range(10):
            #     if self.p1.get_button(i):
            #         print(f"Button {i} pressed")

        up_down = self.p1.get_hat(0)[1]
        pygame.event.pump()  # process event queue

        return (
            np.around(last_commands, 3),
            self.A_pressed,
            self.B_pressed,
            self.X_pressed,
            self.Y_pressed,
            self.LB_pressed,
            self.RB_pressed,
            left_trigger,
            right_trigger,
            up_down,
        )

    def get_last_command(self):
        A_pressed = False
        B_pressed = False
        X_pressed = False
        Y_pressed = False
        LB_pressed = False
        RB_pressed = False
        up_down = 0
        try:
            (
                self.last_commands,
                A_pressed,
                B_pressed,
                X_pressed,
                Y_pressed,
                LB_pressed,
                RB_pressed,
                self.last_left_trigger,
                self.last_right_trigger,
                up_down,
            ) = self.cmd_queue.get(
                False
            )  # non blocking
        except Exception:
            pass

        self.buttons.update(
            A_pressed,
            B_pressed,
            X_pressed,
            Y_pressed,
            LB_pressed,
            RB_pressed,
            up_down == 1,
            up_down == -1,
        )

        return (
            self.last_commands,
            self.buttons,
            self.last_left_trigger,
            self.last_right_trigger,
        )

if __name__ == "__main__":
    controller = XBoxController(20)

    while True:
        print(controller.get_last_command())
        time.sleep(0.05)
