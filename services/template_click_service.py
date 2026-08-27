"""จับภาพหน้าจอ Express → หา template → คลิก"""

from __future__ import annotations

from typing import Callable

from models.screen_region import ScreenRegion
from models.step_match_result import StepMatchResult
from models.template_click_settings import TemplateClickSettings
from services.image_service import ImageService
from services.template_detect_service import detect_step_match


class TemplateNotFoundError(RuntimeError):
    pass


class TemplateClickService:
    def __init__(
        self,
        image: ImageService,
        settings: TemplateClickSettings,
        *,
        on_status: Callable[[str], None] | None = None,
        on_highlight: Callable[[ScreenRegion], None] | None = None,
    ) -> None:
        self.image = image
        self.settings = settings
        self.on_status = on_status
        self.on_highlight = on_highlight

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    def find(
        self,
        action_id: str,
        *,
        search_region: tuple[int, int, int, int] | None = None,
    ) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        screen = self.image.screenshot()
        region = search_region if search_region is not None else action.search_region
        return detect_step_match(
            screen,
            action.target,
            search_region=region,
        )

    def click(
        self,
        action_id: str,
        *,
        search_region: tuple[int, int, int, int] | None = None,
    ) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        match = self.find(action_id, search_region=search_region)
        if not match.found:
            message = (
                f"จับภาพไม่ผ่าน — ไม่พบ {action.target.label} "
                f"(score {match.score:.0%}, ต้อง ≥ {action.target.match_threshold:.0%})"
            )
            self._status(message)
            raise TemplateNotFoundError(message)

        center_x, center_y = match.center
        label = f"{action.target.label} ({match.score:.0%})"
        self._status(f"จับภาพผ่าน — {label} ที่ ({center_x}, {center_y})")
        self._highlight_match(match, label)
        self.image.click_at(center_x, center_y)
        return match

    def hover(
        self,
        action_id: str,
        *,
        search_region: tuple[int, int, int, int] | None = None,
    ) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        match = self.find(action_id, search_region=search_region)
        if not match.found:
            message = (
                f"จับภาพไม่ผ่าน — ไม่พบ {action.target.label} "
                f"(score {match.score:.0%}, ต้อง ≥ {action.target.match_threshold:.0%})"
            )
            self._status(message)
            raise TemplateNotFoundError(message)

        center_x, center_y = match.center
        label = f"{action.target.label} ({match.score:.0%})"
        self._status(f"จับภาพผ่าน — {label} ที่ ({center_x}, {center_y})")
        self._highlight_match(match, label)
        self.image.move_to(center_x, center_y)
        return match

    def _highlight_match(self, match: StepMatchResult, label: str) -> None:
        if not self.on_highlight:
            return
        self.on_highlight(
            ScreenRegion.from_match(
                match.x,
                match.y,
                match.width,
                match.height,
                label=label,
            )
        )

    def _status(self, message: str) -> None:
        if self.on_status:
            self.on_status(message)
