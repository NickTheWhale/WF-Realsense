"""
title:   RealSenseOPC client application options class
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import difflib as diff
import logging as log

import pyrealsense2 as rs


class Options():
    def __init__(self, profile, config):
        """create an Options() object to get and set camera settings

        :param profile: realsense camera profile
        :type profile: pyrealsense2.profile
        :param config: configuration dictionary
        :type config: dict
        """
        self.__profile = profile
        self.__config = config
        self.__camera_options = []
        self.__user_options = []
        self.__depth_sensor = self.__profile.get_device().first_depth_sensor()

    def get_camera_options(self):
        """queries depth sensor and retrieves all supported options

        :return: camera options
        :rtype: list
        """
        cam_ops = self.__depth_sensor.get_supported_options()
        for op in cam_ops:
            op = op.name
            self.__camera_options.append(op)
        return self.__camera_options

    def get_user_options(self):
        """appends configuration options in the 'camera' section

        :return: every key under the 'camera' section, including those
        which do not pertain to 'pyrealsense2.option'
        :rtype: list
        """
        usr_ops = self.__config['camera']
        for op in usr_ops:
            self.__user_options.append(op)
        return self.__user_options

    def set_all_options(self):
        """checks if the user option exists in the available camera options list,
        checks if option exists within 'pyrealsense2.option', and finally checks
        if the option is writable or readonly. If an option fails to set, the 
        method attempts to find the closest match. The closest match will NOT be
        attempted to set, but logged as a warning
        """
        cam_ops = self.__camera_options
        usr_ops = self.__user_options

        for set_op in usr_ops:
            if cam_ops.count(set_op) > 0:
                if hasattr(rs.option, set_op):
                    if self.writable(set_op):
                        self.set_rs_option(set_op)

            else:
                closest_match = diff.get_close_matches(
                    set_op, self.__camera_options, cutoff=0.7)
                if len(closest_match) > 0:
                    log.warning(
                        f'Failed to set "{set_op}". Did you mean "{closest_match[0]}"?')
                else:
                    log.warning(f'Failed to set "{set_op}"')

    def writable(self, option):
        """checks if 'option' is able to be written to

        :param option: pyrealsense2.option name
        :type option: string
        :return: true if option is writable, false if readonly
        :rtype: bool
        """
        option = getattr(rs.option, option)
        return not self.__depth_sensor.is_option_read_only(option)

    def constrain_option_value(self, option, set_val):
        """constrains a desired set value to the pyrealsense2.option range while
        respecting step size

        :param option: pyrealesense2.option name
        :type option: string
        :param set_val: unconstrained set point
        :type set_val: float
        :return: constrained set point
        :rtype: float
        """
        value_range = self.__depth_sensor.get_option_range(
            getattr(rs.option, option))
        min_val, max_val, step_size = value_range.min, value_range.max, value_range.step
        # round set value to nearest step size
        set_val = step_size * round(set_val / step_size)
        # constrain set_value within value_range
        if min_val <= set_val <= max_val:
            constrained_val = set_val
        else:
            if set_val > max_val:
                set_val = max_val
            elif set_val < min_val:
                set_val = min_val
            constrained_val = set_val
        return constrained_val

    def set_rs_option(self, set_option):
        """constrains configuration value and sets the pyrealsense2.option

        :param set_option: pyrealsense2.option name
        :type set_option: string
        """
        rs_option = getattr(rs.option, set_option)
        raw_val = float(self.__config['camera'][set_option])
        set_val = self.constrain_option_value(set_option, raw_val)
        self.__depth_sensor.set_option(rs_option, set_val)

    def set_rs_option_direct(self, option_name, set_value):
        """set a single camera option directly

        :param option_name: pyrealsense2.option name
        :type option_name: string
        :param set_value: desired set value
        :type set_value: float
        :return: true if success, false if not
        :rtype: bool
        """

        if self.__camera_options.count(option_name) > 0:
            if hasattr(rs.option, option_name):
                if self.writable(option_name):
                    rs_option = getattr(rs.option, option_name)
                    set_value = self.constrain_option_value(
                        option_name, set_value)
                    self.__depth_sensor.set_option(rs_option, set_value)
                    return True
        return False

    def get_camera_value(self, option):
        """retrieves camera setting

        :param option: pyrealsense2.option name
        :type option: string
        :return: returns setting value or None 
        :rtype: float or None
        """
        if self.__camera_options.count(option) > 0:
            if hasattr(rs.option, option):
                rs_option = getattr(rs.option, option)
                value = self.__depth_sensor.get_option(rs_option)
                return value
        return None
    
    def log_camera_settings(self):
        for setting in self.__depth_sensor.get_supported_options():
            try:
                log.debug(f'CAMERA SETTING: {setting.name}: {self.__depth_sensor.get_option(setting)}')
            except RuntimeError:
                log.debug(f'CAMERA SETTING: {setting.name} could not be retrieved')
