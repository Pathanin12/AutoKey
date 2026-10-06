from __future__ import annotations

import re

from constants.date_utils import THAI_MONTHS
from models.month_year_period import MonthYearPeriod
from services.pp30_amount_service import MONEY_RE, line_money, money_amounts

_LINE6_RE = re.compile(r"(?<!\d)6\.\s*รวม")
_LINE7_RE = re.compile(r"(?<!\d)7\.\s*เงินเพิ่ม")
_LINE8_MARKER = "และเงินเพิ่ม"
_COUNT_RE = re.compile(r"(?<!\d)(\d{1,6})(?!\d)")
_BE_YEAR_RE = re.compile(r"พ\.?\s*ศ\.?\s*(\d{4})")
_CHECK_RE = re.compile(r"[ü✓✔☑]")
_NEXT_MONTH_CHECK_RE = re.compile(r"\s*[ü✓✔☑]\s*\(\s*\d{1,2}\s*\)")
_MONTH_NAMES = sorted(THAI_MONTHS, key=len, reverse=True)


def extract_line_6_and_7(text: str) -> tuple[int, float, float, float] | None:
    people = 0
    income = 0.0
    tax: float | None = None
    surcharge = 0.0
    for raw in (text or "").splitlines():
        if _LINE8_MARKER in raw:
            continue
        if _LINE6_RE.search(raw):
            amounts = money_amounts(raw)
            stripped = MONEY_RE.sub(" ", _LINE6_RE.sub(" ", raw, count=1))
            counts = [int(item) for item in _COUNT_RE.findall(stripped)]
            if counts:
                people = counts[-1]
            if len(amounts) >= 2:
                income = amounts[-2]
                tax = amounts[-1]
            elif amounts:
                tax = amounts[-1]
            continue
        if _LINE7_RE.search(raw):
            amount = line_money(raw, allow_zero=True)
            surcharge = 0.0 if amount is None else amount
    if tax is None:
        return None
    return people, income, tax, surcharge


def extract_income_period(text: str) -> MonthYearPeriod | None:
    year = _be_year(text or "")
    month = _checked_month(text or "")
    if year is None or month is None:
        return None
    period = MonthYearPeriod(month=month, year=year % 100)
    return period if period.is_valid else None


def _be_year(text: str) -> int | None:
    marker = text.find("เดือนที่จ่ายเงินได้พึงประเมิน")
    window = text[marker : marker + 500] if marker >= 0 else text
    match = _BE_YEAR_RE.search(window) or _BE_YEAR_RE.search(text)
    if not match:
        return None
    year = int(match.group(1))
    return year if year >= 2500 else None


def _checked_month(text: str) -> int | None:
    pattern = "|".join(re.escape(name) for name in _MONTH_NAMES)
    for match in re.finditer(pattern, text):
        month = THAI_MONTHS[match.group(0)]
        prefix = text[max(0, match.start() - 12) : match.start()]
        suffix = text[match.end() : match.end() + 12]
        if _CHECK_RE.search(prefix):
            return month
        if _CHECK_RE.match(suffix.lstrip()) and not _NEXT_MONTH_CHECK_RE.match(suffix):
            return month
    return None
