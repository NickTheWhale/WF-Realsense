"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: todo
"""


import logging as log
import sys
import time
from configparser import ConfigParser

import cv2
import numpy as np
import numpy.ma as ma
import opcua
import opcua.ua.uatypes
import pyrealsense2 as rs
from opcua import ua

# CONSTANTS
METER_TO_FEET = 3.28084
SHUTDOWN_MSG = "Exiting program"
STARTUP_MSG = "\n\n~~~~~Starting Client Application~~~~~\n"
RESTART_MSG = "Restarting program"
ALLOW_RESTART = True


def parse_config(file):
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
            "allow_restart": 1.0,
            "depth_node": None,
            "enabled_auto_exposure": 1.0,
            "emitter_enabled": 1.0,
            "emitter_on_off": 0.0,
            "error_polling_enabled": 1.0,
            "extra_node": None,
            "framerate": 30,
            "frames_queue_size": 16.0,
            "gain": 16.0,
            "global_time_enabled": 1.0,
            "height": 480,
            "inter_cam_sync_mode": 0.0,
            "ip": 'opc.tcp://localhost:4840',
            "laser_power": 150.0,
            "logging_level": "INFO",
            "opcua_logging_level": "WARNING",
            "output_trigger_enabled": 0.0,
            "region_of_interest": [(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)],
            "stereo_baseline": 95.02674865722656,
            "still_alive_node": None,
            "status_node": None,
            "visual_preset": 0.0,
            "width": 848
        }
        # Read configuration file
        try:
            # Server
            config_dict["ip"] = config_file.get(
                'server', 'ip', fallback=None).replace("'", "").replace('"', "")
            config_dict["depth_node"] = config_file.get(
                'server', 'depth_node', fallback=None).replace("'", "").replace('"', "")
            config_dict["status_node"] = config_file.get(
                'server', 'status_node', fallback=None).replace("'", "").replace('"', "")
            config_dict["still_alive_node"] = config_file.get(
                'server', 'still_alive_node', fallback=None).replace("'", "").replace('"', "")
            config_dict["extra_node"] = config_file.get(
                'server', 'extra_node', fallback=None).replace("'", "").replace('"', "")
            # Camera
            config_dict["width"] = config_file.getint(
                'camera', 'width', fallback=640)
            config_dict["height"] = config_file.getint(
                'camera', 'height', fallback=480)
            config_dict["framerate"] = config_file.getint(
                'camera', 'framerate', fallback=30)
            config_dict["region_of_interest"] = config_file.get(
                'camera', 'region_of_interest', fallback=None)
            config_dict["region_of_interest"] = list(
                eval(config_dict["region_of_interest"]))
            # Logging
            config_dict["logging_level"] = config_file.get(
                'logging', 'logging_level', fallback="INFO").replace("'", "").replace('"', "")
            config_dict["opcua_logging_level"] = config_file.get(
                'logging', 'opcua_logging_level', fallback="WARNING").replace("'", "").replace('"', "")
            # Application
            config_dict["allow_restart"] = bool(config_file.getfloat(
                'application', 'allow_restart', fallback=1.0))
        except Exception as e:
            critical_error(f'Failed to read configuration file {e}')
        return config_dict
    else:
        return False


def dump_options(profile):
    '''
    Function to write avaliable camera options to file. 
    Use for debugging only
    '''
    depth_sensor = profile.get_device().first_depth_sensor()
    file = open('options.txt', 'r')
    available_f = open('avaliable-options.txt', 'w')
    available_f.write("Available options for setting/getting\n")
    available_f.write('\n')
    available_f.close()
    available_f = open('avaliable-options.txt', 'a')
    for option in file:
        option = option.strip()
        try:
            val = depth_sensor.get_option(getattr(rs.option, option))
            log.debug(f'{option} {val}')
            available_f.write(option)
            available_f.write('\n')
        except (RuntimeError, AttributeError):
            pass
    file.close()
    available_f.close()


def critical_error(message="Unkown critical error", allow_rst=True):
    '''
    Function to print error message to either exit program or recall main()
    '''
    if allow_rst:
        log.error(message)
        log.critical(RESTART_MSG)
        main()
    else:
        log.error(message)
        log.critical(SHUTDOWN_MSG)
        sys.exit(1)


def ROI_depth(depth_frame, polygon, blank_image, depth_scale):
    # convert list of coordinate tuples to numpy array
    polygon = np.array(polygon)
    depth_image = np.asanyarray(depth_frame.get_data())
    if len(polygon) > 2:
        # Compute mask from polygon vertices
        mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
        mask = mask.astype('bool')
        mask = np.invert(mask)

        # Apply mask to depth data and ignore invalid/zero distances
        depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
        depth_mask = ma.masked_invalid(depth_mask)
        depth_mask = ma.masked_equal(depth_mask, 0)

        # Comptute average distance of the region of interest
        ROI_depth = depth_mask.mean() * depth_scale * METER_TO_FEET
        return ROI_depth
    else:
        return 0


def main():
    # Initialize automatic restart flag and blank image for masking
    allow_restart = True
    blank_image = np.zeros((480, 848))

    # Create log config
    log.basicConfig(filename="logger.log", filemode="a", level=log.DEBUG,
                    format='%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')

    # Log start of client application
    log.info(STARTUP_MSG)

    # Read Configuration File
    try:
        config_file = parse_config('config.ini')
        if config_file is not False:
            try:
                # Set root logger level
                log_level = getattr(
                    log, config_file["logging_level"].upper(), None)
                log.getLogger().setLevel(log_level)
                # Set opcua module logger level to avoid clutter
                opcua_log_level = getattr(
                    log, config_file["opcua_logging_level"].upper(), None)
                log.getLogger(opcua.__name__).setLevel(opcua_log_level)
                allow_restart = config_file["allow_restart"]
                log.info("Successfully read configuration file")
            except Exception:
                log.warning(
                    "Could not set logging level from configuration file, defaulting level to DEBUG")
        else:
            critical_error("Error reading configuration file", allow_restart)
    except Exception as e:
        critical_error(e)

    # Intel Realsense Setup
    try:
        pipeline = rs.pipeline()
        camera_config = rs.config()
        w, h, f = config_file["width"], config_file["height"], config_file["framerate"]
        camera_config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
        profile = pipeline.start(camera_config)
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        log.info("Successfully connected RealSense camera")
    except RuntimeError:
        critical_error("Failed to connect camera", allow_restart)
    except Exception as e:
        critical_error(e)

    # OPC Server Connection Setup
    try:
        client = opcua.Client(config_file["ip"])
        client.connect()
        log.info("Successfully connected to OPC server")
    except ConnectionRefusedError as e:
        critical_error(e, allow_restart)
    except Exception as e:
        critical_error(e, allow_restart)
    else:
        try:
            depth_node = client.get_node(config_file["depth_node"])
            status_node = client.get_node(config_file["status_node"])
            still_alive_node = client.get_node(config_file["still_alive_node"])
            extra_node = client.get_node(config_file["extra_node"])
            log.info("Successfully retrieved nodes from OPC server")
        except Exception as e:
            critical_error(f'Failed to retrieve nodes: {e}', allow_restart)

    offset_time = time.time()

    tick = False

    # Hardware reset
    # ctx = rs.context()
    # devices = ctx.query_devices()
    # for dev in devices:
    #     dev.hardware_reset()

    while True:

        # Get camera frame
        try:
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            if not depth_frame:
                continue
        except RuntimeError as e:
            critical_error(
                f'Error while retrieving camera frames: {e}', allow_restart)
        except Exception as e:
            critical_error(
                f'Error while retrieving camera frames: {e}', allow_restart)
        else:
            try:
                polygon = config_file["region_of_interest"]
                roi_depth = ROI_depth(
                    depth_frame, polygon, blank_image, depth_scale)
                print(roi_depth)

                distance = depth_frame.get_distance(424, 240) * 3.28084
                depth_array = depth_frame.data
                depth_array = np.asanyarray(depth_array)

                # Send data to PLC
                dv = ua.DataValue(ua.Variant(distance, ua.VariantType.Float))
                depth_node.set_value(dv)

                dv = ua.DataValue(ua.Variant(
                    time.time() - offset_time, ua.VariantType.Float))
                status_node.set_value(dv)

                tick = not tick
                dv = ua.DataValue(ua.Variant(tick, ua.VariantType.Boolean))
                still_alive_node.set_value(dv)

                arr = []
                for i in range(100):
                    arr.append(depth_frame.get_distance(i+270, 240) * 3.28084)

                dv = ua.DataValue(ua.Variant(arr, ua.VariantType.Float))
                extra_node.set_value(dv)
            except Exception as e:
                critical_error(e, allow_restart)

        time.sleep(0.001)


if __name__ == "__main__":
    main()
