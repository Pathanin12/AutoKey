from __future__ import annotations

import unittest

from constants.template_actions import (
    DEFAULT_TEMPLATE_CLICK_ACTIONS,
    MENU_ACCOUNT_TARGET,
    MENU_REPORT_NORMAL_SELECTED_TARGET,
    REPORT_NORMAL_ACTION_IDS,
    REPORT_PREVIEW_ACTION_IDS,
    REPORT_PREVIEW_TITLE_TARGET,
    REPORT_PREVIEW_TMP6_TARGET,
)
from models.step_match_result import StepMatchResult
from models.template_click_settings import TemplateClickSettings
from services.image_service import map_region_to_grab
from services.template_click_service import TemplateClickService
from services.template_match_service import load_step_template, match_score_at


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

    def test_rgb_screenshot_matches_without_rgba_convert(self) -> None:
        from PIL import Image

        template = load_step_template(MENU_ACCOUNT_TARGET).convert("RGB")
        screen = Image.new("RGB", (template.width + 20, template.height + 20), (32, 32, 32))
        screen.paste(template, (8, 6))
        self.assertGreater(match_score_at(screen, template, 8, 6), 0.95)

    def test_click_first_uses_one_screenshot(self) -> None:
        from PIL import Image

        template = load_step_template(MENU_REPORT_NORMAL_SELECTED_TARGET)
        screen = Image.new("RGB", (400, 240), (40, 40, 40))
        screen.paste(template.convert("RGB"), (40, 30))

        class FakeImage:
            def __init__(self) -> None:
                self.shots = 0
                self.clicks: list[tuple[int, int]] = []

            def screenshot_region(self, region):
                del region
                self.shots += 1
                return screen, (0, 0)

            def click_at(self, x: int, y: int) -> None:
                self.clicks.append((x, y))

        fake = FakeImage()
        clicker = TemplateClickService(
            fake,  # type: ignore[arg-type]
            TemplateClickSettings(actions=DEFAULT_TEMPLATE_CLICK_ACTIONS),
        )
        match = clicker.click_first(REPORT_NORMAL_ACTION_IDS)
        self.assertTrue(match.found)
        self.assertEqual(fake.shots, 1)
        self.assertEqual(len(fake.clicks), 1)

    def test_wait_until_first_uses_toolbar_region_first(self) -> None:
        from PIL import Image

        template = load_step_template(REPORT_PREVIEW_TMP6_TARGET)
        screen = Image.new("RGB", (500, 80), (40, 40, 40))
        screen.paste(template.convert("RGB"), (10, 10))

        class FakeImage:
            def __init__(self) -> None:
                self.shots = 0
                self.regions: list[tuple[int, int, int, int] | None] = []

            def screenshot_region(self, region):
                self.regions.append(region)
                self.shots += 1
                return screen.copy(), (0, 0)

            def wait(self, seconds: float | None = None) -> None:
                del seconds

        fake = FakeImage()
        clicker = TemplateClickService(
            fake,  # type: ignore[arg-type]
            TemplateClickSettings(actions=DEFAULT_TEMPLATE_CLICK_ACTIONS),
        )
        match = clicker.wait_until_first(REPORT_PREVIEW_ACTION_IDS, timeout=1, poll_wait=0.01)
        self.assertTrue(match.found)
        self.assertEqual(fake.shots, 1)
        self.assertEqual(fake.regions[0], (0, 0, 1920, 280))

    def test_wait_until_first_accepts_either_preview_template(self) -> None:
        from PIL import Image

        template = load_step_template(REPORT_PREVIEW_TITLE_TARGET)
        screen = Image.new("RGB", (500, 80), (255, 255, 255))
        screen.paste(template.convert("RGB"), (10, 10))

        class FakeImage:
            def __init__(self) -> None:
                self.shots = 0

            def screenshot_region(self, region):
                del region
                self.shots += 1
                shot = Image.new("RGB", screen.size, (255, 255, 255))
                shot.paste(screen)
                return shot, (0, 0)

            def wait(self, seconds: float | None = None) -> None:
                del seconds

        fake = FakeImage()
        clicker = TemplateClickService(
            fake,  # type: ignore[arg-type]
            TemplateClickSettings(actions=DEFAULT_TEMPLATE_CLICK_ACTIONS),
        )
        match = clicker.wait_until_first(REPORT_PREVIEW_ACTION_IDS, timeout=1, poll_wait=0.01)
        self.assertTrue(match.found)
        self.assertGreaterEqual(fake.shots, 1)
        self.assertLessEqual(fake.shots, 2)


if __name__ == "__main__":
    unittest.main()
