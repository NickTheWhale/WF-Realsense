import os
import sys
import time
import tkinter as tk
import tkinter.filedialog as tkFileDialog
import webbrowser
from datetime import datetime
from tkinter import messagebox, ttk
import cv2

import numpy as np
import numpy.ma as ma
import PIL.Image
import PIL.ImageTk

from mask import MaskWidget
from video import VideoCapture

# constants
DOC_WEBSITE = "https://dev.intelrealsense.com/docs"
GITHUB_WEBSITE = "https://github.com/NickTheWhale/WF-Realsense"
MASK_OUTPUT_FILE_NAME = "mask.txt"

HEIGHT = 480
WIDTH = 848
METER_TO_FEET = 3.28084


class App(tk.Tk):
    def __init__(self, window_title):
        super().__init__()

        # create main gui window
        self.title(window_title)
        self.__main_frame = ttk.Frame(self, )
        self.__main_frame.grid(column=0, row=0, sticky="N S E W")
        self.resizable(False, False)

        # video variables
        self.__depth_frame = None
        self.__image = None
        self.__blank_image = np.zeros((HEIGHT, WIDTH))
        self.__filter_level = 1
        self.__update_delay = 10
        self.__roi_depth = 0
        self.__roi_min = 0
        self.__roi_max = 0
        self.__roi_accuracy = 0
        self.__roi_deviation = 0
        self.__roi_invalid = 0
        self.__fps = 0

        try:
            self.__camera = VideoCapture(WIDTH, HEIGHT, 30)
        except RuntimeError as e:
            raise RuntimeError(
                f"Could not find camera, check connections: {e}")

        # initialize widgets. must be called in this order since each method sets
        # up instance variables/objects used in other methods
        self.__mask_widget = MaskWidget()
        self.__init_menu()
        self.__init_info()
        self.__init_video()
        self.__init_terminal()
        self.__init_settings()

        # initial call to update depth stream. each subsequent call is made recursively
        self.loop()

    ###################################################################################
    #                                   WIDGET SETUP                                  #
    ###################################################################################

    def __init_menu(self):
        # ROOT MENU
        self.__rootmenu = tk.Menu(self)

        # FILE MENU
        self.__filemenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__filemenu.add_command(label="Save camera settings",
                                    command=lambda: self.__menu_save_settings())
        self.__filemenu.add_command(label="Save mask",
                                    command=lambda: self.__menu_save_mask())
        self.__filemenu.add_command(label="Save image",
                                    command=lambda: self.__menu_save_image())
        self.__filemenu.add_separator()
        self.__filemenu.add_command(label="Restart")
        self.__filemenu.add_command(label="Exit",
                                    command=lambda: self.on_closing(),
                                    accelerator="Ctrl+Q")
        self.__rootmenu.add_cascade(label="File", menu=self.__filemenu)

        # MASK MENU
        self.__maskmenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__maskmenu.add_command(label="Circle")
        self.__maskmenu.add_command(label="Rectangle")
        self.__maskmenu.add_command(label="Free draw")
        self.__maskmenu.add_separator()
        self.__maskmenu.add_command(label="Undo",
                                    command=self.__menu_undo,
                                    accelerator="Ctrl+Z")
        self.__maskmenu.add_separator()
        self.__maskmenu.add_command(label="Clear",
                                    command=self.__menu_reset,
                                    accelerator="Ctrl+R")
        self.__rootmenu.add_cascade(label="Mask", menu=self.__maskmenu)

        # HELP MENU
        self.__helpmenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__helpmenu.add_command(label="Documentation",
                                    command=lambda: self.__menu_documentation(DOC_WEBSITE))
        self.__helpmenu.add_command(label="GitHub",
                                    command=lambda: self.__menu_github(GITHUB_WEBSITE))
        self.__rootmenu.add_cascade(label="Help", menu=self.__helpmenu)

        # add menu to app
        self.config(menu=self.__rootmenu)

        # BINDINGS
        self.bind_all("<Control-q>", self.on_closing)
        self.bind_all("<Control-z>", self.__menu_undo)
        self.bind_all("<Control-r>", self.__menu_reset)

    def __init_info(self):
        # frame
        self.__depth_info_frame = ttk.Frame(self.__main_frame, width=200)
        self.__depth_info_frame.grid(row=0, column=0, rowspan=2)

        self.__depth_info = ttk.Label(self.__depth_info_frame,
                                      text="         CAMERA INFO HERE        ")
        self.__depth_info.grid(row=0, column=0)

    def __init_video(self):
        # frame
        self.__video_frame = ttk.Frame(self.__main_frame)
        self.__video_frame.grid(row=0, column=1)

        # video label
        self.__video_label = tk.Label(self.__video_frame, cursor="tcross")

        self.__video_label.bind("<Motion>", self.__mask_widget.get_coordinates)
        self.__video_label.bind(
            "<Button-1>", self.__mask_widget.get_coordinates)
        self.__video_label.bind(
            "<Button-3>", self.__mask_widget.get_coordinates)

        self.__video_label.grid(row=0, column=0)

    def __init_settings(self):
        # frame
        self.__settings_frame = ttk.Frame(self.__main_frame)
        self.__settings_frame.grid(row=0, column=2, rowspan=2)

        # settings
        self.__settings_menu = ttk.Label(self.__settings_frame,
                                         text="         SETTINGS MENU HERE         ")
        self.__settings_menu.grid(row=0, column=0)

    def __init_terminal(self):
        # frame
        self.__output_frame = ttk.Frame(self.__main_frame)
        self.__output_frame.grid(row=1, column=1)

        # terminal
        self.__output_field = tk.Text(self.__output_frame,
                                      width=105,
                                      height=10,
                                      yscrollcommand=True,
                                      state="disabled")
        self.__output_field.grid(row=0, column=0)

    def update_stats(self):
        # get frame and polygon
        poly_ret, poly = self.__mask_widget.polygon()
        depth_frame = self.__depth_frame
        if depth_frame is not None:
            if poly_ret and poly is not None:
                if len(poly) > 0:
                    depth_image = np.asanyarray(depth_frame.get_data())

                    # compute mask
                    blank_image = np.zeros((HEIGHT, WIDTH))
                    mask = cv2.fillPoly(blank_image, pts=[poly], color=1)
                    mask = mask.astype('bool')
                    mask = np.invert(mask)

                    # unfiltered mask
                    depth_mask = ma.array(depth_image, mask=mask, fill_value=0)

                    total = ma.count(depth_mask)
                    invalid = (depth_mask == 0).sum()
                    i = self.__roi_percent_invalid = invalid / total * 100

                    # filtered mask
                    depth_mask = ma.masked_invalid(depth_mask)
                    depth_mask = ma.masked_equal(depth_mask, 0)

                    d = self.__roi_depth = depth_mask.mean() * self.__camera.depth_scale * METER_TO_FEET
                    h = self.__roi_max = depth_mask.max() * self.__camera.depth_scale * METER_TO_FEET
                    l = self.__roi_min = depth_mask.min() * self.__camera.depth_scale * METER_TO_FEET
                    s = self.__roi_deviation = depth_mask.std() * self.__camera.depth_scale * \
                        METER_TO_FEET

                    output_text = f"Depth: {d:0.3f}   Max: {h:0.3f}   Min: {l:0.3f}   Std.: {s:0.3f}   Valid: {i:.1f}\n"

                    # update terminal output
                    self.__output_field.configure(state="normal")
                    self.__output_field.insert(tk.INSERT, output_text)
                    self.__output_field.see("end")
                    self.__output_field.configure(state="disabled")

    def loop(self):
        # get frame
        ret, depth_frame = self.__camera.get_depth_frame()
        if ret and depth_frame is not None:
            self.__depth_frame = depth_frame
            depth_color_frame = self.__camera.colorizer.colorize(depth_frame)
            color_image = np.asanyarray(depth_color_frame.get_data())

            self.__mask_widget.draw(color_image)

            # update image
            img = PIL.Image.fromarray(color_image)
            imgtk = PIL.ImageTk.PhotoImage(image=img)
            self.__image = imgtk

            self.__video_label.imgtk = imgtk
            self.__video_label.configure(image=imgtk)
            self.__video_label.update()   # update main frame?

            # update stats
            self.update_stats()

        # recall
        self.__main_frame.after(self.__update_delay, self.loop)

    ###################################################################################
    #                                  MENU CALLBACKS                                 #
    ###################################################################################

    def __menu_save_settings(self):
        path = tkFileDialog.asksaveasfilename(initialdir="C:/",
                                              filetypes=(("image files", "*.bmp"),
                                                         ("all files", "*.*")))
        print(path)

    def __menu_save_mask(self):
        with open(MASK_OUTPUT_FILE_NAME, 'w') as file:
            file.write(str(self.__mask_widget.coordinates))

    def __menu_save_image(self):
        if self.__image is not None:
            # determine if application is a script file or frozen exe
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(__file__)
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")
            imgpil = PIL.ImageTk.getimage(self.__image)
            imgpil.save(
                f'{application_path}\\snapshots\\{timestamp}.bmp', "BMP")
            imgpil.close()

    def __menu_documentation(self, url):
        return webbrowser.open(url)

    def __menu_github(self, url):
        return webbrowser.open(url)

    def __menu_reset(self, evt=None):
        self.__mask_widget.reset()

    def __menu_undo(self, evt=None):
        self.__mask_widget.undo()

    def on_closing(self, evt=None):
        """prompt user if they are sure they want to quit when they hit the 'x'"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
