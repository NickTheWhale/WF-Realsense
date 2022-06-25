import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from video import VideoCapture
import PIL.Image
import PIL.ImageTk


class App(tk.Tk):
    def __init__(self, window_title, video_source=0):
        super().__init__()
        # delay before recalling update_video()
        self.__update_delay = 10

        # open video source
        self.__video_source = video_source
        self.__video = VideoCapture(self.__video_source)

        # create main gui window
        self.title(window_title)
        self.__main_frame = ttk.Frame(self, padding="1 1 1 1")
        self.__main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.resizable(False, False)
        
        # video
        self.__video_frame = ttk.Frame(self.__main_frame, padding="1 1 1 1", relief="raised")
        self.__video_frame.grid(row=0, column=0)
        self.__canvas = tk.Canvas(
            self.__video_frame, width=self.__video.width, height=self.__video.height)
        self.__canvas.grid(row=0, column=0, sticky="N S E W")

        # settings menu
        self.__settings_frame = ttk.Frame(self.__main_frame, padding="1 1 1 1", relief="raised")
        self.__settings_frame.grid(row=0, column=1, rowspan=2)
        self.__settings_menu = ttk.Label(self.__settings_frame, text="SETTINGS MENU HERE")
        self.__settings_menu.grid(row=0, column=0, sticky="N S E W")
        
        # terminal output
        self.__output_frame = ttk.Frame(self.__main_frame, padding="1 1 1 1", relief="raised")
        self.__output_frame.grid(row=1, column=0)
        self.__output_field = ttk.Label(self.__output_frame, text="OUTPUT FIELD HERE")
        self.__output_field.grid(row=0, column=0, sticky="N S E W")
        
        
        self.update_video()

    def update_video(self):
        if self.__video.opened:
            ret, frame = self.__video.get_frame()
            if ret:
                self.__photo = PIL.ImageTk.PhotoImage(
                    image=PIL.Image.fromarray(frame))
                self.__canvas.create_image(0, 0, image=self.__photo, anchor=tk.NW)
        self.__main_frame.after(self.__update_delay, self.update_video)

    def save_image(self):
        raise NotImplementedError

    def on_closing(self):
        """prompt user to quit when they hit the "x"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
