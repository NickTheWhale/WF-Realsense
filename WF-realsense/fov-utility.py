import pyrealsense2 as rs
import numpy as np
import numpy.ma as ma
import cv2
from PIL import Image, ImageDraw


class DrawRectangle():
    def __init__(self):
        self.__coordinates = []
        self.__right_clicked = False
        self.__last_coordinate = ()
        
    def get_coordinates(self, event, x, y, flags, parameters):
        if event == cv2.EVENT_FLAG_LBUTTON:
            if not self.__right_clicked:
                if self.coordinate_valid(x, y):
                    self.__coordinates.append((x, y))
            print(f'Coordinates: {self.__coordinates}')
        elif event == cv2.EVENT_FLAG_RBUTTON:
            if not self.__right_clicked:
                if self.coordinate_valid(x, y):
                    self.__coordinates.append(self.__coordinates[0])
            print(f'Coordinates: {self.__coordinates}')
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
            print(f'Coordinates: {self.__coordinates}')
            self.__right_clicked = False
    
    def redo(self):
        cd = self.__coordinates
        lcd = self.__last_coordinate
        if len(cd) == 0:
            cd.append(lcd)
        elif len(cd) > 0:
            if cd[-1] != lcd:
                cd.append(lcd)
        
    @property
    def coordinates(self):
        return self.__coordinates



def main():
    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # Start streaming
    pipeline.start(config)
    
    try:
        
                
        
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        rect_widget = DrawRectangle()
        
        
        polygon = [(115, 94), (107, 289), (457, 331), (478, 124), (115, 94)]
        width = 640
        height = 480

        img = Image.new('L', (width, height), 0)
        ImageDraw.Draw(img).polygon(polygon, outline=1, fill=1)
        mask = np.array(img)
        
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
                depth_image, alpha=0.08), cv2.COLORMAP_JET)

            cv2.setMouseCallback('RealSense', rect_widget.get_coordinates)
            key = cv2.waitKey(1)

            rect_widget.draw(depth_colormap)

            if key == ord('r'):
                rect_widget.reset()
            elif key == ord('z'):
                rect_widget.undo()
            elif key == ord('y'):
                rect_widget.redo()
            elif key == ord('q'):
                pipeline.stop()
                cv2.destroyAllWindows()
                exit(1)
            
            # Show image
            cv2.imshow('RealSense', depth_colormap)
            key = cv2.waitKey(1)

    finally:

        # Stop streaming
        pipeline.stop()


if __name__ == "__main__":
    main()
