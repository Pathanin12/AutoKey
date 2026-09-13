"""เสียค่าปรับ — จ่ายตังที่มีข้อ 13 หรือ 14 แล้วข้อ 15 = ข้อ 11 + ข้อ 13 + ข้อ 14"""

from __future__ import annotations

from models.pp30_form_values import Pp30FormValues
from services.pp30_amount_service import eq_amount, has_amount, is_vat_base, line_8_and_9


def matches_penalty(values: Pp30FormValues) -> bool:
    if not has_amount(values.line_13) and not has_amount(values.line_14):
        return False
    return _is_pay_like(values.line_8, values.line_10)


def complete_penalty_lines(
    line5: float,
    line7: float,
    labeled: dict[int, float],
    amounts: list[float],
) -> dict[str, float] | None:
    line13 = labeled.get(13, 0.0)
    line14 = labeled.get(14, 0.0)
    if not has_amount(line13) and not has_amount(line14):
        return None
    line8, line9 = line_8_and_9(line5, line7, labeled)
    line10 = labeled.get(10)
    if line10 is None:
        line10 = _infer_pay_line_10(amounts, line5=line5, line7=line7, line8=line8)
    if line10 is None:
        line10 = 0.0
    if not _is_pay_like(line8, line10):
        return None
    line11, line15 = _penalty_line_11_and_15(line8, line10, line13, line14, labeled)
    return {
        "vat_sale": line5,
        "vat_purchase": line7,
        "amount_due": line11,
        "line_8": line8,
        "line_9": line9,
        "line_10": line10,
        "line_12": labeled.get(12, 0.0),
        "line_13": line13,
        "line_14": line14,
        "line_15": line15,
    }


def _penalty_line_11_and_15(
    line8: float,
    line10: float,
    line13: float,
    line14: float,
    labeled: dict[int, float],
) -> tuple[float, float]:
    computed_11 = round(line8 - line10, 2) if has_amount(line10) else line8
    labeled_11 = labeled.get(11)
    labeled_15 = labeled.get(15)
    penalty = round(line13 + line14, 2)
    if labeled_11 is not None and (
        (labeled_15 is not None and eq_amount(labeled_11, labeled_15))
        or (has_amount(penalty) and eq_amount(labeled_11, round(computed_11 + penalty, 2)))
    ):
        labeled_11 = None
    line11 = labeled_11 if labeled_11 is not None else computed_11
    if labeled_15 is not None:
        line15 = labeled_15
        if labeled_11 is None:
            line11 = round(line15 - line13 - line14, 2)
    else:
        line15 = round(line11 + line13 + line14, 2)
    return line11, line15


def _is_pay_like(line8: float, line10: float) -> bool:
    if line8 - line10 > 0.005:
        return True
    return has_amount(line8) and not has_amount(line10)


def _infer_pay_line_10(
    amounts: list[float],
    *,
    line5: float,
    line7: float,
    line8: float,
) -> float | None:
    reserved = (line5, line7, line8)
    best: float | None = None
    for carry in amounts:
        if any(eq_amount(carry, known) for known in reserved):
            continue
        if is_vat_base(carry, amounts):
            continue
        if carry >= line8 - 0.005:
            continue
        due = round(line8 - carry, 2)
        if due <= 0.005:
            continue
        if not any(eq_amount(due, other) for other in amounts):
            continue
        if best is None or carry > best:
            best = carry
    return best
