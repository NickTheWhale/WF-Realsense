import opcua
import time
# import pyrealsense2 as rs


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

# Initialize depth_tag
depth_tag.set_value(-1 / 3.28084)

while True:
    distance = depth_tag.get_value() * 3.28084
    print(f'Distance (feet): {distance:0.4f}')

    time.sleep(0.01)
