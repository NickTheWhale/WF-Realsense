from decimal import Decimal
import tkinter as tk
from tkinter import ttk
from tooltip import ButtonToolTip
from ttkwidgets import TickScale


class SettingSlider(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._root = args[0].root
        self._camera = args[0].camera
        self._from = kwargs.pop('from_')
        self._to = kwargs.pop('to')
        self._step = kwargs.pop('step')
        self._label = kwargs.pop('label')
        self._start = kwargs.pop('start')

        super().__init__(*args, **kwargs)

        self._raw_level = tk.DoubleVar()
        self._level = self.constrain_value(self._start)

        self.configure(text=f'{self._label} {self._level}')
        self.configure(border=1)

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
            helptext=f'Reset "{self._label}" to defualt',
            width=3,
            command=self.reset_callback
        )

        self._slider.grid(row=0, column=0, padx=10)
        self._reset_button.grid(row=0, column=1, padx=5, pady=(0, 10))

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
        ret = self._camera.options.set_rs_option_direct(self._label, self._level)
        if not ret:
            self._root.terminal.write(f'Failed to set "{self._label}" to "{self._level}"')
        else:
            self._root.terminal.write(f'Set "{self._label}" to "{self._level}"')

    def reset(self):
        self.reset_callback()
