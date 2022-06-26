import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

import PIL.Image
import PIL.ImageTk

from video import VideoCapture

ABOUT_WEBSITE = "https://dev.intelrealsense.com/docs"


class App(tk.Tk):
    def __init__(self, window_title, video_source=0):
        super().__init__()
        # delay before recalling update_video()
        self.__update_delay = 50

        # open video source
        self.__video_source = video_source
        self.__video = VideoCapture(self.__video_source)

        # create main gui window
        self.title(window_title)
        self.__main_frame = ttk.Frame(self, )
        self.__main_frame.grid(column=0, row=0, sticky="N S E W")
        self.resizable(False, False)

        # initialize widgets
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
        self.__filemenu.add_command(label="Export camera settings")
        self.__filemenu.add_command(label="Export mask")
        self.__filemenu.add_separator()
        self.__filemenu.add_command(label="Restart")
        self.__filemenu.add_command(label="Exit", command=lambda: self.on_closing())
        self.__rootmenu.add_cascade(label="File", menu=self.__filemenu)

        # MASK MENU
        self.__maskmenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__maskmenu.add_command(label="Circle")
        self.__maskmenu.add_command(label="Rectangle")
        self.__maskmenu.add_command(label="Free draw")
        self.__maskmenu.add_separator()
        self.__maskmenu.add_command(label="Undo")
        self.__maskmenu.add_separator()
        self.__maskmenu.add_command(label="Clear")
        self.__rootmenu.add_cascade(label="Mask", menu=self.__maskmenu)

        # HELP MENU
        self.__helpmenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__helpmenu.add_command(
            label="About", command=lambda: self.menu_about(ABOUT_WEBSITE))
        self.__rootmenu.add_cascade(label="Help", menu=self.__helpmenu)

        # add menu to app
        self.config(menu=self.__rootmenu)

    def __init_video(self):
        # frame
        self.__video_frame = ttk.Frame(self.__main_frame)
        self.__video_frame.grid(row=1, column=0)

        # video image
        self.__canvas = tk.Canvas(
            self.__video_frame, width=self.__video.width, height=self.__video.height)
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

    def menu_about(self, url):
        return webbrowser.open(url)

    def update_video(self):
        if self.__video.opened:
            ret, frame = self.__video.get_frame()
            if ret:
                self.__photo = PIL.ImageTk.PhotoImage(
                    image=PIL.Image.fromarray(frame))
                self.__canvas.create_image(
                    0, 0, image=self.__photo, anchor=tk.NW)
        self.__main_frame.after(self.__update_delay, self.update_video)

    def save_image(self):
        raise NotImplementedError

    def on_closing(self):
        """prompt user if they are sure they want to quit when they hit the 'x'"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
