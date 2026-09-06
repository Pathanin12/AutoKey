from __future__ import annotations

from models.pp30_form_values import Pp30FormValues
from models.pp30_payment_kind import Pp30PaymentKind

_AMOUNT_TOLERANCE = 0.005


class Pp30ClassifyService:
    @staticmethod
    def classify(values: Pp30FormValues) -> Pp30PaymentKind:
        if values.is_all_zero:
            return Pp30PaymentKind.skip_zero()
        if _is_new_shop(values):
            return Pp30PaymentKind.no_pay_new_shop()
        if _is_pay_like(values) and _has_penalty(values):
            return Pp30PaymentKind.penalty()
        if _is_pay_like(values):
            return Pp30PaymentKind.pay()
        if _greater(values.line_10, values.line_8):
            return Pp30PaymentKind.no_pay_normal()
        return Pp30PaymentKind.unknown()


def _is_new_shop(values: Pp30FormValues) -> bool:
    return (
        _eq(values.line_5, 0.0)
        and _eq(values.line_7, values.line_9)
        and _eq(values.line_9, values.line_12)
    )


def _is_pay_like(values: Pp30FormValues) -> bool:
    if _greater(values.line_8, values.line_10):
        return True
    return _has(values.line_8) and not _has(values.line_10)


def _has_penalty(values: Pp30FormValues) -> bool:
    return _has(values.line_13) or _has(values.line_14)


def _eq(left: float, right: float) -> bool:
    return abs(left - right) < _AMOUNT_TOLERANCE


def _greater(left: float, right: float) -> bool:
    return left - right > _AMOUNT_TOLERANCE


def _has(value: float) -> bool:
    return value > _AMOUNT_TOLERANCE
