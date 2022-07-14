import tkinter as tk
import PIL.Image
import PIL.ImageTk


class AppVideo(tk.Frame):
    def __init__(self, root, row, column, rowspan=1, columnspan=1, sticky="NSEW"):
        super().__init__()
        self.__root = root
        self.__main_frame = self.__root.main_frame
        self.__row = row
        self.__column = column
        self.__columnspan = columnspan
        self.__rowspan = rowspan
        self.__sticky = sticky

        self.__create_widgets()

    def __create_widgets(self):
        self.__video_frame = tk.Frame(self.__main_frame)
        self.__video_frame.grid(row=self.__row,
                                column=self.__column,
                                rowspan=self.__rowspan,
                                columnspan=self.__columnspan,
                                sticky=self.__sticky)

        self.__video_label = tk.Label(self.__video_frame, cursor="tcross")
        self.__video_label.bind("<Motion>", self.__root.mask_widget.get_coordinates)
        self.__video_label.bind("<Button-1>", self.__root.mask_widget.get_coordinates)
        self.__video_label.bind("<Button-3>", self.__root.mask_widget.get_coordinates)

        self.__video_label.grid(row=0, column=0)

    def set_image(self, color_image):
        img = PIL.Image.fromarray(color_image)
        imgtk = PIL.ImageTk.PhotoImage(image=img)

        self.__video_label.imgtk = imgtk
        self.__video_label.configure(image=imgtk)
        self.__video_label.update()   # update main frame?

        return imgtk
