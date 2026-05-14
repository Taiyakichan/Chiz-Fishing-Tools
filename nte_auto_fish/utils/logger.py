import logging
from typing import Optional
from nte_auto_fish.gui.bridge import BotBridge

class LogBridgeHandler(logging.Handler):
    """Sends log records to the BotBridge queue for GUI display."""
    
    def __init__(self, bridge: BotBridge):
        super().__init__()
        self.bridge = bridge
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.bridge.push_log(msg)
        except Exception:
            self.handleError(record)

def setup_logging(bridge: Optional[BotBridge] = None):
    """Configure the root logger with standard and bridge handlers."""
    root_log = logging.getLogger("NTE")
    root_log.setLevel(logging.DEBUG)
    root_log.handlers.clear()
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
    root_log.addHandler(ch)
    
    # Bridge handler (if bridge provided)
    if bridge:
        bh = LogBridgeHandler(bridge)
        root_log.addHandler(bh)
    
    return root_log
