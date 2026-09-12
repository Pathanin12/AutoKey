from __future__ import annotations

import unittest
from unittest.mock import patch

from models.run_speed import RunSpeed
from services.image_service import ImageService


class RunSpeedTests(unittest.TestCase):
    def test_parse_defaults_to_x1(self) -> None:
        self.assertEqual(RunSpeed.parse("").key, "1")
        self.assertEqual(RunSpeed.parse("2").key, "1")
        self.assertEqual(RunSpeed.default().wait_scale, 1.0)
        self.assertEqual(RunSpeed.default().label, "x1")

    def test_smaller_label_is_slower(self) -> None:
        self.assertEqual(RunSpeed.parse("1").wait_scale, 1.0)
        self.assertEqual(RunSpeed.parse("0.75").wait_scale, 1.0 / 0.75)
        self.assertEqual(RunSpeed.parse("0.5").wait_scale, 2.0)
        self.assertEqual(RunSpeed.parse("0.25").wait_scale, 4.0)
        self.assertEqual(RunSpeed.parse("0.25").label, "x0.25")
        self.assertEqual(RunSpeed.parse("0.5").label, "x0.5")
        self.assertEqual(RunSpeed.parse("0.75").label, "x0.75")

    def test_image_wait_uses_speed_scale(self) -> None:
        image = ImageService.__new__(ImageService)
        image.action_delay = 0.04
        image.wait_scale = 4.0
        with patch("services.image_service.time.sleep") as sleep:
            image.wait(0.20)
            sleep.assert_called_once_with(0.80)


if __name__ == "__main__":
    unittest.main()
