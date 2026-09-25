from __future__ import annotations

import re

from services.pp30_amount_service import line_money

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
