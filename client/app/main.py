"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""


import configparser
import logging as log
import os
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
from status import (ROI_HIGH_INVALID, TEMP_CRITICAL, TEMP_MAX_SAFE,
                    TEMP_WARNING, StatusCodes)

# CONFIGURATION
LOOP_TIME_WARNING = 100  # loop time warning threshold in milliseconds
STATUS_INTERVAL = 2  # time in seconds to update status
STATUS_LOG_INTERVAL = 60  # time in seconds between status log
# (time in seconds ~= STATUS_INTERVAL * STATUS_LOG_INTERVAL)
WAIT_BEFORE_RESTARTING = 30  # time in seconds to wait before
#                               restarting program in the event of an error.
#                               set to 0 for no wait time
DEBUG = True  # true: log output goes to console, false: log output goes to .log file
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
NUM_OF_ROI = 8 # or this
ROI_FALLBACK = '[(283, 160), (283, 320), (565, 320), (565, 160), (320, 160)]'
ROI_AUTO_EXPOSURE_FALLBACK = '[(106, 60), (742, 60), (742, 420), (106, 420), (106, 60)]'
if DEBUG:
    LOG_FORMAT = '%(levelname)-10s %(asctime)-25s LINE:%(lineno)-5d THREAD:%(thread)-7d %(message)s'
    WAIT_BEFORE_RESTARTING = 0
else:
    LOG_FORMAT = '%(levelname)-10s %(asctime)-25s %(message)s'
MSG_STARTUP = "~~~~~~~~~~~~~~Starting Client Application~~~~~~~~~~~~"
MSG_RESTART = (f"~~~~~~~~~~~~~~Restarting Application in "
               f"{WAIT_BEFORE_RESTARTING} seconds~~~~~~~~~~~~~~\n")
MSG_ERROR_SHUTDOWN = "~~~~~~~~~~~~~~~Error (will not restart)~~~~~~~~~~~~~~\n"


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


def take_picture(image, polygons):
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

        if not dir_exists(path, 'snapshots'):
            snapshot_path = path + '\\snapshots\\'
            os.mkdir(snapshot_path)

        # SAVE IMAGE
        for polygon in polygons:
            if len(polygon) >= 2:
                draw_poly(image, polygon)
        image = image.resize((424, 240), PIL.Image.LANCZOS)
        image.save(f'{path}\\snapshots\\{timestamp}.jpg', optimize=True, quality=10)
        # sleep thread to prevent saving a bunch of pictures
        time.sleep(5)
        log.debug(f'Took picture: "{timestamp}"')

    except ValueError as e:
        log.warning(f'Failed to take picture {timestamp}: {e}')
    except FileExistsError as e:
        log.warning(f'Failed to take picture {timestamp}: {e}')
    except OSError as e:
        log.warning(f'Failed to take picture {timestamp}: {e}')
    finally:
        time.sleep(5)
        global taking_picture
        taking_picture = False


def depth_frame_to_image(depth_frame):
    """attempts to convert 'depth_frame' to a color image

    :param depth_frame: depth frame to convert
    :type depth_frame: pyrealsense2.depth_frame
    :return: (status, color image)
    :rtype: (bool, PIL.Image)
    """
    if isinstance(depth_frame, rs.depth_frame):
        try:
            color_frame = rs.colorizer().colorize(depth_frame)
            color_array = np.asanyarray(color_frame.get_data())
            color_image = PIL.Image.fromarray(color_array)

            ret = (True, color_image)
        except TypeError as e:
            log.warning(f'Failed to convert depth frame to image: {e}')
            ret = (False, None)
        except ValueError as e:
            log.warning(f'Failed to convert depth frame to image: {e}')
            ret = (False, None)
    else:
        ret = (False, None)
    return ret


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
        if isinstance(camera, Camera):
            try:
                camera.stop()
            except RuntimeError:
                pass
        if WAIT_BEFORE_RESTARTING > 0:
            time.sleep(WAIT_BEFORE_RESTARTING)
        main()
    else:
        log.critical(MSG_ERROR_SHUTDOWN)
        if isinstance(camera, Camera):
            try:
                camera.stop()
            except:
                os._exit(1)
        os._exit(1)


def set_roi(camera, roi):
    x1, y1, x2, y2 = roi_box(roi)
    roi = rs.region_of_interest()
    roi.min_x, roi.min_y, roi.max_x, roi.max_y = x1, y1, x2, y2
    camera.set_roi(roi)


def roi_box(rois) -> tuple:
    """calculate bounding box from nested list of coordinates

    :param rois: nested coordinate list: [[(x1, y1)]]
    :type rois: list
    :return: bounding box coordinates: (x1, y1, x2, y2)
    :rtype: tuple
    """
    x = [y[0] for x in rois for y in x if len(x) > 2]
    y = [y[1] for x in rois for y in x if len(x) > 2]
    if len(x) and len(y) > 2:
        x1, y1 = max(min(x), 0), max(min(y), 0)
        x2, y2 = min(max(x), 847), min(max(y), 479)

        if x1 != x2 and y1 != y2:
            return x1, y1, x2, y2

    x1, y1, x2, y2 = 106, 60, 742, 420
    return x1, y1, x2, y2


def get_status(camera, invalid):
    status = StatusCodes.OK
    try:
        asic_temp = camera.asic_temperature
        projector_temp = camera.projector_temperature

        temp_warning = asic_temp > TEMP_WARNING or projector_temp > TEMP_WARNING
        temp_max_safe = asic_temp > TEMP_MAX_SAFE or projector_temp > TEMP_MAX_SAFE
        temp_critical = asic_temp > TEMP_CRITICAL or projector_temp > TEMP_CRITICAL
        high_invalid = invalid > ROI_HIGH_INVALID

        if temp_critical:
            status = StatusCodes.ERROR_TEMP_CRITICAL
        elif temp_max_safe:
            status = StatusCodes.ERROR_TEMP_MAX_SAFE
        elif temp_warning:
            status = StatusCodes.ERROR_TEMP_WARNING
        elif high_invalid:
            status = StatusCodes.ERROR_HIGH_INVALID_PERCENTAGE

    except RuntimeError:
        status = StatusCodes.ERROR_UPDATING_STATUS

    return status


def send_status(status_node, status_value):
    dv = status_value
    dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
    status_node.set_value(dv)


def pprint(config: Config):
    TAB = '      '
    BRANCH = '    ╰─ '
    data = config.data
    log.debug('~~~~~~~~~~configuration file~~~~~~~~~~')
    for section in data:
        log.debug(f'[{section}]:')
        for key in data[section]:
            log.debug(f'{BRANCH}{key}:')
            log.debug(f'{TAB}{BRANCH}{data[section][key]}')


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
    except configparser.Error as e:
        critical_error(e, False)
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
        pprint(config)
        camera.start_callback()

        log.info("Successfully connected RealSense camera")
    except RuntimeError as e:
        critical_error(
            f"Failed to connect camera: {e}")

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
    except KeyError as e:
        critical_error(e, False)
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
        except ua.UaError as e:
            critical_error(f'Failed to retrieve nodes: {e}')

    ##############################################################################
    #                                    ROI                                     #
    ##############################################################################

    polygons = []
    for key in config.data['roi']:
        polygons.append(list(eval(config.get_value('roi', key, fallback='[]'))))

    if len(polygons) < NUM_OF_ROI:
        critical_error(f'Missing region of interests. '
                       f'Need {NUM_OF_ROI}, found {len(polygons)}', False)

    # set exposure roi from config file
    enable_roi_exposure = bool(float(config.get_value(
        'camera', 'region_of_interest_auto_exposure', fallback='0.0')))
    try:
        if enable_roi_exposure:
            x1, y1, x2, y2 = roi_box(polygons)
            roi = rs.region_of_interest()
            roi.min_x, roi.min_y, roi.max_x, roi.max_y = x1, y1, x2, y2
            camera.set_roi(roi)
    except RuntimeError as e:
        log.warning(f'Failed to set region of interest auto exposure '
                    f'from configuration file, defaulting to '
                    f'{ROI_AUTO_EXPOSURE_FALLBACK}')

    ##############################################################################
    #                                    LOOP                                    #
    ##############################################################################

    sleep_time = float(config.get_value(
        'application', 'sleep_time', fallback='10'))
    filter_level = int(config.get_value(
        'camera', 'spatial_filter_level', fallback='0'))

    start = time.time()
    log_start = start
    loop_start = start
    first_loop = True

    roi_select = roi_select_node.get_value()

    log.info('Entering main loop')

    while True:
        if camera.connected:
            # check for valid depth frame
            try:
                # if not camera.depth_frame:
                if not isinstance(camera.depth_frame, rs.depth_frame):
                    print("not a depth frame")
                    time.sleep(0.005)
                    continue
            except RuntimeError as e:
                critical_error(
                    f'Error while retrieving camera frames: {e}')
            else:
                try:
                    roi_depth, roi_invalid, roi_deviation = camera.roi_data(
                        polygons=polygons, roi_select=roi_select, filter_level=filter_level)

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

                    ##############################################
                    #                 RECIEVE DATA               #
                    ##############################################

                    # roi select
                    roi_select = roi_select_node.get_value()

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
                                target=take_picture, args=[img, polygons])
                            if not picture_thread.is_alive():
                                picture_thread.start()

                    ##############################################
                    #               STATUS UPDATE                #
                    ##############################################

                    elapsed = time.time() - start
                    log_elapsed = time.time() - log_start
                    if elapsed > STATUS_INTERVAL:
                        status_code = get_status(camera, roi_invalid)
                        if log_elapsed > STATUS_LOG_INTERVAL:
                            if status_code != StatusCodes.OK:
                                log.warning(f'Status update: {StatusCodes.name(status_code)}')
                            log_start = time.time()
                        if status_code == StatusCodes.ERROR_TEMP_CRITICAL:
                            send_status(status_node, StatusCodes.ERROR_NO_RESTART)
                            critical_error(
                                f'Camera overheating (temp > {TEMP_CRITICAL} celcius)', False,
                                camera)
                        send_status(status_node, status_code)
                        start = time.time()

                    time.sleep(sleep_time / 1000)

                    loop_time = (time.time() - loop_start) * 1000
                    if loop_time > LOOP_TIME_WARNING and not first_loop:
                        log.warning(f'High loop time ({loop_time:.2f} ms)')

                    first_loop = False
                    loop_start = time.time()
                except KeyboardInterrupt:
                    continue
                except Exception as e:
                    critical_error(e)

        else:
            critical_error('Camera disconnected')


if __name__ == "__main__":
    main()
