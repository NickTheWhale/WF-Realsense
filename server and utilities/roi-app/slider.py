from decimal import Decimal
import tkinter as tk
from tkinter import ttk
import sv_ttk


class SettingSlider(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._from = kwargs['from_']
        self._to = kwargs['to']
        self._step = kwargs['step']
        self._label = kwargs['label']
        self._start = kwargs['start']

        kwargs.pop('from_')
        kwargs.pop('to')
        kwargs.pop('step')
        kwargs.pop('label')
        kwargs.pop('start')

        super().__init__(*args, **kwargs)
        
        self._raw_level = tk.DoubleVar()
        self._raw_level.set(self._start)
        self._level = self.constrain_value(self._start)
        
        self.configure(text=f'{self._label} {self._level}')
        self.configure(border=1)
        
        self._slider = ttk.Scale(
            master=self,
            from_=self._from,
            to=self._to,
            orient='horizontal',
            length=300,
            command=self.slider_callback,
            variable=self._raw_level
        )

        self._reset_button = ttk.Button(
            master=self,
            text='↺',
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
        return constrained_val
    
    def reset(self):
        self.reset_callback()


if __name__ == '__main__':
    root = tk.Tk()
    sv_ttk.set_theme('light')
    frame = ttk.Frame(root)
    frame.grid(row=0, column=0)

    slider = SettingSlider(frame, from_=0.0, to=10.0, step=0.01, start=5.0, label='settings')
    slider.grid(row=0, column=0, padx=10, pady=10)

    root.resizable(False, False)
    root.mainloop()
