import threading
import mss
import numpy as np
from typing import Dict, Any

class ScreenCapture:
    """Thread-safe screen capture driver using thread-local MSS instances."""
    
    def __init__(self):
        # We use threading.local() because MSS handles are not always 
        # cross-thread compatible on Windows.
        self._local = threading.local()

    def _get_sct(self) -> Any:
        """Get or create the thread-local MSS instance."""
        if not hasattr(self._local, "sct") or self._local.sct is None:
            self._local.sct = mss.mss()
        return self._local.sct

    def grab(self, region: Dict[str, Any]) -> np.ndarray:
        """
        Grab a screen region and return a BGR numpy array.
        Includes safety logic for Windows GDI 'Access Denied' errors.
        """
        # Ensure integer coordinates (PyInstaller/JSON can sometimes feed floats)
        reg = {
            "top": int(region.get("top", 0)),
            "left": int(region.get("left", 0)),
            "width": max(1, int(region.get("width", 1))),
            "height": max(1, int(region.get("height", 1)))
        }
        
        sct = self._get_sct()
        for attempt in range(3):
            try:
                screenshot = sct.grab(reg)
                img = np.array(screenshot)
                return img[:, :, :3]
            except Exception as e:
                # Common on Windows: CreateDIBSection Access Denied
                # Often happens when the system is under load or switching contexts
                if attempt < 2:
                    threading.Event().wait(0.2) # Small backoff
                    self._local.sct = mss.mss()
                    sct = self._local.sct
                    continue
                raise e
        return np.zeros((reg["height"], reg["width"], 3), dtype=np.uint8)

    def close(self):
        """Release current thread's MSS resource."""
        if hasattr(self._local, "sct") and self._local.sct is not None:
            self._local.sct.close()
            self._local.sct = None
