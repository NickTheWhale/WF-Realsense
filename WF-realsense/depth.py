## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

#####################################################
## librealsense tutorial #1 - Accessing depth data ##
#####################################################

# First import the library
from turtle import distance
import pyrealsense2 as rs
import time

try:
    # Create a context object. This object owns the handles to all connected realsense devices
    pipeline = rs.pipeline()

    # Configure streams
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # Start streaming
    pipeline.start(config)

    while True:
        # This call waits until a new coherent set of frames is available on a device
        # Calls to get_frame_data(...) and get_frame_timestamp(...) on a device will return stable values until wait_for_frames(...) is called
        previous_time = time.time()
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        if not depth: continue
        elapsed_time = time.time() - previous_time
        print(round(elapsed_time * 1000, 3))
        
        # Print a simple text-based representation of the image, by breaking it into 10x20 pixel regions and approximating the coverage of pixels within one meter
        
        coverage = [0]*64
        for y in range(480):
            for x in range(640):
                dist = depth.get_distance(x, y)
                if 0 < dist and dist < 1:
                    coverage[x//10] += 1
            
            if y%20 is 19:
                line = ""
                for c in coverage:
                    # line += " .:nhBXWW"[c//25]   # 9
                    line += " .,-~:;=!*#$@"[c//17] # 13
                coverage = [0]*64
                print(line)
        # w, h = 20, 20
        # dist_array = [[0 for x in range(w)] for y in range(h)] 
        # for y in range(h):
        #     for x in range(w):
        #         dist_array[y][x] = round(depth.get_distance(x+315, y+235) * 3.28084, 2)
                
        # for i in range(h):
        #     print(dist_array[i])
        # print()
        # print()
        
        # center_distance = depth.get_distance(320, 240) * 3.28084
        # if center_distance > 0:
        #     print(f'depth at center: {center_distance:0.3f}')
        # else:
        #     print("depth at center: N/A")
    exit(0)
#except rs.error as e:
#    # Method calls agaisnt librealsense objects may throw exceptions of type pylibrs.error
#    print("pylibrs.error was thrown when calling %s(%s):\n", % (e.get_failed_function(), e.get_failed_args()))
#    print("    %s\n", e.what())
#    exit(1)
except Exception as e:
    print(e)
    pass