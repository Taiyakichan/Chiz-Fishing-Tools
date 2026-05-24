import logging
import time
import threading
import random
import os
import csv
import cv2
from typing import Optional, Any
import win32api
import win32process

from nte_auto_fish.core.state_machine import FishingState, FishingStateMachine
from nte_auto_fish.core.pid_controller import PIDController
from nte_auto_fish.config.roi import scale_roi
from nte_auto_fish.utils.resource import app_root

log = logging.getLogger("NTE.Engine")

LOW_ACTIVITY_STATES = {FishingState.IDLE, FishingState.WAITING, FishingState.RESULT}
NO_BAIT_CHECK_SECONDS = 2.5
NO_BAIT_CHECK_INTERVAL = 0.1
NO_BAIT_TEMPLATE_THRESHOLD = 0.55
RESULT_LOST_AFTER_SECONDS = 3.0
BAR_APPEAR_TIMEOUT_SECONDS = 8.5
GOLDEN_FISH_SECONDS = 11.0
STRUGGLE_ENTER_THRESHOLD = 0.012
STRUGGLE_RELEASE_THRESHOLD = 0.003
STRUGGLE_VELOCITY_THRESHOLD = 0.45
STRUGGLE_VELOCITY_CATCHUP_ERROR = 0.008
STRUGGLE_VELOCITY_BOOST = 0.03
STRUGGLE_MIN_TOLERANCE = 0.005
STRUGGLE_MAX_TOLERANCE = 0.018
STRUGGLE_TOLERANCE_RATIO = 0.12
STRUGGLE_VELOCITY_LEAD = 0.055
STRUGGLE_MAX_LEAD = 0.11
STRUGGLE_STRONG_OUTPUT = 0.085
STRUGGLE_LOOP_WAIT = 0.001
DEBUG_STRUGGLE_ENV = "CHIZ_DEBUG_STRUGGLE"
DEBUG_STRUGGLE_DIR = "debug"
DEBUG_STRUGGLE_CSV = "struggle_debug.csv"
DEBUG_STRUGGLE_COLUMNS = [
    "timestamp",
    "state_time",
    "roi_width",
    "cursor_x",
    "target_x",
    "cursor_width",
    "target_width",
    "cursor_area",
    "target_area",
    "target_velocity",
    "aim_target",
    "error",
    "output",
    "direction",
]

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
        self._last_control_direction = 0
        self._debug_last_sample = 0.0
        self._debug_last_snapshot = 0.0
        self._debug_snapshot_index = 0
        self._debug_csv_ready = False
        
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
        if state == FishingState.STRUGGLING:
            self._wait_for_stop(STRUGGLE_LOOP_WAIT)
            return
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

    def _apply_struggle_control(self, output: float):
        # Hysteresis keeps direction changes decisive instead of rapidly releasing around center.
        if output <= -STRUGGLE_ENTER_THRESHOLD or (
            self._last_control_direction < 0 and output <= -STRUGGLE_RELEASE_THRESHOLD
        ):
            self.drivers.input.keyDown("a")
            self.drivers.input.keyUp("d")
            self._last_control_direction = -1
            return

        if output >= STRUGGLE_ENTER_THRESHOLD or (
            self._last_control_direction > 0 and output >= STRUGGLE_RELEASE_THRESHOLD
        ):
            self.drivers.input.keyDown("d")
            self.drivers.input.keyUp("a")
            self._last_control_direction = 1
            return

        self.drivers.input.keyUp("a")
        self.drivers.input.keyUp("d")
        self._last_control_direction = 0

    def _shape_struggle_output(self, current: float, target: float, output: float) -> float:
        # When the target reverses quickly, binary left/right control needs a stronger nudge
        # than PID alone or it visibly lags behind the target center.
        aim_target = self.pid.aim_target if self.pid.aim_target is not None else target
        chase_error = aim_target - current
        target_velocity = self.pid.target_velocity

        if target_velocity >= STRUGGLE_VELOCITY_THRESHOLD and chase_error > STRUGGLE_VELOCITY_CATCHUP_ERROR:
            return max(output, STRUGGLE_VELOCITY_BOOST + chase_error)

        if target_velocity <= -STRUGGLE_VELOCITY_THRESHOLD and chase_error < -STRUGGLE_VELOCITY_CATCHUP_ERROR:
            return min(output, -STRUGGLE_VELOCITY_BOOST + chase_error)

        return output

    def _compute_direct_struggle_output(
        self,
        current: float,
        target: float,
        target_velocity: float,
        target_width: float,
    ) -> float:
        lead = max(-STRUGGLE_MAX_LEAD, min(STRUGGLE_MAX_LEAD, target_velocity * STRUGGLE_VELOCITY_LEAD))
        aim_target = max(0.0, min(1.0, target + lead))
        error = aim_target - current

        tolerance = max(
            STRUGGLE_MIN_TOLERANCE,
            min(STRUGGLE_MAX_TOLERANCE, target_width * STRUGGLE_TOLERANCE_RATIO),
        )

        if error > tolerance:
            return max(STRUGGLE_STRONG_OUTPUT, error)
        if error < -tolerance:
            return min(-STRUGGLE_STRONG_OUTPUT, error)

        # Stay biased toward the moving center instead of idling on the target edge.
        if target_velocity > 0.08:
            return STRUGGLE_RELEASE_THRESHOLD
        if target_velocity < -0.08:
            return -STRUGGLE_RELEASE_THRESHOLD
        return 0.0

    def _debug_struggle_enabled(self) -> bool:
        env_value = os.environ.get(DEBUG_STRUGGLE_ENV, "").strip().lower()
        if env_value in ("1", "true", "yes", "on"):
            return True
        if env_value in ("0", "false", "no", "off"):
            return False
        try:
            return bool(self.config.settings.get("debug_struggle", False))
        except AttributeError:
            return False

    def _debug_interval(self, key: str, default: float) -> float:
        try:
            return max(0.001, float(self.config.settings.get(key, default)))
        except (TypeError, ValueError, AttributeError):
            return default

    def _debug_dir(self) -> str:
        return os.path.join(app_root(), DEBUG_STRUGGLE_DIR)

    def _ensure_struggle_debug_csv(self) -> str:
        debug_dir = self._debug_dir()
        os.makedirs(debug_dir, exist_ok=True)
        csv_path = os.path.join(debug_dir, DEBUG_STRUGGLE_CSV)
        if not self._debug_csv_ready:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(DEBUG_STRUGGLE_COLUMNS)
            self._debug_csv_ready = True
        return csv_path

    def _record_struggle_debug(
        self,
        frame,
        roi_width: int,
        current: float,
        target: float,
        cursor_width: float,
        target_width: float,
        cursor_area: int,
        target_area: int,
        output: float,
    ):
        if not self._debug_struggle_enabled():
            return

        now = time.time()
        sample_interval = self._debug_interval("debug_struggle_sample_interval", 0.02)
        snapshot_interval = self._debug_interval("debug_struggle_snapshot_interval", 0.25)
        target_velocity = self.pid.target_velocity
        aim_target = self.pid.aim_target if self.pid.aim_target is not None else target
        error = aim_target - current

        try:
            if now - self._debug_last_sample >= sample_interval:
                csv_path = self._ensure_struggle_debug_csv()
                with open(csv_path, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        f"{now:.6f}",
                        f"{self.sm.time_in_state:.6f}",
                        int(roi_width),
                        f"{current:.6f}",
                        f"{target:.6f}",
                        f"{cursor_width:.6f}",
                        f"{target_width:.6f}",
                        int(cursor_area),
                        int(target_area),
                        f"{target_velocity:.6f}",
                        f"{aim_target:.6f}",
                        f"{error:.6f}",
                        f"{output:.6f}",
                        int(self._last_control_direction),
                    ])
                self._debug_last_sample = now

            if now - self._debug_last_snapshot >= snapshot_interval:
                self._write_struggle_snapshot(
                    frame,
                    current,
                    target,
                    cursor_width,
                    target_width,
                    aim_target,
                    output,
                )
                self._debug_last_snapshot = now
        except Exception as e:
            log.debug(f"Struggle debug write failed: {e}")

    def _record_struggle_missing(
        self,
        frame,
        roi_width: int,
        cursor_area: int,
        target_area: int,
    ):
        if not self._debug_struggle_enabled():
            return

        now = time.time()
        sample_interval = self._debug_interval("debug_struggle_sample_interval", 0.02)
        snapshot_interval = self._debug_interval("debug_struggle_snapshot_interval", 0.25)

        try:
            if now - self._debug_last_sample >= sample_interval:
                csv_path = self._ensure_struggle_debug_csv()
                with open(csv_path, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        f"{now:.6f}",
                        f"{self.sm.time_in_state:.6f}",
                        int(roi_width),
                        "",
                        "",
                        "",
                        "",
                        int(cursor_area),
                        int(target_area),
                        "",
                        "",
                        "",
                        "",
                        int(self._last_control_direction),
                    ])
                self._debug_last_sample = now

            if now - self._debug_last_snapshot >= snapshot_interval:
                marked = frame.copy()
                h, _ = marked.shape[:2]
                cv2.putText(
                    marked,
                    f"missing detection cur_area={cursor_area} tgt_area={target_area}",
                    (6, max(14, min(h - 4, 18))),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                self._debug_snapshot_index += 1
                path = os.path.join(self._debug_dir(), f"struggle_{self._debug_snapshot_index:05d}.png")
                os.makedirs(self._debug_dir(), exist_ok=True)
                cv2.imwrite(path, marked)
                self._debug_last_snapshot = now
        except Exception as e:
            log.debug(f"Struggle missing-debug write failed: {e}")

    def _write_struggle_snapshot(
        self,
        frame,
        current: float,
        target: float,
        cursor_width: float,
        target_width: float,
        aim_target: float,
        output: float,
    ):
        debug_dir = self._debug_dir()
        os.makedirs(debug_dir, exist_ok=True)
        marked = frame.copy()
        h, w = marked.shape[:2]
        if w <= 0 or h <= 0:
            return

        def x_px(value: float) -> int:
            return max(0, min(w - 1, int(round(value * w))))

        target_center = x_px(target)
        cursor_center = x_px(current)
        aim_center = x_px(aim_target)
        target_half_width = max(1, int(round(target_width * w / 2)))
        cursor_half_width = max(1, int(round(cursor_width * w / 2)))

        cv2.rectangle(
            marked,
            (max(0, target_center - target_half_width), 0),
            (min(w - 1, target_center + target_half_width), h - 1),
            (60, 180, 60),
            1,
        )
        cv2.rectangle(
            marked,
            (max(0, cursor_center - cursor_half_width), 0),
            (min(w - 1, cursor_center + cursor_half_width), h - 1),
            (0, 220, 255),
            1,
        )
        cv2.line(marked, (target_center, 0), (target_center, h - 1), (0, 255, 0), 1)
        cv2.line(marked, (cursor_center, 0), (cursor_center, h - 1), (0, 255, 255), 2)
        cv2.line(marked, (aim_center, 0), (aim_center, h - 1), (255, 0, 255), 1)
        cv2.putText(
            marked,
            f"out={output:.3f} dir={self._last_control_direction}",
            (6, max(14, min(h - 4, 18))),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        self._debug_snapshot_index += 1
        path = os.path.join(debug_dir, f"struggle_{self._debug_snapshot_index:05d}.png")
        cv2.imwrite(path, marked)

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
        
        cur_x, cur_area, cur_width = self.vision.tracker.find_horizontal_span(
            frame, self.config.hsv_cursor_lower, self.config.hsv_cursor_upper
        )
        tgt_x, tgt_area, tgt_width = self.vision.tracker.find_horizontal_span(
            frame, self.config.hsv_target_lower, self.config.hsv_target_upper
        )
        
        if cur_x is not None and tgt_x is not None:
            self._last_bar_time = time.time()
            w = bar_roi["width"]
            norm_cur = cur_x / w
            norm_tgt = tgt_x / w
            norm_tgt_width = tgt_width / w if w else 0.0
            self._last_cur_norm = norm_cur
            self._last_tgt_norm = norm_tgt

            self.pid.update(norm_cur, norm_tgt)
            output = self._compute_direct_struggle_output(
                norm_cur,
                norm_tgt,
                self.pid.target_velocity,
                norm_tgt_width,
            )
            self._last_pid_power = output
            self._apply_struggle_control(output)
            self._record_struggle_debug(
                frame,
                w,
                norm_cur,
                norm_tgt,
                cur_width / w if w else 0.0,
                norm_tgt_width,
                cur_area,
                tgt_area,
                output,
            )
        else:
            self.drivers.input.keyUp("a")
            self.drivers.input.keyUp("d")
            self._last_control_direction = 0
            self._last_cur_norm = None
            self._last_tgt_norm = None
            self._record_struggle_missing(frame, bar_roi["width"], cur_area, tgt_area)
            
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
