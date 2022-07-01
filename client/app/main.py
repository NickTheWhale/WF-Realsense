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
from opcua import ua

from camera import Camera
from config import Config

# GLOBALS
global taking_picture
taking_picture = False

# CONSTANTS
METER_TO_FEET = 3.28084  # dont change this
WIDTH = 848  # or this
HEIGHT = 480  # or this

DEBUG = True  # true: log output goes to console, false: log output goes to .log file
#                 note- if set to 'true' and the script is being run in an
#                 executable form, make sure a console window pops up when
#                 the program starts, otherwise you will not see any log
#                 information
WAIT_BEFORE_RESTARTING = 5  # seconds. set to 0 for no wait time

MSG_STARTUP = "~~~~~~~~~~~~~~Starting Client Application~~~~~~~~~~~~"
MSG_RESTART = "~~~~~~~~~~~~~~~~~Restarting Application~~~~~~~~~~~~~~\n"
MSG_USER_SHUTDOWN = "~~~~~~~~~~~~~~~~User Exited Application~~~~~~~~~~~~~~\n"
MSG_ERROR_SHUTDOWN = "~~~~~~~~~~~~~~~Error Exited Application~~~~~~~~~~~~~~\n"


# When parsing the configuration file, the parser will check if the file
# has these required sections and key. If the file is missing any of
# the required data, the program will log the error and stop execution.
#    Note- the datatype is not important since key values are all
#    treated as strings. Required keys in any section except for "node"
#    will be checked individually. The "nodes" section is special as only
#    one node is required and the name is irrelevant. As long as the parser
#    is able to read atleast one node key from the file, there should not
#    be an error

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

        if dir_exists(path=path, name='snapshots'):
            # SAVE IMAGE
            image.save(f'{path}\\snapshots\\{timestamp}.jpg')
            # sleep thread to prevent saving a bunch of pictures
            time.sleep(5)
            log.info(f'Took picture: "{timestamp}"')
        else:
            snapshot_path = path + '\\snapshots\\'
            os.mkdir(snapshot_path)
            # SAVE IMAGE
            image.save(f'{path}\\snapshots\\{timestamp}.jpg')
            # sleep thread to prevent saving a bunch of pictures
            time.sleep(5)
            log.info(f'Took picture: "{timestamp}"')
    except Exception as e:
        # sleep thread to prevent saving a bunch of pictures
        time.sleep(5)
        log.warning(f'Failed to take picture {timestamp}: {e}')
    finally:
        global taking_picture
        taking_picture = False


def dir_exists(path: str, name: str) -> bool:
    """check if directory 'name' exists within 'path'

    :param path: full parent path name
    :type path: string
    :param name: name of directory to check
    :type name: string
    :return: if 'name' exists
    :rtype: bool
    """
    dir = os.listdir(path=path)
    return name in dir


def depth_frame_to_image(depth_frame):
    """attempts to convert 'depth_frame' to a color image

    :param depth_frame: depth frame to convert
    :type depth_frame: pyrealsense2.depth_frame
    :return: (status, color image)
    :rtype: (bool, PIL.Image)
    """
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
    log.error(message, exc_info=True)
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
        log.basicConfig(
            level=log.DEBUG,
            format='%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
    else:
        log.basicConfig(filename="logger.log",
                        filemode="a",
                        level=log.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    log.info(MSG_STARTUP)

    try:
        config = Config('configuration.ini', REQUIRED_DATA)
    except configparser.DuplicateOptionError as e:
        critical_error(f'Duplicate option found in configuration file: {e}')
    except RuntimeError as e:
        critical_error(e, False)
    except FileNotFoundError as e:
        critical_error(e, False)
    else:
        try:
            # main logger
            lvl = config.get_value('logging', 'logging_level').upper()
            log_level = getattr(log, lvl, log.DEBUG)
            log.getLogger().setLevel(log_level)

            # opcua logger
            lvl = config.get_value('logging', 'opcua_logging_level').upper()
            opcua_log_level = getattr(log, lvl, log.DEBUG)
            log.getLogger(opcua.__name__).setLevel(opcua_log_level)
            log.info("Successfully set logging levels")
        except KeyError as e:
            log.getLogger().setLevel(log.DEBUG)
            log.getLogger(opcua.__name__).setLevel(log.INFO)
            log.warning(f'Failed to set logging levels from config file: '
                        f'{e} not found in config file')

    # Intel Realsense Setup
    try:
        w, h, f = WIDTH, HEIGHT, int(config.get_value('camera', 'framerate'))
        camera = Camera(config.data, width=w, height=h, framerate=f)
        camera.options.write_all_settings()
        camera.options.log_settings()
        camera.start_callback()

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

    try:
        sleep_time = config.get_value('application', 'sleep_time')
    except KeyError:
        sleep_time = 0.001
    else:
        sleep_time = float(sleep_time)

    log.debug('Entering Loop')

    while True:
        # check for valid depth frame
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
                global taking_picture
                if pic_trig and not taking_picture:
                    taking_picture = True
                    ret, img = depth_frame_to_image(depth_frame)
                    if ret:
                        picture_thread = threading.Thread(
                            target=take_picture, args=[img])
                        if not picture_thread.is_alive():
                            picture_thread.start()

            except Exception as e:
                critical_error(e)

        time.sleep(sleep_time / 1000)

if __name__ == "__main__":
    main()
