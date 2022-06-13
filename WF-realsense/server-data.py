import opcua
import time
from opcua import ua

server = opcua.Server()
server.set_server_name("Realsense OCP")
server.set_endpoint("opc.tcp://localhost:4840")

# Register the OPC-UA namespace
idx = server.register_namespace("http://localhost:4840")
# Start the OPC UA server (no tags at this point)
server.start()

# Populate address space
objects = server.get_objects_node()
camera_obj = objects.add_object(idx, "Camera")
depth_tag = camera_obj.add_variable(idx, "Depth", 0,
                                    varianttype=ua.VariantType.Float)
depth_tag.set_writable(writable=True)
depth_tag.set_value(-1)

previous_distance = 0

while True:
    current_distance = depth_tag.get_value()

    if current_distance != previous_distance:
        previous_distance = current_distance
        print(f'Distance (feet): {current_distance:0.2f}')

    time.sleep(0.005)
