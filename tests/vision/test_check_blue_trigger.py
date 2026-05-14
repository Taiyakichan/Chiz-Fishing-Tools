import unittest
from pathlib import Path

import cv2
import numpy as np

from nte_auto_fish.config.app_config import ConfigManager
from nte_auto_fish.vision.tracker import ObjectTracker


class TestCheckBlueTrigger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = Path(__file__).parent / "data"
        cls.config = ConfigManager(filename="__missing_test_config__.json")
        cls.tracker = ObjectTracker()

    def load_image(self, image_path: Path) -> np.ndarray:
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Failed to load image: {image_path}")
        return img

    def test_blue_trigger_positive_cases(self):
        for image_path in sorted((self.data_dir / "blue_positive").glob("*.png")):
            with self.subTest(image=image_path.name):
                count = self.tracker.check_pixel_count(
                    self.load_image(image_path),
                    self.config.hsv_blue_lower,
                    self.config.hsv_blue_upper,
                )
                self.assertGreater(count, 0)

    def test_blue_trigger_negative_cases(self):
        for image_path in sorted((self.data_dir / "blue_negative").glob("*.png")):
            with self.subTest(image=image_path.name):
                count = self.tracker.check_pixel_count(
                    self.load_image(image_path),
                    self.config.hsv_blue_lower,
                    self.config.hsv_blue_upper,
                )
                self.assertLess(count, self.config.min_blue_pixels)


if __name__ == "__main__":
    unittest.main()
