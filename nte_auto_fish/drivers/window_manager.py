import ctypes
import logging
import time
from typing import Optional, Tuple

import win32api
import win32con
import win32gui
import win32process

log = logging.getLogger("NTE.WindowManager")

class WindowManager:
    def __init__(self, process_name: str = "HTGame.exe"):
        self.process_name = process_name
        self.hwnd: Optional[int] = None
        
        # Ensure process is DPI aware for correct coordinate mapping
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def find_window(self) -> bool:
        """Find the game window by its process name using native Win32 APIs."""
        hwnds = []

        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    handle = win32api.OpenProcess(
                        win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 
                        False, pid
                    )
                    name = win32process.GetModuleFileNameEx(handle, 0)
                    win32api.CloseHandle(handle)
                    if self.process_name.lower() in name.lower():
                        hwnds.append(hwnd)
                except Exception:
                    pass
            return True

        win32gui.EnumWindows(callback, None)
        
        if hwnds:
            self.hwnd = hwnds[0]
            log.info(f"Window found! HWND: {self.hwnd}")
            return True
        
        log.warning(f"Could not find window for process: {self.process_name}")
        return False

    def activate(self) -> bool:
        """Restore and bring the window to the foreground."""
        if not self.hwnd:
            return False
            
        try:
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
                
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.3) 
            return True
        except Exception as e:
            log.error(f"Failed to activate window: {e}")
            return False

    def get_client_rect(self) -> Tuple[int, int, int, int]:
        """Get the client area (x, y, width, height) in screen coordinates."""
        # Auto-retry finding window if missing
        if not self.hwnd:
            if not self.find_window():
                return 0, 0, 0, 0
            
        try:
            point = win32gui.ClientToScreen(self.hwnd, (0, 0))
            _, _, w, h = win32gui.GetClientRect(self.hwnd)
            return point[0], point[1], w, h
        except Exception:
            self.hwnd = None # Reset on failure to trigger re-find
            return 0, 0, 0, 0

    def is_active(self) -> bool:
        """Check if the game window is currently the foreground window."""
        if not self.hwnd:
            return False
        return win32gui.GetForegroundWindow() == self.hwnd
