"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: todo
"""


import configparser
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
BACKUP_CONFIG = {
    # server
    "ip" : 'opc.tcp://localhost:4840',
    # camera
    "framerate"              : '30',
    "emitter_enabled"        : '1.0',
    "emitter_on_off"         : '0.0',
    "enable_auto_exposure"   : '1.0',
    "gain"                   : '16.0',
    "laser_power"            : '150.0',
    "region_of_interest"     : '[(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)]',
    # logging
    "logging_level"          : 'info',
    "opcua_logging_level"    : 'warning',
    # application
    "allow_restart"          : '1.0'
}


def parse_config(file_path):
    file = configparser.ConfigParser()
    status = file.read(file_path)
    if len(status) > 0:
        sections = file.__dict__['_sections'].copy()
        return sections
    else:
        return False


def pretty_print(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty_print(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))
            

def parse_config_old(file):
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
            "width": 848,
            "height": 480,
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
            "opcua_logging_level": "WARNING",
            # application
            "allow_restart": 1.0

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
            config_dict["width"] = config_file.getint('camera', 'width', fallback=848)
            config_dict["height"] = config_file.getint('camera', 'height', fallback=480)
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


def set_camera_options(profile, configuration):
    depth_sensor = profile.get_device().first_depth_sensor()
    try:
        set_val = float(configuration['emitter_enabled'])
        depth_sensor.set_option(rs.emitter_enabled, set_val)
        
        set_val = float(configuration['emitter_on_off'])
        depth_sensor.set_option(rs.emitter_on_off, set_val)
        
        set_val = float(configuration['enable_auto_exposure'])
        depth_sensor.set_option(rs.enable_auto_exposure, set_val)
        
        set_val = float(configuration['gain'])
        depth_sensor.set_option(rs.gain, set_val)
        
        set_val = float(configuration['laser_power'])
        depth_sensor.set_option(rs.laser_power, set_val)
    except Exception as e:
        log.warning("Failed to set 1 or more camera options: {e}")


def critical_error(message="Unkown critical error", allow_rst=True):
    '''
    Function to log error message to either exit program or recall main()
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
    if len(polygon) > 0:
        # Compute mask from polygon vertices
        mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
        mask = mask.astype('bool')
        mask = np.invert(mask)

        # Apply mask to depth data and ignore invalid/zero distances
        depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
        depth_mask = ma.masked_invalid(depth_mask)
        depth_mask = ma.masked_equal(depth_mask, 0)

        # DEBUGGING
        cv2.imshow('', depth_mask * 100)
        cv2.waitKey(1)

        # Comptute average distance of the region of interest
        ROI_depth = depth_mask.mean() * depth_scale * METER_TO_FEET
        return ROI_depth
    else:
        return 0


def main():
    allow_restart = True
    blank_image = np.zeros((480, 848))
    log.basicConfig(filename="logger.log", filemode="a", level=log.DEBUG,
                    format='%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
    log.info(STARTUP_MSG)


    # Read Configuration File. set values from config->backup->hardcoded
    try:
        sections = parse_config('config.ini')
        log_level = getattr(log, sections['logging']['logging_level'].upper(), None)
        log.getLogger().setLevel(log_level)
        opcua_log_level = getattr(log, sections['logging']['opcua_logging_level'].upper(), None)
        log.getLogger(opcua.__name__).setLevel(opcua_log_level)  
        allow_restart = bool(sections['application']['allow_restart'])
        log.info("Successfully read configuration file and set logging levels")
    except Exception as e:
        log.warning("Failed to set logging level based on configuration file: {e}")
        try:
            log_level = getattr(log, BACKUP_CONFIG['logging_level'].upper(), None)
            log.getLogger().setLevel(log_level)
            opcua_log_level = getattr(log, BACKUP_CONFIG['opcua_logging_level'].upper(), None)
            log.getLogger(opcua.__name__).setLevel(opcua_log_level)  
            allow_restart = bool(BACKUP_CONFIG['allow_restart'])
        except Exception as e:
            log.warning("Failed to set logging level from backup config: {e}")
            log.getLogger().setLevel(log.INFO)
            log.getLogger(opcua.__name__).setLevel(log.WARNING)  
            allow_restart = True
            log.info("Successfully set logging levels: INFO, WARNING")
    
    # Intel Realsense Setup
    try:
        pipeline = rs.pipeline()
        camera_config = rs.config()
        try:
            w, h, f = 480, 848, int(sections['camera']['framerate'])
        except Exception as e:
            log.warning(e)
            w, h, f = 480, 848, 30
        camera_config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
        profile = pipeline.start(camera_config)
        pipeline.stop()
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        # DEBUGGING
        set_camera_options(profile, sections)
        pipeline.start(camera_config)
        log.info("Successfully connected RealSense camera")
    except RuntimeError:
        critical_error("Failed to connect camera", allow_restart)
    except Exception as e:
        critical_error(e, allow_restart)

    # OPC Server Connection Setup
    try:
        ip = sections['server']['ip'].strip("'")
        client = opcua.Client(ip)
        client.connect()
        log.info("Successfully connected to {ip}")
    except KeyError:
        client = opcua.Client(BACKUP_CONFIG['ip'].strip("'"))
    except ConnectionRefusedError as e:
        critical_error(e, allow_restart)
    except Exception as e:
        critical_error(e, allow_restart)
    else:
        try:
            depth_node = client.get_node(sections['server']['depth_node'].strip("'").strip('"'))
            status_node = client.get_node(sections['server']['status_node'].strip("'").strip('"'))
            still_alive_node = client.get_node(sections['server']['still_alive_node'].strip("'").strip('"'))
            extra_node = client.get_node(sections['server']['extra_node'].strip("'").strip('"'))
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
                polygon = sections['camera']['region_of_interest']
                roi_depth = ROI_depth(
                    depth_frame, polygon, blank_image, depth_scale)

                distance = depth_frame.get_distance(424, 240) * 3.28084
                depth_array = depth_frame.data
                depth_array = np.asanyarray(depth_array)

                # Send data to PLC
                dv = roi_depth
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                depth_node.set_value(dv)

                dv = time.time() - offset_time
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                status_node.set_value(dv)

                tick = not tick
                dv = tick
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
                still_alive_node.set_value(dv)

                arr = []
                for i in range(100):
                    arr.append(depth_frame.get_distance(i+270, 240) * 3.28084)

                dv = arr
                dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                extra_node.set_value(dv)
            except Exception as e:
                critical_error(e, allow_restart)

        time.sleep(0.001)


if __name__ == "__main__":
    main()
