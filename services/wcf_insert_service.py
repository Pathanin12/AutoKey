from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.wcf_form_config import WcfFormConfig
from models.wcf_row import WcfRow
from services.express_journal_service import ExpressJournalService
from services.wcf_insert_lines_service import pv_wcf


class WcfInsertService:
    @staticmethod
    def voucher(row: WcfRow, form: WcfFormConfig, *, dup_n: int | None = None):
        date = format_express_pv_date(row.pv_date)
        return pv_wcf(row, date, form.description_for(row.period, dup_n))

    @staticmethod
    def insert(
        folder: Path, row: WcfRow, form: WcfFormConfig, *, dup_n: int | None = None
    ) -> str:
        voucher = WcfInsertService.voucher(row, form, dup_n=dup_n)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
