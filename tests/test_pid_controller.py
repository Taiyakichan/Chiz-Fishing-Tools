import unittest
from unittest.mock import patch

from nte_auto_fish.core.pid_controller import PIDController


class TestPIDController(unittest.TestCase):
    def test_output_direction_tracks_target(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0, ff_weight=0.0, deadband=0.0)

        self.assertGreater(pid.update(current=0.2, target=0.8), 0)
        self.assertLess(pid.update(current=0.8, target=0.2), 0)

    def test_deadband_suppresses_small_error(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0, ff_weight=0.0, deadband=0.05)

        self.assertEqual(pid.update(current=0.50, target=0.52), 0.0)

    def test_prediction_leads_moving_target(self):
        pid = PIDController(
            kp=1.0,
            ki=0.0,
            kd=0.0,
            ff_weight=0.0,
            deadband=0.0,
            prediction_horizon=0.05,
            max_prediction=0.1,
            snap_gain=0.0,
            snap_error=1.0,
        )

        with patch("nte_auto_fish.core.pid_controller.time.time", side_effect=[1.0, 1.1]):
            pid.update(current=0.2, target=0.3)
            output = pid.update(current=0.2, target=0.5)

        self.assertGreater(output, 0.3)
        self.assertGreater(pid._last_aim_target, 0.5)

    def test_large_error_gets_snap_boost(self):
        base_pid = PIDController(
            kp=1.0,
            ki=0.0,
            kd=0.0,
            ff_weight=0.0,
            deadband=0.0,
            snap_gain=0.0,
            snap_error=0.04,
        )
        snap_pid = PIDController(
            kp=1.0,
            ki=0.0,
            kd=0.0,
            ff_weight=0.0,
            deadband=0.0,
            snap_gain=0.65,
            snap_error=0.04,
        )

        self.assertGreater(
            snap_pid.update(current=0.2, target=0.5),
            base_pid.update(current=0.2, target=0.5),
        )

    def test_target_reversal_resets_integral_and_velocity_direction(self):
        pid = PIDController(
            kp=0.0,
            ki=1.0,
            kd=0.0,
            ff_weight=0.0,
            deadband=0.0,
        )

        with patch("nte_auto_fish.core.pid_controller.time.time", side_effect=[1.0, 1.1, 1.2]):
            pid.update(current=0.2, target=0.4)
            pid.update(current=0.2, target=0.6)
            pid.update(current=0.2, target=0.3)

        self.assertLess(pid._target_velocity, 0.0)
        self.assertLess(abs(pid._integral), 0.05)


if __name__ == "__main__":
    unittest.main()
