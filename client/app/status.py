"""
title:   RealSenseOPC status class
author:  Nicholas Loehrke 
date:    June 2022
"""

import inspect

TEMP_WARNING = 35
TEMP_MAX_SAFE = 50
TEMP_CRITICAL = 55


class StatusCodes:
    ERROR_UPDATING_STATUS = 1
    OK = 0
    ERROR_NO_RESTART = -1
    ERROR_RESTART = -2
    ERROR_TEMP_WARNING = -3
    ERROR_TEMP_MAX_SAFE = -4
    ERROR_TEMP_CRITICAL = -5

    def name(code):
        error = 'unknown'
        try:
            for i in inspect.getmembers(StatusCodes):
                if not i[0].startswith('_'):
                    if i[1] == code:
                        error = i[0]
        except Exception:
            pass
        return error
