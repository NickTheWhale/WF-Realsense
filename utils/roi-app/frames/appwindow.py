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

from frames.appinfo import AppInfo
from frames.appmenu import AppMenu
from frames.appsettings import AppSettings
from frames.appterminal import AppTerminal
from frames.appvideo import AppVideo
from widgets.scrollframe import VerticalScrollFrame

# constants
DOC_WEBSITE = "https://dev.intelrealsense.com/docs/stereo-depth-camera-d400"
GITHUB_WEBSITE = "https://github.com/NickTheWhale/WF-Realsense"
MASK_OUTPUT_FILE_NAME = "mask.txt"

HEIGHT = 480
WIDTH = 848
METER_TO_FEET = 3.28084

LABEL_FRAME_BORDER = 3

RESIZABLE = False


class AppWindow(tk.Tk):
    def __init__(self, window_title):
        super().__init__()
        # theme
        sv_ttk.set_theme('light')

        # create main gui window
        self.title(window_title)

        if RESIZABLE:
            self.resizable(True, True)
        else:
            self.resizable(False, False)

        self._drag_id = ''

        # camera/video variables
        self._filter_level = 0
        self._roi_depth = 0
        self._roi_min = 0
        self._roi_max = 0
        self._roi_deviation = 0
        self._roi_invalid = 0
        self._frame_number = 0
        self._loop_count = 0
        self._new_frame_count = 0
        self._color_image = None

        self._configurator = Config('configuration.ini')
        self._framerate = int(self._configurator.get_value('camera', 'framerate', 30))
        self._metric = bool(self._configurator.get_value('camera', 'metric', False))
        try:
            self._camera = Camera(width=WIDTH,
                                  height=HEIGHT,
                                  framerate=self._framerate,
                                  metric=self._metric,
                                  config=self._configurator.data)
            self._camera.options.get_camera_options()
            self._camera.scale = 2
            self._camera.start()
        except RuntimeError as e:
            raise RuntimeError(
                f"Could not find camera, check connections: {e}")

        self._mask_widget = MaskWidget(self)

        self._menu = AppMenu(self, tearoff=0)
        self.configure(menu=self._menu)

        self._video_widget = AppVideo(self, border=LABEL_FRAME_BORDER)
        self._video_widget.grid(row=0,
                                column=1,
                                padx=5,
                                pady=5,
                                sticky="N")

        self._terminal_widget = AppTerminal(self, border=LABEL_FRAME_BORDER)
        self._terminal_widget.grid(row=1,
                                   column=1,
                                   padx=5,
                                   pady=5)

        self._settings_widget = AppSettings(self, border=LABEL_FRAME_BORDER)
        self._settings_widget.grid(row=0,
                                   column=3,
                                   rowspan=2,
                                   padx=5,
                                   pady=5,
                                   sticky="NS")

        # bindings
        self.bind_all("<Control-q>", self.on_closing)
        self.bind_all("<Control-z>", self.mask_undo)
        self.bind_all("<Control-r>", self.mask_reset)
        self.bind_all("<Configure>", self.dragging)

        self._start_time = time.time()
        self.after(20, self.loop)
    

    @property
    def mask(self):
        return self._mask_widget

    @property
    def root(self):
        return self

    @property
    def camera(self):
        return self._camera

    @property
    def video(self):
        return self._video_widget

    @property
    def terminal(self):
        return self._terminal_widget

    @property
    def settings(self):
        return self._settings_widget

    @property
    def color_image(self):
        return self._color_image

    @property
    def configurator(self):
        return self._configurator

    @property
    def framerate(self):
        return self._framerate

    @property
    def filter_level(self):
        return self._filter_level

    @filter_level.setter
    def filter_level(self, level):
        if level > 5:
            level = 5
        elif level < 0:
            level = 0
        self._filter_level = level

    def update_roi_stats(self, depth_frame):
        # get frame and polygon
        poly_ret, poly = self._mask_widget.polygon()
        if isinstance(depth_frame, rs.depth_frame):
            if poly_ret and poly is not None:
                if len(poly) > 0:
                    d, i, s, l, h = self._camera.ROI_stats(poly, self._filter_level)

                    self._roi_depth = d
                    self._roi_max = h
                    self._roi_min = l
                    self._roi_deviation = s
                    self._roi_invalid = i

    @property
    def formatted_stats(self):
        d = self._roi_depth
        h = self._roi_max
        l = self._roi_min
        s = self._roi_deviation
        i = self._roi_invalid
        return (f'[Depth:\t{d:.3f}]\t[Max:\t{h:.3f}]\t'
                f'[Min:\t{l:.3f}]\t[Std.:\t{s:.3f}]\t'
                f'[Invalid:\t{i:.1f}]')

    def loop(self):
        # update video and roi stats()
        if not self._video_widget.paused:
            depth_frame = self._camera.depth_frame
            frame_number = self._camera.frame_number
            if isinstance(depth_frame, rs.depth_frame) and frame_number > self._frame_number:
                self._new_frame_count += 1
                self._frame_number = frame_number

                depth_color_frame = self._camera.colorizer.colorize(depth_frame)
                color_image = np.asanyarray(depth_color_frame.get_data())

                self._mask_widget.draw(color_image)
                self._color_image = color_image
                # self._video_widget.set_image()

        if self._new_frame_count > self._framerate:
            if self._mask_widget.ready:
                if not self._terminal_widget.camera_supress:
                    self.update_roi_stats(depth_frame)
                    self._terminal_widget.write(self.formatted_stats)
            self._new_frame_count = 0
        self.after(10, self.loop)

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

    def mask_reset(self, *args, **kwargs):
        self._mask_widget.reset()

    def mask_undo(self, *args, **kwargs):
        self._mask_widget.undo()

    def on_closing(self, *args, **kwargs):
        """prompt user if they are sure they want to quit when they hit the 'x'"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self._camera.connected:
                self._camera.stop()
            self.destroy()
            os._exit(0)

    def fake_callback(self, *args, **kwargs):
        print("fake callback", args, kwargs)

    def dragging(self, event):
        if RESIZABLE:
            if self._drag_id != '':
                self.after_cancel(self._drag_id)
            elif not self._video_widget.paused:
                self._video_widget.pause()
            self._drag_id = self.after(200, self.stop_drag)
        else:
            if event.widget is self:
                if self._drag_id != '':
                    self.after_cancel(self._drag_id)
                if not self._video_widget.paused:
                    self._video_widget.pause()
                self._drag_id = self.after(200, self.stop_drag)

    def stop_drag(self):
        if self._video_widget.paused:
            self._video_widget.unpause()
        self._drag_id = ''


# 'char', 'delta', 'height', 'keycode', 'keysym', 'keysym_num', 'num', 'send_event', 'serial', 'state', 'time', 'type', 'widget', 'width', 'x', 'x_root', 'y', 'y_root']
