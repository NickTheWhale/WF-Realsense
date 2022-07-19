import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from tooltip import ButtonToolTip, CheckButtonToolTip


class AppTerminal(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)
        self.configure(text="terminal", border=10)

        self.__paused = False
        self.__lines = 0
        self.__expanded = False
        self.__camera_supress = False

        self.__create_widgets()

    def __create_widgets(self):
        # terminal text
        self.__scrolled_text = ScrolledText(self,
                                            state='disabled',
                                            height=10,
                                            width=97)
        self.__scrolled_text.grid(row=0, column=0, rowspan=4, sticky="NSEW")
        self.__scrolled_text.configure(font='TkFixedFont')
        self.__scrolled_text.tag_config('INFO', foreground='black')
        self.__scrolled_text.tag_config('DEBUG', foreground='gray')
        self.__scrolled_text.tag_config('WARNING', foreground='orange')
        self.__scrolled_text.tag_config('ERROR', foreground='red')
        self.__scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        self.__scrolled_text.bind('<MouseWheel>', self.on_scroll)

        # BUTTONS
        # pause
        self.__pause_button = ButtonToolTip(
            self,
            text='◼',
            width=3,
            command=self.flip_pause,
            helptext='Pause terminal output'
        )
        self.__pause_button.grid(row=0, column=1)
        
        # camera
        self.__camera_button = CheckButtonToolTip(
            self, 
            text='📷',
            width=3,
            command=self.toggle_camera_supress,
            helptext='Surpress region of interest data'
        )
        self.__camera_button.state(['selected'])
        self.__camera_button.grid(row=1, column=1)
        
        # clear
        self.__clear_button = ButtonToolTip(
            self,
            text='🗑',
            width=3,
            command=self.clear,
            helptext='Clear terminal output'
        )
        self.__clear_button.grid(row=2, column=1)

        # expand
        self.__expand_button = ButtonToolTip(
            self,
            text='⇩',
            width=3,
            command=self.toggle_expand,
            helptext='Expand/collapse terminal'
        )
        self.__expand_button.grid(row=3, column=1)
        

    def write(self, msg):
        if not self.__paused:
            self.__scrolled_text.configure(state='normal')
            self.__scrolled_text.insert(tk.END, f'{msg}\n')
            self.__lines += 1
            self.__scrolled_text.configure(state='disabled')
            # Autoscroll to the bottom
            self.__scrolled_text.yview(tk.END)

    def clear(self):
        self.__scrolled_text.configure(state="normal")
        self.__scrolled_text.delete('1.0', tk.END)
        self.__lines = 0
        self.__scrolled_text.configure(state="disabled")

    def on_scroll(self, evt):
        if evt.delta >= 0:
            if self.__lines > 0:
                self.pause()
        else:
            if self.__paused:
                _, y = self.__scrolled_text.yview()
                if y >= 1:
                    self.unpause()

    def pause(self):
        self.__paused = True
        self.__pause_button['text'] = self.__pause_symbol()

    def unpause(self):
        self.__paused = False
        self.__pause_button['text'] = self.__pause_symbol()

    def flip_pause(self):
        self.__paused = not self.__paused
        self.__pause_button['text'] = self.__pause_symbol()
        
    def toggle_camera_supress(self):
        self.__camera_supress = not self.__camera_supress
        
    @property
    def camera_supress(self):
        return self.__camera_supress

    def toggle_expand(self):
        self.__expanded = not self.__expanded
        if self.__expanded:
            self.__scrolled_text['height'] = 20
            self.__expand_button['text'] = '⇧'
        else:
            self.__scrolled_text['height'] = 10
            self.__expand_button['text'] = '⇩'
            self.__scrolled_text.yview(tk.END)

    def __pause_symbol(self):
        return '▶' if self.__paused else '◼'
