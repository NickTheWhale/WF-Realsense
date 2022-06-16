# title:   RealSenseOPC client application
# author:  Nicholas Loehrke 
# data:    June 2022
# license: todo


import opcua
from opcua import ua
import opcua.ua.uatypes
import pyrealsense2 as rs
from configparser import ConfigParser
import time
import sys
import numpy as np


# CONSTANTS
M_TO_F = 3.28084


def parse_config(file):
    """Function to parse data from configuration file. Sets values to 'None' or common
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
            "extra_node": None,
            "receive_node": None,
            "depth_node": None,
            "emitter_enabled": None,
            "emitter_on_off": None,
            "enabled_auto_exposure": None,
            "error_polling_enabled": None,
            "frames_queue_size": None,
            "framerate": None,
            "gain": None,
            "global_time_enabled": None,
            "height": None,
            "inter_cam_sync_mode": None,
            "ip": None,
            "laser_power": None,
            "output_trigger_enabled": None,
            "region_of_interest": None,
            "stereo_baseline": None,
            "status_node": None,
            "visual_preset": None,
            "width": None
        }
        # Server
        config_dict["ip"] = config_file.get(
            'server', 'ip', fallback=None).replace("'", "")
        config_dict["depth_node"] = config_file.get(
            'server', 'depth_node', fallback=None).replace("'", "")
        config_dict["status_node"] = config_file.get(
            'server', 'status_node', fallback=None).replace("'", "")
        config_dict["receive_node"] = config_file.get(
            'server', 'receive_node', fallback=None).replace("'", "")
        config_dict["extra_node"] = config_file.get(
            'server', 'extra_node', fallback=None).replace("'", "")
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
        for val in config_dict:
            if config_dict[val] is None:
                print(val)
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
            print(f'{option} {val}')
            available_f.write(option)
            available_f.write('\n')
        except (RuntimeError, AttributeError):
            pass
    file.close()
    available_f.close()
    # print(f'{option} is not supported')


def main():

    # Read Configuration File
    print("Reading Configuration... ", end="")
    config_file = parse_config('config.ini')
    if config_file is not False:
        print("success")
        print()
    else:
        print(f'Error Reading Config')
        sys.exit(1)

    # Intel Realsense Setup
    print("Connecting Camera...     ", end="")
    pipeline = rs.pipeline()
    camera_config = rs.config()
    w, h, f = config_file["width"], config_file["height"], config_file["framerate"]
    camera_config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
    profile = pipeline.start(camera_config)
    depth_sensor = profile.get_device().first_depth_sensor()
    print("success")

    dump_options(profile=profile)

    # OPC Server Connection Setup
    print("Connecting to Server...  ", end="")
    client = opcua.Client(config_file["ip"])
    client.connect()
    print("success")
    print()

    print("Gettings Nodes...        ", end="")
    depth_node = client.get_node(config_file["depth_node"])
    status_node = client.get_node(config_file["status_node"])
    client_tick = client.get_node(config_file["receive_node"])
    extra_node = client.get_node(config_file["extra_node"])
    print("success")
    print()

    offset_time = time.time()

    tick = False

    # Hardware reset
    # ctx = rs.context()
    # devices = ctx.query_devices()
    # for dev in devices:
    #     dev.hardware_reset()

    while True:

        # Get camera frame

        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        if not depth:
            continue

        # print(rs.option())

        distance = depth.get_distance(424, 240) * 3.28084
        depth_array = depth.data
        depth_array = np.asanyarray(depth_array)
        # print(depth_array.shape, distance, depth.get_data_size(),
        #       depth.get_height(), depth.get_width())

        # Send data to PLC
        dv = ua.DataValue(ua.Variant(distance, ua.VariantType.Float))
        depth_node.set_value(dv)

        dv = ua.DataValue(ua.Variant(
            time.time() - offset_time, ua.VariantType.Float))
        status_node.set_value(dv)

        tick = not tick
        dv = ua.DataValue(ua.Variant(tick, ua.VariantType.Boolean))
        client_tick.set_value(dv)

        arr = []
        for i in range(100):
            arr.append(depth.get_distance(i+270, 240) * 3.28084)

        dv = ua.DataValue(ua.Variant(arr, ua.VariantType.Float))
        extra_node.set_value(dv)

        time.sleep(0.001)


if __name__ == "__main__":
    main()
