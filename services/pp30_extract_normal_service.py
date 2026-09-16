"""แบบปกติ — ไม่มีข้อ 10 จึงไม่ใช่จ่ายตังหรือเสียค่าปรับ"""

from __future__ import annotations

from models.pp30_form_values import Pp30FormValues
from services.pp30_amount_service import has_amount, line_8_and_9


def matches_normal(values: Pp30FormValues) -> bool:
    return not has_amount(values.line_10)


def complete_normal_lines(
    line5: float,
    line7: float,
    labeled: dict[int, float],
    amounts: list[float],
) -> dict[str, float] | None:
    del amounts
    line8, line9 = line_8_and_9(line5, line7, labeled)
    line10 = labeled.get(10, 0.0)
    if has_amount(line10):
        return None
    line11 = labeled.get(11)
    if line11 is None:
        line11 = line8
    return {
        "vat_sale": line5,
        "vat_purchase": line7,
        "amount_due": line11,
        "line_8": line8,
        "line_9": line9,
        "line_10": 0.0,
        "line_12": labeled.get(12, 0.0),
        "line_13": labeled.get(13, 0.0),
        "line_14": labeled.get(14, 0.0),
        "line_15": labeled.get(15, 0.0),
    }
