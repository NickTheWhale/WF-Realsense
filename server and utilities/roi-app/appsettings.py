from tkinter import ttk
from slider import SettingSlider
from tooltip import ButtonToolTip


class AppSettings(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        self._configurator = self._root.configurator
        self._config = self._configurator.data
        self._camera = self._root.camera
        
        super().__init__(*args, **kwargs)
        self.configure(text='settings', border=10)

        self._sliders = []
        last_row = 0
        for key, value in self._config['camera'].items():
            ret, o = self._camera.options.get_option_range(key)
            if ret:
                start = float(value)
                self._sliders.append(SettingSlider(
                    self,
                    from_=o.min,
                    to=o.max,
                    step=o.step,
                    start=start,
                    label=key
                ))
                self._sliders[last_row].grid(row=last_row, column=0)
                last_row += 1

        self._button_seperator = ttk.Separator(master=self, orient="horizontal")
        self._button_seperator.grid(row=last_row, column=0, sticky="NSEW", pady=8)

        self._button_frame = ttk.Frame(master=self)
        self._button_frame.grid(row=last_row+1, column=0, sticky="NSEW")
        self._button_frame.columnconfigure(0, weight=1)

        self._reset_button = ButtonToolTip(
            master=self._button_frame,
            text='↺',
            helptext='Reset settings back to defualt',
            width=3,
            command=self.reset_callback
        )
        self._reset_button.grid(row=0, column=0, padx=3, pady=3, sticky="E")

        self._save_button = ButtonToolTip(
            master=self._button_frame,
            text='↓',
            helptext='Save settings to camera and configuration file',
            width=3,
            command=self.save_callback
        )
        self._save_button.grid(row=0, column=1, padx=3, pady=3)
        # self.save_callback()

    @property
    def camera(self):
        return self._camera
    
    @property
    def root(self):
        return self._root

    def reset_callback(self, *args, **kwargs):
        for slider in self._sliders:
            slider.reset()

    def save_callback(self, *args, **kwargs):
        for slider in self._sliders:
            slider.save()
