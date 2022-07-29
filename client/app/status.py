"""
title:   RealSenseOPC status class
author:  Nicholas Loehrke 
date:    June 2022
"""

import inspect

TEMP_WARNING = 40
TEMP_MAX_SAFE = 50
TEMP_CRITICAL = 55
ROI_HIGH_INVALID = 60


class StatusCodes:
    ERROR_UPDATING_STATUS = 1
    OK = 0
    ERROR_NO_RESTART = -1
    ERROR_RESTART = -2
    ERROR_TEMP_WARNING = -3
    ERROR_TEMP_MAX_SAFE = -4
    ERROR_TEMP_CRITICAL = -5
    ERROR_HIGH_INVALID_PERCENTAGE = -6


class Status:
    def __init__(self, camera, nodes: dict):
        self._camera = camera
        self._nodes = nodes

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

    def update_status(self):
        status = StatusCodes.OK
        try:
            asic_temp = self._camera.asic_temperature
            projector_temp = self._camera.projector_temperature

            temp_warning = asic_temp > TEMP_WARNING or projector_temp > TEMP_WARNING
            temp_max_safe = asic_temp > TEMP_MAX_SAFE or projector_temp > TEMP_MAX_SAFE
            temp_critical = asic_temp > TEMP_CRITICAL or projector_temp > TEMP_CRITICAL
            high_invalid = self._nodes['roi_invalid'] > ROI_HIGH_INVALID

            if temp_critical:
                status = StatusCodes.ERROR_TEMP_CRITICAL
            elif temp_max_safe:
                status = StatusCodes.ERROR_TEMP_MAX_SAFE
            elif temp_warning:
                status = StatusCodes.ERROR_TEMP_WARNING
            elif high_invalid:
                status = StatusCodes.ERROR_HIGH_INVALID_PERCENTAGE

        except Exception as e:
            status = StatusCodes.ERROR_UPDATING_STATUS

        return status
