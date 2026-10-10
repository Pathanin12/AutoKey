from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date, is_complete_express_date
from models.bt40_form_config import Bt40FormConfig
from models.bt40_form_values import Bt40FormValues
from models.journal_voucher import JournalVoucher
from services.bt40_insert_lines_service import pv_bt40, rv_bt40
from services.express_journal_service import ExpressJournalService


class Bt40InsertService:
    @staticmethod
    def vouchers(values: Bt40FormValues, form: Bt40FormConfig) -> list[JournalVoucher]:
        vouchers: list[JournalVoucher] = []
        rv_date = format_express_pv_date(form.rv_date)
        if values.has_receipt and is_complete_express_date(rv_date):
            vouchers.append(rv_bt40(values, rv_date, form.rv_description))
        pv_date = format_express_pv_date(values.pv_date)
        if values.has_tax and is_complete_express_date(pv_date):
            vouchers.append(pv_bt40(values, pv_date, form.pv_description))
        return [voucher for voucher in vouchers if voucher.lines]

    @staticmethod
    def insert(folder: Path, values: Bt40FormValues, form: Bt40FormConfig) -> str:
        names: list[str] = []
        for voucher in Bt40InsertService.vouchers(values, form):
            names.append(ExpressJournalService.insert(folder, voucher))
        return " ".join(names)
