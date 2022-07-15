import tkinter
from tkinter.constants import *
import logging
import time
from tkinter import END, N, S, E, W, Scrollbar, Text
from tkinter import ttk


class LoggingHandlerFrame(ttk.Frame):

    class Handler(logging.Handler):
        def __init__(self, widget):
            logging.Handler.__init__(self)
            self.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
            self.widget = widget
            self.widget.config(state='disabled')

        def emit(self, record):
            self.widget.config(state='normal')
            self.widget.insert(END, self.format(record) + "\n")
            self.widget.see(END)
            self.widget.config(state='disabled')

    def __init__(self, *args, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

        self.scrollbar = Scrollbar(self)
        self.scrollbar.grid(row=0, column=1, sticky=(N, S, E))

        self.text = Text(self, yscrollcommand=self.scrollbar.set)
        self.text.grid(row=0, column=0, sticky=(N, S, E, W))

        self.scrollbar.config(command=self.text.yview)

        self.logging_handler = LoggingHandlerFrame.Handler(self.text)


def loop():
    print("hi")
    logging.info(time.time())
    tk.after(100, loop)


tk = tkinter.Tk()

log = LoggingHandlerFrame(tk)
log.grid(row=0, column=0)

tk.after(100, loop)
tk.mainloop()
