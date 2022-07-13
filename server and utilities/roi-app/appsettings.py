import tkinter as tk


class AppSettings(tk.Frame):
    def __init__(self, parent, row, column, columnspan=1, rowspan=1):
        super().__init__()
        self.__parent = parent
        self.__row = row
        self.__column = column
        self.__columnspan = columnspan
        self.__rowspan = rowspan
        
        self.__create_widgets()
        
    def __create_widgets(self):
        self.__label = tk.Label(self.__parent, text="   camera settings here    ")
        self.__label.grid(row=self.__row, 
                          column=self.__column, 
                          columnspan=self.__columnspan, 
                          rowspan=self.__rowspan)
        
    def change_text(self, text):
        self.__column = text
        self.__label['text'] = self.__column