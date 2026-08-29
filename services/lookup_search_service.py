"""เปิดช่องค้นหาใน dialog เลือกข้อมูล — คลิกปุ่ม ค้นหา แล้วพิมพ์ (Express โฟกัสช่องให้)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from constants.routes import UI_TEXT
from models.step_match_result import StepMatchResult
from services.image_service import ImageService
from services.lookup_match_service import to_express_vendor_name

if TYPE_CHECKING:
    from services.template_click_service import TemplateClickService


class LookupSelectionMismatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class LookupSearchSettings:
    confirm_enter_count: int = 2
    dialog_wait: float = 0.35
    template_retries: int = 4
    template_retry_delay: float = 0.15
    post_search_wait: float = 0.4
    post_search_click_wait: float = 0.3
    paste_wait: float = 0.15


def search_and_select(
    image: ImageService,
    settings: LookupSearchSettings,
    query: str,
    *,
    confirm_enter_count: int | None = None,
    template_click: TemplateClickService | None = None,
    on_status: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    name = to_express_vendor_name(query)
    if not name:
        return

    _check_stop(should_stop)
    _click_search_button(image, settings, template_click=template_click)
    image.type_keys(name, clear_first=False)
    if on_status:
        on_status(UI_TEXT["type_log"].format(field="ช่องค้นหา", text=name))
    image.wait(settings.paste_wait)

    presses = max(1, confirm_enter_count if confirm_enter_count is not None else settings.confirm_enter_count)
    for index in range(presses):
        _check_stop(should_stop)
        image.press("enter")
        if index + 1 < presses:
            image.wait(settings.post_search_wait)


def _click_search_button(
    image: ImageService,
    settings: LookupSearchSettings,
    *,
    template_click: TemplateClickService | None = None,
) -> StepMatchResult:
    if settings.dialog_wait > 0:
        image.wait(settings.dialog_wait)

    if template_click is None or not template_click.enabled:
        raise RuntimeError("ต้องเปิด template_click และจับภาพปุ่ม ค้นหา")

    from services.template_click_service import TemplateNotFoundError

    attempts = max(1, settings.template_retries)
    last_error: TemplateNotFoundError | None = None
    for attempt in range(attempts):
        try:
            match = template_click.click("lookup_search")
            image.wait(settings.post_search_click_wait)
            return match
        except TemplateNotFoundError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                image.wait(settings.template_retry_delay)
                continue
            raise last_error
    raise RuntimeError("_click_search_button failed unexpectedly")


def _check_stop(should_stop: Callable[[], bool] | None) -> None:
    if should_stop and should_stop():
        raise InterruptedError("หยุดโดยผู้ใช้")
