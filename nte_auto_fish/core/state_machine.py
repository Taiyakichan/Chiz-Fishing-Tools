from enum import Enum
import time

class FishingState(Enum):
    IDLE = "IDLE"           # Not fishing, ready to cast
    CASTING = "CASTING"     # Key pressed, waiting for animation
    WAITING = "WAITING"     # Line in water, waiting for bite (blue)
    HOOKING = "HOOKING"     # Bite detected, pressing hook key
    STRUGGLING = "STRUGGLING" # Playing minigame
    RESULT = "RESULT"       # Success/Failure screen
    ERROR = "ERROR"         # Dialog box/Lost connection

class FishingStateMachine:
    def __init__(self):
        self._state = FishingState.IDLE
        self._last_transition = time.time()

    @property
    def state(self) -> FishingState:
        return self._state

    @property
    def time_in_state(self) -> float:
        return time.time() - self._last_transition

    def transition(self, new_state: FishingState):
        if self._state == new_state:
            return
        # Transitioning...
        self._state = new_state
        self._last_transition = time.time()
