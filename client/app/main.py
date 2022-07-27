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
import PIL.ImageDraw
import pyrealsense2 as rs
from opcua import ua

from camera import Camera
from config import Config
from status import StatusCodes, TEMP_WARNING, TEMP_MAX_SAFE, TEMP_CRITICAL

# CONFIGURATION
STATUS_INTERVAL = 10  # time in seconds to update status
WAIT_BEFORE_RESTARTING = 60  # time in seconds to wait before
#                               restarting program in the event of an error.
#                               set to 0 for no wait time
DEBUG = False  # true: log output goes to console, false: log output goes to .log file
#                 note- if set to 'true' and the script is being run in an
#                 executable form, make sure a console window pops up when
#                 the program starts, otherwise you will not see any log
#                 information

# GLOBALS
global taking_picture
taking_picture = False

# CONSTANTS
METER_TO_FEET = 3.28084  # dont change this
WIDTH = 848  # or this
HEIGHT = 480  # or this
ROI_FALLBACK = '[(283, 160), (283, 320), (565, 320), (565, 160), (320, 160)]'
LOG_FORMAT = '%(levelname)-10s %(asctime)-25s LINE:%(lineno)-5d THREAD:%(thread)-7d %(message)s'
MSG_STARTUP = "~~~~~~~~~~~~~~Starting Client Application~~~~~~~~~~~~"
MSG_RESTART = "~~~~~~~~~~~~~~~~~Restarting Application~~~~~~~~~~~~~~\n"
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


def take_picture(image, polygon):
    """saves picture to 'snapshots' directory. Creates
    directory if not found

    :param image: image
    :type image: image
    """
    log.debug('Taking picture...')
    try:
        # GET FILE PATH
        path = get_program_path()
        # GET TIMESTAMP FOR FILE NAME
        timestamp = datetime.now()
        timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")

        if dir_exists(path=path, name='snapshots'):
            # SAVE IMAGE
            image = draw_poly(image, polygon)
            image.save(f'{path}\\snapshots\\{timestamp}.jpg')
            # sleep thread to prevent saving a bunch of pictures
            time.sleep(5)
            log.info(f'Took picture: "{timestamp}"')
        else:
            snapshot_path = path + '\\snapshots\\'
            os.mkdir(snapshot_path)
            # SAVE IMAGE
            image = draw_poly(image, polygon)
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


def get_program_path() -> str:
    """gets full path name of program. Works if 
    program is frozen

    :return: path
    :rtype: string
    """
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    elif __file__:
        path = os.path.dirname(__file__)
    return path


def draw_poly(image: PIL.Image.Image, poly: list) -> PIL.Image.Image:
    """draw polygon on depth image

    :param image: image
    :type image: PIL.Image
    :param poly: polygon
    :type poly: list
    :return: image with polygon
    :rtype: PIL.Image.Image
    """
    draw = PIL.ImageDraw.Draw(image)
    draw.polygon(poly, width=4)
    return image


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


def critical_error(message="Unkown critical error", allow_restart=True, camera=None):
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
        if camera is not None:
            try:
                camera.stop()
            except Exception:
                pass
        log.critical(MSG_ERROR_SHUTDOWN)
        os._exit(1)
        # sys.exit()


def roi_box(roi):
    """calculate bounding box from list of coordinates.
    If provide roi is not valid, the bounding box defaults
    to [106, 60, 742, 420]

    :param roi: list of (x, y) coordinates
    :type roi: list
    :return: bounding box coordinates
    :rtype: tuple
    """
    if len(roi) > 2:
        x = [i[0] for i in roi]
        y = [i[1] for i in roi]
        x1, y1, x2, y2 = min(x), min(y), max(x), max(y)
    else:
        x1, y1, x2, y2 = 106, 60, 742, 420
    return x1, y1, x2, y2


def get_status(camera):
    status = StatusCodes.OK
    try:
        asic_temp = camera.asic_temperature
        projector_temp = camera.projector_temperature

        temp_warning = asic_temp > TEMP_WARNING or projector_temp > TEMP_WARNING
        temp_max_safe = asic_temp > TEMP_MAX_SAFE or projector_temp > TEMP_MAX_SAFE
        temp_critical = asic_temp > TEMP_CRITICAL or projector_temp > TEMP_CRITICAL

        if temp_critical:
            status = StatusCodes.ERROR_TEMP_CRITICAL
        elif temp_max_safe:
            status = StatusCodes.ERROR_TEMP_MAX_SAFE
        elif temp_warning:
            status = StatusCodes.ERROR_TEMP_WARNING

    except Exception as e:
        status = StatusCodes.ERROR_UPDATING_STATUS
        log.warning(f'Failed to update status: {e}')
        return status
    if status != StatusCodes.OK:
        log.warning(f'Status update: {StatusCodes.name(status)} | '
                    f'Asic: {asic_temp} celcius Projector: {projector_temp} celcius')
    return status


def send_status(status_node, status_value):
    dv = status_value
    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
    status_node.set_value(dv)


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
            format=LOG_FORMAT)
    else:
        log.basicConfig(filename="logger.log",
                        filemode="a",
                        level=log.DEBUG,
                        format=LOG_FORMAT)
    log.info(MSG_STARTUP)

    try:
        config = Config('configuration.ini', REQUIRED_DATA)
    except configparser.DuplicateOptionError as e:
        critical_error(
            f'Duplicate option found in configuration file: {e}', False)
    except RuntimeError as e:
        critical_error(e, False)
    except FileNotFoundError as e:
        critical_error(e, False)
    else:
        try:
            # main logger
            lvl = config.get_value(
                'logging', 'logging_level', fallback='debug').upper()
            log_level = getattr(log, lvl, log.DEBUG)
            log.getLogger().setLevel(log_level)

            # opcua logger
            lvl = config.get_value(
                'logging', 'opcua_logging_level', fallback='warning').upper()
            opcua_log_level = getattr(log, lvl, log.WARNING)
            log.getLogger(opcua.__name__).setLevel(opcua_log_level)
            log.info("Successfully set logging levels")
        except KeyError as e:
            log.getLogger().setLevel(log.DEBUG)
            log.getLogger(opcua.__name__).setLevel(log.WARNING)
            log.warning(f'Failed to set logging levels from config file: '
                        f'{e} not found in config file')

    ##############################################################################
    #                                  CAMERA                                    #
    ##############################################################################

    try:
        # setup camera stream
        f = int(config.get_value('camera', 'framerate', fallback='30'))
        m = bool(float(config.get_value('camera', 'metric', fallback='0.0')))
        camera = Camera(config.data, width=WIDTH,
                        height=HEIGHT, framerate=f, metric=m)
        camera.options.write_all_settings()
        camera.options.log_settings()
        camera.start_callback()

        # set exposure roi from config file
        enable_roi_exposure = bool(float(config.get_value(
            'camera', 'region_of_interest_auto_exposure', fallback='0.0')))

        if enable_roi_exposure:
            config_roi = eval(config.get_value(
                'camera', 'region_of_interest', fallback=ROI_FALLBACK))
            x1, y1, x2, y2 = roi_box(config_roi)
            roi = rs.region_of_interest()
            roi.min_x, roi.min_y, roi.max_x, roi.max_y = x1, y1, x2, y2
            camera.set_roi(roi)

        log.info("Successfully connected RealSense camera")
    except RuntimeError as e:
        critical_error(
            f"Failed to connect camera: RuntimeError: {e}")
    except Exception as e:
        critical_error(e)

    ##############################################################################
    #                                    OPC                                     #
    ##############################################################################

    try:
        ip = str(config.get_value('server', 'ip'))
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

            roi_invalid_node = client.get_node(
                str(config.get_value('nodes', 'roi_invalid_node')))

            roi_deviation_node = client.get_node(
                str(config.get_value('nodes', 'roi_deviation_node')))

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

    # store repeatedly used variables
    sleep_time = float(config.get_value(
        'application', 'sleep_time', fallback='10'))
    polygon = list(eval(config.get_value(
        'camera', 'region_of_interest', fallback=ROI_FALLBACK)))
    filter_level = int(config.get_value(
        'camera', 'spatial_filter_level', fallback='0'))

    log.debug('Starting loop')
    start = time.time()
    while True:
        if camera.connected:
            # check for valid depth frame
            try:
                if not camera.depth_frame:
                    continue
            except RuntimeError as e:
                critical_error(
                    f'Error while retrieving camera frames: {e}')
            except Exception as e:
                critical_error(
                    f'Error while retrieving camera frames: {e}')
            else:
                try:
                    roi_depth, roi_invalid, roi_deviation = camera.ROI_data(
                        polygon=polygon, filter_level=filter_level)

                    ##############################################
                    #                  SEND DATA                 #
                    ##############################################

                    # depth
                    dv = roi_depth
                    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                    roi_depth_node.set_value(dv)

                    # invalid
                    dv = roi_invalid
                    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                    roi_invalid_node.set_value(dv)

                    # deviation
                    dv = roi_deviation
                    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                    roi_deviation_node.set_value(dv)

                    # roi select
                    dv = random.random() * 100
                    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
                    roi_select_node.set_value(dv)

                    ##############################################
                    #                  SEND ALIVE                #
                    ##############################################

                    if not alive_node.get_value():
                        dv = True
                        dv = ua.DataValue(ua.Variant(
                            dv, ua.VariantType.Boolean))
                        alive_node.set_value(dv)

                    ##############################################
                    #                SAVE PICTURE                #
                    ##############################################

                    pic_trig = picture_trigger_node.get_value()
                    global taking_picture
                    if pic_trig and not taking_picture:
                        taking_picture = True
                        ret, img = depth_frame_to_image(camera.depth_frame)
                        if ret:
                            picture_thread = threading.Thread(
                                target=take_picture, args=[img, polygon])
                            if not picture_thread.is_alive():
                                picture_thread.start()

                except Exception as e:
                    critical_error(e)

            elapsed = time.time() - start
            if elapsed > STATUS_INTERVAL:
                status_code = get_status(camera)
                if status_code == StatusCodes.ERROR_TEMP_CRITICAL:
                    send_status(status_node, StatusCodes.ERROR_NO_RESTART)
                    critical_error(
                        f'Camera overheating (temp > {TEMP_CRITICAL} celcius)', False, camera)
                send_status(status_node, status_code)
                start = time.time()

            time.sleep(sleep_time / 1000)

        else:
            critical_error('Camera disconnected')


if __name__ == "__main__":
    main()
