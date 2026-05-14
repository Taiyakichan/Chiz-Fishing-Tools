import json
import tempfile
import unittest
from pathlib import Path

from nte_auto_fish.config.app_config import ConfigManager


class TestConfigManager(unittest.TestCase):
    def test_missing_config_uses_defaults(self):
        config = ConfigManager(filename="__missing_test_config__.json")

        self.assertEqual(config.settings["hook_key"], "f")
        self.assertIn("bar", config.rois)
        self.assertEqual(config.hsv_blue_lower, (100, 160, 140))

    def test_malformed_config_uses_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text("{bad json", encoding="utf-8")

            config = ConfigManager(filename=str(path))

        self.assertEqual(config.settings["close_key"], "escape")
        self.assertEqual(config.hsv_white_upper, (180, 30, 255))

    def test_valid_values_are_coerced_and_invalid_values_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "settings": {
                            "poll_interval": "0.1",
                            "banner_threshold": "500",
                            "hook_key": "e",
                            "recast_delay": -1,
                        },
                        "hsv": {"blue": {"lower": [101, 201, 202], "upper": [999, 0, 0]}},
                    }
                ),
                encoding="utf-8",
            )

            config = ConfigManager(filename=str(path))

        self.assertEqual(config.settings["poll_interval"], 0.1)
        self.assertEqual(config.settings["banner_threshold"], 500)
        self.assertEqual(config.settings["hook_key"], "e")
        self.assertEqual(config.settings["recast_delay"], 2.0)
        self.assertEqual(config.hsv_blue_lower, (101, 201, 202))
        self.assertEqual(config.hsv_blue_upper, (130, 255, 255))

    def test_default_config_loads_from_template_when_local_config_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            example_path = Path(temp_dir) / "config.default.json"
            example_path.write_text(
                json.dumps(
                    {
                        "settings": {
                            "poll_interval": 0.12,
                            "goal_mode": "Fish Limit",
                            "session_cap_min": 0,
                            "session_cap_fish": 25,
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = ConfigManager(filename=str(config_path), example_filename=str(example_path))

            self.assertEqual(config.settings["poll_interval"], 0.12)
            self.assertEqual(config.settings["goal_mode"], "Fish Limit")
            self.assertEqual(config.settings["session_cap_min"], 0)
            self.assertEqual(config.settings["session_cap_fish"], 25)
            self.assertFalse(config_path.exists())

    def test_save_writes_local_config_not_example_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            example_path = Path(temp_dir) / "config.default.json"
            example_path.write_text(json.dumps({"settings": {"hook_key": "e"}}), encoding="utf-8")

            config = ConfigManager(filename=str(config_path), example_filename=str(example_path))
            config.settings["hook_key"] = "f"
            config.save()

            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8"))["settings"]["hook_key"], "f")
            self.assertEqual(json.loads(example_path.read_text(encoding="utf-8"))["settings"]["hook_key"], "e")


if __name__ == "__main__":
    unittest.main()
