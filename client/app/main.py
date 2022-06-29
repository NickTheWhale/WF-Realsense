"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""


import configparser
import logging as log
import os
import random
import sys
import threading
import time
from datetime import datetime

import numpy as np
import opcua
import opcua.ua.uatypes
import PIL.Image
import pyrealsense2 as rs
import win32api
from opcua import ua

from camera import Camera
from config import Config

# CONSTANTS
METER_TO_FEET = 3.28084
WIDTH = 848
HEIGHT = 480

DEBUG = True
WAIT_BEFORE_RESTARTING = 5  # seconds. set to 0 for no wait time

MSG_STARTUP = "~~~~~~~~~~~~~~Starting Client Application~~~~~~~~~~~~"
MSG_RESTART = "~~~~~~~~~~~~~~~~~Restarting Application~~~~~~~~~~~~~~\n"
MSG_USER_SHUTDOWN = "~~~~~~~~~~~~~~~~User Exited Application~~~~~~~~~~~~~~\n"
MSG_ERROR_SHUTDOWN = "~~~~~~~~~~~~~~~Error Exited Application~~~~~~~~~~~~~~\n"

REQUIRED_DATA = {
    "server":
    {
        "ip": None
    },
    "nodes":
    {
        "node": None
    }
}


def on_exit(signal_type):
    """callback to log a user exit by clicking the 'x'

    :param signal_type: win32api parameter
    :type signal_type: int
    """
    log.info(MSG_USER_SHUTDOWN)


def take_picture(image):
    log.debug('Taking picture...')
    try:
        # GET FILE PATH
        if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
        elif __file__:
            path = os.path.dirname(__file__)

        # GET TIMESTAMP FOR FILE NAME
        timestamp = datetime.now()
        timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")

        # SAVE IMAGE
        image.save(f'{path}\\snapshots\\{timestamp}.jpg')
        # sleep thread to prevent saving a bunch of pictures
        time.sleep(5)
        log.debug(f'Took picture: "{timestamp}"')
    except Exception as e:
        # sleep thread to prevent saving a bunch of pictures
        time.sleep(5)
        log.debug(f'Failed to take picture: {e}')


def depth_frame_to_image(depth_frame):
    try:
        color_frame = rs.colorizer().colorize(depth_frame)
        color_array = np.asanyarray(color_frame.get_data())
        color_image = PIL.Image.fromarray(color_array)
        return (True, color_image)
    except Exception as e:
        log.warning(f'Failed to convert depth frame to image: {e}')
        return (False, None)


def critical_error(message="Unkown critical error", allow_restart=True):
    """function to log critical errors with the option to recall main()
    to restart program

    :param message: error message, defaults to "Unkown critical error"
    :type message: str, optional
    :param allow_rst: option to allow resetting of the program, defaults to True
    :type allow_rst: bool, optional
    """
    log.error(message)
    if allow_restart:
        log.critical(MSG_RESTART)
        if WAIT_BEFORE_RESTARTING > 0:
            time.sleep(WAIT_BEFORE_RESTARTING)
        main()
    else:
        log.critical(MSG_ERROR_SHUTDOWN)
        sys.exit(1)


def main():
    """Program entry point. Basic program flow in order:
    1. Read in configuration file settings
    2. Connect to realsense camera
    3. Connect to OPC server
    4. Send data to OPC server
    5. goto 4
    """

    ##############################################################################
    #                                   SETUP                                    #
    ##############################################################################

    if DEBUG:
        log.basicConfig(level=log.DEBUG,
                        format='%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
    else:
        log.basicConfig(filename="logger.log", filemode="a", level=log.DEBUG,
                        format='%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
    log.info(MSG_STARTUP)

    win32api.SetConsoleCtrlHandler(on_exit, True)

    try:
        config = Config('config.ini', REQUIRED_DATA)
    except configparser.DuplicateOptionError as e:
        critical_error(f'Duplicate option found in configuration file: {e}')
    try:
        # main logger
        log_level = getattr(log, config.get_value(
            'logging', 'logging_level').upper(), log.DEBUG)
        log.getLogger().setLevel(log_level)
        # opcua logger
        opcua_log_level = getattr(log, config.get_value(
            'logging', 'opcua_logging_level').upper(), log.DEBUG)
        log.getLogger(opcua.__name__).setLevel(opcua_log_level)

        log.info("Successfully set logging levels")
    except KeyError as e:
        log.getLogger().setLevel(log.DEBUG)
        log.getLogger(opcua.__name__).setLevel(log.INFO)
        log.warning(
            f'Failed to set logging levels from configuration file: {e}')

    # Intel Realsense Setup
    try:
        w, h, f = WIDTH, HEIGHT, int(config.get_value('camera', 'framerate'))
        camera = Camera(config.data, width=w, height=h, framerate=f)
        camera.options.write_all_settings()
        camera.options.log_settings()
        camera.start()

        log.info("Successfully connected RealSense camera")
    except RuntimeError as e:
        critical_error(
            f"Failed to connect camera: RuntimeError: {e}")
    except Exception as e:
        critical_error(e)

    # OPC Server Connection Setup
    try:
        ip = config.get_value('server', 'ip').strip("'").strip('"')
        client = opcua.Client(ip)
        client.connect()
        log.info(f"Successfully connected to {ip}")
    except ConnectionRefusedError as e:
        critical_error(e)
    except Exception as e:
        critical_error(e)
    else:
        try:
            roi_depth_node = client.get_node(
                str(config.get_value('nodes', 'roi_depth_node')))

            roi_accuracy_node = client.get_node(
                str(config.get_value('nodes', 'roi_accuracy_node')))

            roi_select_node = client.get_node(
                str(config.get_value('nodes', 'roi_select_node')))

            status_node = client.get_node(
                str(config.get_value('nodes', 'status_node')))

            picture_trigger_node = client.get_node(
                str(config.get_value('nodes', 'picture_trigger_node')))

            alive_node = client.get_node(
                str(config.get_value('nodes', 'alive_node')))

            log.info("Successfully retrieved nodes from OPC server")
        except Exception as e:
            critical_error(f'Failed to retrieve nodes: {e}')

    ##############################################################################
    #                                    LOOP                                    #
    ##############################################################################
    log.debug('Entering Loop')
    while True:
        try:
            depth_frame = camera.depth_frame
            if not depth_frame:
                continue
        except RuntimeError as e:
            critical_error(
                f'Error while retrieving camera frames: {e}')
        except Exception as e:
            critical_error(
                f'Error while retrieving camera frames: {e}')
        else:
            try:
                polygon = list(eval(config.get_value(
                    'camera', 'region_of_interest')))
                filter_level = int(
                    config.get_value('camera', 'spatial_filter_level'))
                roi_depth = camera.ROI_depth(polygon=polygon,
                                             filter_level=filter_level)

                ################################################
                #                   SEND DATA                  #
                ################################################

                # depth
                dv = roi_depth
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                roi_depth_node.set_value(dv)

                # accuracy
                dv = random.random() * 100
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                roi_accuracy_node.set_value(dv)

                # roi select
                dv = random.random() * 100
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                roi_select_node.set_value(dv)

                # status
                dv = camera.asic_temperature
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                status_node.set_value(dv)

                ##############################################
                #                  SEND ALIVE                #
                ##############################################

                if not alive_node.get_value():
                    dv = True
                    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
                    alive_node.set_value(dv)

                ##############################################
                #                SAVE PICTURE                #
                ##############################################

                pic_trig = picture_trigger_node.get_value()
                if pic_trig:
                    dv = False
                    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
                    picture_trigger_node.set_value(dv)
                    ret, img = depth_frame_to_image(depth_frame)
                    if ret:
                        picture_thread = threading.Thread(
                            target=take_picture, args=[img])
                        if not picture_thread.is_alive():
                            picture_thread.start()

            except Exception as e:
                critical_error(e)

        time.sleep(0.001)


if __name__ == "__main__":
    main()


# deprecated

'''def parse_config_old(file):
    """
    Function to parse data from configuration file. Sets values to 'None' or common
    values if unable to retrieve data 

    :param file: file path
    :type file: string
    :return: False or dictionary with values
    :rtype: boolean or dictionary
    """
    config_file = ConfigParser()
    rs = config_file.read(file)
    if len(rs) > 0:
        # configuration dictionary
        config_dict = {
            # server
            "ip": 'opc.tcp://localhost:4840',
            "depth_node": None,
            "extra_node": None,
            "status_node": None,
            "still_alive_node": None,
            # camera
            "width": WIDTH,
            "height": HEIGHT,
            "framerate": 30,
            "emitter_enabled": 1.0,
            "emitter_on_off": 0.0,
            "enabled_auto_exposure": 1.0,
            "error_polling_enabled": 1.0,
            "frames_queue_size": 16.0,
            "gain": 16.0,
            "global_time_enabled": 1.0,
            "inter_cam_sync_mode": 0.0,
            "laser_power": 150.0,
            "output_trigger_enabled": 0.0,
            "region_of_interest": [(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)],
            "stereo_baseline": 95.02674865722656,
            "visual_preset": 0.0,
            # logging
            "logging_level": "INFO",
            "opcua_logging_level": "WARNING"

        }
        # Read configuration file
        try:
            # Server
            config_dict["ip"] = config_file.get('server', 'ip', fallback=None).replace("'", "").replace('"', "")
            config_dict["depth_node"] = config_file.get('server', 'depth_node', fallback=None).replace("'", "").replace('"', "")
            config_dict["status_node"] = config_file.get('server', 'status_node', fallback=None).replace("'", "").replace('"', "")
            config_dict["still_alive_node"] = config_file.get('server', 'still_alive_node', fallback=None).replace("'", "").replace('"', "")
            config_dict["extra_node"] = config_file.get('server', 'extra_node', fallback=None).replace("'", "").replace('"', "")
            # Camera
            config_dict["width"] = config_file.getint('camera', 'width', fallback=WIDTH)
            config_dict["height"] = config_file.getint('camera', 'height', fallback=HEIGHT)
            config_dict["framerate"] = config_file.getint('camera', 'framerate', fallback=30)
            config_dict["emitter_enabled"] = config_file.getfloat('camera', 'emitter_enabled', fallback=1.0)
            config_dict["emitter_on_off"] = config_file.getfloat('camera', 'emitter_on_off', fallback=0.0)
            config_dict["enabled_auto_exposure"] = config_file.getfloat('camera', 'enable_auto_exposure', fallback=1.0)
            config_dict["error_polling_enabled"] = config_file.getfloat('camera', 'error_polling_enabled', fallback=1.0)
            config_dict["frames_queue_size"] = config_file.getfloat('camera', 'frames_queue_size', fallback=16.0)
            config_dict["gain"] = config_file.getfloat('camera', 'gain', fallback=16.0)
            config_dict["global_time_enabled"] = config_file.getfloat('camera', 'global_time_enabled', fallback=1.0)
            config_dict["inter_cam_sync_mode"] = config_file.getfloat('camera', 'inter_cam_sync_mode', fallback=0.0)
            config_dict["laser_power"] = config_file.getfloat('camera', 'laser_power', fallback=150.0)
            config_dict["output_trigger_enabled"] = config_file.getfloat('camera', 'output_trigger_enabled', fallback=0.0)
            config_dict["region_of_interest"] = list(eval(config_file.get('camera', 'region_of_interest', fallback=None)))
            config_dict["visual_preset"] = config_file.getfloat('camera', 'visual_preset', fallback=0.0)
            # Logging
            config_dict["logging_level"] = config_file.get('logging', 'logging_level', fallback="INFO").replace("'", "").replace('"', "")
            config_dict["opcua_logging_level"] = config_file.get('logging', 'opcua_logging_level', fallback="WARNING").replace("'", "").replace('"', "")
            # Application
            config_dict["allow_restart"] = bool(config_file.getfloat('application', 'allow_restart', fallback=1.0))
        except Exception as e:
            critical_error(f'Failed to read configuration file: {e}')
        return config_dict
    else:
        return False'''


'''def set_camera_options(profile, configuration):
    """function to set all avaliable camera options from configuration file

    :param profile: realsense camera profile
    :type profile: pyrealsense2.profile
    :param configuration: configuration dictionary
    :type configuration: dict
    """
    depth_sensor = profile.get_device().first_depth_sensor()
    try:
        # visual_preset
        raw_val = float(configuration['camera']['visual_preset'])
        set_val = scale_option_value(profile, 'visual_preset', raw_val)
        depth_sensor.set_option(rs.option.visual_preset, set_val)
        # preset_range = depth_sensor.get_option_range(rs.option.visual_preset)
        # for i in range(int(preset_range.max)):
        #     visualpreset = depth_sensor.get_option_value_description(rs.option.visual_preset, i)
        #     print(i, visualpreset)
        # print(configuration['camera']['visual_preset'])
        # emitter_enabled
        set_val = float(configuration['camera']['emitter_enabled'])
        depth_sensor.set_option(rs.option.emitter_enabled, set_val)
        # emitter_on_off
        set_val = float(configuration['camera']['emitter_on_off'])
        depth_sensor.set_option(rs.option.emitter_on_off, set_val)
        # enable_auto_exposure
        set_val = float(configuration['camera']['enable_auto_exposure'])
        depth_sensor.set_option(rs.option.enable_auto_exposure, set_val)
        # gain
        set_val = float(configuration['camera']['gain'])
        depth_sensor.set_option(rs.option.gain, set_val)
        # laser_power
        set_val = float(configuration['camera']['laser_power'])
        depth_sensor.set_option(rs.option.laser_power, set_val)
    except KeyError as e:
        log.warning(e)
    except Exception as e:
        log.warning(f"Failed to set 1 or more camera options: {e}")


def scale_option_value(profile, option, set_val):
    """function to scale desired option value by constraining 
    to available option range reported from the camera

    :param profile: realsense camera profile
    :type profile: pyrealsense2.profile
    :param option: realsense camera option
    :type option: string
    :param set_val: desired set point
    :type set_val: float
    :return: scaled set point
    :rtype: float
    """
    depth_sensor = profile.get_device().first_depth_sensor()
    value_range = depth_sensor.get_option_range(getattr(rs.option, option))
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


def option_valid(option):
    """function to check if a camera option 

    :param option: _description_
    :type option: _type_
    :return: _description_
    :rtype: _type_
    """
    valid_option = hasattr(rs.option, option)
    if valid_option is False:
        log.warning(f'Option "{option}" does not exist')
    return valid_option


def set_option(profile, option, set_val):
    pass'''

'''def pretty_print(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty_print(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))'''

'''def ROI_depth(depth_frame, polygon, blank_image, depth_scale, filter_level=0):
    """function to calculate the average distance within a region of interest. 
    This is done be either averaging the depth within a region of interest, or
    first filtering the depth data and then calculating the average

    :param depth_frame: camera frame containing depth data
    :type depth_frame: pyrealsense2.frame
    :param polygon: polygon vertices [(x1, y1), (x2, y2)]
    :type polygon: list
    :param blank_image: numpy array of zeros with the same dimension as the depth_frame
    :type blank_image: numpy.array
    :param depth_scale: depth scale reported by the camera to convert 
    raw depth data to known units
    :type depth_scale: float
    :param filter_level: spatial filtering level (1-5), defaults to 0
    :type filter_level: int, optional
    :return: distance at the defined region of interest,
    or 0 if no regiong of interest is supplied
    :rtype: float
    """
    # convert list of coordinate tuples to numpy array
    polygon = np.array(polygon)
    if filter_level > 5:
        filter_level = 5
    if len(polygon) > 0:
        if filter_level > 0:
            try:
                # Compute filtered depth image
                spatial = rs.spatial_filter()
                spatial.set_option(rs.option.holes_fill, filter_level)
                filtered_depth_frame = spatial.process(depth_frame)
                filtered_depth_image = np.asanyarray(
                    filtered_depth_frame.get_data())

                # Compute mask form polygon vertices
                mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
                mask = mask.astype('bool')
                mask = np.invert(mask)

                # Apply mask to filtered depth data and ignore invalid/zero distances
                filtered_depth_mask = ma.array(
                    filtered_depth_image, mask=mask, fill_value=0)
                filtered_depth_mask = ma.masked_invalid(filtered_depth_mask)
                filtered_depth_mask = ma.masked_equal(filtered_depth_mask, 0)

                # Compute average distnace of the region of interest
                ROI_depth = filtered_depth_mask.mean() * depth_scale * METER_TO_FEET
            except Exception:
                depth_image = np.asanyarray(depth_frame.get_data())
                # Compute mask from polygon vertices
                mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
                mask = mask.astype('bool')
                mask = np.invert(mask)

                # Apply mask to depth data and ignore invalid/zero distances
                depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
                depth_mask = ma.masked_invalid(depth_mask)
                depth_mask = ma.masked_equal(depth_mask, 0)

                # Compute average distance of the region of interest
                ROI_depth = depth_mask.mean() * depth_scale * METER_TO_FEET
        else:
            depth_image = np.asanyarray(depth_frame.get_data())
            # Compute mask from polygon vertices
            mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
            mask = mask.astype('bool')
            mask = np.invert(mask)

            # Apply mask to depth data and ignore invalid/zero distances
            depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
            depth_mask = ma.masked_invalid(depth_mask)
            depth_mask = ma.masked_equal(depth_mask, 0)

            # Compute average distance of the region of interest
            ROI_depth = depth_mask.mean() * depth_scale * METER_TO_FEET
        return ROI_depth
    else:
        return 0'''

# Hardware reset
# ctx = rs.context()
# devices = ctx.query_devices()
# for dev in devices:
#     dev.hardware_reset()

# try:
#     log_level = getattr(
#         log, sections['logging']['logging_level'].upper(), None)
#     log.getLogger().setLevel(log_level)
#     opcua_log_level = getattr(
#         log, sections['logging']['opcua_logging_level'].upper(), None)
#     log.getLogger(opcua.__name__).setLevel(opcua_log_level)
#     log.info("Successfully read configuration file and set logging levels")
# except Exception as e:
#     log.warning(
#         f"Failed to set logging level based on configuration file: {e}")
#     try:
#         log_level = getattr(
#             log, BACKUP_CONFIG['logging_level'].upper(), None)
#         log.getLogger().setLevel(log_level)
#         opcua_log_level = getattr(
#             log, BACKUP_CONFIG['opcua_logging_level'].upper(), None)
#         log.getLogger(opcua.__name__).setLevel(opcua_log_level)
#     except Exception as e:
#         log.warning(f"Failed to set logging level from backup config: {e}")
#         log.getLogger().setLevel(log.INFO)
#         log.getLogger(opcua.__name__).setLevel(log.WARNING)
#         log.info("Successfully set logging levels: INFO, WARNING")


# BACKUP_CONFIG = {
#     # server
#     "ip": 'opc.tcp://localhost:4840',
#     # camera
#     "framerate": '30',
#     "emitter_enabled": '1.0',
#     "emitter_on_off": '0.0',
#     "enable_auto_exposure": '1.0',
#     "gain": '16.0',
#     "laser_power": '150.0',
#     "region_of_interest": '[(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)]',
#     "spatial_filter_level": '2',
#     # logging
#     "logging_level": 'info',
#     "opcua_logging_level": 'warning'
# }

# def parse_config(file_path):
#     """function to read .ini configuration file and store contents to dictionary

#     :param file_path: file path to .ini file
#     :type file_path: string
#     :return: dictionary of .ini file contents
#     :rtype: dict
#     """
#     file = configparser.ConfigParser()
#     file.read(file_path)
#     sections = file.__dict__['_sections'].copy()
#     return sections
