import opcua
import time
import pyrealsense2 as rs

# Intel Realsense setup
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

print("Connecting Camera...")
pipeline.start(config)
print("Connected")


def main():
    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()

    while True:
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        if not depth:
            continue

        distance = depth.get_distance(320, 240)

        depth_node = client.get_node("ns=2;i=2")
        depth_node.set_value(distance)

        time.sleep(0.01)


if __name__ == "__main__":
    main()
