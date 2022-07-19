import tkinter as tk


class AppMenu(tk.Menu):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]

        super().__init__(*args, **kwargs)

        self.__create_widgets()

    def __create_widgets(self):
        # FILE MENU
        self.__filemenu = tk.Menu(self, tearoff=0)
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
        self.add_cascade(label="File", menu=self.__filemenu)

        # MASK MENU
        self.__maskmenu = tk.Menu(self, tearoff=0)
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
        self.add_cascade(label="Mask", menu=self.__maskmenu)

        # HELP MENU
        self.__helpmenu = tk.Menu(self, tearoff=0)
        self.__helpmenu.add_command(label="Documentation",
                                    command=self.fake_menu_callback)
        self.__helpmenu.add_command(label="GitHub",
                                    command=self.fake_menu_callback)
        self.add_cascade(label="Help", menu=self.__helpmenu)

        # SETTINGS MENU
        self.__settingsmenu = tk.Menu(self, tearoff=0)
        self.__settingsmenu.add_checkbutton(label="dark mode",
                                        command=self._root.toggle_dark_mode)
        self.add_cascade(label="Settings", menu=self.__settingsmenu)

    def fake_menu_callback(self, evt=None):
        print('menu callback', evt)
