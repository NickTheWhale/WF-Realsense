from cmath import nan
from cv2 import CV_32F
from matplotlib.pyplot import text
import pyrealsense2 as rs
import numpy as np
import numpy.ma as ma
from numpy.random import default_rng
import cv2
import pylab as plt
from matplotlib.path import Path

# CONSTANTS
M_TO_F = 3.28084

class MaskWidget():
    def __init__(self):
        self.__coordinates = []
        self.__right_clicked = False
        self.__last_coordinate = ()

    def get_coordinates(self, event, x, y, flags, parameters):
        if event == cv2.EVENT_FLAG_LBUTTON:
            if not self.__right_clicked:
                if self.coordinate_valid(x, y):
                    self.__coordinates.append((x, y))
        elif event == cv2.EVENT_FLAG_RBUTTON:
            if not self.__right_clicked:
                if self.coordinate_valid(x, y):
                    self.__coordinates.append(self.__coordinates[0])
            self.__right_clicked = True

    def reset(self):
        self.__coordinates = []
        self.__right_clicked = False

    def draw(self, image):
        n = len(self.coordinates)
        if n == 1:
            cv2.line(image, self.coordinates[0], self.coordinates[0],
                     color=(255, 255, 255), thickness=3)
        elif n == 2:
            cv2.line(image, self.coordinates[0], self.coordinates[1],
                     color=(255, 255, 255), thickness=2)
        elif n > 2:
            for i in range(n - 1):
                cv2.line(image, self.coordinates[i], self.coordinates[i+1],
                         color=(255, 255, 255), thickness=2)

    def coordinate_valid(self, x, y):
        if x <= 639 and x >= 0:
            if y <= 479 and y >= 0:
                return True
        else:
            return False

    def undo(self):
        if len(self.coordinates) >= 1:
            self.__last_coordinate = self.__coordinates[-1]
            self.__coordinates.pop()
            self.__right_clicked = False

    def redo(self):
        cd = self.__coordinates
        lcd = self.__last_coordinate
        if len(cd) == 0:
            cd.append(lcd)
        elif len(cd) > 0:
            if cd[-1] != lcd:
                cd.append(lcd)

    def polygon(self):
        if len(self.__coordinates) > 2:
            if self.__right_clicked:
                return np.array(self.__coordinates)
        return False

    def text_coordinate(self, text_length):
        cd = self.__coordinates
        text_cd = [0, 0]
        for i in range(len(cd) - 1):
            text_cd[0] += cd[i][0]
            text_cd[1] += cd[i][1]
        text_cd[0] //= len(cd) - 1
        text_cd[0] -= 30
        text_cd[1] //= len(cd) - 1
        text_cd[1] += 12
        return text_cd
        
    @property
    def coordinates(self):
        return self.__coordinates


def main():
    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # Start streaming
    profile = pipeline.start(config)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    
    try:
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        mask_widget = MaskWidget()

        blank_image = np.zeros((480, 640))

        while True:

            # Wait for a coherent pair of frames: depth and color
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            if not depth_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())

            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
                depth_image, alpha=0.07), cv2.COLORMAP_JET)

            cv2.setMouseCallback('RealSense', mask_widget.get_coordinates)
            key = cv2.waitKey(1)

            if key == ord('r'):
                mask_widget.reset()
            elif key == ord('z'):
                mask_widget.undo()
            elif key == ord('y'):
                mask_widget.redo()
            elif key == ord('q'):
                # pipeline.stop()
                cv2.destroyAllWindows()
                exit(1)

            mask_widget.draw(depth_colormap)
            poly = mask_widget.polygon()
            
            if poly is not False:
                # Compute mask from user polygon coordinates
                mask = cv2.fillPoly(blank_image, pts=[poly], color=1)
                mask = mask.astype('bool')
                mask = np.invert(mask)
                
                # Apply mask to depth data
                depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
                depth_mask = ma.masked_invalid(depth_mask)
                depth_mask = ma.masked_equal(depth_mask, 0)
                
                # Compute average distance in the selected region of interest
                ROI_depth = depth_mask.mean() * depth_scale * M_TO_F
                
                # print(f'Average Distance: {ROI_depth:0.3f}')
                mask_widget.text_coordinate
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                text_pos = mask_widget.text_coordinate(len(str(ROI_depth)))
                
                cv2.putText(depth_colormap, str(round(ROI_depth, 2)), 
                            (text_pos), font, 1, (255,255,255), 2, cv2.LINE_AA)
                cv2.imshow('RealSense', depth_colormap)
            else:
                cv2.imshow('RealSense', depth_colormap)
                blank_image = np.zeros((480, 640))
            key = cv2.waitKey(1)

    finally:

        # Stop streaming
        pipeline.stop()


if __name__ == "__main__":
    main()
