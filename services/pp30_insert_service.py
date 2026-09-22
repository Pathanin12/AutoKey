from __future__ import annotations

from constants.date_utils import format_express_pv_date, jv_date_from_pv_date
from models.journal_voucher import JournalVoucher
from models.pp30_form_config import Pp30FormConfig
from models.pp30_form_values import Pp30FormValues
from models.pp30_payment_kind import Pp30PaymentKind
from services.pp30_insert_lines_service import (
    jv_new_shop,
    jv_no_pay_normal,
    jv_normal,
    jv_pay,
    pv_pay_or_normal,
    pv_penalty,
)


class Pp30InsertService:
    @staticmethod
    def vouchers(kind: Pp30PaymentKind, values: Pp30FormValues, form: Pp30FormConfig) -> list[JournalVoucher]:
        pv_date = format_express_pv_date(values.pv_date)
        jv_date = jv_date_from_pv_date(pv_date)
        if kind.is_new_shop:
            return [jv_new_shop(values, jv_date, form.jv_description)]
        if kind.is_no_pay_normal:
            return [jv_no_pay_normal(values, jv_date, form.jv_description)]
        if kind.is_pay:
            return [
                jv_pay(values, jv_date, form.jv_description),
                pv_pay_or_normal(values, pv_date, form.pv_description),
            ]
        if kind.is_penalty:
            return [
                jv_normal(values, jv_date, form.jv_description),
                pv_penalty(values, pv_date, form.pv_description),
            ]
        if kind.is_normal:
            return [
                jv_normal(values, jv_date, form.jv_description),
                pv_pay_or_normal(values, pv_date, form.pv_description),
            ]
        return []
