import os
import sys
import tkinter as tk
import tkinter.filedialog as tkFileDialog
import webbrowser
from datetime import datetime
from tkinter import messagebox, ttk

import time
import numpy as np
import PIL.Image
import PIL.ImageTk
from ttkthemes import ThemedStyle

from appinfo import AppInfo
from appmenu import AppMenu
from appsettings import AppSettings
from appterminal import AppTerminal
from appvideo import AppVideo
from mask import MaskWidget
from newcamera import Camera

# constants
DOC_WEBSITE = "https://dev.intelrealsense.com/docs/stereo-depth-camera-d400"
GITHUB_WEBSITE = "https://github.com/NickTheWhale/WF-Realsense"
MASK_OUTPUT_FILE_NAME = "mask.txt"

HEIGHT = 480
WIDTH = 848
FRAMERATE = 30
METER_TO_FEET = 3.28084


class AppWindow(tk.Tk):
    def __init__(self, window_title):
        super().__init__()

        # create main gui window
        self.title(window_title)
        self.__main_frame = ttk.Frame(self)
        self.__main_frame.grid(column=0, row=0, sticky="N S E W")
        self.resizable(False, False)

        # set theme
        # self.__style = ThemedStyle(self)
        # self.__style.theme_use('arc')

        # camera/video variables
        self.__depth_frame = None
        self.__image = None
        self.__filter_level = 0
        self.__roi_depth = 0
        self.__roi_min = 0
        self.__roi_max = 0
        self.__roi_deviation = 0
        self.__roi_invalid = 0
        self.__frame_number = 0
        self.__loop_count = 0

        try:
            # self.__camera = VideoCapture(WIDTH, HEIGHT, 30)
            self.__camera = Camera(width=WIDTH,
                                   height=HEIGHT,
                                   framerate=FRAMERATE,
                                   metric=False)
            self.__camera.start_callback()
        except RuntimeError as e:
            raise RuntimeError(
                f"Could not find camera, check connections: {e}")

        self.__mask_widget = MaskWidget()

        self.__menu = AppMenu(self, tearoff=0)
        self.__info_frame = AppInfo(self, row=0, column=0, rowspan=2, sticky="N")
        self.__video_frame = AppVideo(self, row=0, column=1)
        self.__terminal_frame = AppTerminal(self, row=1, column=1)
        self.__settings_frame = AppSettings(self, row=0, column=3, rowspan=2, sticky="N")

        # bindings
        self.bind_all("<Control-q>", self.on_closing)
        self.bind_all("<Control-z>", self.__mask_undo)
        self.bind_all("<Control-r>", self.__mask_reset)
        self.__start_time = time.time()

    @property
    def logger(self):
        return self.__logger

    @property
    def main_frame(self):
        return self.__main_frame

    @property
    def mask_widget(self):
        return self.__mask_widget

    @property
    def root(self):
        return self

    def update_roi_stats(self):
        # get frame and polygon
        poly_ret, poly = self.__mask_widget.polygon()
        depth_frame = self.__depth_frame
        if depth_frame is not None:
            if poly_ret and poly is not None:
                if len(poly) > 0:
                    d, i, s, l, h = self.__camera.ROI_stats(poly, self.__filter_level)

                    self.__roi_depth = d
                    self.__roi_max = h
                    self.__roi_min = l
                    self.__roi_deviation = s
                    self.__roi_invalid = i

    @property
    def formatted_stats(self):
        d = self.__roi_depth
        h = self.__roi_max
        l = self.__roi_min
        s = self.__roi_deviation
        i = self.__roi_invalid
        return (f'[Depth:\t{d:.3f}]\t[Max:\t{h:.3f}]\t'
                f'[Min:\t{l:.3f}]\t[Std.:\t{s:.3f}]\t'
                f'[Invalid:\t{i:.1f}]')

    def loop(self):
        # update video and roi stats()
        self.__loop_count += 1
        depth_frame = self.__camera.depth_frame
        frame_number = self.__camera.frame_number
        if depth_frame is not None and frame_number > self.__frame_number:
            self.__frame_number = frame_number
            self.__depth_frame = depth_frame
            depth_color_frame = self.__camera.colorizer.colorize(depth_frame)
            color_image = np.asanyarray(depth_color_frame.get_data())

            self.__mask_widget.draw(color_image)

            # update video
            temp_img = self.__video_frame.set_image(color_image)
            if temp_img is not None:
                self.__image = temp_img

            data = {
                'depth': self.__roi_depth,
                'max': self.__roi_max,
                'min': self.__roi_min,
                'deviation': self.__roi_deviation,
                'invalid': self.__roi_invalid
            }
            self.update_roi_stats()

        if self.__loop_count > 20:
            self.__terminal_frame.write(self.formatted_stats)
            self.__loop_count = 0

    def get_program_path(self) -> str:
        """gets full path name of program. Works if 
        program is frozen

        :return: path
        :rtype: string
        """
        if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
        elif __file__:
            path = os.path.dirname(__file__)
        return path

    def dir_exists(self, path: str, name: str) -> bool:
        """check if directory 'name' exists within 'path'

        :param path: full parent path name
        :type path: string
        :param name: name of directory to check
        :type name: string
        :return: if 'name' exists
        :rtype: bool
        """
        dir = os.listdir(path=path)
        return name in dir

    ###################################################################################
    #                                  MENU CALLBACKS                                 #
    ###################################################################################

    def __menu_save_settings(self):
        path = tkFileDialog.asksaveasfilename(
            initialdir="C:/",
            filetypes=(("image files", "*.bmp"),
                       ("all files", "*.*")))
        print(path)

    def __menu_save_mask(self):
        with open(MASK_OUTPUT_FILE_NAME, 'w') as file:
            file.write(str(self.__mask_widget.coordinates))
            self.__settings_frame.change_text(
                str(self.__mask_widget.coordinates))

    def __menu_save_image(self):
        image = self.__image
        if image is not None:
            # determine if application is a script file or frozen exe
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(__file__)
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")
            imgpil = PIL.ImageTk.getimage(image)
            imgpil.save(
                f'{application_path}\\snapshots\\{timestamp}.bmp', "BMP")
            imgpil.close()

    def __menu_save_image_WIP(self):
        """saves picture to 'snapshots' directory. Creates
        directory if not found

        :param image: image
        :type image: image
        """
        image = self.__image
        if image is not None:
            # GET FILE PATH
            path = self.get_program_path()
            # GET TIMESTAMP FOR FILE NAME
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")

            if self.dir_exists(path=path, name='snapshots'):
                # SAVE IMAGE
                image.save(f'{path}\\snapshots\\{timestamp}.jpg')
                # sleep thread to prevent saving a bunch of pictures
            else:
                snapshot_path = path + '\\snapshots\\'
                os.mkdir(snapshot_path)
                # SAVE IMAGE
                image.save(f'{path}\\snapshots\\{timestamp}.jpg')

    def __menu_documentation(self, url):
        return webbrowser.open(url)

    def __menu_github(self, url):
        return webbrowser.open(url)

    def __mask_reset(self, evt=None):
        self.__mask_widget.reset()

    def __mask_undo(self, evt=None):
        self.__mask_widget.undo()

    def on_closing(self, evt=None):
        """prompt user if they are sure they want to quit when they hit the 'x'"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            os._exit(0)

    def fake_callback(self, *args, **kwargs):
        print("fake callback", args, kwargs)
