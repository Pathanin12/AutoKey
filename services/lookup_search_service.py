"""เปิดช่องค้นหาใน dialog เลือกข้อมูล — จับภาพปุ่ม ค้นหา แล้วคลิก (fallback เป็น Tab+Enter)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from services.image_service import ImageService

if TYPE_CHECKING:
    from services.template_click_service import TemplateClickService


@dataclass(frozen=True)
class LookupSearchSettings:
    """Tab ไปปุ่ม ค้นหา แล้ว Enter — ใช้เมื่อจับภาพไม่ได้"""

    button_tabs: int = 2
    field_tabs: int = 0
    confirm_enter_count: int = 1


def activate_search_button(
    image: ImageService,
    settings: LookupSearchSettings,
    *,
    template_click: TemplateClickService | None = None,
) -> None:
    if template_click is not None and template_click.enabled:
        from services.template_click_service import TemplateNotFoundError

        try:
            template_click.click("lookup_search")
            image.wait(0.3)
            if settings.field_tabs > 0:
                image.press("tab", presses=settings.field_tabs)
                image.wait(0.2)
            return
        except TemplateNotFoundError:
            if not template_click.settings.fallback_to_keyboard:
                raise

    if settings.button_tabs > 0:
        image.press("tab", presses=settings.button_tabs)
        image.wait(0.2)
    image.press("enter")
    image.wait(0.3)
    if settings.field_tabs > 0:
        image.press("tab", presses=settings.field_tabs)
        image.wait(0.2)


def search_and_select(
    image: ImageService,
    settings: LookupSearchSettings,
    query: str,
    *,
    confirm_enter_count: int | None = None,
    template_click: TemplateClickService | None = None,
) -> None:
    name = query.strip()
    if not name:
        return
    activate_search_button(image, settings, template_click=template_click)
    image.type_thai(name, clear_first=True)
    image.wait(0.3)
    presses = max(1, confirm_enter_count if confirm_enter_count is not None else settings.confirm_enter_count)
    for _ in range(presses):
        image.press("enter")
        image.wait(0.3)
