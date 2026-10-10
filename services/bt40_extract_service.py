from __future__ import annotations

import re

from constants.date_utils import THAI_MONTHS, format_express_pv_date
from models.month_year_period import MonthYearPeriod
from services.pnd30_extract_service import extract_pv_date
from services.pp30_amount_service import line_money, money_amounts

_MONTH_NAMES = sorted(THAI_MONTHS, key=len, reverse=True)
_LINE7_RE = re.compile(r"(?<!\d)7\.")
_LINE8_RE = re.compile(r"(?<!\d)8\.")
_LINE13_RE = re.compile(r"(?<!\d)13\.\s*เงินเพิ่ม")
_LINE14_RE = re.compile(r"(?<!\d)14\.\s*เบี้ยปรับ")
_LINE17_RE = re.compile(r"(?<!\d)17\.\s*รวมภาษีทั้งสิ้น")
_PRINT_DATE_RE = re.compile(
    r"พิมพ์\s*ณ\s*วันที่\s*(\d{1,2})\s*("
    + "|".join(re.escape(name) for name in _MONTH_NAMES)
    + r")\s*(?:พ\.?\s*ศ\.?\s*)?(\d{4})"
)


def extract_bt40_amounts(text: str) -> tuple[float, float, float, float] | None:
    line7 = _line7_receipt(text or "")
    line13 = _labeled_amount(text or "", _LINE13_RE)
    line14 = _labeled_amount(text or "", _LINE14_RE)
    line17 = _labeled_amount(text or "", _LINE17_RE)
    if line7 is None and line17 is None:
        return None
    return (
        0.0 if line7 is None else line7,
        0.0 if line13 is None else line13,
        0.0 if line14 is None else line14,
        0.0 if line17 is None else line17,
    )


def extract_bt40_pv_date(text: str) -> str:
    printed = _PRINT_DATE_RE.search(text or "")
    if printed:
        day_text, month_name, year_text = printed.groups()
        month = THAI_MONTHS.get(month_name)
        if month is not None:
            return format_express_pv_date(f"{int(day_text):02d}/{month:02d}/{year_text}")
    return extract_pv_date(text)


_BE_YEAR_RE = re.compile(r"พ\.?\s*ศ\.?[.\s]*(\d{4})")
_CHECKED_MONTH_RE = re.compile(
    r"[ü✓✔☑]\s*\(\s*(\d{1,2})\s*\)\s*(" + "|".join(re.escape(name) for name in _MONTH_NAMES) + r")"
)


def extract_bt40_period(text: str) -> MonthYearPeriod | None:
    window = _month_window(text or "")
    year_match = _BE_YEAR_RE.search(window) or _BE_YEAR_RE.search(text or "")
    month_match = _CHECKED_MONTH_RE.search(window)
    if year_match is None or month_match is None:
        return None
    year = int(year_match.group(1))
    if year < 2500:
        return None
    month = THAI_MONTHS.get(month_match.group(2))
    if month is None:
        return None
    period = MonthYearPeriod(month=month, year=year % 100)
    return period if period.is_valid else None


def _month_window(text: str) -> str:
    start = text.find("เดือนภาษี")
    if start < 0:
        start = 0
    end = len(text)
    for marker in ("ประเภทกิจการ", "1. การธนาคาร"):
        pos = text.find(marker, start)
        if 0 <= pos < end:
            end = pos
    return text[start:end]


def _line7_receipt(text: str) -> float | None:
    collecting = False
    chunks: list[str] = []
    for raw in text.splitlines():
        if _LINE8_RE.search(raw):
            break
        if _LINE7_RE.search(raw):
            collecting = True
        if collecting:
            chunks.append(raw)
    amounts = money_amounts("\n".join(chunks))
    if not amounts:
        return None
    return amounts[0]


def _labeled_amount(text: str, pattern: re.Pattern[str]) -> float | None:
    for raw in text.splitlines():
        if pattern.search(raw):
            amount = line_money(raw, allow_zero=True)
            return 0.0 if amount is None else amount
    return None
