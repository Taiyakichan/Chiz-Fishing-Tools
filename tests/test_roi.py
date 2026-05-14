import unittest

from nte_auto_fish.config.roi import game_viewport, scale_pixel_roi, scale_ratio_roi


class TestRoiScaling(unittest.TestCase):
    def test_3440x1440_uses_centered_16x9_viewport(self):
        self.assertEqual(
            game_viewport(3440, 1440),
            {"left": 440, "top": 0, "width": 2560, "height": 1440},
        )

    def test_progress_ratio_scales_inside_ultrawide_game_viewport(self):
        viewport = game_viewport(3440, 1440)

        self.assertEqual(
            scale_ratio_roi(
                {"top": 0.05463, "left": 0.314844, "width": 0.37526, "height": 0.02963},
                viewport,
            ),
            {"top": 79, "left": 1246, "width": 961, "height": 43},
        )

    def test_button_fallback_scales_inside_ultrawide_game_viewport(self):
        viewport = game_viewport(3440, 1440)

        self.assertEqual(
            scale_pixel_roi({"top": 1760, "left": 3400, "width": 440, "height": 360}, viewport),
            {"top": 2347, "left": 4973, "width": 587, "height": 480},
        )


if __name__ == "__main__":
    unittest.main()
