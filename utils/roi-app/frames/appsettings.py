import tkinter as tk
from tkinter import ttk

from widgets.settings import SettingsEntry, SettingsSlider
from widgets.tooltip import ButtonToolTip
from widgets.scrollframe import VerticalScrollFrame


class AppSettings(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        self._configurator = self._root.configurator
        self._config_data = self._configurator.data
        self._camera = self._root.camera

        super().__init__(*args, **kwargs)
        self.configure(text='settings')

        self._scroll_widget = VerticalScrollFrame(self)
        self._scroll_widget.grid(row=0, column=0, padx=5, sticky="NS")
        self._scroll_frame = self._scroll_widget.interior

        self._entry_text = tk.StringVar()
        self._entry_text.set('myConfig')

        # camera options
        self._sliders = []
        last_row = 0
        for key, value in self._config_data['camera'].items():
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

        # server options
        self._entries = []
        for option in self._config_data['server']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='server',
                start=self._configurator.get_value('server', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        # node options
        for option in self._config_data['nodes']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='nodes',
                start=self._configurator.get_value('nodes', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        # logging options
        for option in self._config_data['logging']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='logging',
                start=self._configurator.get_value('logging', option, '')
            ))
            self._entries[-1].grid(row=last_row, column=0)
            last_row += 1

        # application options
        for option in self._config_data['application']:
            self._entries.append(SettingsEntry(
                self._scroll_frame,
                root=self._root,
                label=option,
                section='application',
                start=self._configurator.get_value('application', option, '')
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
            width=25,
            textvariable=self._entry_text,
        )
        self._filename_entry_box.grid(row=0, column=0, padx=3, pady=3, sticky="S")

        self._reset_button = ButtonToolTip(
            master=self._button_frame,
            text='↺',
            helptext='Reset settings back to defualt',
            width=3,
            command=self.reset_callback
        )
        self._reset_button.grid(row=0, column=1, padx=3, pady=3, sticky="E")

        self._save_button = ButtonToolTip(
            master=self._button_frame,
            text='↓',
            helptext='Save settings to camera and configuration file',
            width=3,
            command=self.save_callback
        )
        self._save_button.grid(row=0, column=2, padx=3, pady=3)

        self._root.bind("<Button-1>", self.mouse_click_callback)
        self._root.bind("<Return>", self.return_callback)

        # grid config
        self._button_frame.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def reset_callback(self, *args, **kwargs):
        for slider in self._sliders:
            slider.reset()

    def save_callback(self, *args, **kwargs):
        self._root.terminal.write_camera('Saving...')
        self._root.update_idletasks()

        for slider in self._sliders:
            slider.save()
        for entry in self._entries:
            entry.save()

        with open(f'{self._entry_text.get()}.ini', 'w') as file:
            self._configurator.set(
                'camera',
                'region_of_interest',
                str(self._root.mask.coordinates)
            )
            self._configurator.save(file)

        self._root.terminal.write_camera(f'Saved configuration to "{self._entry_text.get()}.ini"')

    def mouse_click_callback(self, event):
        if self._root.focus_get() is not event.widget:
            self._root.focus_set()

    def return_callback(self, event):
        focused = self._root.focus_get()
        if focused is self._filename_entry_box:
            self._root.focus_set()

        else:
            for entry in self._entries:
                if focused is entry.entry:
                    self._root.focus_set()
                    break

    def resize(self):
        self._scroll_widget.resize()

    @property
    def camera(self):
        return self._camera

    @property
    def root(self):
        return self._root
