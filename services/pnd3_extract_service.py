from __future__ import annotations

import re

from services.pp30_amount_service import line_money

_LINE1_RE = re.compile(r"(?<!\d)1\.\s*")
_LINE3_RE = re.compile(r"(?<!\d)3\.\s*เงินเพิ่ม")
_LINE4_MARKER = "และเงินเพิ่ม"


def extract_line_1_and_3(text: str) -> tuple[float, float] | None:
    line1: float | None = None
    line3: float | None = None
    for raw in (text or "").splitlines():
        if _LINE4_MARKER in raw:
            continue
        if _LINE3_RE.search(raw):
            amount = line_money(raw, allow_zero=True)
            line3 = 0.0 if amount is None else amount
            continue
        if "รวมยอดเงินได้ทั้งสิ้น" in raw or (_LINE1_RE.search(raw) and "รวมยอดเงินได้" in raw):
            amount = line_money(raw, allow_zero=True)
            if amount is not None:
                line1 = amount
    if line1 is None:
        return None
    return line1, 0.0 if line3 is None else line3
