import tkinter as tk
from tkinter import ttk


class CreateToolTip():
    """create a tooltip for a given widget"""

    def __init__(self, widget, text='button', delay=500, helpx=35, helpy=30):
        self.helpx = helpx
        self.helpy = helpy
        self.waittime = delay  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + self.helpx
        y += self.widget.winfo_rooty() + self.helpy
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = ttk.Label(
            self.tw,
            text=self.text,
            justify='left',
            relief='solid',
            borderwidth=1,
            wraplength=self.wraplength
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class ButtonToolTip(ttk.Button):
    def __init__(self, *args, **kwargs):

        self._helptext = kwargs.pop('helptext', 'button')
        self._delay = kwargs.pop('delay', 500)
        self._helpx = kwargs.pop('helpx', 35)
        self._helpy = kwargs.pop('helpy', 30)

        super().__init__(*args, **kwargs)
        CreateToolTip(
            self,
            text=self._helptext,
            delay=self._delay,
            helpx=self._helpx,
            helpy=self._helpy
        )


class CheckButtonToolTip(ttk.Checkbutton):
    def __init__(self, *args, **kwargs):
        
        self._helptext = kwargs.pop('helptext', 'button')
        self._delay = kwargs.pop('delay', 500)
        self._helpx = kwargs.pop('helpx', 35)
        self._helpy = kwargs.pop('helpy', 30)
        
        super().__init__(*args, **kwargs, style='Toggle.TButton')
        CreateToolTip(
            self,
            text=self._helptext,
            delay=self._delay,
            helpx=self._helpx,
            helpy=self._helpy
        )
