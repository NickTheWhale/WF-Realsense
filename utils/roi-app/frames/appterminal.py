import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from widgets.tooltip import ButtonToolTip, CheckButtonToolTip


class AppTerminal(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)
        self.configure(border=10)

        self._paused = False
        self._lines = 0
        self._expanded = False
        self._camera_supress = False

        self._create_widgets()

    def _create_widgets(self):
        # terminal text
        self._scrolled_text = ScrolledText(self,
                                            state='disabled',
                                            height=10,
                                            width=97)
        self._scrolled_text.grid(row=0, column=0, rowspan=4, sticky="NSEW")
        self._scrolled_text.configure(font='TkFixedFont')
        self._scrolled_text.tag_config('INFO', foreground='black')
        self._scrolled_text.tag_config('DEBUG', foreground='gray')
        self._scrolled_text.tag_config('WARNING', foreground='orange')
        self._scrolled_text.tag_config('ERROR', foreground='red')
        self._scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        self._scrolled_text.bind('<MouseWheel>', self.on_scroll)

        # BUTTONS
        # pause
        self._pause_button = ButtonToolTip(
            self,
            text='◼',
            width=3,
            command=self.flip_pause,
            helptext='Pause terminal output'
        )
        self._pause_button.grid(row=0, column=1)
        
        # camera
        self._camera_button = CheckButtonToolTip(
            self, 
            text='📷',
            width=3,
            command=self.toggle_camera_supress,
            helptext='Surpress region of interest data'
        )
        self._camera_button.state(['selected'])
        self._camera_button.grid(row=1, column=1)
        
        # clear
        self._clear_button = ButtonToolTip(
            self,
            text='🗑',
            width=3,
            command=self.clear,
            helptext='Clear terminal output'
        )
        self._clear_button.grid(row=2, column=1)

        # expand
        self._expand_button = ButtonToolTip(
            self,
            text='⇩',
            width=3,
            command=self.toggle_expand,
            helptext='Expand/collapse terminal'
        )
        self._expand_button.grid(row=3, column=1)
        self.set_status()
        

    def write(self, msg):
        if not self._paused:
            self._scrolled_text.configure(state='normal')
            self._scrolled_text.insert('end', f'{msg}\n')
            self._lines += 1
            self._scrolled_text.configure(state='disabled')
            # Autoscroll to the bottom
            self._scrolled_text.yview('end')
            
    def write_error(self, msg):
        self.write(f'[Error] {msg}')
        
    def write_warning(self, msg):
        self.write(f'[Warning] {msg}')
        
    def write_camera(self, msg):
        self.write(f'[Camera] {msg}')

    def clear(self):
        self._scrolled_text.configure(state="normal")
        self._scrolled_text.delete('1.0', tk.END)
        self._lines = 0
        self._scrolled_text.configure(state="disabled")

    def on_scroll(self, evt):
        if evt.delta >= 0:
            if self._lines > 0:
                self.pause()
        else:
            if self._paused:
                _, y = self._scrolled_text.yview()
                if y >= 1:
                    self.unpause()

    def pause(self):
        self._paused = True
        self.set_status()
        
    def unpause(self):
        self._paused = False
        self.set_status()

    def flip_pause(self):
        self._paused = not self._paused
        self.set_status()
        
    def toggle_camera_supress(self):
        self._camera_supress = not self._camera_supress
        
    def toggle_expand(self):
        self._expanded = not self._expanded
        if self._expanded:
            self._scrolled_text['height'] = 20
            self._expand_button['text'] = '⇧'
        else:
            self._scrolled_text['height'] = 10
            self._expand_button['text'] = '⇩'
            self._scrolled_text.yview(tk.END)
            
    def set_status(self):
        self._pause_button['text'] = self._pause_symbol()
        status = 'paused' if self._paused else 'running'
        self.configure(text=f'terminal ({status})')
        self.update_idletasks()

    def _pause_symbol(self):
        return '▶' if self._paused else '◼'

    @property
    def camera_supress(self):
        return self._camera_supress
    
    @property
    def paused(self):
        return self._paused
    
    @property
    def text(self):
        return self._scrolled_text