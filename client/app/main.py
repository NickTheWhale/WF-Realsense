"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""


import configparser
import logging as log
import sys
import time
from options import Options as op
import cv2
import numpy as np
import numpy.ma as ma
import opcua
import opcua.ua.uatypes
import pyrealsense2 as rs
import win32api
from opcua import ua

# CONSTANTS
WAIT_BEFORE_RESTARTING = 5  # seconds. set to 0 for no wait time
METER_TO_FEET = 3.28084
SHUTDOWN_MSG = "Exiting program"
STARTUP_MSG = "~~~~~~~~~~~~~Starting Client Application~~~~~~~~~~~~~"
RESTART_MSG = "Restarting program"
USER_SHUTDOWN_MSG = "~~~~~~~~~~~~~~~User Exited Application~~~~~~~~~~~~~~~"
ALLOW_RESTART = True
BACKUP_CONFIG = {
    # server
    "ip": 'opc.tcp://localhost:4840',
    # camera
    "framerate": '30',
    "emitter_enabled": '1.0',
    "emitter_on_off": '0.0',
    "enable_auto_exposure": '1.0',
    "gain": '16.0',
    "laser_power": '150.0',
    "region_of_interest": '[(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)]',
    "spatial_filter_level": '2',
    # logging
    "logging_level": 'info',
    "opcua_logging_level": 'warning',
    # application
    "allow_restart": '1.0'
}


def on_exit(signal_type):
    """callback to log a user exit by clicking the 'x'

    :param signal_type: win32api parameter
    :type signal_type: unknown
    """
    log.info(USER_SHUTDOWN_MSG)


def parse_config(file_path):
    """function to read .ini configuration file and store contents to dictionary

    :param file_path: file path to .ini file
    :type file_path: string
    :return: dictionary of .ini file contents
    :rtype: dict
    """
    file = configparser.ConfigParser()
    file.read(file_path)
    sections = file.__dict__['_sections'].copy()
    return sections


def pretty_print(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty_print(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))


def dump_options(profile):
    """function to get available camera options and dump to a text file.
       Debugging use only. 
    :param profile: pyrealsense2 camera profile object
    :type profile: pyrealsense2.profile
    """
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
    print(f'{option} min: {min_val} max: {max_val} step: {step_size}')
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
    pass


def critical_error(message="Unkown critical error", allow_rst=True):
    """function to log critical errors with the option to recall main()
    to restart program

    :param message: error message, defaults to "Unkown critical error"
    :type message: str, optional
    :param allow_rst: option to allow resetting of the program, defaults to True
    :type allow_rst: bool, optional
    """
    if allow_rst:
        log.error(message)
        log.critical(RESTART_MSG)
        if bool(WAIT_BEFORE_RESTARTING):
            time.sleep(WAIT_BEFORE_RESTARTING)
        main()
    else:
        log.error(message)
        log.critical(SHUTDOWN_MSG)
        sys.exit(1)


def ROI_depth(depth_frame, polygon, blank_image, depth_scale, filter_level=0):
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
        colorizer = rs.colorizer()
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

                filtered_depth_colormap = np.asanyarray(
                    colorizer.colorize(filtered_depth_frame).get_data())
                cv2.imshow('Filtered Mask', filtered_depth_colormap)
                cv2.waitKey(1)
                # Compute average distnace of the region of interest
                ROI_depth = filtered_depth_mask.mean() * depth_scale * METER_TO_FEET
            except Exception as e:
                print(e)
                sys.exit(1)
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

            depth_color_map = np.asanyarray(
                colorizer.colorize(depth_frame).get_data())

            cv2.imshow('Depth colormap', depth_color_map)
            cv2.waitKey(1)

            # Compute average distance of the region of interest
            ROI_depth = depth_mask.mean() * depth_scale * METER_TO_FEET
        return ROI_depth
    else:
        return 0


def main():
    """Program entry point. Basic program flow in order:
    1. Read in configuration file settings
    2. Connect to realsense camera
    3. Connect to OPC server
    4. Send data to OPC server
    5. goto 4
    """    
    
    allow_restart = True
    blank_image = np.zeros((480, 848))
    log.basicConfig(filename="logger.log", filemode="a", level=log.DEBUG,
                    format='%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
    log.info(STARTUP_MSG)

    win32api.SetConsoleCtrlHandler(on_exit, True)
    # Read Configuration File. set values from config->backup->hardcoded
    try:
        sections = parse_config('config.ini')
        log_level = getattr(
            log, sections['logging']['logging_level'].upper(), None)
        log.getLogger().setLevel(log_level)
        opcua_log_level = getattr(
            log, sections['logging']['opcua_logging_level'].upper(), None)
        log.getLogger(opcua.__name__).setLevel(opcua_log_level)
        allow_restart = bool(sections['application']['allow_restart'])
        log.info("Successfully read configuration file and set logging levels")
    except Exception as e:
        log.warning(
            f"Failed to set logging level based on configuration file: {e}")
        try:
            log_level = getattr(
                log, BACKUP_CONFIG['logging_level'].upper(), None)
            log.getLogger().setLevel(log_level)
            opcua_log_level = getattr(
                log, BACKUP_CONFIG['opcua_logging_level'].upper(), None)
            log.getLogger(opcua.__name__).setLevel(opcua_log_level)
            allow_restart = bool(BACKUP_CONFIG['allow_restart'])
        except Exception as e:
            log.warning(f"Failed to set logging level from backup config: {e}")
            log.getLogger().setLevel(log.INFO)
            log.getLogger(opcua.__name__).setLevel(log.WARNING)
            allow_restart = True
            log.info("Successfully set logging levels: INFO, WARNING")

    # Intel Realsense Setup
    try:
        pipeline = rs.pipeline()
        camera_config = rs.config()
        try:
            w, h, f = 848, 480, int(sections['camera']['framerate'])
        except Exception as e:
            log.warning(e)
            w, h, f = 848, 480, 30
        camera_config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
        profile = pipeline.start(camera_config)
        pipeline.stop()
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        # DEBUGGING
        set_camera_options(profile, sections)
        pipeline.start(camera_config)
        log.info("Successfully connected RealSense camera")
    except RuntimeError as e:
        critical_error(f"Failed to connect camera: {e}", allow_restart)
    except Exception as e:
        critical_error(e, allow_restart)

    
    
    # testing
                                 
    camera_options = op(profile, sections)
    available_options = camera_options.get_available_options()
    config_options = camera_options.get_config_options()
    
    
    
    
    # end testing
    
    
    
    # OPC Server Connection Setup
    try:
        ip = sections['server']['ip'].strip("'")
        client = opcua.Client(ip)
        client.connect()
        log.info(f"Successfully connected to {ip}")
    except KeyError:
        client = opcua.Client(BACKUP_CONFIG['ip'].strip("'"))
    except ConnectionRefusedError as e:
        critical_error(e, allow_restart)
    except Exception as e:
        critical_error(e, allow_restart)
    else:
        try:
            depth_node = client.get_node(
                sections['server']['depth_node'].strip("'").strip('"'))
            status_node = client.get_node(
                sections['server']['status_node'].strip("'").strip('"'))
            still_alive_node = client.get_node(
                sections['server']['still_alive_node'].strip("'").strip('"'))
            extra_node = client.get_node(
                sections['server']['extra_node'].strip("'").strip('"'))
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
                polygon = list(eval(sections['camera']['region_of_interest']))
                try:
                    filter_level = int(
                        sections['camera']['spatial_filter_level'])
                except KeyError as e:
                    filter_level = int(BACKUP_CONFIG['spatial_filter_level'])
                    log.warn(e)
                roi_depth = ROI_depth(
                    depth_frame, polygon, blank_image, depth_scale, filter_level)

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


# deprecated
'''
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
        '''
