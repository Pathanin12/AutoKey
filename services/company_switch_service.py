"""โฟล์เลือกบริษัท — โฟล์แรก=ค้นหาใน dialog | โฟล์สุดท้าย=กด 8→8 เท่านั้น"""

from __future__ import annotations

from dataclasses import dataclass

from constants.flow_model import FLOW_1_SEARCH_ENTER_COUNT
from services.image_service import ImageService
from services.lookup_search_service import LookupSearchSettings, search_and_select


@dataclass(frozen=True)
class CompanySwitchSettings:
    menu_others: str
    submenu_keys: list[str]
    menu_wait: float
    lookup_search: LookupSearchSettings
    search_enter_count: int = FLOW_1_SEARCH_ENTER_COUNT
    exit_pv_esc_count: int = 2


def open_change_company_menu(image: ImageService, settings: CompanySwitchSettings) -> None:
    """โฟล์สุดท้าย — จากเมนูหลัก: 8 อื่นๆ → 8 เปลี่ยนบริษัท"""
    image.press(settings.menu_others)
    image.wait(settings.menu_wait)
    for key in settings.submenu_keys:
        if not key:
            continue
        image.press(str(key))
        image.wait(settings.menu_wait)


def select_company_on_dialog(
    image: ImageService,
    company_name: str,
    settings: CompanySwitchSettings,
) -> None:
    """โฟล์แรก — อยู่ dialog เลือกข้อมูลแล้ว: Tab→ค้นหา → พิมพ์ → Enter×2"""
    name = company_name.strip()
    if not name:
        return
    search_and_select(
        image,
        settings.lookup_search,
        name,
        confirm_enter_count=settings.search_enter_count,
    )
