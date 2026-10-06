from __future__ import annotations

import re

from services.pp30_amount_service import line_money, money_amounts

_LINE6_RE = re.compile(r"(?<!\d)6\.\s*รวม")
_LINE7_RE = re.compile(r"(?<!\d)7\.\s*เงินเพิ่ม")
_LINE8_MARKER = "และเงินเพิ่ม"


def extract_line_6_and_7(text: str) -> tuple[float, float] | None:
    tax: float | None = None
    surcharge = 0.0
    for raw in (text or "").splitlines():
        if _LINE8_MARKER in raw:
            continue
        if _LINE6_RE.search(raw):
            amounts = money_amounts(raw)
            if amounts:
                tax = amounts[-1]
            continue
        if _LINE7_RE.search(raw):
            amount = line_money(raw, allow_zero=True)
            surcharge = 0.0 if amount is None else amount
    if tax is None:
        return None
    return tax, surcharge
