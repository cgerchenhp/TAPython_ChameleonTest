# -*- coding: utf-8 -*-
import random
import numpy as np

import unreal
from Utilities.Utils import Singleton


class ChameleonTest(metaclass=Singleton):
    def __init__(self, jsonPath:str):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_image = "imageInUI"
        self.ui_output = "OutputText"
        self.rt = None

    def load_rt_if_needed(self):
        if not self.rt:
            self.rt = unreal.load_asset("/Game/Chameleon/Rt_forRawData")

    def on_button_FillSlate_click(self):
        print("fillSlate call")
        width = height = 1

        image_im = np.ones((height, width, 1), dtype=np.uint8) * random.randint(0, 255)
        self.data.set_image_data(self.ui_image, image_im.data.tobytes(), width=width, height=height, channel_num=1)

        print("Done")


    def on_button_fillRtOnePixel_click(self):
        self.load_rt_if_needed()
        unreal.PythonTextureLib.set_render_target_data(self.rt, raw_data=b'\xff', raw_data_width=1, raw_data_height=1, raw_data_channel_num=1)


    def fill_check_pixels(self):
        width = 256
        height = 128
        im = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                im[y, x, 0] = x
                im[y, x, 1] = y
        image_bytes = im.data.tobytes()
        unreal.PythonTextureLib.set_render_target_data(self.rt, raw_data=image_bytes
                                                       , raw_data_width=width
                                                       , raw_data_height=height
                                                       , raw_data_channel_num=3
                                                       , use_srgb=False
                                                       , texture_filter_value=0)

    def fill_checkboard(self):
        width = height = 256
        im = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                im[y, x] = 255 if x % 2 == y % 2 else 0
        unreal.PythonTextureLib.set_render_target_data(self.rt, raw_data=im.data.tobytes()
                                                        , raw_data_width=width
                                                        , raw_data_height=height
                                                        , raw_data_channel_num=1
                                                        , use_srgb=False
                                                        , texture_filter_value=0)


    def on_button_fillRt_click(self):
        print("fillRt call")
        self.load_rt_if_needed()
        raw_data = b'\xff\xff\xff'
        raw_data += b'\x00\x00\x00'
        raw_data += b'\xff\x00\x00'
        raw_data += b'\x00\xff\x00'

        unreal.PythonTextureLib.set_render_target_data(self.rt, raw_data
                                                       , raw_data_width=2
                                                       , raw_data_height=2
                                                       , raw_data_channel_num=3
                                                       , use_srgb=False
                                                       , texture_filter_value=0
                                                       , bgr=True)
        print(f"Set slate ")







