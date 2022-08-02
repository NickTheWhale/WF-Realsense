import tkinter as tk
from tkinter import filedialog
import webbrowser
import sv_ttk


DOC_URL = "https://dev.intelrealsense.com/docs/stereo-depth-camera-d400"
GITHUB_URL = "https://github.com/NickTheWhale/WF-Realsense"
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
        self.__filemenu.add_command(label="Save configuration",
                                    command=self.save_configuration)
        self.__filemenu.add_command(label="Load configuration",
                                    command=self.load_configuration)
        self.__filemenu.add_command(label="Save image as",
                                    command=self.save_image)
        self.__filemenu.add_separator()
        self.__filemenu.add_command(label="Restart", 
                                    command=self.restart)
        self.__filemenu.add_command(label="Exit",
                                    command=self.exit,
                                    accelerator="Ctrl+Q")
        self.add_cascade(label="File", menu=self.__filemenu)

        # HELP MENU
        self.__helpmenu = tk.Menu(self, tearoff=0)
        self.__helpmenu.add_command(label="Documentation",
                                    command=lambda url=DOC_URL: self.documentation(url))
        self.__helpmenu.add_command(label="GitHub",
                                    command=lambda url=GITHUB_URL: self.github(url))
        self.add_cascade(label="Help", menu=self.__helpmenu)

    def fake_menu_callback(self, evt=None):
        print('menu callback', evt)

    def save_configuration(self):
        print('save config')
        
    def load_configuration(self):
        print('load config')

    def save_image(self):
        path = filedialog.asksaveasfilename(
            initialdir="C:/",
            filetypes=(("image files", "*.bmp"),
                       ("all files", "*.*")))
        print(path)

    def restart(self):
        print('restart')
        
    def exit(self):
        self._root.on_closing()

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
    
    
    
    def documentation(self, url):
        return webbrowser.open(url)

    def github(self, url):
        return webbrowser.open(url)

    # def mask_reset(self, *args, **kwargs):
    #     self._mask_widget.reset()

    # def mask_undo(self, *args, **kwargs):
    #     self._mask_widget.undo()
        
    def toggle_dark_mode(self, *args, **kwargs):
        sv_ttk.toggle_theme()        
