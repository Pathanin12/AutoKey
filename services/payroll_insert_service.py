from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.payroll_form_config import PayrollFormConfig
from models.payroll_row import PayrollRow
from services.express_journal_service import ExpressJournalService
from services.payroll_insert_lines_service import pv_payroll


class PayrollInsertService:
    @staticmethod
    def voucher(row: PayrollRow, form: PayrollFormConfig):
        date = format_express_pv_date(form.pv_date)
        return pv_payroll(row, date, form.description)

    @staticmethod
    def insert(folder: Path, row: PayrollRow, form: PayrollFormConfig) -> str:
        voucher = PayrollInsertService.voucher(row, form)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
