import random
import time
import pydirectinput
from typing import Set

# High performance mode for controls
pydirectinput.PAUSE = 0.0

class InputManager:
    """Handles humanized keyboard and mouse inputs."""
    
    def __init__(self):
        self._held_keys: Set[str] = set()

    def press(self, key: str, duration: float = 0.08, jitter: float = 0.05):
        """Press and release a key with slight randomization."""
        press_time = duration + random.uniform(-jitter, jitter)
        press_time = max(0.02, press_time)
        
        pydirectinput.keyDown(key)
        time.sleep(press_time)
        pydirectinput.keyUp(key)

    def keyDown(self, key: str):
        if key not in self._held_keys:
            pydirectinput.keyDown(key)
            self._held_keys.add(key)

    def keyUp(self, key: str):
        if key in self._held_keys:
            pydirectinput.keyUp(key)
            self._held_keys.discard(key)

    def release_all(self):
        """Emergency release of all held keys."""
        for key in list(self._held_keys):
            self.keyUp(key)

    def click(self, x: int, y: int):
        """Perform a mouse click at screen coordinates."""
        pydirectinput.click(x, y)
