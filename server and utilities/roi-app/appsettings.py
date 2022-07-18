from tkinter import ttk
from slider import SettingSlider


class AppSettings(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)

        self.configure(text='settings', border=10)

        self._sliders = []
        for i in range(9):
            self._sliders.append(SettingSlider(
                self,
                from_=0.0,
                to=10.0,
                step=0.1,
                start=5.0,
                label='settings'
            ))
            self._sliders[i].grid(row=i, column=0)

        self._button_seperator = ttk.Separator(master=self, orient="horizontal")
        self._button_seperator.grid(row=9, column=0, sticky="NSEW", pady=10)
        
        self._button_frame = ttk.Frame(master=self)
        self._button_frame.grid(row=10, column=0, sticky="NSEW")
        self._button_frame.columnconfigure(0, weight=1)

        self._reset_button = ttk.Button(
            master=self._button_frame,
            text='↺',
            command=self.reset_callback
        )
        self._reset_button.grid(row=0, column=0, padx=5, pady=5, sticky="E")
        
        self._save_button = ttk.Button(
            master=self._button_frame,
            text='↓',
            command=self.save_callback
        )
        self._save_button.grid(row=0, column=1, padx=5, pady=5)
        

    def reset_callback(self):
        for slider in self._sliders:
            slider.reset()
        print('reset all settings to default')
        
    def save_callback(self):
        self._args[0].mask_reset()
        print('settings saved')