from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date, is_complete_express_date
from models.journal_voucher import JournalVoucher
from models.pnd2_form_config import Pnd2FormConfig
from models.pnd2_form_values import Pnd2FormValues
from services.express_journal_service import ExpressJournalService
from services.pnd2_insert_lines_service import pv_pnd2, pv_pnd2_tax


class Pnd2InsertService:
    @staticmethod
    def vouchers(values: Pnd2FormValues, form: Pnd2FormConfig) -> list[JournalVoucher]:
        items: list[JournalVoucher] = []
        dividend = pv_pnd2(values, format_express_pv_date(form.pv_date), values.description)
        if dividend.lines:
            items.append(dividend)
        tax_date = format_express_pv_date(values.pv_date)
        if (
            is_complete_express_date(tax_date)
            and values.period is not None
            and values.period.is_valid
        ):
            tax = pv_pnd2_tax(values, tax_date, values.tax_description)
            if tax.lines:
                items.append(tax)
        return items

    @staticmethod
    def insert(folder: Path, values: Pnd2FormValues, form: Pnd2FormConfig) -> str:
        names = [
            ExpressJournalService.insert(folder, voucher)
            for voucher in Pnd2InsertService.vouchers(values, form)
            if voucher.lines
        ]
        return " ".join(names)
