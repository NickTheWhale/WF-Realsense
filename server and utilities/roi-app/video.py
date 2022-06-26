import cv2


class VideoCapture:
    def __init__(self, video_source=0):
        self.__video = cv2.VideoCapture(video_source)
        if not self.__video.isOpened():
            raise ValueError(f"Unabled to open video source {video_source}")

        self.__width = self.__video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.__height = self.__video.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.__video.isOpened():
            ret, frame = self.__video.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    def __del__(self):
        if self.__video.isOpened():
            self.__video.release()

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def opened(self):
        return self.__video.isOpened()

    @property
    def frame(self):
        ret, frame = self.__video.read()
        if ret:
            return frame
        else:
            None
