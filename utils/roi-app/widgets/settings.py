import configparser
from decimal import Decimal
import tkinter as tk
from tkinter import ttk
from widgets.tooltip import ButtonToolTip
from ttkwidgets import TickScale


class SettingsSlider(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._root = kwargs.pop('root')
        self._camera = self._root.camera
        self._configurator = self._root.configurator
        self._from = kwargs.pop('from_')
        self._to = kwargs.pop('to')
        self._step = kwargs.pop('step')
        self._label = kwargs.pop('label')
        self._section = kwargs.pop('section')
        self._start = kwargs.pop('start')

        super().__init__(*args, **kwargs)

        self._raw_level = tk.DoubleVar()
        self._level = self.constrain_value(self._start)

        self.configure(text=f'{self._label} {self._level}', border=1)

        self._slider = TickScale(
            master=self,
            from_=self._from,
            to=self._to,
            orient='horizontal',
            length=200,
            tickinterval=0,
            showvalue=0,
            resolution=self._step,
            command=self.slider_callback,
            variable=self._raw_level
        )
        self._raw_level.set(self._start)

        self._reset_button = ButtonToolTip(
            master=self,
            text='↺',
            helptext=f'Reset "{self._label}" to "{self._start}"',
            width=3,
            command=self.reset_callback
        )

        self._slider.grid(row=0, column=0, padx=2)
        self._reset_button.grid(row=0, column=1, padx=2, pady=(0, 2))

    def slider_callback(self, *args):
        """called on slider moved"""

        self._level = self.constrain_value(float(args[0]))
        self.configure(text=f'{self._label} {self._level}')

    def reset_callback(self, *args):
        """called on reset button press"""

        self._raw_level.set(self._start)
        self.slider_callback(self._start,)

    def constrain_value(self, set_val):
        """constrain value with respect to from, to, and step"""

        min_val, max_val, step_size = self._from, self._to, self._step
        # round set value to nearest step size
        set_val = step_size * round(set_val / step_size)
        set_val = Decimal(set_val).quantize(Decimal(str(step_size)))
        # constrain set_value within value_range
        if min_val <= set_val <= max_val:
            constrained_val = set_val
        else:
            if set_val > max_val:
                set_val = max_val
            elif set_val < min_val:
                set_val = min_val
            constrained_val = set_val
        return float(constrained_val)

    def save(self):
        if self._section == 'camera':
            # save to camera
            ret = self._camera.options.set_rs_option_direct(self._label, self._level)
            if not ret:
                self._root.terminal.write_camera(
                    f'Failed to set "{self._label}" to "{self._level}"')
            else:
                self._root.terminal.write_camera(
                    f'Set "{self._label}" to "{self._level}"')

        # write to configurator file
        self._configurator.set(self._section, self._label, str(self._level))

    def reset(self):
        self.reset_callback()


class SettingsEntry(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._root = kwargs.pop('root')
        self._camera = self._root.camera
        self._configurator = self._root.configurator
        self._label = kwargs.pop('label')
        self._section = kwargs.pop('section')
        self._start = kwargs.pop('start')

        self._text = tk.StringVar()
        self._text.set(self._start)

        super().__init__(*args, **kwargs)

        self.configure(text=self._label, border=1)

        self._entry = ttk.Entry(
            master=self,
            width=26,
            textvariable=self._text
        )
        self._entry.grid(row=0, column=0, padx=3, pady=3)

        self._reset_button = ButtonToolTip(
            master=self,
            text='↺',
            helptext=f'Reset "{self._label}" to "{self._start}"',
            width=3,
            command=self.reset_callback
        )
        self._reset_button.grid(row=0, column=1, padx=3, pady=3)

    def save(self):
        self._root.terminal.write_camera(f'Saved {self._text.get()} to {self._label}')
        self._configurator.set(self._section, self._label, str(self._text.get()))

    def reset(self):
        self.reset_callback()

    def reset_callback(self):
        self._text.set(self._start)
        
    @property
    def entry(self):
        return self._entry
