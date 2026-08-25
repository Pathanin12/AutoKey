"""จับภาพหน้าจอ Express → หา template → คลิก"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.routes import PROJECT_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH
from models.screen_region import ScreenRegion
from models.step_match_result import StepMatchResult
from models.template_click_settings import TemplateClickAction, TemplateClickSettings
from services.image_service import ImageService
from services.template_match_service import load_image
from services.template_detect_service import detect_step_match


class TemplateNotFoundError(RuntimeError):
    pass


class TemplateClickService:
    def __init__(
        self,
        image: ImageService,
        settings: TemplateClickSettings,
        *,
        dry_run: bool = False,
        on_status: Callable[[str], None] | None = None,
        on_highlight: Callable[[ScreenRegion], None] | None = None,
    ) -> None:
        self.image = image
        self.settings = settings
        self.dry_run = dry_run
        self.on_status = on_status
        self.on_highlight = on_highlight

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    def find(self, action_id: str) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        screen = self.capture_screen()
        return detect_step_match(
            screen,
            action.target,
            search_region=action.search_region,
        )

    def click(self, action_id: str) -> StepMatchResult:
        action = self.settings.get_action(action_id)
        match = self.find(action_id)
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

        if self.dry_run:
            self._status(f"[dry_run] คลิก {label} ที่ ({center_x}, {center_y})")
        else:
            self.image.click_at(center_x, center_y)
        return match

    def capture_screen(self):
        if self.dry_run:
            reference = self._resolve_dry_run_reference()
            if reference is not None:
                image = load_image(reference)
                if image.size != (SCREEN_WIDTH, SCREEN_HEIGHT):
                    image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT))
                return image.convert("RGBA")

        return self.image.screenshot()

    def _resolve_dry_run_reference(self) -> Path | None:
        configured = self.settings.dry_run_reference.strip()
        if configured:
            path = Path(configured)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            if path.exists():
                return path
        return None

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
