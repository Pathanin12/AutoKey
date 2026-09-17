"""จับภาพหน้าจอ Express → หา template → คลิก"""

from __future__ import annotations

import time
from typing import Callable

from models.screen_region import ScreenRegion
from models.step_match_result import StepMatchResult
from models.template_click_settings import TemplateClickSettings
from models.template_target import TemplateTarget
from services.image_service import ImageService
from services.template_detect_service import detect_step_match
from services.template_match_service import clear_screen_cv_cache


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
        region = search_region if search_region is not None else action.search_region
        screen, origin = self.image.screenshot_region(region)
        try:
            match = detect_step_match(screen, action.target)
            return match.translated(origin[0], origin[1])
        finally:
            _close_screen(screen)

    def click(
        self,
        action_id: str,
        *,
        search_region: tuple[int, int, int, int] | None = None,
    ) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        match = self.find(action_id, search_region=search_region)
        return self._click_match(action.target, match)

    def click_first(
        self,
        action_ids: tuple[str, ...],
        *,
        search_region: tuple[int, int, int, int] | None = None,
    ) -> StepMatchResult:
        """ถ่ายหน้าจอครั้งเดียว แล้วลองหลาย template"""
        if not action_ids:
            raise TemplateNotFoundError("ไม่มีปุ่มให้จับภาพ")
        first = self.settings.get_action(action_ids[0])
        region = search_region if search_region is not None else first.search_region
        screen, origin = self.image.screenshot_region(region)
        last_match: StepMatchResult | None = None
        last_threshold = first.target.match_threshold
        try:
            for action_id in action_ids:
                action = self.settings.get_action(action_id)
                match = detect_step_match(screen, action.target).translated(origin[0], origin[1])
                last_match = match
                last_threshold = action.target.match_threshold
                if match.found:
                    return self._click_match(action.target, match)
        finally:
            _close_screen(screen)
        score = last_match.score if last_match else 0.0
        labels = " / ".join(
            self.settings.get_action(action_id).target.label for action_id in action_ids
        )
        message = (
            f"จับภาพไม่ผ่าน — ไม่พบ {labels} "
            f"(score {score:.0%}, ต้อง ≥ {last_threshold:.0%})"
        )
        self._status(message)
        raise TemplateNotFoundError(message)

    def _click_match(self, target: TemplateTarget, match: StepMatchResult) -> StepMatchResult:
        if not match.found:
            message = (
                f"จับภาพไม่ผ่าน — ไม่พบ {target.label} "
                f"(score {match.score:.0%}, ต้อง ≥ {target.match_threshold:.0%})"
            )
            self._status(message)
            raise TemplateNotFoundError(message)

        center_x, center_y = match.center
        label = f"{target.label} ({match.score:.0%})"
        self._status(f"จับภาพผ่าน — {label} ที่ ({center_x}, {center_y})")
        self._highlight_match(match, label)
        self.image.click_at(center_x, center_y)
        return match

    def wait_until_found(
        self,
        action_id: str,
        *,
        timeout: float = 60.0,
        poll_wait: float = 0.25,
        should_stop: Callable[[], bool] | None = None,
    ) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        deadline = time.monotonic() + timeout
        last: StepMatchResult | None = None
        while True:
            if should_stop and should_stop():
                raise InterruptedError("หยุดโดยผู้ใช้")
            last = self.find(action_id)
            if last.found:
                self._status(
                    f"จับภาพผ่าน — {action.target.label} ({last.score:.0%})"
                )
                return last
            if time.monotonic() >= deadline:
                score = last.score if last else 0.0
                raise TemplateNotFoundError(
                    f"รอไม่เจอ {action.target.label} "
                    f"(score {score:.0%}, ต้อง ≥ {action.target.match_threshold:.0%})"
                )
            self.image.wait(poll_wait)

    def wait_until_first(
        self,
        action_ids: tuple[str, ...],
        *,
        timeout: float = 60.0,
        poll_wait: float = 0.25,
        should_stop: Callable[[], bool] | None = None,
    ) -> StepMatchResult:
        if not action_ids:
            raise TemplateNotFoundError("ไม่มีปุ่มให้จับภาพ")
        first = self.settings.get_action(action_ids[0])
        labels = " / ".join(
            self.settings.get_action(action_id).target.label for action_id in action_ids
        )
        deadline = time.monotonic() + timeout
        last_match: StepMatchResult | None = None
        last_threshold = first.target.match_threshold
        while True:
            if should_stop and should_stop():
                raise InterruptedError("หยุดโดยผู้ใช้")
            for action_id in action_ids:
                action = self.settings.get_action(action_id)
                region = action.search_region
                screen, origin = self.image.screenshot_region(region)
                try:
                    match = detect_step_match(screen, action.target).translated(origin[0], origin[1])
                    last_match = match
                    last_threshold = action.target.match_threshold
                    if match.found:
                        self._status(
                            f"จับภาพผ่าน — {action.target.label} ({match.score:.0%})"
                        )
                        return match
                finally:
                    _close_screen(screen)
            if time.monotonic() >= deadline:
                score = last_match.score if last_match else 0.0
                raise TemplateNotFoundError(
                    f"รอไม่เจอ {labels} "
                    f"(score {score:.0%}, ต้อง ≥ {last_threshold:.0%})"
                )
            self.image.wait(poll_wait)

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


def _close_screen(screen) -> None:
    clear_screen_cv_cache(screen)
    close = getattr(screen, "close", None)
    if close is None:
        return
    close()
