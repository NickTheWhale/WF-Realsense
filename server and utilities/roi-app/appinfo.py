import tkinter as tk


class AppInfo(tk.Frame):
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
        self.__info_frame = tk.Frame(self.__main_frame, width=200)
        self.__info_frame.grid(row=self.__row,
                               column=self.__column,
                               rowspan=self.__rowspan,
                               columnspan=self.__columnspan,
                               sticky=self.__sticky)
        # self.__info_label = tk.Label(self.__info_frame,
        #                              text="            [CAMERA INFO HERE]            ")
        # self.__info_label.grid(row=0, column=0)

    def update(self, data):
        self.__data = data
        data_labels = []

        row = 0
        for key, value in data.items():
            text = f'{key}: {value:.3f}'
            data_labels.append(tk.Label(self.__info_frame,
                                        text=text))
            data_labels[row].grid(row=row, column=0)
            row += 1
