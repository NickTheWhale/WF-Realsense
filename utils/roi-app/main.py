import os
import sys
from pathlib import Path
from frames.appwindow import AppWindow
try:
    import pyi_splash
except ImportError:
    pass


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
    raw_path = get_program_path()

    path = Path(raw_path)

    # print('raw', raw_path)
    # print('parent', path.parent)

    try:
        app = AppWindow("ROI Utility", raw_path)
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
    except:
        try:
            pyi_splash.close()
        except Exception:
            pass
        raise

    # theme
    # app.tk.call('source', 'theme\\azure.tcl')
    # app.tk.call('set_theme', 'light')
    
    else:
        try:
            pyi_splash.close()
        except Exception:
            pass

        app.mainloop()
        app.destroy()


if __name__ == "__main__":
    main()
