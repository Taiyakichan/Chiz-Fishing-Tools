import threading
import time
import keyboard

from nte_auto_fish.config.app_config import ConfigManager
from nte_auto_fish.config.roi import game_viewport, scale_roi
from nte_auto_fish.core.engine import FishingEngine
from nte_auto_fish.drivers.input_manager import InputManager
from nte_auto_fish.drivers.screen_capture import ScreenCapture
from nte_auto_fish.drivers.window_manager import WindowManager
from nte_auto_fish.gui.app import NTEFishingBotGUI
from nte_auto_fish.gui.bridge import BotBridge
from nte_auto_fish.gui.roi_picker import TkRoiPicker, TkRoiPreview
from nte_auto_fish.utils.logger import setup_logging
from nte_auto_fish.vision.detector import UIDetector
from nte_auto_fish.vision.tracker import ObjectTracker


class Drivers:
    def __init__(self):
        self.window = WindowManager()
        self.capture = ScreenCapture()
        self.input = InputManager()


class Vision:
    def __init__(self):
        self.tracker = ObjectTracker()
        self.detector = UIDetector()


class NteBotController(NTEFishingBotGUI):
    def __init__(self):
        super().__init__()
        self.bot_config = ConfigManager()
        self.bridge = BotBridge()
        self.log_manager = setup_logging(self.bridge)
        self.drivers = Drivers()
        self.vision = Vision()
        self.engine = FishingEngine(self.drivers, self.vision, self.bot_config, self.bridge)

        self._game_found = self.drivers.window.find_window()
        if self._game_found:
            self._log("Game found.")
        else:
            self._log("Ready to start.", important=True)

        self._load_settings_to_ui(self.bot_config)
        self._refresh_setup_status()
        if self.bot_config.loaded_default_template:
            self._log("Default config loaded. Save once after setup.", important=True)

        self.poller_running = True
        threading.Thread(target=self._bridge_poller, daemon=True).start()
        
        # Global Hotkeys: F1 to start, F2 to stop
        def _hk_start(): self.after(0, self._on_start)
        def _hk_stop(): self.after(0, self._on_stop)
        keyboard.add_hotkey('f1', _hk_start)
        keyboard.add_hotkey('f2', _hk_stop)

    def _bridge_poller(self):
        while self.poller_running:
            status = self.bridge.poll_status()
            if status:
                self.after(0, lambda s=status: self._apply_engine_status(s))

            log_line = self.bridge.poll_log()
            if log_line:
                self.log(log_line)
            time.sleep(0.08)

    def _apply_engine_status(self, status):
        if status.state == "ERROR" and getattr(self, "_running", False):
            self._on_stop()
        elif status.state != "ERROR":
            self.set_state(status.state)

        self._catch_count = status.fish_caught
        self._catch_card.set(f"{status.fish_caught:03d}")

    def _on_calibrate_bar(self):
        self.engine.stop()
        super()._on_calibrate_bar()
        picker = TkRoiPicker(
            lambda roi: self._save_calibration(roi, "bar"),
            prompt="Drag to select FISHING BAR area",
            color="#f0d8e8",
        )
        picker.show()

    def _on_calibrate_banner(self):
        self.engine.stop()
        super()._on_calibrate_banner()
        picker = TkRoiPicker(
            lambda roi: self._save_calibration(roi, "banner"),
            prompt="Drag to select BANNER area (where white text appears)",
            color="#65DBFF",
        )
        picker.show()

    def _on_calibrate_button(self):
        self.engine.stop()
        super()._on_calibrate_button()
        picker = TkRoiPicker(
            lambda roi: self._save_calibration(roi, "button"),
            prompt="Drag to select HOOK BUTTON area",
            color="#FFB86C",
        )
        picker.show()

    def _save_calibration(self, roi, target_key):
        self.drivers.window.find_window()
        rect_x, rect_y, width, height = self.drivers.window.get_client_rect()
        if width <= 0 or height <= 0:
            self.log("ERROR: Game window not found during calibration!", important=True)
            return

        viewport = game_viewport(width, height)
        viewport_left = rect_x + viewport["left"]
        viewport_top = rect_y + viewport["top"]
        self.bot_config.rois[target_key] = {
            "left": (roi["left"] - viewport_left) / float(viewport["width"]),
            "top": (roi["top"] - viewport_top) / float(viewport["height"]),
            "width": roi["width"] / float(viewport["width"]),
            "height": roi["height"] / float(viewport["height"]),
        }
        self.bot_config.save()
        self._refresh_setup_status()
        self.log("ROI saved.", important=True)
        self._update_footer("* Standby - ROI locked")

    def _on_start(self):
        if not self._startup_ready():
            return
        # Clear stale terminal states from the polling cache so it doesn't instantly auto-stop again!
        if self.bridge.last_status and self.bridge.last_status.state == "ERROR":
            self.bridge.last_status.state = "IDLE"
            
        super()._on_start()
        self.engine.start()
        self._update_footer("* Engine running - ROI locked")

    def _on_stop(self):
        super()._on_stop()
        self.engine.stop()
        self._update_footer("* Engine stopped")

    def _on_save_settings(self):
        self._save_settings_from_ui(self.bot_config)
        self._refresh_setup_status()
        self._update_footer("* Settings saved locally")

    def _on_preview_rois(self):
        self.engine.stop()
        self._game_found = self.drivers.window.find_window()
        self._refresh_setup_status()
        if not self._game_found:
            self.log("Game window not found.", important=True)
            return

        client_rect = self.drivers.window.get_client_rect()
        rois = {}
        for name in ("bar", "banner", "button"):
            rois[name] = scale_roi(self.bot_config.get_roi(name), client_rect)
        preview = TkRoiPreview(rois)
        preview.show()

    def _on_find_game(self):
        self._game_found = self.drivers.window.find_window()
        self._refresh_setup_status()
        if self._game_found:
            self.log("Game found.", important=True)
        else:
            self.log("Game window not found.", important=True)

    def _on_test_hook(self):
        key = self._set_hook_key.get().strip() or self.bot_config.settings.get("hook_key", "f")
        if self.drivers.window.find_window():
            self.drivers.window.activate()
        self.drivers.input.press(key, duration=0.05, jitter=0.0)
        self.log(f"Tested hook key: {key}", important=True)

    def _on_test_close(self):
        key = self._set_close_key.get().strip() or self.bot_config.settings.get("close_key", "escape")
        if self.drivers.window.find_window():
            self.drivers.window.activate()
        self.drivers.input.press(key, duration=0.05, jitter=0.0)
        self.log(f"Tested close key: {key}", important=True)

    def _on_release_controls(self):
        self.drivers.input.release_all()
        self.log("Controls are safe.", important=True)

    def _startup_ready(self):
        self._game_found = self.drivers.window.find_window()
        self._refresh_setup_status()
        if not self._game_found:
            self.log("Game window not found.", important=True)
            self._update_footer("* Start blocked - game missing")
            return False

        missing = [name for name in ("bar", "banner") if not self._roi_ready(name)]
        if missing:
            self.log(f"Calibrate missing area: {', '.join(missing)}", important=True)
            self._update_footer("* Start blocked - ROI missing")
            return False

        if not self._save_settings_from_ui(self.bot_config):
            self._update_footer("* Start blocked - settings invalid")
            return False
        self._refresh_setup_status()
        return True

    def _roi_ready(self, name):
        roi = self.bot_config.rois.get(name)
        if not isinstance(roi, dict):
            return False
        return all(float(roi.get(field, 0)) > 0 for field in ("width", "height"))

    def _roi_summary(self):
        button = self.bot_config.rois.get("button", {})
        return {
            "bar": self._roi_ready("bar"),
            "banner": self._roi_ready("banner"),
            "button": self._roi_ready("button"),
            "button_calibrated": isinstance(button.get("left"), (float, int)) and float(button.get("left", 0)) <= 1.0,
        }

    def _refresh_setup_status(self):
        self.set_roi_status(self._roi_ready("bar") and self._roi_ready("banner"))
        self.set_setup_status(
            config_saved=self.bot_config.has_local_config,
            game_found=self._game_found,
            rois=self._roi_summary(),
        )

    def on_closing(self):
        self.poller_running = False
        keyboard.unhook_all_hotkeys()
        self.engine.stop()
        self.destroy()
