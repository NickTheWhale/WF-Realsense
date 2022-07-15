import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class AppTerminal(tk.Frame):
    def __init__(self, root, row, column, rowspan=1, columnspan=1, sticky="NSEW"):
        super().__init__()
        self.__root = root
        self.__main_frame = root.main_frame
        self.__row = row
        self.__column = column
        self.__columnspan = columnspan
        self.__rowspan = rowspan
        self.__sticky = sticky

        self.__paused = False

        self.__create_widgets()

    def __create_widgets(self):
        # terminal frame
        self.__terminal_frame = tk.Frame(self.__main_frame)
        self.__terminal_frame.grid(row=self.__row,
                                   column=self.__column,
                                   rowspan=self.__rowspan,
                                   columnspan=self.__columnspan,
                                   sticky=self.__sticky)

        # terminal text
        self.__scrolled_text = ScrolledText(self.__terminal_frame,
                                            state='disabled',
                                            height=10,
                                            width=103)
        self.__scrolled_text.grid(row=0, column=0, rowspan=2, sticky="NSEW")
        self.__scrolled_text.configure(font='TkFixedFont')
        self.__scrolled_text.tag_config('INFO', foreground='black')
        self.__scrolled_text.tag_config('DEBUG', foreground='gray')
        self.__scrolled_text.tag_config('WARNING', foreground='orange')
        self.__scrolled_text.tag_config('ERROR', foreground='red')
        self.__scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        self.__scrolled_text.bind('<MouseWheel>', self.on_scroll)

        # buttons
        self.__pause_button = tk.Button(self.__terminal_frame,
                                        text='◼',
                                        command=self.flip_pause)
        self.__pause_button.grid(row=0, column=1)

        self.__clear_button = tk.Button(self.__terminal_frame,
                                        text='🗑',
                                        command=self.clear)
        self.__clear_button.grid(row=1, column=1)

    def write(self, msg):
        if not self.__paused:
            self.__scrolled_text.configure(state='normal')
            self.__scrolled_text.insert(tk.END, msg + '\n')
            self.__scrolled_text.configure(state='disabled')
            # Autoscroll to the bottom
            self.__scrolled_text.yview(tk.END)

    def clear(self):
        self.__num_lines = 0
        self.__scrolled_text.configure(state="normal")
        self.__scrolled_text.delete('1.0', tk.END)
        self.__scrolled_text.configure(state="disabled")

    def on_scroll(self, evt):
        if evt.delta >= 0:
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

    def __pause_symbol(self):
        return '▶' if self.__paused else '◼'

    @property
    def lines(self):
        return int(self.__scrolled_text.index('end-2c').split('.')[0])
