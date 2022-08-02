import tkinter as tk
from tkinter import ttk

import numpy as np
import PIL.Image
import PIL.ImageTk
from widgets.tooltip import ButtonToolTip, CheckButtonToolTip
from tkinter import messagebox


class AppVideo(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)

        self.configure(text='video')

        self._paused = False
        self._roi_select = tk.IntVar()
        self._roi_select.set(1)
        self._roi_select_all = tk.BooleanVar()
        self._roi_select_all.set(False)

        # resize variables
        self._padx = 0
        self._pady = 0
        self._width = 0
        self._border = 0

        # region WIDGETS
        # video
        self._video_label = ttk.Label(
            master=self,
            cursor="tcross",
            relief="sunken",
            border=self._border
        )
        self._video_label.grid(row=0, column=0, columnspan=2)

        # MASK CONTROLS
        self._mask_control_frame = ttk.Labelframe(self,
                                                  text='mask controls',
                                                  border=self._border)
        self._mask_control_frame.grid(row=1, column=0, padx=self._padx, pady=self._pady)

        # reset
        self._mask_reset_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='🗑',
            command=self.mask_reset,
            width=self._width,
            helptext='Reset (clear) mask(s)'
        )
        self._mask_reset_button.grid(row=0, column=0, padx=self._padx, pady=self._pady)

        # undo
        self._mask_undo_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='⎌',
            command=self.mask_undo,
            width=self._width,
            helptext='Undo last mask command'
        )
        self._mask_undo_button.grid(row=0, column=1, padx=self._padx, pady=self._pady)

        # see
        self._mask_see_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='👓',
            command=self.mask_see_raw,
            width=self._width,
            helptext='Output list of coordinates to terminal'
        )
        self._mask_see_button.grid(row=0, column=2, padx=self._padx, pady=self._pady)

        # complete
        self._mask_complete_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='✓',
            command=self.mask_complete,
            width=self._width,
            helptext='Complete (close) mask'
        )
        self._mask_complete_button.grid(row=0, column=3, padx=self._padx, pady=self._pady)

        # see all
        self._mask_see_all_button = CheckButtonToolTip(
            master=self._mask_control_frame,
            text='all',
            command=self.mask_see_all,
            width=self._width,
            helptext='View all masks',
            variable=self._roi_select_all
        )
        self._mask_see_all_button.grid(row=0, column=4, padx=self._padx, pady=self._pady)

        self._mask_select_combobox = ttk.Combobox(
            master=self._mask_control_frame,
            textvariable=self._roi_select,
            width=1,
            takefocus=False
        )
        values = [x+1 for x in range(len(self._root.masks))]
        self._mask_select_combobox.configure(values=values, state='readonly')
        self._mask_select_combobox.grid(row=0, column=5, padx=self._padx, pady=self._pady)

        # VIDEO CONTROLS
        self._video_controls_frame = ttk.Labelframe(
            self, text='video controls', border=self._border)
        self._video_controls_frame.grid(row=1, column=1)

        # pause
        self._video_pause_button = ButtonToolTip(
            master=self._video_controls_frame,
            text='◼',
            command=self.toggle_pause,
            width=self._width,
            helptext='Pause/unpause video'
        )
        self._video_pause_button.grid(row=0, column=0, padx=self._padx, pady=self._pady)

        # restart
        self._video_restart_button = ButtonToolTip(
            master=self._video_controls_frame,
            text='⟳',
            command=self.restart_camera,
            width=self._width,
            helptext='Restart camera stream'
        )
        self._video_restart_button.grid(row=0, column=1, padx=self._padx, pady=self._pady)

        # reset
        self._video_reset_button = ButtonToolTip(
            master=self._video_controls_frame,
            text='↺',
            command=self.reset_camera,
            width=self._width,
            helptext='Hardware reset camera and stop stream. '
            'Use "Restart camera" button to resume stream'
        )
        self._video_reset_button.grid(
            row=0, column=2, padx=self._padx, pady=self._pady)

        # resize
        self._video_resize_button = CheckButtonToolTip(
            master=self._video_controls_frame,
            text='⤢',
            command=self.resize_callback,
            width=self._width,
            helptext='Resize camera stream'
        )
        self._video_resize_button.grid(
            row=0, column=3, padx=self._padx, pady=self._pady)
        # endregion WIDGETS

        # BINDINGS
        self._video_label.bind("<Motion>", self.get_coordinates)
        self._video_label.bind("<Button-1>", self.get_coordinates)
        self._video_label.bind("<Button-3>", self.get_coordinates)

        self.after(50, self.set_image)

    def set_image(self):
        if not self._paused:
            color_image = self._root.color_image
            if isinstance(color_image, np.ndarray):
                img_h = color_image.shape[0]
                img_w = color_image.shape[1]

                if (self._root.camera.width // img_w == self._root.camera.scale and
                        self._root.camera.height // img_h == self._root.camera.scale):
                    img = PIL.Image.fromarray(color_image)
                    imgtk = PIL.ImageTk.PhotoImage(image=img)

                    self._video_label.imgtk = imgtk
                    self._video_label.configure(image=imgtk)
                    self._video_label.update()
                    self.set_active_mask()

        self.after(50, self.set_image)

    def pause(self):
        self._paused = True
        self.set_pause_symbol()

    def unpause(self):
        self._paused = False
        self.set_pause_symbol()

    def toggle_pause(self):
        self._paused = not self._paused
        self.set_pause_symbol()
        if self._paused:
            if self._root.camera.connected:
                self._root.camera.stop()
        else:
            if not self._root.camera.connected:
                self._root.camera.start()
        return self._paused

    def set_pause_symbol(self):
        symbol = '▶' if self._paused else '◼'
        status = 'paused' if self._paused else 'running'
        self.set_status(status)
        self._video_pause_button['text'] = symbol
        self.update_idletasks()

    def mask_reset(self):
        if self._roi_select_all.get():
            title = "Clear region of interests"
            msg = "Do you want to clear all region of interests?"
            if messagebox.askokcancel(title, msg):
                for i in range(len(self._root.masks)):
                    self._root.masks[i].reset()
        else:
            self._root.masks[self.roi_select].reset()

    def mask_undo(self):
        self._root.masks[self.roi_select].undo()

    def mask_see_raw(self):
        if self._roi_select_all.get():
            for i in range(len(self._root.masks)):
                self._root.terminal.write(self._root.masks[i].coordinates)
        else:
            self._root.terminal.write(self._root.masks[self.roi_select].coordinates)

    def mask_see_all(self):
        pass

    def mask_complete(self):
        self._root.masks[self.roi_select].complete()

    def restart_camera(self):
        self.pause()
        self._root.camera.restart()
        self.unpause()
        self._root.settings.sync()

    def reset_camera(self):
        self.pause()
        self._video_reset_button['state'] = 'disabled'
        self._root.camera.reset()
        self._video_reset_button['state'] = 'enabled'
        self._root.settings.sync()

    def resize_callback(self):
        self.pause()
        if self._root.camera.scale <= 1:
            self._root.camera.scale = 2
        elif self._root.camera.scale > 1:
            self._root.camera.scale = 1
        self._root.terminal.resize()
        self._root.settings.resize()
        self.resize()
        self._root.resize()
        self.unpause()

    def resize(self):
        if self._root.camera.scale > 1:
            self._padx = 0
            self._pady = 0
            self._width = 0
            self._border = 0
        else:
            self._padx = 3
            self._pady = 3
            self._width = 4
            self._border = 3

        # video
        self._video_label.configure(border=self._border)

        # masks
        self._mask_control_frame.configure(border=self._border)
        self._mask_reset_button.configure(width=self._width)
        self._mask_undo_button.configure(width=self._width)
        self._mask_see_button.configure(width=self._width)
        self._mask_complete_button.configure(width=self._width)
        self._mask_see_all_button.configure(width=self._width)
        self._mask_select_combobox.configure(width=self._width)

        columns, rows = self._mask_control_frame.grid_size()
        for column in range(columns):
            self._mask_control_frame.columnconfigure(column, pad=self._padx)
        for row in range(rows):
            self._mask_control_frame.rowconfigure(row, pad=self._pady)

        # camera
        self._video_controls_frame.configure(border=self._border)
        self._video_pause_button.configure(width=self._width)
        self._video_restart_button.configure(width=self._width)
        self._video_reset_button.configure(width=self._width)
        self._video_resize_button.configure(width=self._width)

        columns, rows = self._video_controls_frame.grid_size()
        for column in range(columns):
            self._video_controls_frame.columnconfigure(column, pad=self._padx)
        for row in range(rows):
            self._video_controls_frame.rowconfigure(row, pad=self._pady)

    def set_status(self, status):
        self.configure(text=f'video ({status})')

    def get_coordinates(self, *args, **kwargs):
        if not self._paused:
            self._root.masks[self.roi_select].get_coordinates(*args, **kwargs)

    def set_active_mask(self):
        for i in range(len(self._root.masks)):
            activate = i == self._roi_select.get() - 1
            if activate:
                self._root.masks[i].active = True
            else:
                self._root.masks[i].active = False

    @property
    def paused(self):
        return self._paused

    @property
    def roi_select(self):
        return self._roi_select.get() - 1

    @property
    def roi_select_all(self):
        return self._roi_select_all.get()
