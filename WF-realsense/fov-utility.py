import sys

import cv2
import numpy as np
import numpy.ma as ma
import pyrealsense2 as rs

# CONSTANTS
M_TO_F = 3.28084


class MaskWidget():
    def __init__(self):
        self.__coordinates = []
        self.__right_clicked = False
        self.__last_coordinate = ()

    def get_coordinates(self, event, x, y, flags, parameters):
        '''
        Method to store mouse coordinates only if they are valid
        '''
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
        '''
        Method to reset coordinate list and mouse right click flag
        '''
        self.__coordinates = []
        self.__right_clicked = False

    def draw(self, image):
        '''
        Method to draw lines between coordinates
        '''
        n = len(self.coordinates)
        if n == 1:
            cv2.line(image, self.coordinates[0], self.coordinates[0],
                     color=(38, 37, 37), thickness=3)
        elif n == 2:
            cv2.line(image, self.coordinates[0], self.coordinates[1],
                     color=(38, 37, 37), thickness=2)
        elif n > 2:
            for i in range(n - 1):
                cv2.line(image, self.coordinates[i], self.coordinates[i+1],
                         color=(38, 37, 37), thickness=2)

    def coordinate_valid(self, x, y):
        '''
        Method to check if coordinated are valid
        '''
        if x <= 847 and x >= 0:
            if y <= 479 and y >= 0:
                return True
        else:
            return False

    def undo(self):
        '''
        Method to undo previous coordinate capture
        '''
        if len(self.coordinates) >= 1:
            self.__last_coordinate = self.__coordinates[-1]
            self.__coordinates.pop()
            self.__right_clicked = False

    def redo(self):
        '''
        Method to redo a single undo command. 
        Does not support more than one redo
        '''
        cd = self.__coordinates
        lcd = self.__last_coordinate
        if len(cd) == 0:
            cd.append(lcd)
        elif len(cd) > 0:
            if cd[-1] != lcd:
                cd.append(lcd)

    def polygon(self):
        '''
        Method to return numpy array of coordinates
        '''
        if len(self.__coordinates) > 2:
            if self.__right_clicked:
                return np.array(self.__coordinates)
        return False

    def text_coordinate(self, text_length):
        '''
        Method to calculate depth text placement. 
        Averages vertext positions of polygon and returns the 
        text coordinates
        '''
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
        '''
        Method to return coordinate list
        '''
        return self.__coordinates


def main():
    try:
        # Create/open file to output mask
        file = open('mask-output.txt', 'w')
        file.write(
            "Copy this into RealSenseOPC Client Application configuration file")
        file.write('\n')
        file.close()

        # Configure depth and color streams
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)

        # Start streaming
        profile = pipeline.start(config)

        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()

        cv2.namedWindow('RealSense FOV Utility', cv2.WINDOW_AUTOSIZE)
        mask_widget = MaskWidget()

        blank_image = np.zeros((480, 848))

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

            cv2.setMouseCallback('RealSense FOV Utility',
                                 mask_widget.get_coordinates)
            key = cv2.waitKey(1)

            if key == ord('r'):
                mask_widget.reset()
            elif key == ord('z'):
                mask_widget.undo()
            elif key == ord('y'):
                mask_widget.redo()
            elif key == ord('q'):
                cv2.destroyAllWindows()
                sys.exit(0)

            mask_widget.draw(depth_colormap)
            poly = mask_widget.polygon()

            if poly is not False:
                # Write polygon vertices to file
                write_to_file = True
                if write_to_file:
                    file = open('mask-output.txt', 'w')
                    file.write(
                        "Copy this into RealSenseOPC Client Application configuration file")
                    file.write('\n')
                    file.write(str(mask_widget.coordinates))
                    file.close()
                    write_to_file = False

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

                mask_widget.text_coordinate

                font = cv2.FONT_HERSHEY_SIMPLEX
                text_pos = mask_widget.text_coordinate(len(str(ROI_depth)))

                cv2.putText(depth_colormap, f'{ROI_depth:0.2f}',
                            (text_pos), font, 1, (38, 37, 37), 2, cv2.LINE_AA)
                cv2.imshow('RealSense FOV Utility', depth_colormap)
                cv2.setWindowTitle('RealSense FOV Utility',
                                   f'RealSense FOV Utility   '
                                   f'ROI Depth: {ROI_depth:0.4f} (feet)')
                cv2.imshow('depth_mask', depth_mask * 100)

            else:
                write_to_file = False
                cv2.imshow('RealSense FOV Utility', depth_colormap)
                cv2.setWindowTitle('RealSense FOV Utility',
                                   'RealSense FOV Utility')
                blank_image = np.zeros((480, 848))

            # Display color image
            key = cv2.waitKey(1)

    finally:

        # Stop streaming
        pipeline.stop()


if __name__ == "__main__":
    main()
