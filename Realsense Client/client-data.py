import opcua
from opcua import ua
import opcua.ua.uatypes
import pyrealsense2 as rs
from configparser import ConfigParser
import time


def parse_config(file):
    config = ConfigParser()
    config.read(file)
    








def main():
    MOVING_AVERAGE = True

    # Intel Realsense setup
    print("Connecting Camera...    ", end="")
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 90)
    pipeline.start()
    print("success")

    # Rolling average buffer
    num_of_readings = 20
    readings = [0] * num_of_readings
    previous_distance = 0

    
    print("Connecting to Server... ", end="")
    client = opcua.Client("opc.tcp://localhost:4840")
    # client = opcua.Client("opc.tcp://192.168.0.1:4840")
    client.connect()
    print("success")
    
    print("Gettings Nodes...       ", end="")
    depth_node = client.get_node('ns=3;s="OPC Testing"."Realsense Depth"')
    timer_node = client.get_node('ns=3;s="OPC Testing"."Counter"')
    client_tick = client.get_node('ns=3;s="OPC Testing"."Client Tick"')
    array_node = client.get_node('ns=3;s="OPC Testing"."Realsense Depth Array"')
    
    depth_node = client.get_node('ns=2;i=2')
    timer_node = client.get_node('ns=2;i=3')
    client_tick = client.get_node('ns=2;i=4')
    array_node = client.get_node('ns=2;i=5')
    print("success")
    

    offset_time = time.time()
    
    tick = False
    
    while True:
        now = time.time()
        
        # Get camera frame
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        if not depth:
            continue
        
        # Calculate distance
        # depth_array = np.asanyarray(depth.get_data())
        
        distance = depth.get_distance(320, 240) * 3.28084
        
        readings.append(distance)

        if len(readings) > num_of_readings:
            readings.pop(0)

        current_distance = round(sum(readings) / num_of_readings, 3)
        
        if MOVING_AVERAGE:
            if current_distance != previous_distance:
                previous_distance = current_distance
                
                # Send data to PLC
                dv = ua.DataValue(ua.Variant(current_distance, ua.VariantType.Float))
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
                
        else:
            # Send data to PLC
            dv = ua.DataValue(ua.Variant(current_distance, ua.VariantType.Float))
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
