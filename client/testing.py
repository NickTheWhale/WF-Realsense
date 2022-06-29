from math import sqrt
import time

from app.camera import Camera
from app.config import Config

REQUIRED_DATA = {
    "server":
    {
        "ip": None
    },
    "nodes":
    {
        "node": None
    }
}

s_x = s_y = s_z = 0

global position_threshold
position_threshold = 2


def setup_camera(config, width, height, framerate=0):
    camera = Camera(config.data, width, height, framerate)

    camera.start()
    return camera


def has_moved(x, y, z):
    if abs(s_x - x) > position_threshold:
        moved = True
    if abs(s_y - y) > position_threshold:
        moved = True
    if abs(s_z - z) > position_threshold:
        moved = True
    else:
        moved = False
    return moved

def main():
    config = Config('config.ini', REQUIRED_DATA)
    camera = setup_camera(config, 848, 480, 30)

    try:
        ret, s_x, s_y, s_z = camera.accel_data()
        while not ret:
            print("getting starting position")
            ret, s_x, s_y, s_z = camera.accel_data()

        print(s_x, s_y, s_z)
        time.sleep(2)
        while True:
            if camera.connected:
                if not camera.depth_frame:
                    continue
                depth = camera.ROI_depth(
                    list(eval(config.get_value('camera', 'region_of_interest'))))
                ret, x, y, z = camera.accel_data()

                ta = sqrt(abs(x*x + y*y + z*z))
                
                if ret:
                    if has_moved(x, y, z):
                        print("camera has moved from original position")
                        time.sleep(5)

                    print(
                        f'Depth: {depth:.3f}  x: {x:.3f}  y: {y:.3f}  z: {z:.3f}  t: {ta:.3f}')

            time.sleep(0.001)

    except KeyboardInterrupt:
        camera.stop()
        print("Done")


if __name__ == "__main__":
    main()
