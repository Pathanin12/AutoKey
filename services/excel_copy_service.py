"""โฟกัส Excel → Go To เซลล์ชื่อ vendor → Ctrl+C"""

from __future__ import annotations

import sys
from typing import Callable

from constants.routes import UI_TEXT
from models.excel_copy_context import ExcelCopyContext
from models.window_focus_settings import WindowFocusSettings
from services.clipboard_service import read_text
from services.image_service import ImageService
from services.lookup_match_service import clipboard_matches_query
from services.window_focus_service import focus_express_window, focus_window_by_title


def copy_legal_name_from_excel(
    image: ImageService,
    context: ExcelCopyContext,
    *,
    express_focus: WindowFocusSettings,
    on_status: Callable[[str], None] | None = None,
) -> str:
    if sys.platform != "win32":
        return _fallback_copy(context, on_status=on_status)

    name = context.legal_name
    if not name:
        raise RuntimeError("ไม่พบชื่อ vendor ใน Excel")

    if on_status:
        on_status(
            UI_TEXT["excel_copy_log"].format(
                cell=context.cell_address,
                text=name,
            )
        )

    if not _focus_excel_workbook(context, on_status=on_status):
        if on_status:
            on_status("ไม่พบหน้าต่าง Excel — ใช้ copy จากข้อมูลในไฟล์แทน")
        return _fallback_copy(context, on_status=on_status)

    image.wait(0.15)
    image.press("f5")
    image.wait(0.25)
    image.type_text(context.cell_address, clear_first=True)
    image.press("enter")
    image.wait(0.15)
    image.copy_selection()
    image.wait(0.2)

    clipboard = read_text().strip()
    if not clipboard:
        if on_status:
            on_status("Excel copy ว่าง — ใช้ copy จากข้อมูลในไฟล์แทน")
        return _fallback_copy(context, on_status=on_status)

    if not clipboard_matches_query(clipboard, name):
        if on_status:
            on_status(
                f"Excel copy ไม่ตรง — ต้องการ: {name} / ได้: {clipboard[:80]}"
            )
        return _fallback_copy(context, on_status=on_status)

    focus_express_window(express_focus, on_status=on_status)
    image.wait(0.1)
    return clipboard


def _focus_excel_workbook(
    context: ExcelCopyContext,
    *,
    on_status: Callable[[str], None] | None = None,
) -> bool:
    needles = (
        context.excel_path.name,
        context.excel_path.stem,
    )
    for needle in needles:
        if not needle:
            continue
        if focus_window_by_title(
            needle,
            on_status=on_status,
            success_label=f"โฟกัส Excel แล้ว: {needle}",
        ):
            return True
    return False


def _fallback_copy(
    context: ExcelCopyContext,
    *,
    on_status: Callable[[str], None] | None = None,
) -> str:
    from services.clipboard_service import copy_text

    copy_text(context.legal_name)
    clipboard = read_text().strip()
    if not clipboard:
        raise RuntimeError(f"Clipboard ว่าง — ไม่สามารถ copy: {context.legal_name}")
    if on_status:
        on_status(
            UI_TEXT["clipboard_copy_log"].format(
                field="ค้นหา (จากข้อมูล Excel)",
                text=context.legal_name,
            )
        )
    return clipboard
