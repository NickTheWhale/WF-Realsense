import tkinter as tk


class AppMenu(tk.Menu):
    def __init__(self, root, tearoff=0):
        super().__init__()
        
        self.__root = root
        self.__tearoff = tearoff

        self.__create_widgets()

    def __create_widgets(self):
        # ROOT MENU
        self.__rootmenu = tk.Menu(self.__root)

        # FILE MENU
        self.__filemenu = tk.Menu(self.__rootmenu, tearoff=self.__tearoff)
        self.__filemenu.add_command(label="Save camera settings",
                                    command=self.fake_menu_callback)
        self.__filemenu.add_command(label="Save mask",
                                    command=self.fake_menu_callback)
        self.__filemenu.add_command(label="Save image",
                                    command=self.fake_menu_callback)
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
                                    command=self.fake_menu_callback)
        self.__helpmenu.add_command(label="GitHub",
                                    command=self.fake_menu_callback)
        self.__rootmenu.add_cascade(label="Help", menu=self.__helpmenu)

        # add menu to app
        self.__root.config(menu=self.__rootmenu)

        # BINDINGS
        self.bind_all("<Control-q>", self.fake_menu_callback)
        self.bind_all("<Control-z>", self.fake_menu_callback)
        self.bind_all("<Control-r>", self.fake_menu_callback)

    def fake_menu_callback(self, evt=None):
        print('menu callback', evt)


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