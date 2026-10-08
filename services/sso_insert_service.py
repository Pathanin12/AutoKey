from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date
from models.sso_form_config import SsoFormConfig
from models.sso_form_values import SsoFormValues
from services.express_journal_service import ExpressJournalService
from services.sso_insert_lines_service import pv_sso


class SsoInsertService:
    @staticmethod
    def voucher(values: SsoFormValues, form: SsoFormConfig, *, dup_n: int | None = None):
        date = format_express_pv_date(values.pv_date)
        return pv_sso(values, date, form.description_for(dup_n))

    @staticmethod
    def insert(
        folder: Path, values: SsoFormValues, form: SsoFormConfig, *, dup_n: int | None = None
    ) -> str:
        voucher = SsoInsertService.voucher(values, form, dup_n=dup_n)
        if not voucher.lines:
            return ""
        return ExpressJournalService.insert(folder, voucher)
