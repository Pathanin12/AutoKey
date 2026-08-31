from __future__ import annotations

import calendar
import re
from datetime import date

PV_DATE_EXAMPLE = "25/07/69"
_SEPARATORS = re.compile(r"[/\-.\s]+")


def default_work_date() -> str:
    today = date.today()
    be_year = today.year + 543
    return format_express_pv_date(
        f"{today.day:02d}/{today.month:02d}/{be_year % 100:02d}"
    )


def mask_express_pv_date(value: str) -> str:
    """ใส่ / ขณะพิมพ์ เช่น 250769 → 25/07/69"""
    digits = "".join(ch for ch in value if ch.isdigit())[:6]
    if len(digits) <= 2:
        return digits
    if len(digits) <= 4:
        return f"{digits[:2]}/{digits[2:]}"
    return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"


def format_express_pv_date(value: str) -> str:
    """Express PV: วัน/เดือน/ปี(2 หลัก) เช่น 25/07/69"""
    text = value.strip()
    if not text:
        return ""

    parts = _date_parts(text)
    if parts is None:
        return mask_express_pv_date(text)

    day, month, year = parts
    year = _express_year(year)
    return f"{day:02d}/{month:02d}/{year:02d}"


def _date_parts(text: str) -> tuple[int, int, int] | None:
    chunks = [part for part in _SEPARATORS.split(text) if part]
    if len(chunks) == 3:
        try:
            return int(chunks[0]), int(chunks[1]), int(chunks[2])
        except ValueError:
            return None

    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 6:
        return int(digits[:2]), int(digits[2:4]), int(digits[4:6])
    if len(digits) == 8:
        return int(digits[:2]), int(digits[2:4]), int(digits[4:8])
    return None


def _express_year(year: int) -> int:
    if year >= 2400:
        return year % 100
    if year >= 1900:
        return (year + 543) % 100
    return year % 100


def _ce_year(year: int) -> int:
    if year >= 2400:
        return year - 543
    if year >= 1900:
        return year
    return 2500 + (year % 100) - 543


def express_month_date_range(pv_date: str) -> tuple[str, str]:
    """วันแรกและวันสุดท้ายของเดือนจากวันที่ UI เช่น 01/08/69 และ 31/08/69"""
    parts = _date_parts(pv_date.strip())
    if parts is None:
        raise ValueError(f"วันที่ใบสำคัญไม่ถูกต้อง: {pv_date}")
    _day, month, year = parts
    year2 = _express_year(year)
    last_day = calendar.monthrange(_ce_year(year), month)[1]
    start = f"01/{month:02d}/{year2:02d}"
    end = f"{last_day:02d}/{month:02d}/{year2:02d}"
    return start, end


def express_month_folder_name(pv_date: str) -> str:
    """โฟลเดอร์เดือนจากวันที่ UI เช่น 08-69"""
    parts = _date_parts(pv_date.strip())
    if parts is None:
        raise ValueError(f"วันที่ใบสำคัญไม่ถูกต้อง: {pv_date}")
    _day, month, year = parts
    return f"{month:02d}-{_express_year(year):02d}"
