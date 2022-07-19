from tkinter import ttk
from tooltip import ButtonToolTip

import PIL.Image
import PIL.ImageTk
import numpy as np


class AppVideo(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)

        self.configure(text='video', border=10)

        self._paused = False

        # video
        self._video_label = ttk.Label(
            master=self,
            cursor="tcross",
            relief="sunken",
            border=2
        )
        self._video_label.grid(row=0, column=0, columnspan=2)

        # MASK CONTROLS
        self._mask_control_frame = ttk.Labelframe(self, text='mask controls', border=5)
        self._mask_control_frame.grid(row=1, column=0)

        # reset
        self._mask_reset_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='↺',
            command=self.mask_reset,
            width=3,
            helptext='Reset (clear) current mask'
        )
        self._mask_reset_button.grid(row=0, column=0, padx=3)

        # undo
        self._mask_undo_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='⎌',
            command=self.mask_undo,
            width=3,
            helptext='Undo last mask command'
        )
        self._mask_undo_button.grid(row=0, column=1, padx=3)

        # see
        self._mask_see_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='👓',
            command=self.mask_see_raw,
            width=3,
            helptext='Output list of coordinates to terminal'
        )
        self._mask_see_button.grid(row=0, column=2, padx=3)
        
        # complete
        self._mask_complete_button = ButtonToolTip(
            master=self._mask_control_frame,
            text='✓',
            command=self.mask_complete,
            width=3,
            helptext='Complete (close) mask'
        )
        self._mask_complete_button.grid(row=0, column=3, padx=3)

        # VIDEO CONTROLS
        self._video_controls_frame = ttk.Labelframe(self, text='video controls', border=5)
        self._video_controls_frame.grid(row=1, column=1)

        # pause
        self._video_pause_button = ButtonToolTip(
            master=self._video_controls_frame,
            text='◼',
            command=self.toggle_pause,
            width=3,
            helptext='Pause/unpause video'
        )
        self._video_pause_button.grid(row=0, column=0, padx=3)

        # restart
        self._video_restart_button = ButtonToolTip(
            master=self._video_controls_frame,
            text='⟳',
            command=self.restart_camera,
            width=3,
            helptext='Restart camera stream'
        )
        self._video_restart_button.grid(row=0, column=1, padx=3)

        # reset
        self._camera_reset_button = ButtonToolTip(
            master=self._video_controls_frame,
            text='↺',
            command=self.reset_camera,
            width=3,
            helptext='Hardware reset camera and stop stream. '
            'Use "Restart camera" button to resume stream'
        )
        self._camera_reset_button.grid(row=0, column=2, padx=3)

        # BINDINGS
        self._video_label.bind("<Motion>", self.get_coordinates)
        self._video_label.bind("<Button-1>", self.get_coordinates)
        self._video_label.bind("<Button-3>", self.get_coordinates)

        self.after(50, self.set_image)

    def set_image(self):
        if not self._paused:
            color_image = self._root.color_image
            if isinstance(color_image, np.ndarray):
                img = PIL.Image.fromarray(color_image)
                imgtk = PIL.ImageTk.PhotoImage(image=img)

                self._video_label.imgtk = imgtk
                self._video_label.configure(image=imgtk)
                self._video_label.update()
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
        self._video_pause_button['text'] = symbol

    def mask_reset(self):
        self._root.mask_reset()

    def mask_undo(self):
        self._root.mask_undo()

    def mask_see_raw(self):
        self._root.terminal.write(self._root.mask.coordinates)
    
    def mask_complete(self):
        self._root.mask.complete()

    def restart_camera(self):
        self._root.camera.restart()

    def reset_camera(self):
        self._camera_reset_button['state'] = 'disabled'
        self._root.camera.reset()
        self._camera_reset_button['state'] = 'enabled'

    def get_coordinates(self, *args, **kwargs):
        if not self._paused:
            self._root.mask.get_coordinates(*args, **kwargs)

    @property
    def paused(self):
        return self._paused
