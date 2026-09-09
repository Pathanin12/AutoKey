"""ยอดเงินบนแบบ ภพ.30 — ยังไม่จัดประเภท"""

from __future__ import annotations

import re

AMOUNT_TOLERANCE = 0.005
MONEY_RE = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})+|\d{1,7})\.(\d{2})(?!\d)")


def parse_money(raw: str) -> float:
    return float(raw.replace(",", ""))


def money_amounts(text: str) -> list[float]:
    amounts: list[float] = []
    for match in MONEY_RE.finditer(text or ""):
        value = parse_money(match.group(0))
        if value <= 0:
            continue
        amounts.append(round(value, 2))
    return amounts


def eq_amount(left: float, right: float) -> bool:
    return abs(left - right) < AMOUNT_TOLERANCE


def has_amount(value: float) -> bool:
    return value > AMOUNT_TOLERANCE


def is_vat_base(amount: float, amounts: list[float]) -> bool:
    """ฐานขาย/ซื้อ ที่ภาษี ~7% ไม่ใช่ข้อ 8/10/11"""
    for vat in amounts:
        if vat <= AMOUNT_TOLERANCE or vat >= amount:
            continue
        if amount <= vat * 5:
            continue
        if 0.065 <= vat / amount <= 0.075:
            return True
    return False


def line_money(line: str, *, allow_zero: bool) -> float | None:
    matches = list(MONEY_RE.finditer(line or ""))
    if not matches:
        return None
    value = parse_money(matches[-1].group(0))
    if value < 0:
        return None
    if not allow_zero and value <= 0:
        return None
    return round(value, 2)


def line_8_and_9(line5: float, line7: float, labeled: dict[int, float]) -> tuple[float, float]:
    if line5 > line7:
        line8 = labeled.get(8, round(line5 - line7, 2))
        line9 = labeled.get(9, 0.0)
    else:
        line8 = labeled.get(8, 0.0)
        line9 = labeled.get(9, round(line7 - line5, 2))
    return line8, line9
