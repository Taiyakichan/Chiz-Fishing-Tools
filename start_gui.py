import ctypes
import sys
import os
import subprocess
from nte_auto_fish.gui.controller import NteBotController


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except (AttributeError, OSError):
        return False

def main():
    # Set working directory to the location of the EXE or Script
    if getattr(sys, 'frozen', False):
        app_root = os.path.dirname(sys.executable)
    else:
        app_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_root)

    # Force DPI Awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass

    if not is_admin():
        # Re-run the active entrypoint with admin rights using properly quoted arguments.
        entrypoint = os.path.abspath(sys.argv[0])
        params = subprocess.list2cmdline([entrypoint, *sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

    app = NteBotController()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
