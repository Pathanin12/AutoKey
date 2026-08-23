"""โฟล์เลือกบริษัท — โฟล์แรก=ค้นหาเลย โฟล์สุดท้าย=กด 8 ก่อน (ดู constants/flow_model.py)"""

from __future__ import annotations

from dataclasses import dataclass

from constants.flow_model import FLOW_1_SEARCH_ENTER_COUNT
from services.image_service import ImageService


@dataclass(frozen=True)
class CompanySwitchSettings:
    menu_others: str
    submenu_keys: list[str]
    menu_wait: float
    use_search_button: bool = True
    search_enter_count: int = FLOW_1_SEARCH_ENTER_COUNT
    dismiss_work_date: bool = True


def select_company(
    image: ImageService,
    company_name: str,
    settings: CompanySwitchSettings,
    *,
    press_menu_others: bool = False,
) -> None:
    name = company_name.strip()
    if not name:
        return

    if press_menu_others:
        image.press(settings.menu_others)
        image.wait(settings.menu_wait)
        for key in settings.submenu_keys:
            if not key:
                continue
            image.press(str(key))
            image.wait(settings.menu_wait)

    if settings.use_search_button:
        image.click_if_found("btn_search.png")
        image.wait(0.3)

    image.type_thai(name, clear_first=True)
    image.wait(0.3)

    presses = max(1, settings.search_enter_count)
    for _ in range(presses):
        image.press("enter")
        image.wait(0.3)

    # Enter×2 แล้ว dialog วันที่ทำการ เด้งขึ้น — ไม่กด ตกลoud dialog เลือกข้อมูล
    if settings.dismiss_work_date:
        _dismiss_work_date_dialog(image, settings.menu_wait)


def _dismiss_work_date_dialog(image: ImageService, menu_wait: float) -> None:
    if image.click_if_found("btn_ok.png"):
        image.wait(menu_wait)
        return
    image.press("enter")
    image.wait(menu_wait)
