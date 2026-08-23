from __future__ import annotations

from datetime import date


def default_work_date() -> str:
    today = date.today()
    return f"{today.day:02d}/{today.month:02d}/{today.year + 543}"
