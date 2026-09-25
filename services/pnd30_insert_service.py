from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.pnd30_form_config import Pnd30FormConfig
from models.pnd30_form_values import Pnd30FormValues
from services.express_journal_service import ExpressJournalService
from services.pnd30_insert_lines_service import pv_pnd30


class Pnd30InsertService:
    @staticmethod
    def voucher(values: Pnd30FormValues, form: Pnd30FormConfig):
        date = format_express_pv_date(values.pv_date)
        return pv_pnd30(values, date, form.description)

    @staticmethod
    def insert(folder: Path, values: Pnd30FormValues, form: Pnd30FormConfig) -> str:
        voucher = Pnd30InsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
