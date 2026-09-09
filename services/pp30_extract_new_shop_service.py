"""ไม่จ่ายตังเปิดร้านใหม่ — ข้อ 5 = 0 และ ข้อ 7 = ข้อ 9 = ข้อ 12"""

from __future__ import annotations

from collections import Counter

from models.pp30_form_values import Pp30FormValues
from services.pp30_amount_service import eq_amount, has_amount, is_vat_base, money_amounts


def matches_new_shop(values: Pp30FormValues) -> bool:
    return (
        eq_amount(values.line_5, 0.0)
        and eq_amount(values.line_7, values.line_9)
        and eq_amount(values.line_9, values.line_12)
    )


def complete_new_shop_lines(
    line5: float | None,
    line7: float | None,
    labeled: dict[int, float],
    text: str,
) -> dict[str, float] | None:
    if line5 is not None and has_amount(line5):
        return None
    inferred = _infer_purchase(text, labeled, line7)
    if inferred is None:
        return None
    sale, purchase = inferred
    line9 = labeled.get(9, purchase)
    line12 = labeled.get(12, purchase)
    if not eq_amount(purchase, line9) or not eq_amount(line9, line12):
        return None
    return {
        "vat_sale": sale,
        "vat_purchase": purchase,
        "amount_due": 0.0,
        "line_8": labeled.get(8, 0.0),
        "line_9": line9,
        "line_10": labeled.get(10, 0.0),
        "line_12": line12,
        "line_13": labeled.get(13, 0.0),
        "line_14": labeled.get(14, 0.0),
        "line_15": labeled.get(15, 0.0),
    }


def _infer_purchase(
    text: str,
    labeled: dict[int, float],
    line7: float | None,
) -> tuple[float, float] | None:
    purchase = labeled.get(7, line7) if line7 is not None else labeled.get(7)
    line9 = labeled.get(9)
    line12 = labeled.get(12)
    if purchase is not None and line9 is not None and eq_amount(purchase, line9):
        if line12 is None or eq_amount(purchase, line12):
            return 0.0, purchase
    line5 = labeled.get(5)
    if purchase is not None and line5 is not None and eq_amount(line5, 0.0):
        return 0.0, purchase
    amounts = money_amounts(text)
    triples = sorted(
        (amount for amount, count in Counter(amounts).items() if count >= 3),
        reverse=True,
    )
    for amount in triples:
        if is_vat_base(amount, amounts):
            continue
        return 0.0, amount
    return None
