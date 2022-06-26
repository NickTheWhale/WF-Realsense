import os
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from datetime import datetime

import PIL.Image
import PIL.ImageTk

from video import VideoCapture
from mask import MaskWidget

DOC_WEBSITE = "https://dev.intelrealsense.com/docs"
GITHUB_WEBSITE = "https://github.com/NickTheWhale/WF-Realsense"
MASK_OUTPUT_FILE_NAME = "mask.txt"


class App(tk.Tk):
    def __init__(self, window_title, video_source=0):
        super().__init__()
        # delay before recalling update_video()
        self.__update_delay = 10

        # open video source
        self.__video_source = video_source
        self.__video = VideoCapture(self.__video_source)
        self.__frame = None
        self.__photo = None

        # create main gui window
        self.title(window_title)
        self.__main_frame = ttk.Frame(self, )
        self.__main_frame.grid(column=0, row=0, sticky="N S E W")
        self.resizable(False, False)

        # initialize widgets
        self.__mask_widget = MaskWidget()
        self.__init_menu()
        self.__init_video()
        self.__init_settings()
        self.__init_terminal()

        self.update_video()

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

    def __init_video(self):
        # frame
        self.__video_frame = ttk.Frame(self.__main_frame)
        self.__video_frame.grid(row=1, column=0)

        # video image
        self.__canvas = tk.Canvas(
            self.__video_frame, width=self.__video.width, height=self.__video.height, cursor="tcross")
        self.__canvas.bind("<Motion>", self.__mask_widget.get_coordinates)
        self.__canvas.bind("<Button-1>", self.__mask_widget.get_coordinates)
        self.__canvas.bind("<Button-3>", self.__mask_widget.get_coordinates)
        self.__canvas.grid(row=0, column=0)

    def __init_settings(self):
        # frame
        self.__settings_frame = ttk.Frame(self.__main_frame)
        self.__settings_frame.grid(row=1, column=1, rowspan=2)

        # settings
        self.__settings_menu = ttk.Label(
            self.__settings_frame, text="SETTINGS MENU HERE")
        self.__settings_menu.grid(row=0, column=0)

    def __init_terminal(self):
        # frame
        self.__output_frame = ttk.Frame(self.__main_frame)
        self.__output_frame.grid(row=2, column=0)

        # terminal
        self.__output_field = tk.Text(
            self.__output_frame, width=78, height=10, yscrollcommand=True)
        self.__output_field.grid(row=0, column=0)

    def update_video(self):
        if self.__video.opened:
            ret, self.__frame = self.__video.get_frame()
            if ret:
                self.__mask_widget.draw(self.__frame)
                self.__photo = PIL.ImageTk.PhotoImage(
                    image=PIL.Image.fromarray(self.__frame))
                self.__canvas.create_image(
                    0, 0, image=self.__photo, anchor=tk.NW)
        self.__main_frame.after(self.__update_delay, self.update_video)

    ###################################################################################
    #                                  MENU CALLBACKS                                 #
    ###################################################################################

    def __menu_save_settings(self):
        raise NotImplementedError

    def __menu_save_mask(self):
        with open(MASK_OUTPUT_FILE_NAME, 'w') as file:
            file.write(str(self.__mask_widget.coordinates))

    def __menu_save_image(self):
        if self.__photo is not None:
            # determine if application is a script file or frozen exe
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(__file__)
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")
            imgpil = PIL.ImageTk.getimage(self.__photo)
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
