"""กลับ dialog เลือกข้อมูล — Shift+F11 → Tab → Enter×2"""

from __future__ import annotations

from constants.routes import AFTER_SAVE_WAIT, COMPANY_DIALOG_WAIT
from services.image_service import ImageService


def return_to_company_dialog(image: ImageService) -> None:
    image.press("shift", "f11")
    image.wait(AFTER_SAVE_WAIT)
    image.press("tab")
    image.press("enter", presses=2)
    image.wait(COMPANY_DIALOG_WAIT)
