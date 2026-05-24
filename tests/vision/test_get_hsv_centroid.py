import unittest
from pathlib import Path

import cv2
import numpy as np

from nte_auto_fish.config.app_config import ConfigManager
from nte_auto_fish.vision.tracker import ObjectTracker


class TestHSVCentroid(unittest.TestCase):
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

    def assert_centroid_cases(self, folder, lower, upper, expected):
        for image_path in sorted((self.data_dir / folder).glob("*.png")):
            with self.subTest(image=image_path.name):
                result, _area = self.tracker.find_centroid_x(
                    self.load_image(image_path), lower, upper, min_area=80.0
                )
                if expected:
                    self.assertIsNotNone(result)
                else:
                    self.assertIsNone(result)

    def assert_span_cases(self, folder, lower, upper, expected):
        for image_path in sorted((self.data_dir / folder).glob("*.png")):
            with self.subTest(image=image_path.name):
                result, area, width = self.tracker.find_horizontal_span(
                    self.load_image(image_path), lower, upper, min_area=80.0
                )
                if expected:
                    self.assertIsNotNone(result)
                    self.assertGreater(area, 0.0)
                    self.assertGreater(width, 0.0)
                else:
                    self.assertIsNone(result)

    def test_get_bar_positive_cases(self):
        self.assert_centroid_cases(
            "hsv_centroid_bar_positive",
            self.config.hsv_target_lower,
            self.config.hsv_target_upper,
            True,
        )

    def test_get_bar_negative_cases(self):
        self.assert_centroid_cases(
            "hsv_centroid_bar_negative",
            self.config.hsv_target_lower,
            self.config.hsv_target_upper,
            False,
        )

    def test_get_cursor_positive_cases(self):
        self.assert_centroid_cases(
            "hsv_centroid_cursor_positive",
            self.config.hsv_cursor_lower,
            self.config.hsv_cursor_upper,
            True,
        )

    def test_get_cursor_negative_cases(self):
        self.assert_centroid_cases(
            "hsv_centroid_cursor_negative",
            self.config.hsv_cursor_lower,
            self.config.hsv_cursor_upper,
            False,
        )

    def test_get_bar_span_positive_cases(self):
        self.assert_span_cases(
            "hsv_centroid_bar_positive",
            self.config.hsv_target_lower,
            self.config.hsv_target_upper,
            True,
        )


if __name__ == "__main__":
    unittest.main()
