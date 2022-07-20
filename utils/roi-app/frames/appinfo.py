from tkinter import ttk

class AppInfo(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)

        self.configure(text="info", border=10)

        label = ttk.Label(self, text="info here")
        label.grid(row=0, column=0)
        
        self.columnconfigure(0, pad=220)
