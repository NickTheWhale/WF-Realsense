import cv2
import numpy as np
import numpy.ma as ma
import pyrealsense2 as rs

# constants
METER_TO_FEET = 3.28084

class MaskWidget():
    def __init__(self):
        """create mask widget

        :param image: numpy array
        :type image: numpy array
        """
        self.__coordinates = []
        self.__coordinates_copy = []
        self.__right_clicked = False
        self.__left_clicked = False
        self.__x = -1
        self.__y = -1
        self.__line_color = (255, 255, 255)

    def get_coordinates(self, event):
        """mouse movement callback. Stores mouse coordinates if they are within
        the image

        :param event: opencv mouse event
        :type event: cv2.event
        :param x: x coordinate cursor
        :type x: int
        :param y: y coordinate cursor
        :type y: int
        :param flags: opencv callback requirement
        :type flags: unknown
        :param parameters: opencv callback requrement
        :type parameters: unknown
        """
        self.__x = event.x
        self.__y = event.y
        if event.num == 1:
            self.__left_clicked = True
            if not self.__right_clicked:
                if self.coordinate_valid(event.x, event.y):
                    self.__coordinates.append((event.x, event.y))
        elif event.num == 3:
            if self.__left_clicked:
                if not self.__right_clicked:
                    if self.coordinate_valid(event.x, event.y) and len(self.coordinates) > 0:
                        self.__coordinates.append(self.__coordinates[0])
                        self.__coordinates_copy = self.__coordinates
            self.__right_clicked = True

    def reset(self, evt=None):
        """resets mask widget state. Clears coordinates and right click flag
        """
        self.__coordinates = []
        self.__right_clicked = False
        self.__left_clicked = False

    def draw(self, image):
        """draws opencv lines between stored coordinates
        """
        n = len(self.coordinates)
        if n == 1:
            cv2.line(image, self.coordinates[0], self.coordinates[0],
                     color=self.__line_color, thickness=3)
        elif n == 2:
            cv2.line(image, self.coordinates[0], self.coordinates[1],
                     color=self.__line_color, thickness=2)
        elif n > 2:
            for i in range(n - 1):
                cv2.line(image, self.coordinates[i], self.coordinates[i+1],
                         color=self.__line_color, thickness=2)

    def coordinate_valid(self, x, y):
        """checks if a coordiante lies within an image

        :param x: x coordinate
        :type x: int
        :param y: y coordinate
        :type y: int
        :return: validity
        :rtype: bool
        """
        if x <= 847 and x >= 0:
            if y <= 479 and y >= 0:
                return True
        else:
            return False

    def undo(self, evt=None):
        """removes last coordinate in stored list and resets right click flag
        """
        if len(self.coordinates) >= 1:
            self.__coordinates.pop()
            self.__right_clicked = False
        # elif len(self.coordinates) == 0:
        #     self.__coordinates = self.__coordinates_copy

    def polygon(self):
        """returns array of coordinates if right click flag is true

        :return: coordinates
        :rtype: numpy.array
        """
        if len(self.__coordinates) > 0:
            if self.__right_clicked:
                return (True, np.array(self.__coordinates))
        return (False, None)

    def text_coordinate(self):
        """averages location of all stored coordinates

        :return: average location
        :rtype: list
        """
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
    def cursor_xy(self):
        """cursor position

        :return: x, y coordinate
        :rtype: int tuple
        """
        return self.__x, self.__y

    @property
    def coordinates(self):
        """coordinates

        :return: list of coordinates
        :rtype: list
        """
        return self.__coordinates
    
    @property
    def line_color(self):
        return self.__line_color
    
    @line_color.setter
    def line_color(self, color):
        self.__line_color = color
    
    
    
    ##############################################################
    # dont use
    ##############################################################
    
    
    def raw_depth_mask(self, depth_frame, polygon, blank_image):
        if len(polygon) > 0:
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # compute mask
            mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
            mask = mask.astype('bool')
            mask = np.invert(mask)
            
            depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
            return depth_mask            
                
    def clean_depth_mask(self, depth_frame, polygon, blank_image):
        if len(polygon) > 0:
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # compute mask
            mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
            mask = mask.astype('bool')
            mask = np.invert(mask)
            
            # mask depth frame and ignore invalid/zero distances
            depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
            depth_mask = ma.masked_invalid(depth_mask)
            depth_mask = ma.masked_equal(depth_mask, 0)
            
            return depth_mask     
        
    def ROI_depth(self, depth_frame, polygon, blank_image, depth_scale, filter_level=0):
        """function to calculate the average distance within a region of interest. 
        This is done be either averaging the depth within a region of interest, or
        first filtering the depth data and then calculating the average

        :param depth_frame: camera frame containing depth data
        :type depth_frame: pyrealsense2.frame
        :param polygon: polygon vertices [(x1, y1), (x2, y2)]
        :type polygon: list
        :param blank_image: numpy array of zeros with the same dimension as the depth_frame
        :type blank_image: numpy.array
        :param depth_scale: depth scale reported by the camera to convert 
        raw depth data to known units
        :type depth_scale: float
        :param filter_level: spatial filtering level (1-5), defaults to 0
        :type filter_level: int, optional
        :return: distance (in feet) at the defined region of interest,
        or 0 if no regiong of interest is supplied
        :rtype: float
        """
        
        # convert list of coordinate tuples to numpy array
        polygon = np.array(polygon)
        if filter_level > 5:
            filter_level = 5
        if len(polygon) > 0:
            if filter_level > 0:
                # Compute filtered depth image
                spatial = rs.spatial_filter()
                spatial.set_option(rs.option.holes_fill, filter_level)
                filtered_depth_frame = spatial.process(depth_frame)
                filtered_depth_image = np.asanyarray(
                    filtered_depth_frame.get_data())

                # Compute mask form polygon vertices
                mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
                mask = mask.astype('bool')
                mask = np.invert(mask)

                # Apply mask to filtered depth data and ignore invalid/zero distances
                filtered_depth_mask = ma.array(
                    filtered_depth_image, mask=mask, fill_value=0)
                filtered_depth_mask = ma.masked_invalid(filtered_depth_mask)
                filtered_depth_mask = ma.masked_equal(filtered_depth_mask, 0)

                # Compute average distnace of the region of interest
                ROI_depth = filtered_depth_mask.mean() * depth_scale * METER_TO_FEET
            else:
                depth_image = np.asanyarray(depth_frame.get_data())
                # Compute mask from polygon vertices
                mask = cv2.fillPoly(blank_image, pts=[polygon], color=1)
                mask = mask.astype('bool')
                mask = np.invert(mask)

                # Apply mask to depth data and ignore invalid/zero distances
                depth_mask = ma.array(depth_image, mask=mask, fill_value=0)
                depth_mask = ma.masked_invalid(depth_mask)
                depth_mask = ma.masked_equal(depth_mask, 0)

                # Compute average distance of the region of interest
                ROI_depth = depth_mask.mean() * depth_scale * METER_TO_FEET
            return ROI_depth
        else:
            return 0