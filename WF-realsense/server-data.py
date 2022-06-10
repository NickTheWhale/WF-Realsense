import opcua
import time
import pyrealsense2 as rs


s = opcua.Server()
s.set_server_name("OpcUa Test Server")
s.set_endpoint("opc.tcp://localhost:4840")

# Register the OPC-UA namespace
idx = s.register_namespace("http://localhost:4840")
# start the OPC UA server (no tags at this point)
s.start()

objects = s.get_objects_node()
# Define a Weather Station object with some tags
myobject = objects.add_object(idx, "Station")

# Add a Temperature tag with a value and range
myvar1 = myobject.add_variable(idx, "Temperature", 25)
myvar1.set_writable(writable=True)

# Add a Windspeed tag with a value and range
myvar2 = myobject.add_variable(idx, "Windspeed", 11)
myvar2.set_writable(writable=True)


# Create a context object. This object owns the handles to all connected realsense devices
pipeline = rs.pipeline()

# Configure streams
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start streaming
print("Connecting Camera...")
pipeline.start(config)
print("Connected")

while True:
    frames = pipeline.wait_for_frames()
    depth = frames.get_depth_frame()
    if not depth:
        continue

    w, h = 640, 480
    pixels = [[0 for x in range(w)] for y in range(h)] 
    
    for y in range(480):
        for x in range(640):
            pixels[y][x] = round(depth.get_distance(x, y) * 3.28084, 2)

    myvar1.set_value(pixels)
    # myvar2.set_value(random.randrange(10, 20))
    time.sleep(.01)
