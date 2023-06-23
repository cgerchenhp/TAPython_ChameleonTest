# -*- coding: utf-8 -*-
import unreal
import numpy as np
import math
from Utilities.Utils import Singleton


class ImagePainter(metaclass=Singleton):
    def __init__(self, jsonPath:str):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_image = "ImageCanvas"
        self.ui_output = "Output"
        self.width = self.height = 64
        self.im = np.ones((self.height, self.width, 4), dtype=np.uint8) * 255
        self.im[:, :, 0:3] = self.im[:, :, 0:3] * 0.5

        self.brush = np.ones((8, 8, 1), dtype=np.uint8)

        for y in range(8):
            for x in range(8):
                v = max(0, 4-math.sqrt((x-4)*(x-4) + (y-4)*(y-4)))/4 * 255
                self.brush[y, x, 0] = 0


        a = 0.25
        b = 0.5
        c = 0.75
        array = [
            0, a, b, c, c, b, a, 0,
            a, c, 1, 1, 1, 1, c, a,
            b, 1, 1, 1, 1, 1, 1, b,
            c, 1, 1, 1, 1, 1, 1, c,
            c, 1, 1, 1, 1, 1, 1, c,
            b, 1, 1, 1, 1, 1, 1, b,
            a, c, 1, 1, 1, 1, c, a,
            0, a, b, c, c, b, a, 0
        ]
        array = [1-x for x in array]
        self.brush = np.array( array, dtype=np.uint8).reshape((8,8,1)) * 255



        self.data.set_image_data(self.ui_image, self.im.data.tobytes(), self.width, self.height, channel_num=3)

    def on_button_click(self):
        pass

    def on_mouse_move(self, uv, mouse_flags):
        self.data.set_text(self.ui_output, f"{uv}, mouse_flags: {mouse_flags}")
        x = round(uv[0] * self.width)
        y = round(uv[1] * self.height)

        if mouse_flags == 4:
            s = 0
            e = 1
        elif mouse_flags == 2:
            s = 1
            e = 2
        elif mouse_flags == 1:
            s = 2
            e = 3

        if mouse_flags:
            if mouse_flags == 1:
                self.im[y-4:y+4, x-4:x+4, 3:4] = np.minimum(self.im[y-4:y+4, x-4:x+4, 3:4], self.brush)
            else:
                self.im[y - 4:y + 4, x - 4:x + 4, e:s] = +np.maximum(self.im[y - 4:y + 4, x - 4:x + 4, e:s], self.brush)
                self.im[y - 4:y + 4, x - 4:x + 4, 3:4] = np.maximum(self.im[y - 4:y + 4, x - 4:x + 4, 3:4], self.brush)


        self.data.set_image_data(self.ui_image, self.im.data.tobytes(), self.width, self.height, channel_num=4)

    def on_mouse_leave(self, mouse_flags):
        print("mouse leave")

    def reset(self):
        self.im = np.ones((self.height, self.width, 4), dtype=np.uint8) * 255
        self.im[:, :, 0:3] = self.im[:, :, 0:3] * 0.5
        self.data.set_image_data(self.ui_image, self.im.data.tobytes(), self.width, self.height, channel_num=4)

    def on_tick(self):
        pass