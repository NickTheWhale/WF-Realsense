import opcua
import time
import pyrealsense2 as rs


sv = opcua.Server()
sv.set_server_name("Realsense OCP")
sv.set_endpoint("opc.tcp://localhost:4840")

# Register the OPC-UA namespace
idx = sv.register_namespace("http://localhost:4840")
# start the OPC UA server (no tags at this point)
sv.start()

objects = sv.get_objects_node()
# Define camera object
camera_obj = objects.add_object(idx, "Camera")

depth_tag = camera_obj.add_variable(idx, "Depth", 64)
depth_tag.set_writable(writable=True)

# Create a context object. 
# This object owns the handles to all connected realsense devices
pipeline = rs.pipeline()

# Configure streams
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start streaming
print("Connecting Camera...")
pipeline.start(config)
print("Connected")

# Initialize depth_tag
depth_tag.set_value(0)
while True:
    frames = pipeline.wait_for_frames()
    depth = frames.get_depth_frame()
    if not depth:
        continue

    # w, h = 10, 10
    # pixels = [[0 for x in range(w)] for y in range(h)] 
    
    # for y in range(h):
    #     for x in range(w):
    #         pixels[y][x] = depth.get_distance(x*(640//w), y*(480//h)) * 3.28084
    #         pixels[y][x] = round(pixels[y][x], 1)
    
    # myvar1.set_value(pixels)
    
    distance = depth.get_distance(320, 240)
    
    # depth_tag.set_value(distance * 3.28084)
    depth_val = depth_tag.get_value()
    print(depth_val)
    
    time.sleep(.01)
