from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.pnd2_form_config import Pnd2FormConfig
from models.pnd2_form_values import Pnd2FormValues
from services.express_journal_service import ExpressJournalService
from services.pnd2_insert_lines_service import pv_pnd2


class Pnd2InsertService:
    @staticmethod
    def voucher(values: Pnd2FormValues, form: Pnd2FormConfig):
        date = format_express_pv_date(values.pv_date)
        return pv_pnd2(values, date, form.description)

    @staticmethod
    def insert(folder: Path, values: Pnd2FormValues, form: Pnd2FormConfig) -> str:
        voucher = Pnd2InsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
