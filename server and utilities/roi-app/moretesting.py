from tkinter import *
import random
from random import randint 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
import threading
from datetime import datetime

continuePlotting = False

def change_state():
    global continuePlotting
    if continuePlotting == True:
        continuePlotting = False
    else:
        continuePlotting = True    

def data_points():
    yList = []
    for x in range (0, 20):
        yList.append(random.randint(0, 100))

    return yList

def app():
    # initialise a window and creating the GUI
    root = Tk()
    root.config(background='white')
    root.geometry("1000x700")

    lab = Label(root, text="Live Plotting", bg = 'white').pack()

    fig = Figure()

    ax = fig.add_subplot(111)
    ax.set_ylim(0,100)
    ax.set_xlim(1,30)
    ax.grid()

    graph = FigureCanvasTkAgg(fig, master=root)
    graph.get_tk_widget().pack(side="top",fill='both',expand=True)

    # Updated the Canvas 
    def plotter():
        while continuePlotting:
            ax.cla()
            ax.grid()
            ax.set_ylim(0,100)
            ax.set_xlim(1,20)

            dpts = data_points()
            ax.plot(range(20), dpts, marker='o', color='orange')
            graph.draw()
            time.sleep(1)

    def gui_handler():
        change_state()
        threading.Thread(target=plotter).start()

    b = Button(root, text="Start/Stop", command=gui_handler, bg="red", fg="white")
    b.pack()

    root.mainloop()

if __name__ == '__main__':
    app()