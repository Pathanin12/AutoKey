"""เปิดช่องค้นหาใน dialog เลือกข้อมูล — จับภาพปุ่ม ค้นหา แล้วคลิกเท่านั้น (ไม่ใช้ Tab)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from services.image_service import ImageService
from services.lookup_match_service import names_match
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
    verify_method: str = "ocr"
    post_search_wait: float = 0.4
    selection_name_subitems: tuple[int, ...] = (1, 0, 2, 3)
    selection_match_threshold: float = 0.85
    express_title_contains: str = "Express"
    selection_ocr_grid_region: tuple[int, int, int, int] = (520, 380, 980, 580)
    selection_ocr_name_x: tuple[int, int] = (640, 970)
    selection_ocr_row_height: int = 22
    selection_ocr_lang: str = "tha+eng"
    tesseract_cmd: str = ""

    @property
    def ocr_settings(self) -> LookupOcrSettings:
        return LookupOcrSettings(
            grid_region=self.selection_ocr_grid_region,
            name_x=self.selection_ocr_name_x,
            row_height=self.selection_ocr_row_height,
            lang=self.selection_ocr_lang,
            tesseract_cmd=self.tesseract_cmd,
        )


def activate_search_button(
    image: ImageService,
    settings: LookupSearchSettings,
    *,
    template_click: TemplateClickService | None = None,
) -> None:
    if settings.dialog_wait > 0:
        image.wait(settings.dialog_wait)

    if template_click is None or not template_click.enabled:
        raise RuntimeError("ต้องเปิด template_click และจับภาพปุ่ม ค้นหา")

    from services.template_click_service import TemplateNotFoundError

    attempts = max(1, settings.template_retries)
    for attempt in range(attempts):
        try:
            template_click.click("lookup_search")
            image.wait(0.1)
            return
        except TemplateNotFoundError:
            if attempt + 1 < attempts:
                image.wait(settings.template_retry_delay)
                continue
            raise


def search_and_select(
    image: ImageService,
    settings: LookupSearchSettings,
    query: str,
    *,
    confirm_enter_count: int | None = None,
    template_click: TemplateClickService | None = None,
    on_status: Callable[[str], None] | None = None,
) -> None:
    name = query.strip()
    if not name:
        return

    activate_search_button(image, settings, template_click=template_click)
    image.type_thai(name, clear_first=True)
    image.wait(0.15)

    presses = max(1, confirm_enter_count if confirm_enter_count is not None else settings.confirm_enter_count)
    if settings.verify_selection:
        image.press("enter")
        image.wait(settings.post_search_wait)
        _verify_lookup_selection(image, settings, name, on_status=on_status)
        select_presses = max(1, presses - 1)
    else:
        select_presses = presses

    for _ in range(select_presses):
        image.press("enter")
        image.wait(0.15)


def _verify_lookup_selection(
    image: ImageService,
    settings: LookupSearchSettings,
    query: str,
    *,
    on_status: Callable[[str], None] | None = None,
) -> None:
    selected = _read_verified_selection_text(image, settings)
    if selected and _looks_like_search_field(selected, query):
        selected = ""

    if names_match(query, selected, settings.selection_match_threshold):
        return

    message = f"ค้นหา vendor ไม่ตรง — ต้องการ: {query} / ได้: {selected or '(ว่าง)'}"
    if on_status:
        on_status(message)
    raise LookupSelectionMismatchError(message)


def _read_verified_selection_text(image: ImageService, settings: LookupSearchSettings) -> str:
    method = settings.verify_method.strip().lower() or "ocr"
    if method in {"ocr", "ocr_then_uia"}:
        text = read_highlighted_vendor_name(image, settings.ocr_settings)
        if text:
            return text
    if method in {"uia", "ocr_then_uia"}:
        return read_selected_row_text(
            name_subitems=settings.selection_name_subitems,
            express_title_contains=settings.express_title_contains,
        )
    return ""


def _looks_like_search_field(selected: str, query: str) -> bool:
    if not selected:
        return True
    return names_match(query, selected, 1.0)
