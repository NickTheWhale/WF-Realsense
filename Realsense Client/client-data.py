import opcua
from opcua import ua
import opcua.ua.uatypes
import pyrealsense2 as rs
from configparser import ConfigParser
import time
import sys
import numpy as np

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
        config = {
            "ip": None,
            "depth_node": None,
            "timer_node": None,
            "client_node": None,
            "array_node": None,
            "width": None,
            "height": None,
            "framerate": None,
            "region_of_interest": None
        }
        # Server
        config["ip"] = config_file.get('server', 'ip', fallback=None).replace("'", "")
        config["depth_node"] = config_file.get('server', 'depth_node', fallback=None).replace("'", "")
        config["timer_node"]= config_file.get('server', 'timer_node', fallback=None).replace("'", "")
        config["client_node"] = config_file.get('server', 'client_node', fallback=None).replace("'", "")
        config["array_node"] = config_file.get('server', 'array_node', fallback=None).replace("'", "")
        # Camera
        config["width"] = config_file.getint('camera', 'width', fallback=640)
        config["height"] = config_file.getint('camera', 'height', fallback=480)
        config["framerate"] = config_file.getint('camera', 'framerate', fallback=30)
        config["region_of_interest"] = config_file.get('camera', 'region_of_interest', fallback=None)
        for val in config:
            if config[val] is None:
                return False
        return config
    else:
        return False
    

def main():
    
    # Read Configuration File
    print("Reading Configuration... ", end="")
    config_f = parse_config('config.ini')
    if config_f is not False:
        print("success")
    else:
        print(f'Error Reading Config')
        sys.exit(1)
    
    # Intel Realsense Setup
    print("Connecting Camera...     ", end="")
    pipeline = rs.pipeline()
    config = rs.config()
    w, h, f = config_f["width"], config_f["height"], config_f["framerate"]
    config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
    pipeline.start()
    print("success")

    # OPC Server Connection Setup
    print("Connecting to Server...  ", end="")
    client = opcua.Client(config_f["ip"])
    client.connect()
    print("success")
    
    print("Gettings Nodes...        ", end="")    
    depth_node = client.get_node(config_f["depth_node"])
    timer_node = client.get_node(config_f["timer_node"])
    client_tick = client.get_node(config_f["client_node"])
    array_node = client.get_node(config_f["array_node"])
    print("success")
    

    offset_time = time.time()
    
    tick = False
    
    
    # Hardware reset
    # ctx = rs.context()
    # devices = ctx.query_devices()
    # for dev in devices:
    #     dev.hardware_reset()
    
    while True:
        
        # Get camera frame
        
        frames = pipeline.poll_for_frames()
        depth = frames.get_depth_frame()
        if not depth:
            continue
    
        # Calculate distance
        # depth_array = np.asanyarray(depth.get_data())
        
        distance = depth.get_distance(424, 200) * 3.28084
        depth_array = depth.get_data()
        depth_array = np.asanyarray(depth_array)
        print(depth_array.shape, distance)
        
        # Send data to PLC
        dv = ua.DataValue(ua.Variant(distance, ua.VariantType.Float))
        depth_node.set_value(dv)
        
        dv = ua.DataValue(ua.Variant(time.time() - offset_time, ua.VariantType.Float))
        timer_node.set_value(dv)
        
        tick = not tick
        dv = ua.DataValue(ua.Variant(tick, ua.VariantType.Boolean))
        client_tick.set_value(dv)
        
        arr = []
        for i in range(100):
            arr.append(depth.get_distance(i+270, 240) * 3.28084)
            
        dv = ua.DataValue(ua.Variant(arr, ua.VariantType.Float))
        array_node.set_value(dv)
        
        time.sleep(0.001)


if __name__ == "__main__":
    main()
