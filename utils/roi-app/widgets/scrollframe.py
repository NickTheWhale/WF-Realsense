import tkinter as tk
from tkinter import ttk


class RootFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        self._root = kwargs.pop('root')
        super().__init__(*args, **kwargs)

    @property
    def root(self):
        return self._root


class VerticalScrollFrame(ttk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame.
    * Construct and pack/place/grid normally.
    * This frame only allows vertical scrolling.
    """

    def __init__(self, *args, **kwargs):

        self._args = args
        self._root = args[0].root

        self._entered = False
        self._lower_height = 380
        self._upper_height = 675
        self._expand_offset = 180

        super().__init__(*args, **kwargs)

        self._scrollbar = ttk.Scrollbar(self, orient='vertical')
        self._scrollbar.grid(row=0, column=1, sticky="NS")

        self._canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                                 yscrollcommand=self._scrollbar.set,
                                 height=self._lower_height)
        self._canvas.grid(row=0, column=0)

        self._scrollbar.config(command=self._canvas.yview)

        # Reset the view
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it.
        self._interior = ttk.Frame(self._canvas)
        interior_id = self._canvas.create_window(0, 0, window=self._interior,
                                                 anchor='nw')

        # Track changes to the canvas and frame width and sync them,
        # also updating the scrollbar.
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            size = (self._interior.winfo_reqwidth(), self._interior.winfo_reqheight())
            self._canvas.config(scrollregion="0 0 %s %s" % size)
            if self._interior.winfo_reqwidth() != self._canvas.winfo_width():
                # Update the canvas's width to fit the inner frame.
                self._canvas.config(width=self._interior.winfo_reqwidth())
        self._interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if self._interior.winfo_reqwidth() != self._canvas.winfo_width():
                # Update the inner frame's width to fill the canvas.
                self._canvas.itemconfigure(interior_id, width=self._canvas.winfo_width())

        self._canvas.bind("<Configure>", _configure_canvas)
        self._root.bind("<MouseWheel>", self.on_mousewheel)
        self._root.bind("<Enter>", self.on_enter)
        self._root.bind("<Leave>", self.on_exit)

    def on_enter(self, event):
        if event.widget is self:
            self._entered = True

    def on_exit(self, event):
        if event.widget is self:
            self._entered = False

    def on_mousewheel(self, event: tk.Event):
        if self._entered:
            if not event.widget is self._scrollbar:
                if event.delta > 0:
                    self._canvas.yview_scroll(-1, what='units')
                elif event.delta < 0:
                    self._canvas.yview_scroll(1, what='units')

    def resize(self):
        new_height = 0
        if self._root.camera.scale <= 1:
            new_height = self._upper_height
        elif self._root.camera.scale > 1:
            new_height = self._lower_height
        if self._root.terminal.expanded:
            new_height += self._expand_offset
        
        self._canvas.configure(height=new_height)
        
        
    @property
    def interior(self):
        return self._interior

    @property
    def root(self):
        return self._root
