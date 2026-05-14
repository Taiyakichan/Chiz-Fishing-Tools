import unittest
import time

from nte_auto_fish.core.engine import FishingEngine


class DummyInput:
    def __init__(self):
        self.released = False

    def release_all(self):
        self.released = True


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


if __name__ == "__main__":
    unittest.main()
