from tkinter import Frame
import cv2
import numpy as np
import pyrealsense2 as rs
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.filedialog as tkFileDialog
from tkinter.constants import LEFT, TRUE
from tkinter import ttk
from time import sleep
from pathlib import Path

class Application:
    def __init__(self):
        self.window = tk.Tk()
        self.window['bg'] = '#002A54'
        self.window.title("tkinter + pyrealsense recorder")
        self.window.protocol('WM_DELETE_WINDOW', self.destructor)

        self.combo = ttk.Combobox(self.window, values=["Color","Depth"], state="readonly", postcommand=self.combo_changed)
        self.combo.current(0)
        self.combo.pack(side="top", fill="x", padx="5", pady="5")

        self.mainImage = tk.Label(master=self.window)
        self.mainImage.pack(side="top", fill="both", expand="yes", padx="5", pady="5")

        self.fr_buttons = tk.Frame(self.window, bg=self.window["bg"])
        self.fr_buttons.pack(side="bottom", fill="x")
        openButton = tk.Button(self.fr_buttons, text="Record", padx=10, pady=5, command=self.record_bag)        
        openButton.pack(side="left", fill="x", expand="yes", padx="5", pady="5")
        stopButton = tk.Button(self.fr_buttons, text="Stop", padx=10, pady=5, command=self.stop_bag)        
        stopButton.pack(side="left", fill="x", expand="yes", padx="5", pady="5")
        self.recording = False
        self.pipeline = None
        self.recoder = None

    def destructor(self):
        """ Destroy the root object and release all resources """
        print("[INFO] closing...")
        if self.pipeline is not None:
            self.recording = False
            sleep(0.1)
            self.pipeline.stop()
            self.pipeline = None
        self.window.destroy()
        cv2.destroyAllWindows()  # it is not mandatory in this application
    
    def combo_changed(self):
        self.combo.update()
        
    def record_bag(self):
        if self.pipeline is None:
            self.pipeline = rs.pipeline()
        else:
            self.pipeline.stop()
            self.pipeline = rs.pipeline()
        path = tkFileDialog.asksaveasfilename(initialdir="C:/rosbag/", 
                                              filetypes = (("bag files","*.bag"),
                                                           ("all files","*.*")))
        print(path)
        try:
            # Config pipeline
            config = rs.config()
            rs.config.enable_record_to_file(config, path)
            config.enable_stream(rs.stream.depth)
            config.enable_stream(rs.stream.color)
            profile = self.pipeline.start(config)
          
            colorizer = rs.colorizer()

            self.recorder = profile.get_device().as_recorder()

            n = 0
            #Thread sleep so the stream has time to start recording
            self.recording = True
            sleep(0.1)           
            while (self.recording):
                n += 1
                frames=self.pipeline.wait_for_frames()

                if self.combo.current() == 1:
                    # Just Depth frame
                    depth_frame = frames.get_depth_frame()
                    if not depth_frame: continue
                    depth_color_frame = colorizer.colorize(depth_frame)
                    color_image = np.asanyarray(depth_color_frame.get_data())
                else:
                    #if self.combo.current() == "Color":
                    # Just Color frame
                    color_frame = frames.get_color_frame()
                    if not color_frame: continue
                    color_image = np.asanyarray(color_frame.get_data())
                
                img = Image.fromarray(color_image)
                imgtk = ImageTk.PhotoImage(image=img)
                self.mainImage.imgtk = imgtk
                self.mainImage.configure(image=imgtk)
                self.mainImage.update()            
        finally:
            pass

    def stop_bag(self):
        if self.pipeline is not None:
            self.recording = False
            print("Stopping...")
            sleep(10)
            self.pipeline.stop()
            self.pipeline = None
            print("Stopped")

print("[INFO] starting...")
pba = Application()
pba.window.mainloop()  