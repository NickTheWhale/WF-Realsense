"""
title:   RealSenseOPC Camera and CameraOptions classes
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import difflib as diff
import logging as log
import time

import cv2
import numpy as np
import numpy.ma as ma
import pyrealsense2 as rs

# CONSTANTS
METER_TO_FEET = 3.28084


class Camera():
    def __init__(self, config: dict, width=848, height=480, framerate=0, metric=False):
        """create a Camera object to interface with camera. 
        Creating a Camera object also creates a CameraOptions object
        used for setting and getting camera settings

        :param config: configuration dictionary
        :type config: dict
        :param width: depth stream width, defaults to 848
        :type width: int, optional
        :param height: depth stream height, defaults to 480
        :type height: int, optional
        :param framerate: depth stream framerate, defaults to auto-negotiation
        :type framerate: int, optional
        """
        # connect to camera
        self.__context = rs.context()
        self.__context.set_devices_changed_callback(self.__disconnect_callback)
        self.__pipeline = rs.pipeline()
        self.__pipeline_config = rs.config()
        # depth stream
        self.__pipeline_config.enable_stream(rs.stream.depth,
                                             width,
                                             height,
                                             rs.format.z16,
                                             framerate)
        self.__profile = self.__pipeline.start(self.__pipeline_config)
        self.__pipeline.stop()
        self.__depth_sensor = self.__profile.get_device().first_depth_sensor()
        self.__depth_scale = self.__depth_sensor.get_depth_scale()

        # options object used to alter camera settings. all settings must
        #   be configured before calling the start() method of the camera
        self.options = CameraOptions(self.__profile, config)

        # camera attributes
        self.__conversion = METER_TO_FEET * self.__depth_scale
        if metric:
            self.__conversion = self.__depth_scale
        self.__depth_frame = None
        self.__connected = False
        self.__frame_number = 0
        # roi attributes
        self.__height = height
        self.__width = width

    def __depth_callback(self, fs):
        """called when a new frameset arrives. Updates self.__depth_frame
        and self.__frame_number

        :param fs: rs.type
        :type fs: rs.type
        """
        self.__depth_frame = fs.as_frameset().get_depth_frame()
        self.__frame_number = self.__depth_frame.frame_number

    def start(self):
        """start pipeline and setup new frameset callback"""
        self.__profile = self.__pipeline.start(self.__pipeline_config,
                                               self.__depth_callback)
        self.__connected = True

    def stop(self):
        """stop pipeline"""
        self.__pipeline.stop()
        self.__connected = False

    def reset(self):
        """performs a hardware reset on every available device"""
        if self.__connected:
            self.stop()
        ctx = rs.context()
        devices = ctx.query_devices()
        for dev in devices:
            log.info(f'Resetting device: {dev}')
            dev.hardware_reset()
            time.sleep(4)

    def set_roi(self, roi):
        """set auto exposure region of interest

        :param roi: region of interest
        :type roi: pyrealsense2.region_of_interest
        """
        sensor = self.__profile.get_device().first_roi_sensor()
        sensor.set_region_of_interest(roi)

    def get_roi(self):
        """get camera auto exposure region of interest

        :return: region of interest
        :rtype: pyrealsense2.region_of_interest
        """
        sensor = self.__profile.get_device().first_roi_sensor()
        return sensor.get_region_of_interest()

    def __disconnect_callback(self, info):
        """called when a camera device is connected or disconnected. Updates  
        self.__connected

        :param info: rs.event
        :type info: rs.event
        """
        devs = info.get_new_devices()
        if devs.size() < 1:
            self.__connected = False

    def roi_data(self, polygons: list, roi_select: int, filter_level=0):
        """compute average of n-number of polygons"""

        ret = float(0), float(100), float(0)
        depth_frame = self.__depth_frame
        if isinstance(depth_frame, rs.depth_frame):
            filter_level = min(max(int(filter_level), 0), 5)

            # clamp roi_select to 8 bit integer
            roi_select = min(max(int(roi_select), 0), 255)

            # build select list (ex. 137 -> [1, 0, 0, 0, 1, 0, 0, 1])
            select_list = []
            for bit in format(roi_select, '08b'):
                select_list.append(bool(int(bit)))

            # build polygon list ( [[x1, y1, x2, y2], [x1, y1, x2, y2]] )
            polygon_list = []
            for i in range(len(polygons)):
                if select_list[i]:
                    polygon_list.append(np.array(polygons[i]))
            polygon_list = np.asanyarray(polygon_list)

            if len(polygon_list) > 0:
                blank_image = np.zeros((self.__height, self.__width))

                # create depth image and filter if necessary
                if filter_level == 0:
                    depth_image = np.asanyarray(depth_frame.get_data())
                else:
                    spatial = rs.spatial_filter()
                    spatial.set_option(rs.option.holes_fill, filter_level)
                    depth_image = spatial.process(depth_frame)
                    depth_image = np.asanyarray(depth_image.get_data())

                # Compute mask from polygon vertices
                mask = blank_image
                for polygon in polygon_list:
                    if len(polygon) > 0:
                        mask += cv2.fillPoly(blank_image, pts=[polygon], color=1)
                mask = mask.astype('bool')
                mask = np.invert(mask)

                # Apply mask to depth data
                depth_mask = ma.array(depth_image, mask=mask, fill_value=0)

                # calculate standard deviation and percentage of invalid pixels
                total = ma.count(depth_mask)
                if total > 0:
                    invalid = (depth_mask == 0).sum()
                    invalid = (invalid / total) * 100
                    deviation = depth_mask.std() * self.__conversion
                else:
                    deviation = float(0)
                    invalid = float(100)

                # filter out invalid and 0 distances
                depth_mask = ma.masked_invalid(depth_mask)
                depth_mask = ma.masked_equal(depth_mask, 0)

                # Compute average distance of the region of interest
                ROI_depth = depth_mask.mean() * self.__conversion

                if isinstance(ROI_depth, np.float64):
                    ret = ROI_depth.item(), invalid, deviation
                else:
                    ret = float(0), invalid, deviation
        return ret

    @property
    def asic_temperature(self):
        """asic temperature in degrees celcius. Raises RunTimeError
        if the camera is disconnected

        :return: temperature in degrees celcius
        :rtype: float
        """
        return self.options.get_camera_value('asic_temperature')

    @property
    def projector_temperature(self):
        """dot projector temperature in degrees celcius. Raises 
        RunTimeError if the camera is disconnected

        :return: temperature in degrees celcius
        :rtype: float
        """
        return self.options.get_camera_value('projector_temperature')

    @property
    def depth_frame(self):
        """returns depth frame

        :return: depth frame
        :rtype: rs.depth_frame
        """
        return self.__depth_frame

    @depth_frame.setter
    def depth_frame(self, df):
        """set depth frame

        :param df: depth frame
        :type df: pyrealsense2.depth_frame
        """
        self.__depth_frame = df

    @property
    def connected(self):
        """connection status of camera. Do not use this as the only
        connection error detection

        :return: connection status
        :rtype: bool
        """
        return self.__connected

    @property
    def frame_number(self) -> int:
        """return frame number from last depth callback

        :return: frame number
        :rtype: int
        """
        return self.__frame_number


class CameraOptions():
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

    def write_all_settings(self):
        """combines get_camera_options(), get_user_options(), and 
        set_all_options() into one method
        """
        self.get_camera_options()
        self.get_user_options()
        self.set_all_options()

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
        cam_ops = self.__camera_options
        for op in usr_ops:
            if op in cam_ops:
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

    def log_settings(self):
        """iterates through supported camera options and logs the
        option name and value
        """
        for setting in self.__depth_sensor.get_supported_options():
            try:
                log.debug(
                    f'CAMERA SETTING: {setting.name}: {self.__depth_sensor.get_option(setting)}')
            except RuntimeError:
                log.debug(
                    f'CAMERA SETTING: {setting.name} could not be retrieved')
