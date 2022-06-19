"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
data:    June 2022
license: todo
"""


import logging as log
import sys
import time
from configparser import ConfigParser

import numpy as np
import opcua
import opcua.ua.uatypes
import pyrealsense2 as rs
from opcua import ua

# CONSTANTS
METER_TO_FEET = 3.28084


def parse_config(file):
    """
    Function to parse data from configuration file. Sets values to 'None' or common
    values if unable to retrieve data 

    :param file: file path
    :type file: string
    :return: False or values
    :rtype: boolean or dictionary
    """
    config_file = ConfigParser()
    rs = config_file.read(file)
    if len(rs) > 0:
        # configuration dictionary
        config_dict = {
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
            "output_trigger_enabled": 0.0,
            "region_of_interest": [(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)],
            "stereo_baseline": 95.02674865722656,
            "still_alive_node": None,
            "status_node": None,
            "visual_preset": 0.0,
            "width": 848
        }
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
        for val in config_dict:
            if config_dict[val] is None:
                log.debug(val)
        return config_dict
    else:
        return False


def dump_options(profile):
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


def main():
    # Create log config
    log.basicConfig(filename="logger.log", filemode="a", level=log.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(lineno)d:%(message)s')

    # Read Configuration File
    config_file = parse_config('config.ini')
    if config_file is not False:
        try:
            log_level = getattr(
                log, config_file["logging_level"].upper(), None)
            log.getLogger().setLevel(log_level)
        except Exception:
            log.warning(
                "Could not set logging level from configuration file, defaulting level to DEBUG")
        log.info("Successfully read configuration file")
    else:
        log.critical("Failed to read configuration file, exiting program")
        sys.exit(1)

    # Intel Realsense Setup
    try:
        pipeline = rs.pipeline()
        camera_config = rs.config()
        w, h, f = config_file["width"], config_file["height"], config_file["framerate"]
        camera_config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
        profile = pipeline.start(camera_config)
        log.info("Successfully connected RealSense camera")
    except RuntimeError:
        log.error("Failed to connect camera")

    # OPC Server Connection Setup
    try:
        client = opcua.Client(config_file["ip"])
        client.connect()
        log.info("Successfully connected to OPC server")
    except ConnectionRefusedError as e:
        log.error(e)
    except Exception:
        log.error("Unknown error connecting to server")
    else:
        depth_node = client.get_node(config_file["depth_node"])
        status_node = client.get_node(config_file["status_node"])
        still_alive_node = client.get_node(config_file["still_alive_node"])
        extra_node = client.get_node(config_file["extra_node"])
        log.info("Successfully retrieved nodes from OPC server")

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
            depth = frames.get_depth_frame()
            if not depth:
                continue
        except RuntimeError as e:
            log.error(e)
            log.critical("Exiting program")
            sys.exit(1)
        # log.debug(rs.option())
        else:
            distance = depth.get_distance(424, 240) * 3.28084
            depth_array = depth.data
            depth_array = np.asanyarray(depth_array)
            # log.debug(depth_array.shape, distance, depth.get_data_size(),
            #       depth.get_height(), depth.get_width())

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
                arr.append(depth.get_distance(i+270, 240) * 3.28084)

            dv = ua.DataValue(ua.Variant(arr, ua.VariantType.Float))
            extra_node.set_value(dv)

        time.sleep(0.001)


if __name__ == "__main__":
    main()
