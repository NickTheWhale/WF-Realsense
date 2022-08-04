import configparser
import threading
import tkinter as tk
from tkinter import ttk

from camera.config import Config
from widgets.settings import SettingsEntry, SettingsSlider, SettingsCombobox
from widgets.tooltip import ButtonToolTip
from widgets.scrollframe import VerticalScrollFrame


camera_options = {
    'framerate': [0, 5, 30, 60, 90],
    'region_of_interest_auto_exposure': [0.0, 1.0],
    'spatial_filter_level': [0, 1, 2, 3, 4, 5],
    'metric': [0.0, 1.0]
}


class AppSettings(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        self._camera = self._root.camera

        super().__init__(*args, **kwargs)

        self._padx = 0
        self._pady = 0
        self._width = 0
        self._entry_width = 23

        self.init()

    def init(self):
        self.configure(text=f'settings ({self._root.configurator.name})')

        self._scroll_widget = VerticalScrollFrame(self)
        self._scroll_widget.grid(row=0, column=0, padx=self._padx, sticky="NS")
        self._scroll_frame = self._scroll_widget.interior

        self._entry_text = tk.StringVar()
        # self._entry_text.set(self._root.configurator.name.split('.')[0])
        self._entry_text.set('configuration')

        # camera options
        self._sliders = []
        self._entries = []
        last_row = 0
        for key, value in self._root.configurator.data['camera'].items():
            ret, option = self._camera.options.get_option_range(key)
            if ret:
                try:
                    start = float(value)
                except ValueError as e:
                    start = option.default
                    self._root.terminal.write_warning(f'{key}: {e}. Defaulted to {start}')

                self._sliders.append(SettingsSlider(
                    self._scroll_frame,
                    root=self._root,
                    from_=option.min,
                    to=option.max,
                    step=option.step,
                    start=start,
                    label=key,
                    section='camera'
                ))
                self._sliders[-1].grid(row=last_row, column=0)
                last_row += 1

        for key, value in self._root.configurator.data['camera'].items():
            ret, _ = self._camera.options.get_option_range(key)
            if not ret:
                try:
                    self._entries.append(SettingsCombobox(
                        self._scroll_frame,
                        root=self._root,
                        label=key,
                        section='camera',
                        start=value,
                        values=camera_options[key]
                    ))
                    self._entries[-1].grid(row=last_row, column=0)
                    last_row += 1
                except KeyError:
                    pass

        # server options
        for option in self._root.configurator.data['server']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='server',
                start=self._root.configurator.get_value('server', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        # node options
        for option in self._root.configurator.data['nodes']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='nodes',
                start=self._root.configurator.get_value('nodes', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        # logging options
        for option in self._root.configurator.data['logging']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='logging',
                start=self._root.configurator.get_value('logging', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        # application options
        for option in self._root.configurator.data['application']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='application',
                start=self._root.configurator.get_value('application', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        self._button_seperator = ttk.Separator(master=self, orient="horizontal")
        self._button_seperator.grid(row=1, column=0, sticky="NSEW", pady=8)

        # bottom frame
        self._button_frame = ttk.Frame(master=self)
        self._button_frame.grid(row=2, column=0, sticky="S")

        self._filename_entry_box = ttk.Entry(
            master=self._button_frame,
            width=self._entry_width,
            textvariable=self._entry_text,
        )
        self._filename_entry_box.grid(row=0, column=0, padx=self._padx, pady=self._pady)

        self._reset_button = ButtonToolTip(
            master=self._button_frame,
            text='↺',
            helptext='Reset settings back to defualt',
            width=self._width,
            command=self.reset_callback
        )
        self._reset_button.grid(row=0,
                                column=1,
                                padx=self._padx,
                                pady=self._pady)

        self._open_button = ButtonToolTip(
            master=self._button_frame,
            text='⤒',
            helptext='Open and load settings from configuration file',
            width=self._width,
            command=self.open_callback
        )
        self._open_button.grid(row=0,
                               column=2,
                               padx=self._padx,
                               pady=self._pady)

        self._save_button = ButtonToolTip(
            master=self._button_frame,
            text='⤓',
            helptext='Save settings to camera and configuration file',
            width=self._width,
            command=self.save_callback
        )
        self._save_button.grid(row=0,
                               column=3,
                               padx=self._padx,
                               pady=self._pady)

        self._root.bind("<Button-1>", self.mouse_click_callback)
        self._root.bind("<Return>", self.return_callback)

        # grid config
        self._button_frame.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def reset_callback(self, *args, **kwargs):
        for slider in self._sliders:
            slider.reset()
        for entry in self._entries:
            entry.reset()

    def save_callback(self, *args, **kwargs):
        self._root.video.pause()
        self.save()

    def open_callback(self, *args, **kwargs):
        self._root.video.pause()
        self.open()
    
    def open(self):
        filename = self._entry_text.get().strip().split('.')[0] + '.ini'
        try:
            self._root.configurator = Config(filename)
        except configparser.Error:
            self._root.terminal.write_error(f'Failed to open "{filename}"')
        except FileNotFoundError as e:
            self._root.terminal.write_error(e)
        except RuntimeError as e:
            self._root.terminal.write_error(e)
        else:
            self._root.configurator = Config(filename)
            self.init()

            self.resize()
            self.sync()
            self._root.video.unpause()

    def mouse_click_callback(self, event):
        if self._root.focus_get() is not event.widget:
            self._root.focus_set()

    def return_callback(self, event):
        focused = self._root.focus_get()
        if focused is self._filename_entry_box:
            self._root.focus_set()

        else:
            for entry in self._entries:
                if hasattr(entry, 'entry'):
                    if focused is entry.entry:
                        self._root.focus_set()
                        break
                elif hasattr(entry, 'combobox'):
                    if focused is entry.combobox:
                        self._root.focus_set()
                        break

    def save(self):
        try:
            self._root.terminal.write_camera('Saving...')
            self._root.update_idletasks()

            for mask in self._root.masks:
                mask.complete()
            for slider in self._sliders:
                slider.save()
            for entry in self._entries:
                entry.save()

            with open(f'{self._entry_text.get()}.ini', 'w') as file:
                for i in range(len(self._root.masks)):
                    self._root.configurator.set(
                        'roi',
                        f'roi_{i+1}',
                        str(self._root.masks[i].coordinates)
                    )

                self._root.configurator.save(file)

            self._root.terminal.write_camera(
                f'Saved configuration to "{self._entry_text.get()}.ini"')
        except RuntimeError:
            self._root.terminal.write_error(
                ('Failed to save configuration file. '
                 'This may be due to a configuration '
                 'conflict or other camera related issue. '
                 'Try default settings, resetting camera, '
                 'or restarting application if issues persist'))
        else:
            self.init()

            self.resize()
            self.sync()
            self._root.video.unpause()

    def sync(self):
        try:
            self._root.terminal.write_camera('Syncing.....')
            self._root.update_idletasks()
            self._root.terminal.pause()
            for mask in self._root.masks:
                mask.complete()
            for slider in self._sliders:
                slider.save()
            for entry in self._entries:
                entry.save()
            self._root.terminal.unpause()
            self.sync_camera()
        except Exception as e:
            self._root.terminal.write_error(f'Failed to sync configuration: {e}')
        else:
            self._root.terminal.write('Synced')

    def sync_camera(self):
        self._root.camera.filter_level = int(float(self._root.configurator.get_value(
            'camera', 'spatial_filter_level', '0')))
        self._root.camera.metric = bool(float(self._root.configurator.get_value(
            'camera', 'metric', '0')))

    def resize(self):
        self._scroll_widget.resize()

        if self._root.camera.scale > 1:
            self._padx = 0
            self._pady = 0
            self._width = 0
            self._entry_width = 23
        else:
            self._padx = 3
            self._pady = 3
            self._width = 3
            self._entry_width = 20

        self._filename_entry_box.configure(width=self._entry_width)
        self._reset_button.configure(width=self._width)
        self._open_button.configure(width=self._width)
        self._save_button.configure(width=self._width)

        columns, rows = self._button_frame.grid_size()
        for column in range(columns):
            self._button_frame.columnconfigure(column, pad=self._padx)
        for row in range(rows):
            self._button_frame.rowconfigure(row, pad=self._pady)

    @property
    def camera(self):
        return self._camera

    @property
    def root(self):
        return self._root
