from __future__ import annotations

from pathlib import Path

from constants.date_utils import express_date_to_dbf, express_month_date_range, format_express_pv_date
from constants.routes import ACCOUNT_INCOME, JOURNAL_DOCSTAT, VATREC_SALE
from models.express_vat_record import ExpressVatRecord
from models.income_form_config import IncomeFormConfig
from models.income_form_values import IncomeFormValues
from services.express_journal_service import ExpressJournalService
from services.express_vat_service import ExpressVatService
from services.income_insert_lines_service import rv_income


class IncomeInsertService:
    @staticmethod
    def description(values: IncomeFormValues, form: IncomeFormConfig) -> str:
        return f"{form.rv_description.strip()}{values.branch_last5}"

    @staticmethod
    def voucher(values: IncomeFormValues, form: IncomeFormConfig):
        date = format_express_pv_date(values.invoice_date)
        return rv_income(values, date, IncomeInsertService.description(values, form))

    @staticmethod
    def insert(folder: Path, values: IncomeFormValues, form: IncomeFormConfig) -> str:
        voucher = IncomeInsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        name = ExpressJournalService.insert(folder, voucher)
        date = format_express_pv_date(values.invoice_date)
        voudat = express_date_to_dbf(date)
        period_start, _end = express_month_date_range(date)
        rest = next((line.amount for line in voucher.lines if line.account == ACCOUNT_INCOME), 0.0)
        ExpressVatService.insert(
            folder,
            ExpressVatRecord(
                vatrec=VATREC_SALE,
                vatprd=express_date_to_dbf(period_start),
                vatdat=voudat,
                docdat=voudat,
                refnum=values.invoice_number,
                descrp=voucher.description,
                amt01=round(rest or (values.total_amount + values.wht_amount - values.vat_amount), 2),
                vat01=round(values.vat_amount, 2),
                taxid=values.tax_id,
                docstat=JOURNAL_DOCSTAT,
                docnum=name,
            ),
        )
        return name
