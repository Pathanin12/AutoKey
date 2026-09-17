from __future__ import annotations

import unittest

from models.step_match_result import StepMatchResult
from services.menu_navigation_service import open_general_journal_menu, open_payment_journal_menu
from services.template_click_service import TemplateNotFoundError


class FakeImage:
    def __init__(self) -> None:
        self.clicks: list[tuple[int, int]] = []
        self.keys: list[tuple[str, ...]] = []

    def wait(self, seconds: float | None = None) -> None:
        del seconds

    def click_at(self, x: int, y: int) -> None:
        self.clicks.append((x, y))

    def press(self, *keys: str, presses: int = 1) -> None:
        for _ in range(presses):
            self.keys.append(keys)


class FakeClick:
    enabled = True

    def __init__(self) -> None:
        self.journal_clicks = 0

    def click(self, action_id: str, search_region=None):
        del search_region
        if action_id in {"menu_general_journal", "menu_payment_journal"}:
            self.journal_clicks += 1
            raise TemplateNotFoundError("ไม่พบเมนู")
        return StepMatchResult(True, 1.0, 10, 10, 40, 20)

    def hover(self, action_id: str, search_region=None):
        del action_id, search_region
        return StepMatchResult(True, 1.0, 100, 50, 80, 20)


class MenuNavigationTests(unittest.TestCase):
    def test_general_journal_falls_back_after_one_miss(self) -> None:
        image = FakeImage()
        clicker = FakeClick()
        open_general_journal_menu(image, clicker)  # type: ignore[arg-type]
        self.assertEqual(clicker.journal_clicks, 1)
        self.assertEqual(len(image.clicks), 1)

    def test_payment_journal_falls_back_after_one_miss(self) -> None:
        image = FakeImage()
        clicker = FakeClick()
        open_payment_journal_menu(image, clicker)  # type: ignore[arg-type]
        self.assertEqual(clicker.journal_clicks, 1)
        self.assertEqual(image.keys, [])
        self.assertEqual(len(image.clicks), 1)
        first = FakeImage()
        open_general_journal_menu(first, FakeClick())  # type: ignore[arg-type]
        self.assertEqual(image.clicks[0][0], first.clicks[0][0])
        self.assertGreater(image.clicks[0][1], first.clicks[0][1])


if __name__ == "__main__":
    unittest.main()
