"""ไม่จ่ายตังแบบปกติ — ข้อ 10 มากกว่าข้อ 8 แล้วข้อ 12 = ข้อ 10 - ข้อ 8"""

from __future__ import annotations

from models.pp30_form_values import Pp30FormValues
from services.pp30_amount_service import eq_amount, is_vat_base, line_8_and_9


def matches_no_pay_normal(values: Pp30FormValues) -> bool:
    return values.line_10 - values.line_8 > 0.005


def complete_no_pay_normal_lines(
    line5: float,
    line7: float,
    labeled: dict[int, float],
    amounts: list[float],
) -> dict[str, float] | None:
    line8, line9 = line_8_and_9(line5, line7, labeled)
    line10 = labeled.get(10)
    inferred = _infer_overpay_carry(amounts, line5=line5, line7=line7, line8=line8)
    if line10 is None and inferred is not None:
        line10 = inferred[0]
    if line10 is None or line10 - line8 <= 0.005:
        return None
    line12 = labeled.get(12)
    if line12 is None and inferred is not None and eq_amount(line10, inferred[0]):
        line12 = inferred[1]
    if line12 is None:
        line12 = round(line10 - line8, 2)
    return {
        "vat_sale": line5,
        "vat_purchase": line7,
        "amount_due": labeled.get(11, 0.0),
        "line_8": line8,
        "line_9": line9,
        "line_10": line10,
        "line_12": line12,
        "line_13": labeled.get(13, 0.0),
        "line_14": labeled.get(14, 0.0),
        "line_15": labeled.get(15, 0.0),
    }


def _infer_overpay_carry(
    amounts: list[float],
    *,
    line5: float,
    line7: float,
    line8: float,
) -> tuple[float, float] | None:
    reserved = (line5, line7, line8)
    best: tuple[float, float] | None = None
    for carry in amounts:
        if any(eq_amount(carry, known) for known in reserved):
            continue
        if is_vat_base(carry, amounts):
            continue
        if carry <= line8 + 0.005:
            continue
        refund = round(carry - line8, 2)
        if any(eq_amount(refund, known) for known in reserved):
            continue
        if not any(eq_amount(refund, other) for other in amounts):
            continue
        if best is None or carry > best[0]:
            best = (carry, refund)
    return best
