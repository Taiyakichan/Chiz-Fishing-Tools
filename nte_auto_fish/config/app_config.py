import copy
import json
import os
from typing import Any, Dict, Tuple

from nte_auto_fish.utils.resource import resource_path

DEFAULT_CONFIG_FILENAME = "config.json"
DEFAULT_TEMPLATE_FILENAME = "config.default.json"

class ConfigManager:
    """Manages bot settings, ROI coordinates, and HSV ranges."""
    
    def __init__(self, filename: str = DEFAULT_CONFIG_FILENAME, example_filename: str = DEFAULT_TEMPLATE_FILENAME):
        self.filename = filename
        self.example_filename = example_filename
        self.loaded_path: str | None = None
        self.loaded_default_template = False
        
        # --- Default Settings ---
        self.defaults = {
            "settings": {
            "min_blue_pixels": 600,
            "max_struggle_secs": 60,
            "poll_interval": 0.05,
            "banner_threshold": 3000,
            "recast_delay": 2.0,
            "session_cap_min": 120,
            "session_cap_fish": 0,
            "goal_mode": "Time Limit",
            "hook_key": "f",
            "close_key": "escape",
            },
            "rois": {
                "button": {"left": 1680, "top": 890, "width": 120, "height": 110},
                "bar": {"left": 200, "top": 0, "width": 1520, "height": 500},
                "banner": {"left": 460, "top": 100, "width": 1000, "height": 80},
            },
            "hsv": {
                "blue": {"lower": (100, 160, 140), "upper": (130, 255, 255)},
                "cursor": {"lower": (18, 115, 240), "upper": (40, 150, 255)},
                "target": {"lower": (75, 190, 190), "upper": (100, 255, 255)},
                "white": {"lower": (0, 0, 210), "upper": (180, 30, 255)},
            },
        }
        self.settings = copy.deepcopy(self.defaults["settings"])
        
        # --- Default ROIs (Native 1920x1080) ---
        self.rois: Dict[str, Dict[str, int]] = copy.deepcopy(self.defaults["rois"])
        
        # --- Default HSV Ranges ---
        self.hsv = copy.deepcopy(self.defaults["hsv"])
        
        self.load()
        if self._should_create_local_config():
            self.save()
    
    def get_roi(self, name: str) -> Dict[str, Any]:
        return self.rois.get(name, {"left": 0, "top": 0, "width": 100, "height": 100})

    def save(self):
        data = {
            "settings": self.settings,
            "rois": self.rois,
            "hsv": self.hsv
        }
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load(self):
        config_path = self._select_config_path()
        self.loaded_path = config_path
        self.loaded_default_template = bool(config_path and os.path.abspath(config_path) != os.path.abspath(self.filename))
        if not config_path:
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.settings = self._merge_settings(data.get("settings", {}))
                self.rois = self._merge_rois(data.get("rois", {}))
                self.hsv = self._merge_hsv(data.get("hsv", {}))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self.settings = copy.deepcopy(self.defaults["settings"])
            self.rois = copy.deepcopy(self.defaults["rois"])
            self.hsv = copy.deepcopy(self.defaults["hsv"])

    def _select_config_path(self) -> str | None:
        if os.path.exists(self.filename):
            return self.filename

        if os.path.basename(self.filename) != DEFAULT_CONFIG_FILENAME:
            return None

        if os.path.exists(self.example_filename):
            return self.example_filename

        bundled_example = resource_path(self.example_filename)
        if os.path.exists(bundled_example):
            return bundled_example

        return None

    def _should_create_local_config(self) -> bool:
        return os.path.basename(self.filename) == DEFAULT_CONFIG_FILENAME and not os.path.exists(self.filename)

    @property
    def has_local_config(self) -> bool:
        return os.path.exists(self.filename)

    def _merge_settings(self, raw: Any) -> Dict[str, Any]:
        settings = copy.deepcopy(self.defaults["settings"])
        if not isinstance(raw, dict):
            return settings

        numeric_fields = {
            "min_blue_pixels": int,
            "max_struggle_secs": int,
            "poll_interval": float,
            "banner_threshold": int,
            "recast_delay": float,
        }
        for key, caster in numeric_fields.items():
            if key in raw:
                try:
                    value = caster(raw[key])
                    if value > 0:
                        settings[key] = value
                except (TypeError, ValueError):
                    pass

        for key in ("session_cap_min", "session_cap_fish"):
            if key in raw:
                try:
                    value = int(raw[key])
                    if value >= 0:
                        settings[key] = value
                except (TypeError, ValueError):
                    pass

        for key in ("hook_key", "close_key"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                settings[key] = value.strip()

        goal_mode = raw.get("goal_mode")
        if goal_mode in ("Time Limit", "Fish Limit"):
            settings["goal_mode"] = goal_mode
        return settings

    def _merge_rois(self, raw: Any) -> Dict[str, Dict[str, Any]]:
        rois = copy.deepcopy(self.defaults["rois"])
        if not isinstance(raw, dict):
            return rois
        for name, roi in raw.items():
            if not isinstance(roi, dict):
                continue
            parsed = {}
            for field in ("left", "top", "width", "height"):
                try:
                    val = roi[field]
                    parsed[field] = float(val) if isinstance(val, (float, int)) else 0.0
                except (TypeError, ValueError):
                    break
            if set(parsed) == {"left", "top", "width", "height"} and parsed["width"] > 0 and parsed["height"] > 0:
                # Cast the values back to what the system expects
                rois[name] = parsed
        return rois

    def _merge_hsv(self, raw: Any) -> Dict[str, Dict[str, Tuple[int, int, int]]]:
        hsv = copy.deepcopy(self.defaults["hsv"])
        if not isinstance(raw, dict):
            return hsv
        for name, ranges in raw.items():
            if name not in hsv or not isinstance(ranges, dict):
                continue
            lower = self._parse_hsv_triplet(ranges.get("lower"))
            upper = self._parse_hsv_triplet(ranges.get("upper"))
            if lower is not None:
                hsv[name]["lower"] = lower
            if upper is not None:
                hsv[name]["upper"] = upper
        return hsv

    def _parse_hsv_triplet(self, value: Any) -> Tuple[int, int, int] | None:
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            return None
        try:
            h, s, v = [int(part) for part in value]
        except (TypeError, ValueError):
            return None
        if 0 <= h <= 180 and 0 <= s <= 255 and 0 <= v <= 255:
            return (h, s, v)
        return None

    @property
    def hsv_blue_lower(self) -> Tuple[int, ...]: return tuple(self.hsv["blue"]["lower"])
    @property
    def hsv_blue_upper(self) -> Tuple[int, ...]: return tuple(self.hsv["blue"]["upper"])
    
    @property
    def hsv_cursor_lower(self) -> Tuple[int, ...]: return tuple(self.hsv["cursor"]["lower"])
    @property
    def hsv_cursor_upper(self) -> Tuple[int, ...]: return tuple(self.hsv["cursor"]["upper"])
    
    @property
    def hsv_target_lower(self) -> Tuple[int, ...]: return tuple(self.hsv["target"]["lower"])
    @property
    def hsv_target_upper(self) -> Tuple[int, ...]: return tuple(self.hsv["target"]["upper"])

    @property
    def hsv_white_lower(self) -> Tuple[int, ...]: return tuple(self.hsv["white"]["lower"])
    @property
    def hsv_white_upper(self) -> Tuple[int, ...]: return tuple(self.hsv["white"]["upper"])

    @property
    def min_blue_pixels(self) -> int: return self.settings["min_blue_pixels"]
