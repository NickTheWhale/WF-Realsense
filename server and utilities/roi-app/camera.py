import cv2
import pyrealsense2 as rs
import numpy as np
import numpy.ma as ma

# constats
METER_TO_FEET = 3.28084

class VideoCapture:
    def __init__(self, width=848, height=480, framerate=30):
        # depth stream setup
        try:
            self.__pipeline = rs.pipeline()
            self.__camera_config = rs.config()
            self.__width = width
            self.__height = height
            self.__framerate = framerate
            self.__camera_config.enable_stream(rs.stream.depth, 
                                            self.__width, 
                                            self.__height, 
                                            rs.format.z16, 
                                            self.__framerate)
            self.__profile = self.__pipeline.start(self.__camera_config)
            self.__depth_sensor = self.__profile.get_device().first_depth_sensor()
            self.__depth_scale = self.__depth_sensor.get_depth_scale()
            self.__colorizer = rs.colorizer()
        except RuntimeError as e:
            raise e

    def get_depth_frame(self, timeout=5000):
        try:
            frames = self.__pipeline.wait_for_frames(timeout_ms=timeout)
            depth_frame = frames.get_depth_frame()
            return (True, depth_frame)
        except RuntimeError:
            return (False, None)

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height
    
    @property
    def framerate(self):
        return self.__framerate
    
    @property
    def depth_scale(self):
        return self.__depth_scale
    
    @property
    def depth_sensor(self):
        return self.__depth_sensor

    @property
    def config(self):
        return self.__camera_config
    
    @property
    def profile(self):
        return self.__profile
    
    @property
    def pipeline(self):
        return self.__pipeline
    
    @property
    def colorizer(self):
        return self.__colorizer