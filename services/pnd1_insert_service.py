from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.pnd1_form_config import Pnd1FormConfig
from models.pnd1_form_values import Pnd1FormValues
from services.express_journal_service import ExpressJournalService
from services.pnd1_insert_lines_service import pv_pnd1


class Pnd1InsertService:
    @staticmethod
    def voucher(values: Pnd1FormValues, form: Pnd1FormConfig):
        date = format_express_pv_date(values.pv_date)
        return pv_pnd1(values, date, form.description)

    @staticmethod
    def insert(folder: Path, values: Pnd1FormValues, form: Pnd1FormConfig) -> str:
        voucher = Pnd1InsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
