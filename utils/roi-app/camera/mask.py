import cv2
import numpy as np

# constants
METER_TO_FEET = 3.28084


class MaskWidget():
    def __init__(self, *args, **kwargs):
        """create mask widget"""

        self._root = args[0]
        self._id = kwargs.pop('id', None)

        self.__coordinates = []
        self.__right_clicked = False
        self.__left_clicked = False
        self.__x = -1
        self.__y = -1

        self.__active = False

        self.__line_color = (255, 255, 255)
        self.__box_color = (0, 0, 0)
        self.__text_color = (255, 255, 255)

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

        self._x = event.x * self._root.camera.scale
        self._y = event.y * self._root.camera.scale

        if event.num == 1:
            self.__left_clicked = True
            if not self.__right_clicked:
                if self.coordinate_valid(self._x, self._y):
                    self.__coordinates.append((self._x, self._y))
        elif event.num == 3:
            if self.__left_clicked:
                if not self.__right_clicked:
                    if self.coordinate_valid(self._x, self._y) and len(self.coordinates) > 0:
                        self.__coordinates.append(self.__coordinates[0])
            self.__right_clicked = True

    def reset(self, *args, **kwargs):
        """resets mask widget state. Clears coordinates and right click flag"""

        self.__coordinates = []
        self.__right_clicked = False
        self.__left_clicked = False

    def draw(self, image):
        """draws opencv lines between stored coordinates"""

        coordinates = self.__coordinates
        scaled_coordinates = []

        for coordinate in coordinates:
            scaled_coordinates.append(
                (coordinate[0] // self._root.camera.scale,
                 coordinate[1] // self._root.camera.scale)
            )

        n = len(scaled_coordinates)
        if n > 0:
            if self.__active:
                self.__line_color = (255, 255, 255)
                self.__box_color = (0, 0, 0)
                self.__text_color = (255, 255, 255)
            else:
                self.__line_color = (150, 150, 150)
                self.__box_color = (30, 30, 30)
                self.__text_color = (150, 150, 150)
            
            if n == 1:
                cv2.line(image, scaled_coordinates[0], scaled_coordinates[0],
                         color=self.__line_color, thickness=3)
            elif n == 2:
                cv2.line(image, scaled_coordinates[0], scaled_coordinates[1],
                         color=self.__line_color, thickness=2)
            elif n > 2:
                for i in range(n - 1):
                    cv2.line(image, scaled_coordinates[i], scaled_coordinates[i+1],
                             color=self.__line_color, thickness=2)
            if self.ready:
                if isinstance(self._id, int) and n >= 2:
                    x1, y1, x2, y2 = self.box(scaled_coordinates)
                    cv2.line(image, (x1, y1), (x2, y1), color=self.__box_color, thickness=1)
                    cv2.line(image, (x2, y1), (x2, y2), color=self.__box_color, thickness=1)
                    cv2.line(image, (x2, y2), (x1, y2), color=self.__box_color, thickness=1)
                    cv2.line(image, (x1, y2), (x1, y1), color=self.__box_color, thickness=1)

                    text_pos = (((x2-x1)//2)+x1-7, ((y2-y1)//2)+y1+10)

                    cv2.putText(img=image,
                                text=str(self._id),
                                org=text_pos,
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=1,
                                color=self.__text_color,
                                thickness=2,
                                lineType=cv2.LINE_AA)

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

    def undo(self, *args, **kwargs):
        """removes last coordinate in stored list and resets right click flag"""
        if len(self.coordinates) >= 1:
            self.__coordinates.pop()
            self.__right_clicked = False

    def polygon(self):
        """returns array of coordinates if right click flag is true

        :return: coordinates
        :rtype: numpy.array
        """
        if len(self.__coordinates) > 0:
            if self.__right_clicked:
                return (True, np.array(self.__coordinates))
        return (False, None)

    def text_coordinate(self, coordinates):
        """averages location of all stored coordinates

        :return: average location
        :rtype: list
        """
        cd = coordinates
        text_cd = [0, 0]
        for i in range(len(cd) - 1):
            text_cd[0] += cd[i][0]
            text_cd[1] += cd[i][1]
        text_cd[0] //= len(cd) - 1
        text_cd[0] -= 30
        text_cd[1] //= len(cd) - 1
        text_cd[1] += 12
        return text_cd

    def box(self, coordinates):
        """calculate bounding box"""
        cd = coordinates
        x = [x[0] for x in cd]
        y = [y[1] for y in cd]
        x1, y1 = min(x), min(y)
        x2, y2, = max(x), max(y)
        return x1, y1, x2, y2

    def complete(self):
        coordinates = self.coordinates
        if len(coordinates) >= 2:
            if coordinates[0] != coordinates[-1]:
                self.__coordinates.append(self.__coordinates[0])
            self.__right_clicked = True
            self.__left_clicked = True

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

    @coordinates.setter
    def coordinates(self, coordinates):
        """set coordinates if valid"""
        for coordinate in coordinates:
            x = coordinate[0]
            y = coordinate[1]
            if not self.coordinate_valid(x, y):
                return

        self.__coordinates = coordinates

    @property
    def line_color(self):
        """line color getter"""
        return self.__line_color

    @line_color.setter
    def line_color(self, color):
        """line color setter"""
        self.__line_color = color

    @property
    def box_color(self):
        """bounding box color getter"""
        return self.__box_color

    @box_color.setter
    def box_color(self, color):
        """bonding box color setter"""
        self.__box_color = color

    @property
    def text_color(self):
        """text color getter"""
        return self.__text_color

    @text_color.setter
    def text_color(self, color):
        """text color setter"""
        self.__text_color = color

    @property
    def active(self):
        """active getter"""
        return self.__active

    @active.setter
    def active(self, active):
        """active setter"""
        self.__active = active

    @property
    def ready(self):
        """true if coordinates > 0 and right clicked"""
        return True if len(self.__coordinates) > 0 and self.__right_clicked else False
