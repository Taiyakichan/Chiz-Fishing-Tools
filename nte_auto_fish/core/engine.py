import logging
import time
import threading
import random
import os
import cv2
from typing import Optional, Any
import win32api
import win32process

from nte_auto_fish.core.state_machine import FishingState, FishingStateMachine
from nte_auto_fish.core.pid_controller import PIDController
from nte_auto_fish.config.roi import scale_roi

log = logging.getLogger("NTE.Engine")

LOW_ACTIVITY_STATES = {FishingState.IDLE, FishingState.WAITING, FishingState.RESULT}
NO_BAIT_CHECK_SECONDS = 2.5
NO_BAIT_CHECK_INTERVAL = 0.1
NO_BAIT_TEMPLATE_THRESHOLD = 0.55
RESULT_LOST_AFTER_SECONDS = 3.0
BAR_APPEAR_TIMEOUT_SECONDS = 8.5
GOLDEN_FISH_SECONDS = 11.0

class FishingEngine:
    def __init__(self, drivers: Any, vision: Any, config: Any, bridge: Optional[Any] = None):
        self.drivers = drivers
        self.vision = vision
        self.config = config
        self.bridge = bridge
        
        self.sm = FishingStateMachine()
        self.pid = PIDController()
        
        self._last_cur_norm: Optional[float] = None
        self._last_tgt_norm: Optional[float] = None
        self._last_pid_power: float = 0.0
        self._last_banner_pixels: int = 0
        self._last_button_pixels: int = 0
        self._last_target_pixels: int = 0
        
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        self.fish_caught = 0
        self.session_start = 0.0

    def start(self):
        if self._running: return
        self._running = True
        self._stop_event.clear()
        self.fish_caught = 0  # CRITICAL: Reset catch counter back to 0 on a fresh start!
        self.sm.transition(FishingState.IDLE) # Force a hard reset to IDLE!
        self.session_start = time.time()
        
        # Set process priority to High
        try:
            win32process.SetPriorityClass(win32api.GetCurrentProcess(), win32process.HIGH_PRIORITY_CLASS)
        except win32api.error:
            pass

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        log.info("Engine thread started.")

    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._thread and threading.current_thread() != self._thread:
            self._thread.join(timeout=1.0)
        self.drivers.input.release_all()
        log.info("Engine thread stopped.")

    def _run_loop(self):
        while self._running:
            try:
                if not self.drivers.window.is_active():
                    self.drivers.window.activate()
                    if self._wait_for_stop(1.0):
                        break
                    continue

                state = self.sm.state
                
                if state == FishingState.IDLE: self._handle_idle()
                elif state == FishingState.WAITING: self._handle_waiting()
                elif state == FishingState.STRUGGLING: self._handle_struggling()
                elif state == FishingState.RESULT: self._handle_result()
                
                self._push_status()

                self._sleep_after_state(state)

            except Exception as e:
                log.exception(f"Engine Loop Error: {e}")
                if self._wait_for_stop(1.0):
                    break

    def _wait_for_stop(self, seconds: float) -> bool:
        return self._stop_event.wait(max(0.0, seconds)) or not self._running

    def _poll_interval(self) -> float:
        try:
            interval = float(self.config.settings.get("poll_interval", 0.05))
        except (TypeError, ValueError, AttributeError):
            interval = 0.05
        return max(0.01, interval)

    def _sleep_after_state(self, state: FishingState):
        interval = self._poll_interval()
        if state in LOW_ACTIVITY_STATES:
            self._wait_for_stop(interval + random.uniform(0, min(0.02, interval * 0.4)))
            return
        self._wait_for_stop(max(0.01, interval * 0.2))

    def _grab_named_roi(self, name: str, label: str):
        roi = self._get_roi_abs(name)
        try:
            return self.drivers.capture.grab(roi)
        except Exception as e:
            log.warning(f"Grab failed ({label}): {e}")
            return None

    def _count_pixels(self, frame, lower, upper) -> int:
        return self.vision.tracker.check_pixel_count(frame, lower, upper)

    def _push_status(self):
        if not self.bridge: return
        from nte_auto_fish.gui.bridge import EngineStatus
        
        status = EngineStatus(
            state=self.sm.state.value,
            fish_caught=self.fish_caught,
            session_time="Running",
            fps=0.0,
            current_x=self._last_cur_norm,
            target_x=self._last_tgt_norm,
            pid_power=self._last_pid_power,
            banner_pixels=self._last_banner_pixels,
            button_pixels=self._last_button_pixels,
            target_pixels=self._last_target_pixels,
        )
        self.bridge.push_status(status)

    def _handle_idle(self):
        max_mins = self.config.settings.get("session_cap_min", 120)
        max_fish = self.config.settings.get("session_cap_fish", 0)
        elapsed = time.time() - getattr(self, "session_start", time.time())
        
        if (max_mins > 0 and elapsed >= max_mins * 60) or (max_fish > 0 and self.fish_caught >= max_fish):
            log.info("Session limit reached! Gracefully stopping.")
            self.sm.transition(FishingState.IDLE)
            self.stop()
            return
            
        log.info("Casting line...")
        self.sm.transition(FishingState.CASTING)
        hook_key = self.config.settings.get("hook_key", "f")
        duration = 0.1 + random.uniform(-0.02, 0.02)
        self.drivers.input.press(hook_key, duration=duration)
        
        # Check for NO BAIT template right after casting
        from nte_auto_fish.utils.resource import resource_path
        bait_path = resource_path("assets/no_bait.png")
        if os.path.exists(bait_path):
            no_bait_tmpl = cv2.imread(bait_path)
            if no_bait_tmpl is not None:
                start_cast = time.time()
                found_bait_warning = False
                
                while self._running and time.time() - start_cast < NO_BAIT_CHECK_SECONDS:
                    try:
                        rect_x, rect_y, w, h = self.drivers.window.get_client_rect()
                        center_roi = {"left": rect_x + w//10, "top": int(rect_y + h*0.2), "width": int(w*0.8), "height": int(h*0.5)}
                        screen = self.drivers.capture.grab(center_roi)
                        import numpy as np
                        screen_cv = np.array(screen)
                        
                        res = self.vision.detector.find_template(screen_cv, no_bait_tmpl, threshold=NO_BAIT_TEMPLATE_THRESHOLD)
                        if res:
                            log.error(f"Out of bait banner found! Auto-stopping.")
                            self.sm.transition(FishingState.ERROR)
                            self.stop()
                            found_bait_warning = True
                            break
                    except Exception as e:
                        log.debug(f"Bait check grab error: {e}")
                    if self._wait_for_stop(NO_BAIT_CHECK_INTERVAL):
                        return
                    
                if found_bait_warning:
                    return
        else:
            if self._wait_for_stop(1.5 + random.uniform(0.2, 0.5)):
                return
            log.info("Warning: 'assets/no_bait.png' missing. Bait check skipped.")
            
        self.sm.transition(FishingState.WAITING)

    def _handle_waiting(self):
        # 1. Check for Top Banner (Priority)
        banner_frame = self._grab_named_roi("banner", "Banner")
        if banner_frame is None:
            return
            
        white_cnt = self._count_pixels(
            banner_frame, self.config.hsv_white_lower, self.config.hsv_white_upper
        )
        self._last_banner_pixels = white_cnt
        
        # Periodic debug log (~every 3s)
        if int(time.time()) % 3 == 0 and not hasattr(self, "_last_banner_log"):
            log.info(f"WAITING... Banner Pixels: {white_cnt}")
            self._last_banner_log = True
        elif int(time.time()) % 3 != 0:
            if hasattr(self, "_last_banner_log"): delattr(self, "_last_banner_log")

        banner_threshold = self.config.settings.get("banner_threshold", 3000)
        
        # Simple resolution-scaled threshold
        # Reference area at 1080p for a 1000x80 ROI is 80,000
        active_area = banner_frame.shape[0] * banner_frame.shape[1]
        scaled_threshold = banner_threshold * (active_area / 80000.0)
        
        if white_cnt > scaled_threshold:
            log.info(f"BANNER BITE! ({white_cnt} px > {int(scaled_threshold)} scaled threshold)")
            self.drivers.input.press("f")
            self.sm.transition(FishingState.STRUGGLING)
            return

        # 2. Check for Bar Jump (Green target appears)
        bar_frame = self._grab_named_roi("bar", "Bar")
        if bar_frame is None:
            return
            
        green_cnt = self._count_pixels(
            bar_frame, self.config.hsv_target_lower, self.config.hsv_target_upper
        )
        self._last_target_pixels = green_cnt
        if green_cnt > 1500:
            log.info("Bar jump detected! Hooking...")
            self.drivers.input.press("f", duration=0.1)
            self.sm.transition(FishingState.STRUGGLING)
            self.pid.reset()
            return

        # 3. Check for Hook Button (Blue/Yellowish prompt)
        btn_frame = self._grab_named_roi("button", "Button")
        if btn_frame is None:
            return
            
        blue_cnt = self._count_pixels(
            btn_frame, self.config.hsv_blue_lower, self.config.hsv_blue_upper
        )
        self._last_button_pixels = blue_cnt
        
        target_pixels = self.config.settings.get("min_blue_pixels", 600)
        if blue_cnt > target_pixels:
            log.info(f"Button hook triggered ({blue_cnt} px)")
            self.drivers.input.press("f")
            self.sm.transition(FishingState.STRUGGLING)
            self.pid.reset()
            return

    def _handle_struggling(self):
        max_secs = self.config.settings.get("max_struggle_secs", 60)
        if max_secs > 0 and self.sm.time_in_state > max_secs:
            log.warning("Struggle timeout reached. Transitioning to RESULT.")
            self.drivers.input.keyUp("a")
            self.drivers.input.keyUp("d")
            self.last_struggle_duration = self.sm.time_in_state
            self.sm.transition(FishingState.RESULT)
            return

        bar_roi = self._get_roi_abs("bar")
        frame = self.drivers.capture.grab(bar_roi)
        
        cur_x, cur_area = self.vision.tracker.find_centroid_x(
            frame, self.config.hsv_cursor_lower, self.config.hsv_cursor_upper
        )
        tgt_x, tgt_area = self.vision.tracker.find_centroid_x(
            frame, self.config.hsv_target_lower, self.config.hsv_target_upper
        )
        
        if cur_x is not None and tgt_x is not None:
            self._last_bar_time = time.time()
            w = bar_roi["width"]
            norm_cur = cur_x / w
            norm_tgt = tgt_x / w
            self._last_cur_norm = norm_cur
            self._last_tgt_norm = norm_tgt
            
            output = self.pid.update(norm_cur, norm_tgt)
            self._last_pid_power = output
            
            if output < -0.05:
                self.drivers.input.keyDown("a")
                self.drivers.input.keyUp("d")
            elif output > 0.05:
                self.drivers.input.keyDown("d")
                self.drivers.input.keyUp("a")
            else:
                self.drivers.input.keyUp("a")
                self.drivers.input.keyUp("d")
        else:
            self.drivers.input.keyUp("a")
            self.drivers.input.keyUp("d")
            self._last_cur_norm = None
            self._last_tgt_norm = None
            
            has_seen_bar = hasattr(self, "_last_bar_time") and self._last_bar_time > getattr(self.sm, "_last_transition", 0)
            
            if has_seen_bar:
                # We tracked the bar, but now it's gone. Combat ended!
                if time.time() - self._last_bar_time > RESULT_LOST_AFTER_SECONDS:
                    log.info("Target lost. Transitioning to RESULT.")
                    self.last_struggle_duration = self.sm.time_in_state
                    self.sm.transition(FishingState.RESULT)
            else:
                # We haven't seen the bar yet. Give the camera animation time to finish!
                if self.sm.time_in_state > BAR_APPEAR_TIMEOUT_SECONDS:
                    log.info("Target never appeared (Insta-catch or failed). Transitioning to RESULT.")
                    self.last_struggle_duration = self.sm.time_in_state
                    self.sm.transition(FishingState.RESULT)

    def _handle_result(self):
        recast_delay = self.config.settings.get("recast_delay", 2.0)
        
        struggle_duration = getattr(self, "last_struggle_duration", 0.0)
        if struggle_duration > GOLDEN_FISH_SECONDS:
            log.info(f"Golden fish combat ({struggle_duration:.1f}s)! Adding 6.0s delay.")
            recast_delay += 6.0
            
        log.info(f"Result detected. Waiting {recast_delay}s before closing...")
        if self._wait_for_stop(recast_delay):
            return
        
        log.info("Closing rewards via [ESC + Neutral Click]...")
        self.fish_caught += 1
        
        # 1. Press ESC (Main closer)
        close_key = self.config.settings.get("close_key", "escape")
        self.drivers.input.press(close_key)
        if self._wait_for_stop(1.0):
            return
        
        # 2. Safety Click in NEUTRAL area (Bottom 10% of window)
        rect_x, rect_y, w, h = self.drivers.window.get_client_rect()
        self.drivers.input.click(rect_x + w // 2, rect_y + int(h * 0.9)) 
        if self._wait_for_stop(0.5):
            return
            
        if self._wait_for_stop(2.5 + random.uniform(0.5, 1.0)):
            return
        self.sm.transition(FishingState.IDLE)

    def _get_roi_abs(self, name: str) -> dict:
        roi = self.config.get_roi(name)
        return scale_roi(roi, self.drivers.window.get_client_rect())
