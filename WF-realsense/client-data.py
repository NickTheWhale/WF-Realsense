import opcua
import time
import pyrealsense2 as rs


def main():
    MOVING_AVERAGE = True

    # Intel Realsense setup
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 90)

    print("Connecting Camera... ", end="")
    pipeline.start(config)
    print("success")

    # Rolling average buffer
    num_of_readings = 20
    readings = [0] * num_of_readings

    previous_distance = 0

    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()

    depth_node = client.get_node("ns=2;i=2")

    while True:
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        if not depth:
            continue

        distance = depth.get_distance(320, 240) * 3.28084

        readings.append(distance)

        if len(readings) > num_of_readings:
            readings.pop(0)

        current_distance = round(sum(readings) / num_of_readings, 3)

        if MOVING_AVERAGE:
            if current_distance != previous_distance:
                previous_distance = current_distance
                depth_node.set_value(current_distance)
                print(f'Distance (feet): {current_distance:0.2f}')
        else:
            depth_node.set_value(distance)

        time.sleep(0.001)


if __name__ == "__main__":
    main()
