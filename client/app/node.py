"""
title:   RealSenseOPC client application node class
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import opcua
import opcua.ua.uatypes
from opcua import ua


class Node():
    def __init__(self, name, address, uatype):
        self.__name = name
        self.__address = address
        self.__type = uatype
    def set_value(self, value):
        pass