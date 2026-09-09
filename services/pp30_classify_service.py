from __future__ import annotations

from models.pp30_form_values import Pp30FormValues
from models.pp30_payment_kind import Pp30PaymentKind
from services.pp30_extract_new_shop_service import matches_new_shop
from services.pp30_extract_no_pay_normal_service import matches_no_pay_normal
from services.pp30_extract_pay_service import matches_pay
from services.pp30_extract_penalty_service import matches_penalty


class Pp30ClassifyService:
    @staticmethod
    def classify(values: Pp30FormValues) -> Pp30PaymentKind:
        if values.is_all_zero:
            return Pp30PaymentKind.skip_zero()
        if matches_new_shop(values):
            return Pp30PaymentKind.no_pay_new_shop()
        if matches_penalty(values):
            return Pp30PaymentKind.penalty()
        if matches_pay(values):
            return Pp30PaymentKind.pay()
        if matches_no_pay_normal(values):
            return Pp30PaymentKind.no_pay_normal()
        return Pp30PaymentKind.unknown()
