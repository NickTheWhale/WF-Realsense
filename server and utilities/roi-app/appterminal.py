import tkinter as tk


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
        self.__num_lines = 0
        self.__max_lines = 8

        self.__create_widgets()

    def __create_widgets(self):
        # frame
        self.__terminal_frame = tk.Frame(self.__main_frame)
        self.__terminal_frame.grid(row=self.__row,
                                   column=self.__column,
                                   rowspan=self.__rowspan,
                                   columnspan=self.__columnspan,
                                   sticky=self.__sticky)

        # terminal
        self.__terminal_text = tk.Text(self.__terminal_frame,
                                       width=103,
                                       height=10,
                                       yscrollcommand=True,
                                       state="disabled")
        self.__terminal_text.grid(row=0, column=0, rowspan=3)

        # pause button
        self.__pause_button = tk.Button(self.__terminal_frame,
                                        text='◼',
                                        command=self.pause)
        self.__pause_button.grid(row=0, column=1)

        # clear button
        self.__clear_button = tk.Button(self.__terminal_frame,
                                        text='🗑',
                                        command=self.clear)
        self.__clear_button.grid(row=1, column=1)

        # scrollbar
        self.__terminal_scrollbar = tk.Scrollbar(self.__terminal_frame,
                                                 command=self.__terminal_text.yview)
        self.__terminal_scrollbar.grid(row=2, column=1, sticky="NSEW")
        self.__terminal_text["yscrollcommand"] = self.__terminal_scrollbar.set

        # configure rows/columns
        self.__terminal_frame.rowconfigure(2, pad=65)
        
    def write(self, msg):
        if not self.__paused:
            self.__num_lines += 1
            self.__terminal_text.configure(state="normal")
            self.__terminal_text.insert(tk.INSERT, msg)
            self.__terminal_text.see("end")

            # if self.__num_lines > self.__max_lines:
            #     self.__terminal_text.delete('1.0', '5.0')
            #     self.__num_lines = self.lines
            #     print(self.__num_lines)

            self.__terminal_text.configure(state="disabled")

    def clear(self):
        self.__num_lines = 0
        self.__terminal_text.configure(state="normal")
        self.__terminal_text.delete('1.0', tk.END)
        self.__terminal_text.configure(state="disabled")

    def pause(self):
        self.__paused = not self.__paused
        self.__pause_button['text'] = self.__pause_symbol(self.__paused)

    def __pause_symbol(self, paused):
        return '▶' if paused else '◼'

    @property
    def lines(self):
        return int(self.__terminal_text.index('end-1c').split('.')[0])

    @property
    def max_lines(self):
        return self.__max_lines

    @max_lines.setter
    def max_lines(self, max_lines):
        self.__max_lines = max_lines
