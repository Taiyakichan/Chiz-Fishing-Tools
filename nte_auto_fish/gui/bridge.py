import queue
from dataclasses import dataclass
from typing import Optional

@dataclass
class EngineStatus:
    state: str
    fish_caught: int
    session_time: str
    fps: float
    current_x: Optional[float]
    target_x: Optional[float]
    pid_power: float = 0.0
    banner_pixels: int = 0
    button_pixels: int = 0
    target_pixels: int = 0
    log_message: Optional[str] = None

class BotBridge:
    """Thread-safe conduit between GUI and Engine."""
    
    def __init__(self):
        self.cmd_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        self.last_status: Optional[EngineStatus] = None

    def push_command(self, cmd: str, args: Optional[dict] = None):
        self.cmd_queue.put({"cmd": cmd, "args": args})

    def poll_command(self) -> Optional[dict]:
        try:
            return self.cmd_queue.get_nowait()
        except queue.Empty:
            return None

    def push_status(self, status: EngineStatus):
        self.status_queue.put(status)

    def poll_status(self) -> Optional[EngineStatus]:
        # Get the latest new status only (clear the queue if multiple are backed up).
        last = None
        while not self.status_queue.empty():
            last = self.status_queue.get_nowait()
        if last:
            self.last_status = last
        return last

    def push_log(self, msg: str):
        self.log_queue.put(msg)

    def poll_log(self) -> Optional[str]:
        try:
            return self.log_queue.get_nowait()
        except queue.Empty:
            return None
