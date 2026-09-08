from __future__ import annotations

import unittest

from constants.template_actions import MENU_ACCOUNT_TARGET
from models.step_match_result import StepMatchResult
from services.image_service import map_region_to_grab
from services.template_match_service import load_step_template


class ScreenshotRegionTests(unittest.TestCase):
    def test_full_screen_has_no_grab_box(self) -> None:
        grab, origin = map_region_to_grab(
            None,
            logical_size=(1920, 1080),
            actual_size=(1920, 1080),
        )
        self.assertIsNone(grab)
        self.assertEqual(origin, (0, 0))

    def test_same_resolution_keeps_pixel_box(self) -> None:
        grab, origin = map_region_to_grab(
            (80, 0, 980, 90),
            logical_size=(1920, 1080),
            actual_size=(1920, 1080),
        )
        self.assertEqual(grab, (80, 0, 900, 90))
        self.assertEqual(origin, (80, 0))

    def test_scales_region_when_screen_is_larger(self) -> None:
        grab, origin = map_region_to_grab(
            (0, 0, 960, 540),
            logical_size=(1920, 1080),
            actual_size=(3840, 2160),
        )
        self.assertEqual(grab, (0, 0, 1920, 1080))
        self.assertEqual(origin, (0, 0))

    def test_match_translated_adds_crop_origin(self) -> None:
        match = StepMatchResult(True, 0.95, 10, 12, 40, 20)
        moved = match.translated(80, 40)
        self.assertEqual(moved.x, 90)
        self.assertEqual(moved.y, 52)
        self.assertEqual(moved.center, (110, 62))

    def test_load_step_template_reuses_cached_image(self) -> None:
        first = load_step_template(MENU_ACCOUNT_TARGET)
        second = load_step_template(MENU_ACCOUNT_TARGET)
        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
