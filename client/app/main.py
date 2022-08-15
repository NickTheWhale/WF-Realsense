"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import logging as log
import os
import sys
import time

import opcua
import opcua.ua.uatypes
import pyrealsense2 as rs
from opcua import ua, Node

from camera import Camera
from config import Config
from status import Status

# CONFIGURATION
DEBUG = False  # true: log output goes to console, false: log output goes to .log file
#                 note- if set to 'true' and the script is being run in an
#                 executable form, make sure a console window pops up when
#                 the program starts, otherwise you will not see any log
#                 information
LOOP_TIME_TIMEOUT = 5000  # time in milliseconds before exiting hanging program
STATUS_INTERVAL = 1  # time in seconds to send status to server
STATUS_LOG_INTERVAL = 60  # time in seconds between status log to file
# (time in seconds ~= STATUS_INTERVAL * STATUS_LOG_INTERVAL)
WAIT_BEFORE_RESTARTING = 30  # time in seconds to wait before
#                               restarting program in the event of an error.
#                               set to 0 for no wait time


# CONSTANTS
WIDTH = 848  # or this
HEIGHT = 480  # or this
NUM_OF_ROI = 8  # or this
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


def _setup_config(path: str) -> Config:
    """setup configuration. Return Config object upon success
    or exit program on failure"""
    try:
        config = Config(path, REQUIRED_DATA)
    except Exception as e:
        log.basicConfig(filename='logger.log',
                        filemode='a',
                        level=log.DEBUG,
                        format=LOG_FORMAT)
        log.critical(f'Error reading configuration file: {e}')
        log.critical(MSG_ERROR_SHUTDOWN)
        os._exit(1)
    except:
        log.basicConfig(filename='logger.log',
                        filemode='a',
                        level=log.DEBUG,
                        format=LOG_FORMAT)
        log.critical(f'Error reading configuration file')
        log.critical(MSG_ERROR_SHUTDOWN)
        os._exit(1)
    return config


def _setup_logging(config: Config) -> None:
    """setup root and opcua logging levels"""
    if DEBUG:
        log.basicConfig(level=log.DEBUG)
    else:
        log.basicConfig(filename='logger.log', filemode='a', level=log.DEBUG, format=LOG_FORMAT)
    try:
        # root logger
        raw_level = config.get_value('logging', 'logging_level', fallback='debug').upper()
        log_level = getattr(log, raw_level, log.DEBUG)
        log.getLogger().setLevel(log_level)

        # opcua module logger
        raw_level = config.get_value('logging', 'opcua_logging_level', fallback='warning').upper()
        opcua_log_level = getattr(log, raw_level, log.WARNING)
        log.getLogger(opcua.__name__).setLevel(opcua_log_level)

        log.info('Successfully setup logging')
    except (ValueError, TypeError, KeyError) as e:
        log.getLogger().setLevel(log.INFO)
        log.getLogger(opcua.__name__).setLevel(log.WARNING)
        log.warning(f'Failed to set logging levels from user configuration: {e}')


def _setup_opc(config: Config) -> opcua.Client:
    """setup opc connection"""
    try:
        config_copy = config
        ip = str(config.get_value('server', 'ip'))
        client = opcua.Client(ip)
        client.connect()
        log.info(f'Successfully setup opc client connection to "{ip}"')
    except ConnectionError as e:
        sleep_time = 5
        log.critical(f'Failed to connect to "{ip}". Retrying in {sleep_time} seconds: {e}')
        time.sleep(sleep_time)
        _setup_opc(config_copy)
    except KeyError as e:
        sleep_time = 5
        log.critical(f'Failed to connect to opc server. Retrying in {sleep_time} seconds: {e}')
        time.sleep(sleep_time)
        _setup_opc(config_copy)
    return client


def _setup_camera(config: Config) -> Camera:
    try:
        # connect camera
        config_copy = config
        framerate = int(config.get_value('camera', 'framerate', fallback='0'))
        metric = bool(float(config.get_value('camera', 'metric', fallback='0.0')))
        camera = Camera(config.data,
                        width=WIDTH,
                        height=HEIGHT,
                        framerate=framerate,
                        metric=metric)
        camera.options.write_all_settings()
        camera.options.log_settings()
        camera.start()

        log.info('Successfully setup camera')
    except RuntimeError as e:
        sleep_time = 5
        log.critical(f'Failed to setup camera. Retrying in {sleep_time} seconds: {e}')
        time.sleep(sleep_time)
        _setup_camera(config_copy)
    return camera


def setup() -> tuple:
    """setup components

    :return: client, camera, config
    :rtype: tuple
    """
    try:
        steps = ['configuration setup', 'logging setup', 'opc setup', 'camera setup']
        step = 0
        config = _setup_config('configuration.ini')
        step += 1
        _setup_logging(config)
        step += 1
        client = _setup_opc(config)
        step += 1
        camera = _setup_camera(config)
    except RecursionError:
        log.critical('Maximum setup retries reached')
        log.critical(MSG_ERROR_SHUTDOWN)
        os._exit(1)
    except Exception as e:
        log.critical(f'Error in setup. Could not complete "{steps[step]}": {e}')
        os._exit(1)

    return client, camera, config


class App:
    def __init__(
            self, client: opcua.Client, camera: Camera, configurator: Config):

        self._running = False

        self._client = client
        self._camera = camera
        self._configurator = configurator

        # nodes
        self._nodes = {
            'roi_depth': None,
            'roi_invalid': None,
            'roi_deviation': None,
            'roi_select': None,
            'status': None,
            'alive': None
        }
        self.get_nodes()

        # status
        self._status = Status(self._camera, self._nodes)
        self._previous_status = self._status.status
        self.send_status()

        # camera
        self._sleep_time = float(self._configurator.get_value(
            'application', 'sleep_time', fallback='20'))
        self._spatial_filter_level = int(self._configurator.get_value(
            'camera', 'spatial_filter_level', fallback='0'))

        self._roi_depth = 0.0
        self._roi_invalid = 100.0
        self._roi_deviation = 0.0

        # get regions of interest
        self._polygons = []
        for key in self._configurator.data['roi']:
            poly = list(eval(self._configurator.get_value('roi', key, fallback='[]')))
            self._polygons.append(poly)
        if len(self._polygons) < NUM_OF_ROI:
            self.error(f'Missing regions of interest from configuration file. '
                       f'Need {NUM_OF_ROI}, found {len(self._polygons)}', False)


        self.set_roi_exposure()

        self._sleep_time = float(self._configurator.get_value(
            'application', 'sleep_time', '15')) / 1000

        self._last_log_time = time.time()
        self._start_time = time.time()

    def run(self):
        """main loop"""
        try:
            log.info('Running')
            self._start_time = time.time()
            self._running = True
            while self._camera.connected and self._running:
                self.update_roi_data()
                self.send_roi_data()
                self.send_alive()
                self.send_status()
                time.sleep(self._sleep_time)
        except Exception as e:
            self.error(f'Failure in main program loop: {e}')

    def update_roi_data(self) -> None:
        """query camera for updated roi data"""
        self._roi_select = self._nodes['roi_select'].get_value()

        self._roi_depth, self._roi_invalid, self._roi_deviation = self._camera.roi_data(
            polygons=self._polygons, roi_select=self._roi_select, filter_level=self._spatial_filter_level)

    def send_roi_data(self) -> None:
        """send depth, invalid, and deviation to server"""
        self.write_node(self._nodes['roi_depth'], self._roi_depth, ua.VariantType.Float)
        self.write_node(self._nodes['roi_invalid'], self._roi_invalid, ua.VariantType.Float)
        self.write_node(self._nodes['roi_deviation'], self._roi_deviation, ua.VariantType.Float)

    def send_alive(self) -> bool:
        """set alive to true if false"""
        if not self._nodes['alive'].get_value():
            self.write_node(self._nodes['alive'], True, ua.VariantType.Boolean)
            return True
        return False

    def send_status(self) -> None:
        """send status to server"""
        new_status = self._status.status
        if new_status != self._previous_status:
            self._previous_status = new_status
            self.write_node(self._nodes['status'], new_status, ua.VariantType.Int16)
            return True
        return False

    def write_node(self, node: Node, value, type: ua.VariantType) -> bool:
        """write value to node

        :param node: node
        :type node: Node
        :param value: write value
        :type value: any
        :param type: value type to convert value to
        :type type: ua.VariantType
        """
        try:
            dv = ua.DataValue(ua.Variant(value, type))
            node.set_value(dv)
        except ua.UaError as e:
            log.error(f'Failed to set "{node.get_browse_name()}" to "{value}": {e}')
            return False
        return True

    def get_nodes(self) -> None:
        """retrieve nodes from opc server"""
        try:
            self._nodes = {
                'roi_depth': self.get_node('roi_depth_node'),
                'roi_invalid': self.get_node('roi_invalid_node'),
                'roi_deviation': self.get_node('roi_deviation_node'),
                'roi_select': self.get_node('roi_select_node'),
                'status': self.get_node('status_node'),
                'alive': self.get_node('alive_node')
            }
        except (ua.UaError, KeyError) as e:
            self.error(f'Failed to retrieve nodes from server: {e}', False)

    def get_node(self, name: str) -> Node:
        """retrieve node from opc server"""
        return self._client.get_node(str(self._configurator.get_value('nodes', name)))

    def roi_box(self) -> tuple:
        """calculate bounding box from nested list of coordinates

        :param rois: nested coordinate list: [[(x1, y1)]]
        :type rois: list
        :return: bounding box coordinates: (x1, y1, x2, y2)
        :rtype: tuple
        """
        polys = self._polygons
        x = [y[0] for x in polys for y in x if len(x) > 2]
        y = [y[1] for x in polys for y in x if len(x) > 2]
        if len(x) and len(y) > 2:
            x1, y1 = max(min(x), 0), max(min(y), 0)
            x2, y2 = min(max(x), 847), min(max(y), 479)

            if x1 != x2 and y1 != y2:
                return x1, y1, x2, y2

        x1, y1, x2, y2 = 106, 60, 742, 420
        return x1, y1, x2, y2

    def set_roi_exposure(self) -> bool:
        """set camera auto exposure roi from config file"""
        try:
            enable_roi_exposure = bool(float(self._configurator.get_value(
                'camera', 'region_of_interest_auto_exposure', fallback='0.0')))
            if enable_roi_exposure:
                x1, y1, x2, y2, = self.roi_box()
                roi = rs.region_of_interest()
                roi.min_x, roi.min_y, roi.max_x, roi.max_y = x1, y1, x2, y2
                self._camera.set_roi(roi)
        except RuntimeError:
            log.warning('Failed to set region of interest auto exposure '
                        'from configuration file')
            return False
        return True

    def loop_time(self) -> None:
        """measure loop time"""
        now = time.time()
        delta = (now - self._start_time) * 1000
        self._start_time = time.time()
        return delta

    def error(self, message="Unknown error", restart=True) -> None:
        """log error message, then restart or exit"""
        log.error(message, exc_info=True)
        self.disconnect()
        if restart:
            log.critical(MSG_RESTART)
            if WAIT_BEFORE_RESTARTING > 0:
                time.sleep(WAIT_BEFORE_RESTARTING)
            setup()
        else:
            log.critical(MSG_ERROR_SHUTDOWN)
            sys.exit(1)

    def disconnect(self) -> None:
        """disconnect client and camera"""
        self._running = False
        try:
            self._client.disconnect()
        except RuntimeError:
            pass
        try:
            self._camera.stop()
        except RuntimeError:
            pass

    def stop(self) -> None:
        """disconnect client and camera, then exit"""
        self.disconnect()
        sys.exit(0)


def main():
    client, camera, config = setup()
    app = App(client, camera, config)

    try:
        app.run()
    except KeyboardInterrupt:
        print('Exiting')
        app.stop()


if __name__ == '__main__':
    main()
