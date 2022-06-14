import opcua
import time
import pyrealsense2 as rs
import numpy as np


def main():
    MOVING_AVERAGE = True
    
    width = 4
    height = 4

    # Intel Realsense setup
    print("Connecting Camera... ", end="")
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)
    profile = pipeline.start(config)
    print("success")

    # Rolling average buffer
    num_of_readings = 20
    readings = [0] * num_of_readings

    previous_distance = 0

    
    
    # client = opcua.Client("opc.tcp://localhost:4840")
    client = opcua.Client("opc.tcp://192.168.0.1:4840")
    client.connect()

    depth_node = client.get_node("ns=2;i=2")
    timer_node = client.get_node("ns=2;i=3")
    
    # Window calculations
    vert_l = 240 - height // 2
    vert_u = 241 + height // 2
    horz_l = 320 - width // 2
    horz_u = 321 + width // 2

    offset_time = time.time()
    
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

        
        # # narrow_depth_array = depth_array[218:237, 314:327]
        # narrow_depth_array = depth_array[vert_l:vert_u, horz_l:horz_u]
        # depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
        # distance = narrow_depth_array.mean() * depth_scale * 3.28084
        
        # print(distance)
        
        # # print(narrow_depth_array * depth_scale * 3.28084)
        
        # # print(f'Distance: {distance}  DArr: {depth_array(320, 240)}')
        
        readings.append(distance)

        if len(readings) > num_of_readings:
            readings.pop(0)

        current_distance = round(sum(readings) / num_of_readings, 3)
        
        if MOVING_AVERAGE:
            if current_distance != previous_distance:
                previous_distance = current_distance
                depth_node.set_value(current_distance)
                timer_node.set_value(time.time() - offset_time)
                print(f'Distance (feet): {current_distance:0.2f}')
        else:
            depth_node.set_value(distance)
            timer_node.set_value(time.time())
            print(f'Distance (feet): {distance:0.2f}')
            

        time.sleep(0.001)


if __name__ == "__main__":
    main()
