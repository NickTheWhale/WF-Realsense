import tkinter as tk
import tkinter.ttk as ttk
import sv_ttk

root = tk.Tk()
mainframe = tk.Frame(root)


# Model

class Limiter(ttk.Scale):
    """ ttk.Scale sublass that limits the precision of values. """

    def __init__(self, *args, **kwargs):
        self.precision = kwargs.pop('precision')  # Remove non-std kwarg.
        self.chain = kwargs.pop('command', lambda *a: None)  # Save if present.
        super(Limiter, self).__init__(*args, command=self._value_changed, **kwargs)

    def _value_changed(self, newvalue):
        newvalue = round(float(newvalue), self.precision)
        self.winfo_toplevel().globalsetvar(self.cget('variable'), (newvalue))
        self.chain(newvalue)  # Call user specified function.


# Sample client callback.
def callback(newvalue):
    print('callback({!r})'.format(newvalue))

input_var = tk.DoubleVar(value=0.)
spin = tk.Spinbox(mainframe, textvariable=input_var, wrap=True, width=10)
slide = Limiter(mainframe, variable=input_var, orient='horizontal', length=200,
                command=callback, precision=4)

spin['to'] = 1.0
spin['from'] = 0.0
spin['increment'] = 0.01
slide['to'] = 1.0
slide['from'] = 0.0
# slide['digits'] = 4
# slide['resolution'] = 0.01

# Layout

weights = {'spin': 1, 'slide': 100}

mainframe.grid_rowconfigure(0, weight=1)
mainframe.grid_columnconfigure(0, weight=weights['spin'])
mainframe.grid_columnconfigure(1, weight=weights['slide'])
spin.grid(row=0, column=0, sticky='news')
slide.grid(row=0, column=1, sticky='news')

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
mainframe.grid(row=0, column=0)

root.mainloop()