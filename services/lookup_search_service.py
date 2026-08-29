"""เปิดช่องค้นหาใน dialog เลือกข้อมูล — คลิกปุ่ม ค้นหา แล้ววางเลย (Express โฟกัสช่องให้)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from constants.routes import UI_TEXT
from models.step_match_result import StepMatchResult
from services.clipboard_service import copy_text
from services.image_service import ImageService
from services.lookup_match_service import (
    is_plausible_vendor_name,
    name_similarity,
    names_match,
    names_match_complete,
)
from services.lookup_ocr_service import LookupOcrSettings, read_highlighted_vendor_name
from services.lookup_selection_read_service import read_selected_row_text

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
    verify_selection: bool = True
    verify_method: str = "ocr_then_uia"
    post_search_wait: float = 0.4
    selection_name_subitems: tuple[int, ...] = (1, 0, 2, 3)
    selection_match_threshold: float = 0.85
    selection_down_max_attempts: int = 15
    selection_down_wait: float = 0.4
    express_title_contains: str = "Express"
    selection_ocr_grid_region: tuple[int, int, int, int] = (520, 380, 980, 580)
    selection_ocr_name_x: tuple[int, int] = (530, 780)
    selection_ocr_row_height: int = 22
    selection_ocr_lang: str = "tha"
    tesseract_cmd: str = ""
    post_search_click_wait: float = 0.3
    paste_wait: float = 0.15

    @property
    def ocr_settings(self) -> LookupOcrSettings:
        return LookupOcrSettings(
            grid_region=self.selection_ocr_grid_region,
            name_x=self.selection_ocr_name_x,
            row_height=self.selection_ocr_row_height,
            lang=self.selection_ocr_lang,
            tesseract_cmd=self.tesseract_cmd,
        )


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
    name = query.strip()
    if not name:
        return

    _check_stop(should_stop)
    copy_text(name)
    _click_search_button(image, settings, template_click=template_click)
    image.paste_clipboard(clear_first=False)
    if on_status:
        on_status(UI_TEXT["paste_log"].format(field="ช่องค้นหา", text=name))
    image.wait(settings.paste_wait)

    presses = max(1, confirm_enter_count if confirm_enter_count is not None else settings.confirm_enter_count)
    if settings.verify_selection:
        image.press("enter")
        image.wait(settings.post_search_wait)
        _verify_lookup_selection(
            image,
            settings,
            name,
            on_status=on_status,
            should_stop=should_stop,
        )
        select_presses = max(1, presses - 1)
    else:
        select_presses = presses

    for _ in range(select_presses):
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
            image.wait(settings.post_search_click_wait)
            return match
        except TemplateNotFoundError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                image.wait(settings.template_retry_delay)
                continue
            raise last_error
    raise RuntimeError("_click_search_button failed unexpectedly")


def _verify_lookup_selection(
    image: ImageService,
    settings: LookupSearchSettings,
    query: str,
    *,
    on_status: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    attempts = max(1, settings.selection_down_max_attempts)
    last_selected = ""

    for attempt in range(attempts):
        _check_stop(should_stop)

        selected = _read_verified_selection_text(image, settings, query)
        if selected and _looks_like_search_field(selected, query):
            selected = ""
        last_selected = selected

        if names_match_complete(query, selected, settings.selection_match_threshold):
            if on_status and attempt > 0:
                on_status(f"เลือก vendor แถวที่ {attempt + 1}: {selected}")
            return

        if attempt + 1 >= attempts:
            break

        if on_status:
            shown = selected if is_plausible_vendor_name(selected) else "OCR ไม่ชัด"
            on_status(
                f"ชื่อไม่ตรงครบ — กด Down ({shown or 'ว่าง'}) "
                f"→ ต้องการ: {query}"
            )
        image.press("down")
        _interruptible_wait(image, settings.selection_down_wait, should_stop=should_stop)

    message = f"ค้นหา vendor ไม่ตรง — ต้องการ: {query} / ได้: {last_selected or '(ว่าง)'}"
    if on_status:
        on_status(message)
    raise LookupSelectionMismatchError(message)


def _read_verified_selection_text(
    image: ImageService,
    settings: LookupSearchSettings,
    query: str,
) -> str:
    method = settings.verify_method.strip().lower() or "ocr_then_uia"
    ocr_text = ""
    uia_text = ""

    if method in {"ocr", "ocr_then_uia"}:
        raw = read_highlighted_vendor_name(image, settings.ocr_settings, expected=query)
        if raw and is_plausible_vendor_name(raw):
            ocr_text = raw

    if method in {"uia", "ocr_then_uia"}:
        raw = read_selected_row_text(
            name_subitems=settings.selection_name_subitems,
            express_title_contains=settings.express_title_contains,
        )
        if raw and is_plausible_vendor_name(raw):
            uia_text = raw

    if ocr_text and uia_text:
        if name_similarity(query, uia_text) >= name_similarity(query, ocr_text):
            return uia_text
        return ocr_text

    return uia_text or ocr_text


def _looks_like_search_field(selected: str, query: str) -> bool:
    if not selected:
        return True
    return names_match(query, selected, 1.0)


def _check_stop(should_stop: Callable[[], bool] | None) -> None:
    if should_stop and should_stop():
        raise InterruptedError("หยุดโดยผู้ใช้")


def _interruptible_wait(
    image: ImageService,
    seconds: float,
    *,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    import time

    if seconds <= 0:
        _check_stop(should_stop)
        return

    deadline = time.monotonic() + seconds
    while True:
        _check_stop(should_stop)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        image.wait(min(0.08, remaining))
