"""เปิดช่องค้นหาใน dialog เลือกข้อมูล — แทนคลิกปุ่ม ค้นหา"""

from __future__ import annotations

from dataclasses import dataclass

from services.image_service import ImageService


@dataclass(frozen=True)
class LookupSearchSettings:
    """Tab ไปปุ่ม ค้นหา แล้ว Enter — ปรับใน config.yaml ถ้าโฟกัสไม่ตรง"""

    button_tabs: int = 2
    field_tabs: int = 0
    confirm_enter_count: int = 1


def activate_search_button(image: ImageService, settings: LookupSearchSettings) -> None:
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
) -> None:
    name = query.strip()
    if not name:
        return
    activate_search_button(image, settings)
    image.type_thai(name, clear_first=True)
    image.wait(0.3)
    presses = max(1, confirm_enter_count if confirm_enter_count is not None else settings.confirm_enter_count)
    for _ in range(presses):
        image.press("enter")
        image.wait(0.3)
