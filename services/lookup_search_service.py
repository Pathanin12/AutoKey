"""เปิดช่องค้นหาใน dialog เลือกข้อมูล — คลิก ค้นหา แล้ววางด้วย type_thai"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from constants.routes import UI_TEXT
from models.step_match_result import StepMatchResult
from services.image_service import ImageService
from services.lookup_match_service import to_express_vendor_name
from services.lookup_ocr_verify_service import check_highlighted_vendor

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
    verify_selection: bool = True
    verify_similarity: float = 0.75
    ocr_region: tuple[int, int, int, int] = (480, 280, 1020, 600)


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
    image.type_thai(name, clear_first=True)
    image.wait(0.15)
    if on_status:
        on_status(UI_TEXT["paste_log"].format(field="ช่องค้นหา", text=name))

    presses = max(1, confirm_enter_count if confirm_enter_count is not None else settings.confirm_enter_count)
    if settings.verify_selection:
        _check_stop(should_stop)
        image.wait(settings.post_search_wait)
        if on_status:
            on_status("กำลัง OCR แถวแรกในกริด...")
        _verify_first_selection(query, settings, on_status=on_status)

    for _ in range(presses):
        _check_stop(should_stop)
        image.press("enter")
        image.wait(0.15)


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
            image.wait(0.1)
            return match
        except TemplateNotFoundError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                image.wait(settings.template_retry_delay)
                continue
            raise last_error
    raise RuntimeError("_click_search_button failed unexpectedly")


def _verify_first_selection(
    query: str,
    settings: LookupSearchSettings,
    *,
    on_status: Callable[[str], None] | None = None,
) -> None:
    check = check_highlighted_vendor(query, region=settings.ocr_region)
    preview = _preview_ocr_text(check.actual)
    percent = f"{check.similarity:.0%}"
    if on_status:
        on_status(f"OCR แถวแรก {percent}: {preview}")
    if check.similarity < settings.verify_similarity:
        raise LookupSelectionMismatchError(
            f"ชื่อที่เลือกไม่ถึง {settings.verify_similarity:.0%} "
            f"— ต้องการ: {check.expected} / อ่านได้: {preview} ({percent})"
        )


def _preview_ocr_text(text: str, limit: int = 80) -> str:
    value = text.strip() or "(ว่าง)"
    if len(value) <= limit:
        return value
    return value[:limit] + "…"


def _check_stop(should_stop: Callable[[], bool] | None) -> None:
    if should_stop and should_stop():
        raise InterruptedError("หยุดโดยผู้ใช้")
