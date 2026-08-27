from __future__ import annotations

from datetime import date


def default_work_date() -> str:
    today = date.today()
    be_year = today.year + 543
    return format_express_pv_date(
        f"{today.day:02d}/{today.month:02d}/{be_year % 100:02d}"
    )


def format_express_pv_date(value: str) -> str:
    """Express PV: วัน/เดือน/ปี(2 หลัก) เช่น 25/07/69"""
    text = value.strip()
    if not text:
        return ""

    parts = text.split("/")
    if len(parts) != 3:
        return text

    day_s, month_s, year_s = (part.strip() for part in parts)
    try:
        day = int(day_s)
        month = int(month_s)
        year = int(year_s)
    except ValueError:
        return text

    if year >= 2400:
        year = year % 100
    elif year >= 1900:
        year = (year + 543) % 100

    return f"{day:02d}/{month:02d}/{year:02d}"
