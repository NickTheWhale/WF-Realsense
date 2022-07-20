import threading
import time

from frames.appwindow import AppWindow

# constants
LOOP_DELAY = 1  # sleep time in ms between update loops

class App(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__ready = False
        self.start()

    def run(self):
        self.__app = AppWindow("ROI Utility")
        self.__app.protocol("WM_DELETE_WINDOW", self.__app.on_closing)
        self.__ready = True
        self.__app.mainloop()

    @property
    def ready(self):
        return self.__ready

    @property
    def root(self):
        return self.__app

def main():
    app = App()

    while not app.ready:
        time.sleep(0.1)

    # while app.is_alive():
    #     app.root.loop()
    #     if LOOP_DELAY > 0:
    #         time.sleep(LOOP_DELAY / 1000)
    #     else:
    #         pass


if __name__ == "__main__":
    main()
