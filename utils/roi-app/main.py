import os
import sys

from frames.appwindow import AppWindow


def get_program_path() -> str:
    """gets full path name of program. Works if 
    program is frozen

    :return: path
    :rtype: string
    """
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    elif __file__:
        path = os.path.dirname(__file__)
    return path


def main():
    path = get_program_path()

    app = AppWindow("ROI Utility", path)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    # theme
    # app.tk.call('source', 'theme\\azure.tcl')
    # app.tk.call('set_theme', 'light')

    app.mainloop()


if __name__ == "__main__":
    main()
