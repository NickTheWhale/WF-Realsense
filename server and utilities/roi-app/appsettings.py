import os
import tkinter as tk
from tkinter import ttk


class AppSettings(tk.Frame):
    def __init__(self, root, row, column, rowspan=1, columnspan=1, sticky="NSEW"):
        super().__init__()
        self.__root = root
        self.__main_frame = root.main_frame
        self.__row = row
        self.__column = column
        self.__columnspan = columnspan
        self.__rowspan = rowspan
        self.__sticky = sticky

        self.__create_widgets()

    def __create_widgets(self):
        # frame
        self.__settings_frame = tk.Frame(self.__main_frame)
        self.__settings_frame.grid(row=self.__row,
                                   column=self.__column,
                                   rowspan=self.__rowspan,
                                   columnspan=self.__columnspan,
                                   sticky=self.__sticky)

        # sliders
        self.__slider_frame = tk.Frame(self.__settings_frame)
        self.__slider_frame.grid(row=0, column=0, sticky="N")

        df = [(5, 90, 5, 30),
              (0, 1, 1, 1),
              (0, 1, 1, 0),
              (0, 1, 1, 1),
              (30, 360, 30, 150),
              (0, 1, 1, 1),
              (0, 5, 1, 0),
              (0, 4, 1, 4),
              (0, 1, 1, 1)
              ]

        for row in range(9):
            start = tk.DoubleVar()
            start.set(df[row][3])  # set starting value

            label = (tk.Label(self.__slider_frame,
                              text=f'setting {row+1}'))
            label.grid(row=row, column=0)

            scale = (tk.Scale(self.__slider_frame,
                              from_=df[row][0],
                              to=df[row][1],
                              resolution=df[row][2],
                              orient=tk.HORIZONTAL,
                              width=15,
                              length=200,
                              variable=start))
            scale.grid(row=row, column=1)
            scale['command'] = lambda scale=scale: self.scale_move(scale)
            
        # buttons
        self.__button_frame = tk.Frame(self.__settings_frame)
        self.__button_frame.grid(row=1, column=0, sticky="E")
        
        self.__reset_button = tk.Button(self.__button_frame,
                                        text="Reset")
        self.__reset_button.grid(row=0, column=0)

    def scale_move(self, scale):
        print(scale, type(scale))
