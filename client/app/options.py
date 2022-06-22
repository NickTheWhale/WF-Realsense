"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import logging as log
from matplotlib.style import available

import pyrealsense2 as rs


class Options():
    def __init__(self, profile, config):
        self.__profile = profile
        self.__config = config
        self.__available_options = []
        self.__depth_sensor = self.__profile.get_device().first_depth_sensor()

    def get_available_options(self):
        available_options = []
        options = self.__depth_sensor.get_supported_options()
        for option in options:
            if self.__depth_sensor.is_option_read_only(option) is False:
                available_options.append(option)
        return available_options
        
    def set_all_options(self):
        raise NotImplementedError

    def __option_valid(self):
        raise NotImplementedError

    def __scale_option_value(self):
        raise NotImplementedError

    def __set_option(self):
        raise NotImplementedError
    
    def get_config_options(self):
        for option in self.__config['camera']:
            print(option)
