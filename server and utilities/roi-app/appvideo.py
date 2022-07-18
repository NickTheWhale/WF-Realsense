from tkinter import ttk
import PIL.Image
import PIL.ImageTk

class AppVideo(ttk.Labelframe):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._root = self._args[0]
        super().__init__(*args, **kwargs)
        
        self.configure(text='video', border=10)
        
        self._paused = False

        # video
        self._video_label = ttk.Label(self, cursor="tcross")
        self._video_label.grid(row=0, column=0)
        
        # mask controls
        self._mask_control_frame = ttk.Labelframe(
            master=self,
            text='mask controls',
            border=10
        )
        self._mask_control_frame.grid(row=1, column=0)
        
        self._mask_reset_button = ttk.Button(
            master=self._mask_control_frame,
            text=u"\u21BA", # counterclockwise undo arrow
            command=self.mask_reset,
            width=3
        )
        
        self._mask_undo_button = ttk.Button(
            master=self._mask_control_frame,
            text=u"\u238C", # undo unicode
            command=self.mask_undo,
            width=3
        )
        
        self._mask_see_raw_button = ttk.Button(
            master=self._mask_control_frame,
            text=u"\U0001F453", # glasses unicode
            command=self.mask_see_raw,
            width=3
        )
        self._mask_reset_button.grid(row=0, column=0, padx=3)
        self._mask_undo_button.grid(row=0, column=1, padx=3)
        self._mask_see_raw_button.grid(row=0, column=2, padx=3)
        
        # video controls
        self._video_control_frame = ttk.Labelframe(
            master=self,
            text='video controls',
            border=10
        )
        self._video_control_frame.grid(row=1, column=1)
        
        self._video_pause_button = ttk.Button(
            master=self._video_control_frame,
            text='◼'
        )
        self._video_pause_button.grid(row=0, column=0)

        # bindings
        self._video_label.bind("<Motion>", self._root.mask.get_coordinates)
        self._video_label.bind("<Button-1>", self._root.mask.get_coordinates)
        self._video_label.bind("<Button-3>", self._root.mask.get_coordinates)


    def set_image(self, color_image):
        if not self._paused:
            img = PIL.Image.fromarray(color_image)
            imgtk = PIL.ImageTk.PhotoImage(image=img)

            self._video_label.imgtk = imgtk
            self._video_label.configure(image=imgtk)
            self._video_label.update()

        
    def toggle_paused(self):
        self._paused = not self._paused
        symbol = '▶' if self._paused else '◼'
        self._video_pause_button['text'] = symbol

    def mask_reset(self):
        self._root.mask_reset()
        
    def mask_undo(self):
        self._root.mask_undo()
        
    def mask_see_raw(self):
        print(self._root.mask.coordinates)