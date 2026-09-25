from __future__ import annotations

import re

from constants.date_utils import THAI_MONTHS, format_express_pv_date
from services.pp30_amount_service import line_money

_SLASH_DATE_RE = re.compile(
    r"วันที่่?\s*[:：]?\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})"
)
_FILE_DATE_RE = re.compile(
    r"ยื่นวันที่่?\s*(\d{1,2})\s*เดือน\s*([ก-๙.]+)\s*พ\.?\s*ศ\.?\s*(\d{4})"
)
_LINE3_RE = re.compile(r"(?<!\d)3\.\s*เงินเพิ่ม")
_LINE4_MARKER = "และเงินเพิ่ม"


def extract_line_2_and_3(text: str) -> tuple[float, float] | None:
    line2: float | None = None
    line3: float | None = None
    for raw in (text or "").splitlines():
        if _LINE4_MARKER in raw:
            continue
        if _LINE3_RE.search(raw):
            amount = line_money(raw, allow_zero=True)
            line3 = 0.0 if amount is None else amount
            continue
        if "รวมยอดภาษีที่นำส่ง" in raw:
            amount = line_money(raw, allow_zero=True)
            if amount is not None:
                line2 = amount
    if line2 is None:
        return None
    return line2, 0.0 if line3 is None else line3


def extract_pv_date(text: str) -> str:
    slash = _SLASH_DATE_RE.search(text or "")
    if slash:
        day, month, year = slash.groups()
        return format_express_pv_date(f"{int(day):02d}/{int(month):02d}/{year}")
    filed = _FILE_DATE_RE.search(text or "")
    if not filed:
        return ""
    day_text, month_name, year_text = filed.groups()
    month = THAI_MONTHS.get(month_name.replace(".", ""))
    if month is None:
        return ""
    return format_express_pv_date(f"{int(day_text):02d}/{month:02d}/{year_text}")
