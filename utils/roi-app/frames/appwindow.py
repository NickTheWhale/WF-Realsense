import copy
import os
import sys
import time
import tkinter as tk
import tkinter.filedialog as tkFileDialog
import webbrowser
from tkinter import messagebox

import numpy as np
import pyrealsense2 as rs
import sv_ttk
from camera.config import Config
from camera.mask import MaskWidget
from camera.newcamera import Camera

from frames.appmenu import AppMenu
from frames.appsettings import AppSettings
from frames.appterminal import AppTerminal
from frames.appvideo import AppVideo

# constants
HEIGHT = 480
WIDTH = 848
METER_TO_FEET = 3.28084


class AppWindow(tk.Tk):
    def __init__(self, window_title, path):
        """create main window and sub frames"""
        self._path = path
        super().__init__()
        # theme
        sv_ttk.set_theme('light')
        self.resizable(False, False)
        # create main gui window
        self._title = window_title
        self.__title = window_title
        self.title(self._title)

        self._drag_id = ''

        # camera/video variables
        number_of_roi = 8
        self._roi_depth = 0
        self._roi_min = 0
        self._roi_max = 0
        self._roi_deviation = 0
        self._roi_invalid = 0
        self._frame_number = 0
        self._loop_count = 0
        self._new_frame_count = 0
        self._color_image = None

        # resize variables
        self._padx = 1
        self._pady = 1
        self._border = 1

        # find configuration files
        config_filename = ''
        for root, dirs, files in os.walk(self._path):
            for file in files:
                if file.endswith('.ini') and file != 'defaultconfiguration.ini':
                    if root == self._path:
                        config_filename = file
        if config_filename == '':
            for root, dirs, files in os.walk(self._path):
                for file in files:
                    if file.endswith('.ini'):
                        if file == 'defaultconfiguration.ini':
                            if root == self._path:
                                config_filename = file

        if config_filename == '':
            raise FileNotFoundError(
                "Could not find a valid configuration file. Make "
                "sure there is at least one valid *.ini configuration "
                "file located in the same directory as this program."
            )

        # connect camera
        self._configurator = Config(config_filename)
        self._framerate = int(self._configurator.get_value('camera', 'framerate', '30'))
        try:
            self._camera = Camera(width=WIDTH,
                                  height=HEIGHT,
                                  framerate=self._framerate,
                                  config=self._configurator.data)
            self._camera.options.get_camera_options()
            self._camera.scale = 2
            self._camera.start()
        except RuntimeError as e:
            if hasattr(self, '_camera'):
                if self._camera.connected:
                    self._camera.stop()
            self.destroy()
            raise RuntimeError("Could not connect to camera. Make sure camera "
                               "is plugged in properly and not already in use.")
            os._exit(1)

        # set some camera settings
        self._camera.filter_level = int(self._configurator.get_value(
            'camera', 'spatial_filter_level', '0'))
        self._camera.metric = bool(float(self._configurator.get_value(
            'camera', 'metric', '0.0')))

        self._mask_widgets = []
        for id in range(number_of_roi):
            self._mask_widgets.append(MaskWidget(self, id=id+1))

        # get region of interests from configuration
        polygons = []
        for key in self._configurator.data['roi']:
            polygons.append(list(eval(self._configurator.get_value('roi', key, fallback='[]'))))
        for _ in range(number_of_roi - len(polygons)):
            polygons.append([])
        for i in range(number_of_roi):
            self._mask_widgets[i].coordinates = polygons[i]
            self._mask_widgets[i].complete()

        # build frames
        self._menu = AppMenu(self, tearoff=0)
        self.configure(menu=self._menu)

        self._video_widget = AppVideo(self, border=self._border)
        self._video_widget.grid(row=0,
                                column=1,
                                padx=self._padx,
                                pady=self._pady,
                                sticky="N")

        self._terminal_widget = AppTerminal(self, border=self._border)
        self._terminal_widget.grid(row=1,
                                   column=1,
                                   padx=self._padx,
                                   pady=self._pady)

        self._settings_widget = AppSettings(self, border=self._border)
        self._settings_widget.grid(row=0,
                                   column=3,
                                   rowspan=2,
                                   padx=self._padx,
                                   pady=self._pady,
                                   sticky="NS")

        # bindings
        self.bind_all("<Control-q>", self.on_closing)
        self.bind_all("<Control-z>", self._video_widget.mask_undo)
        self.bind_all("<Control-r>", self._video_widget.mask_reset)
        self.bind_all("<Configure>", self.dragging)

        self._start_time = time.time()
        self.after(20, self.loop)

    @property
    def path(self):
        """root program path getter"""
        return self._path

    @property
    def masks(self):
        """list of mask widgets getter"""
        return self._mask_widgets

    @property
    def root(self):
        """self (appwindow) getter"""
        return self

    @property
    def camera(self):
        """camera getter"""
        return self._camera

    @property
    def video(self):
        """video frame getter"""
        return self._video_widget

    @property
    def terminal(self):
        """terminal frame getter"""
        return self._terminal_widget

    @property
    def settings(self):
        """setting frame getter"""
        return self._settings_widget

    @property
    def color_image(self):
        """color image getter"""
        return self._color_image

    @property
    def configurator(self):
        """config class getter"""
        return self._configurator

    @configurator.setter
    def configurator(self, configurator):
        """config class setter"""
        self._configurator = configurator

    @property
    def framerate(self):
        """framerate getter"""
        return self._framerate
    
    @property
    def title_(self):
        """window title getter"""
        return self._title
    
    @title_.setter
    def title_(self, title):
        """window title setter"""
        self.title(' '.join((self.__title, title)))
        self._title = title

    def update_roi_stats(self, depth_frame):
        """computes roi data 

        :param depth_frame: camera depth frame
        :type depth_frame: pyrealsense2.depth_frame
        """
        # get frame and polygon
        if self._video_widget.roi_select_all:
            polygons = []
            for i in range(len(self._mask_widgets)):
                ret, poly = self._mask_widgets[i].polygon()
                if ret:
                    polygons.append(poly)

            if isinstance(depth_frame, rs.depth_frame):
                d, i, s = self._camera.ROI_datan(polygons)

                self._roi_depth = d
                self._roi_deviation = s
                self._roi_invalid = i
        else:
            polygons = []
            ret, poly = self._mask_widgets[self._video_widget.roi_select].polygon()
            if ret:
                polygons.append(poly)

            if isinstance(depth_frame, rs.depth_frame):
                d, i, s = self._camera.ROI_datan(polygons)

                self._roi_depth = d
                self._roi_deviation = s
                self._roi_invalid = i

    @property
    def formatted_stats(self):
        """returns depth, std., and invalid % in formatted string"""
        d = self._roi_depth
        s = self._roi_deviation
        i = self._roi_invalid
        return (f'[Depth:\t{d:.3f}]\t'
                f'[Std.:\t{s:.3f}]\t'
                f'[Invalid:\t{i:.1f}]')

    def loop(self):
        """updates video and draws masks"""
        # update video and roi stats()
        if not self._video_widget.paused:
            depth_frame = self._camera.depth_frame
            frame_number = self._camera.frame_number
            if isinstance(depth_frame, rs.depth_frame) and frame_number > self._frame_number:
                self._new_frame_count += 1
                self._frame_number = frame_number

                depth_color_frame = self._camera.colorizer.colorize(depth_frame)
                color_image = np.asanyarray(depth_color_frame.get_data())

                # self._mask_widget.draw(color_image)
                if self._video_widget.roi_select_all:
                    for i in range(len(self._mask_widgets)):
                        self._mask_widgets[i].draw(color_image)
                else:
                    self._mask_widgets[self._video_widget.roi_select].draw(color_image)

                self._color_image = color_image
                # self._video_widget.set_image()

        if self._new_frame_count > self._framerate:
            if self._mask_widgets[self._video_widget.roi_select].ready:
                if not self._terminal_widget.camera_supress:
                    self.update_roi_stats(depth_frame)
                    self._terminal_widget.write(self.formatted_stats)
            self._new_frame_count = 0
        self.after(10, self.loop)

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

    def resize(self):
        """resizes frames based on camera scale"""
        if self._camera.scale > 1:
            self._padx = 1
            self._pady = 1
            self._border = 1
        else:
            self._padx = 5
            self._pady = 5
            self._border = 5

        columns, rows = self.grid_size()
        for column in range(columns):
            self.columnconfigure(column, pad=self._padx)
        for row in range(rows):
            self.rowconfigure(row, pad=self._pady)

        self._video_widget.configure(border=self._border)
        self._terminal_widget.configure(border=self._border)
        self._settings_widget.configure(border=self._border)

    def dragging(self, event):
        """called when main window is dragged"""
        if event.widget is self:
            if self._drag_id != '':
                self.after_cancel(self._drag_id)
            if not self._video_widget.paused:
                self._video_widget.pause()
            self._drag_id = self.after(200, self.stop_drag)

    def stop_drag(self):
        """called when main window stops being dragged"""
        if self._video_widget.paused:
            self._video_widget.unpause()
        self._drag_id = ''

    def on_closing(self, *args, **kwargs):
        """prompt user if they are sure they want to quit when they hit the 'x'"""
        try:
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                if self._camera.connected:
                    self._camera.stop()
                self.destroy()
                os._exit(0)
        except:
            os._exit(0)
