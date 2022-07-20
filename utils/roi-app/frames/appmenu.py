import tkinter as tk
from tkinter import filedialog
import webbrowser
import sv_ttk


DOC_WEBSITE = "https://dev.intelrealsense.com/docs/stereo-depth-camera-d400"
GITHUB_WEBSITE = "https://github.com/NickTheWhale/WF-Realsense"
MASK_OUTPUT_FILE_NAME = "mask.txt"



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
                                        command=self.toggle_dark_mode)
        self.add_cascade(label="Settings", menu=self.__settingsmenu)

    def fake_menu_callback(self, evt=None):
        print('menu callback', evt)




    def _menu_save_settings(self):
        path = filedialog.asksaveasfilename(
            initialdir="C:/",
            filetypes=(("image files", "*.bmp"),
                       ("all files", "*.*")))
        print(path)

    def _menu_save_mask(self):
        with open(MASK_OUTPUT_FILE_NAME, 'w') as file:
            file.write(str(self._mask_widget.coordinates))
            self._settings_widget.change_text(
                str(self._mask_widget.coordinates))

    # region
    # def _menu_save_image(self):
    #     image = self._image
    #     if image is not None:
    #         # determine if application is a script file or frozen exe
    #         if getattr(sys, 'frozen', False):
    #             application_path = os.path.dirname(sys.executable)
    #         elif __file__:
    #             application_path = os.path.dirname(__file__)
    #         timestamp = datetime.now()
    #         timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")
    #         imgpil = PIL.ImageTk.getimage(image)
    #         imgpil.save(
    #             f'{application_path}\\snapshots\\{timestamp}.bmp', "BMP")
    #         imgpil.close()

    # def _menu_save_image_WIP(self):
    #     """saves picture to 'snapshots' directory. Creates
    #     directory if not found

    #     :param image: image
    #     :type image: image
    #     """
    #     image = self._image
    #     if image is not None:
    #         # GET FILE PATH
    #         path = self.get_program_path()
    #         # GET TIMESTAMP FOR FILE NAME
    #         timestamp = datetime.now()
    #         timestamp = timestamp.strftime("%d-%m-%Y %H-%M-%S")

    #         if self.dir_exists(path=path, name='snapshots'):
    #             # SAVE IMAGE
    #             image.save(f'{path}\\snapshots\\{timestamp}.jpg')
    #             # sleep thread to prevent saving a bunch of pictures
    #         else:
    #             snapshot_path = path + '\\snapshots\\'
    #             os.mkdir(snapshot_path)
    #             # SAVE IMAGE
    #             image.save(f'{path}\\snapshots\\{timestamp}.jpg')
    # endregion
    
    
    
    def _menu_documentation(self, url):
        return webbrowser.open(url)

    def _menu_github(self, url):
        return webbrowser.open(url)

    # def mask_reset(self, *args, **kwargs):
    #     self._mask_widget.reset()

    # def mask_undo(self, *args, **kwargs):
    #     self._mask_widget.undo()
        
    def toggle_dark_mode(self, *args, **kwargs):
        sv_ttk.toggle_theme()        
