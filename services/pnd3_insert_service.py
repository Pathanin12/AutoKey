from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.pnd3_form_config import Pnd3FormConfig
from models.pnd3_form_values import Pnd3FormValues
from services.express_journal_service import ExpressJournalService
from services.pnd3_insert_lines_service import pv_pnd3


class Pnd3InsertService:
    @staticmethod
    def voucher(values: Pnd3FormValues, form: Pnd3FormConfig):
        date = format_express_pv_date(values.pv_date)
        return pv_pnd3(values, date, form.description)

    @staticmethod
    def insert(folder: Path, values: Pnd3FormValues, form: Pnd3FormConfig) -> str:
        voucher = Pnd3InsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
