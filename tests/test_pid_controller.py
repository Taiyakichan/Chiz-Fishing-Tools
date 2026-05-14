import unittest

from nte_auto_fish.core.pid_controller import PIDController


class TestPIDController(unittest.TestCase):
    def test_output_direction_tracks_target(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0, ff_weight=0.0, deadband=0.0)

        self.assertGreater(pid.update(current=0.2, target=0.8), 0)
        self.assertLess(pid.update(current=0.8, target=0.2), 0)

    def test_deadband_suppresses_small_error(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0, ff_weight=0.0, deadband=0.05)

        self.assertEqual(pid.update(current=0.50, target=0.52), 0.0)


if __name__ == "__main__":
    unittest.main()
