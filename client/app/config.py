"""
title:   RealSenseOPC client application config class
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import configparser


class Config():
    def __init__(self, file_name):
        self.__file_name = file_name
        