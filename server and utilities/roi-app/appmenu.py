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
        
        
class AppMenu(tk.Menu):
    def __init__(self, parent, tearoff=0):
        super().__init__()
        self.__parent = parent
        self.__tearoff = tearoff
                
        self.__create_widgets()
        
    def __create_widgets(self):        
        # ROOT MENU
        self.__rootmenu = tk.Menu(self.__parent)

        # FILE MENU
        self.__filemenu = tk.Menu(self.__rootmenu, tearoff=self.__tearoff)
        self.__filemenu.add_command(label="Save camera settings",
                                    command= self.fake_menu_callback)
        self.__filemenu.add_command(label="Save mask",
                                    command= self.fake_menu_callback)
        self.__filemenu.add_command(label="Save image",
                                    command= self.fake_menu_callback)
        self.__filemenu.add_separator()
        self.__filemenu.add_command(label="Restart")
        self.__filemenu.add_command(label="Exit",
                                    command=lambda: self.fake_menu_callback,
                                    accelerator="Ctrl+Q")
        self.__rootmenu.add_cascade(label="File", menu=self.__filemenu)

        # MASK MENU
        self.__maskmenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__maskmenu.add_command(label="Circle")
        self.__maskmenu.add_command(label="Rectangle")
        self.__maskmenu.add_command(label="Free draw")
        self.__maskmenu.add_separator()
        self.__maskmenu.add_command(label="Undo",
                                    command=self.fake_menu_callback,
                                    accelerator="Ctrl+Z")
        self.__maskmenu.add_separator()
        self.__maskmenu.add_command(label="Clear",
                                    command=self.fake_menu_callback,
                                    accelerator="Ctrl+R")
        self.__rootmenu.add_cascade(label="Mask", menu=self.__maskmenu)

        # HELP MENU
        self.__helpmenu = tk.Menu(self.__rootmenu, tearoff=0)
        self.__helpmenu.add_command(label="Documentation",
                                    command= self.fake_menu_callback)
        self.__helpmenu.add_command(label="GitHub",
                                    command= self.fake_menu_callback)
        self.__rootmenu.add_cascade(label="Help", menu=self.__helpmenu)

        # add menu to app
        self.__parent.config(menu=self.__rootmenu)

        # BINDINGS
        self.bind_all("<Control-q>", self.fake_menu_callback)
        self.bind_all("<Control-z>", self.fake_menu_callback)
        self.bind_all("<Control-r>", self.fake_menu_callback)
        
    def fake_menu_callback(self, evt=None):
        print('menu callback', evt)