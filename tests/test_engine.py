import unittest
import time

from nte_auto_fish.core.engine import FishingEngine


class DummyInput:
    def __init__(self):
        self.released = False
        self.down_calls = []
        self.up_calls = []

    def release_all(self):
        self.released = True

    def keyDown(self, key):
        self.down_calls.append(key)

    def keyUp(self, key):
        self.up_calls.append(key)


class DummyDrivers:
    def __init__(self):
        self.input = DummyInput()


class DummyVision:
    pass


class DummyConfig:
    def __init__(self, settings=None):
        self.settings = settings or {}


class TestFishingEngine(unittest.TestCase):
    def test_stop_releases_held_input(self):
        drivers = DummyDrivers()
        engine = FishingEngine(drivers, DummyVision(), DummyConfig())

        engine.stop()

        self.assertTrue(drivers.input.released)

    def test_poll_interval_uses_configured_check_speed(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig({"poll_interval": 0.2}))

        self.assertEqual(engine._poll_interval(), 0.2)

    def test_poll_interval_has_minimum_floor(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig({"poll_interval": 0}))

        self.assertEqual(engine._poll_interval(), 0.01)

    def test_wait_for_stop_returns_promptly_when_stop_is_set(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig())
        engine._stop_event.set()

        start = time.time()
        self.assertTrue(engine._wait_for_stop(1.0))
        self.assertLess(time.time() - start, 0.1)

    def test_struggle_control_uses_hysteresis_to_hold_direction(self):
        drivers = DummyDrivers()
        engine = FishingEngine(drivers, DummyVision(), DummyConfig())

        engine._apply_struggle_control(0.02)
        engine._apply_struggle_control(0.004)

        self.assertEqual(engine._last_control_direction, 1)
        self.assertEqual(drivers.input.down_calls.count("d"), 2)

    def test_struggle_control_releases_when_output_returns_to_center(self):
        drivers = DummyDrivers()
        engine = FishingEngine(drivers, DummyVision(), DummyConfig())

        engine._apply_struggle_control(-0.02)
        engine._apply_struggle_control(0.0)

        self.assertEqual(engine._last_control_direction, 0)
        self.assertIn("a", drivers.input.up_calls)
        self.assertIn("d", drivers.input.up_calls)

    def test_shape_struggle_output_boosts_fast_right_reversal(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig())
        engine.pid._last_aim_target = 0.55
        engine.pid._target_velocity = 0.8

        shaped = engine._shape_struggle_output(current=0.48, target=0.52, output=0.01)

        self.assertGreater(shaped, 0.03)

    def test_shape_struggle_output_boosts_fast_left_reversal(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig())
        engine.pid._last_aim_target = 0.40
        engine.pid._target_velocity = -0.9

        shaped = engine._shape_struggle_output(current=0.49, target=0.45, output=-0.01)

        self.assertLess(shaped, -0.03)

    def test_direct_struggle_output_pushes_right_when_off_center(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig())

        output = engine._compute_direct_struggle_output(
            current=0.42,
            target=0.50,
            target_velocity=0.0,
            target_width=0.08,
        )

        self.assertGreater(output, 0.05)

    def test_direct_struggle_output_biases_with_target_velocity_inside_zone(self):
        engine = FishingEngine(DummyDrivers(), DummyVision(), DummyConfig())

        output = engine._compute_direct_struggle_output(
            current=0.50,
            target=0.50,
            target_velocity=0.2,
            target_width=0.08,
        )

        self.assertGreater(output, 0.0)


if __name__ == "__main__":
    unittest.main()
