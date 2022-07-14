import threading
import time
from appwindow import AppWindow


# constants

LOOP_DELAY = 50  # sleep time in ms between update loops


class App(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__ready = False
        self.start()

    def run(self):
        self.__app = AppWindow("ROI Utility")
        self.__ready = True
        self.__app.protocol("WM_DELETE_WINDOW", self.__app.on_closing)
        self.__app.mainloop()

    @property
    def ready(self):
        return self.__ready

    @property
    def app_window(self):
        return self.__app


def main():
    try:
        app = App()
    except RuntimeError as e:
        print(e)
    else:
        while not app.ready:
            time.sleep(0.1)
        while app.is_alive():
            # print("its alive")
            app.app_window.update()
            time.sleep(LOOP_DELAY / 1000)
        print("exited program")


if __name__ == "__main__":
    main()


def old_main():
    try:
        app = AppWindow("ROI Utility")
    except RuntimeError as e:
        print(e)
    else:
        # gui loop
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
