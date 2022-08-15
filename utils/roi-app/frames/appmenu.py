import os
import tkinter as tk
from tkinter import filedialog
import webbrowser
import PIL
import numpy as np
from pathlib import Path
import pyrealsense2 as rs


DOC_URL = "https://dev.intelrealsense.com/docs/stereo-depth-camera-d400"
GITHUB_URL = "https://github.com/NickTheWhale/WF-Realsense"


class AppMenu(tk.Menu):
    def __init__(self, *args, **kwargs):
        """create menubar"""
        self._root = args[0]

        super().__init__(*args, **kwargs)

        self._create_widgets()

    def _create_widgets(self):
        # FILE MENU
        self.__filemenu = tk.Menu(self, tearoff=0)
        self.__filemenu.add_command(label="Save configuration",
                                    command=self.save_configuration)
        self.__filemenu.add_command(label="Load configuration",
                                    command=self.load_configuration)
        self.__filemenu.add_command(label="Save image as",
                                    command=self.save_image)
        self.__filemenu.add_separator()
        self.__filemenu.add_command(label="Exit",
                                    command=self.exit,
                                    accelerator="Ctrl+Q")
        self.add_cascade(label="File", menu=self.__filemenu)

        # HELP MENU
        self.__helpmenu = tk.Menu(self, tearoff=0)
        self.__helpmenu.add_command(label="Camera Documentation",
                                    command=lambda url=DOC_URL: self.open_documentation(url))
        self.__helpmenu.add_command(label="App Documentation",
                                    command=lambda url=GITHUB_URL: self.open_github(url))
        self.add_cascade(label="Help", menu=self.__helpmenu)

    def save_configuration(self):
        raw_path = filedialog.asksaveasfilename(
            initialdir=self._root.path,
            filetypes=(("configuration files", ".ini"),))

        path = Path(raw_path)
        if path.name:
            path = path.with_suffix('.ini')
            self._root.settings.save(path)

    def load_configuration(self):
        raw_path = os.path.basename(filedialog.askopenfilename(
            filetypes=(("configuration files", ".ini"),)))

        path = Path(raw_path)

        if path.name:
            path = path.with_suffix('.ini')
            self._root.settings.open(path)

    def save_image(self):
        try:
            path = filedialog.asksaveasfilename(
                initialdir=self._root.path,
                filetypes=(("image files", "*.jpg"),
                           ("all files", "*.*")))
            if path != '':
                depth_frame = self._root.camera.depth_frame
                if isinstance(depth_frame, rs.depth_frame):
                    color_frame = rs.colorizer().colorize(depth_frame)
                    color_array = np.asanyarray(color_frame.get_data())
                    for i in range(len(self._root.masks)):
                        self._root.masks[i].draw(color_array)
                    color_image = PIL.Image.fromarray(color_array)
                    color_image = color_image.resize((848, 480))
                    color_image.save(f'{path}.jpg')
                else:
                    self._root.terminal.write_error(
                        'Failed to save image: '
                        'supplied depth frame was invalid')
        except Exception as e:
            self._root.terminal.write_error(f'Failed to save image: {e}')

    def exit(self):
        self._root.on_closing()

    def open_documentation(self, url):
        return webbrowser.open(url)

    def open_github(self, url):
        return webbrowser.open(url)
