from __future__ import annotations

from pathlib import Path

from constants.date_utils import express_date_to_dbf, express_month_date_range, format_express_pv_date
from constants.routes import (
    INCOME_PV_BOTH_DESC,
    INCOME_PV_DEPOSIT_DESC,
    INCOME_PV_INSTALL_DESC,
    INCOME_PV_RECEIPT,
    INCOME_PV_TAX_DESC,
    JOURNAL_DOCSTAT,
    VATREC_PURCHASE,
)
from models.express_vat_record import ExpressVatRecord
from models.income_form_config import IncomeFormConfig
from models.income_form_values import IncomeFormValues
from services.express_journal_service import ExpressJournalService
from services.express_vat_service import ExpressVatService
from services.income_pv_insert_lines_service import pv_income_receipt, pv_income_tax
from services.pp30_amount_service import has_amount


class IncomePvInsertService:
    @staticmethod
    def description(values: IncomeFormValues, form: IncomeFormConfig) -> str:
        month, year = values.description_month_year(form.start_date)
        if values.kind == INCOME_PV_RECEIPT:
            return _receipt_description(values, month, year)
        return INCOME_PV_TAX_DESC.format(month=month, year=year, branch=values.branch_last5)

    @staticmethod
    def voucher(values: IncomeFormValues, form: IncomeFormConfig):
        date = format_express_pv_date(values.invoice_date) or form.start_date
        description = IncomePvInsertService.description(values, form)
        if values.kind == INCOME_PV_RECEIPT:
            return pv_income_receipt(values, date, description)
        return pv_income_tax(values, date, description)

    @staticmethod
    def insert(folder: Path, values: IncomeFormValues, form: IncomeFormConfig) -> str:
        voucher = IncomePvInsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        name = ExpressJournalService.insert(folder, voucher)
        date = voucher.voudat_express
        voudat = express_date_to_dbf(date)
        period_start, _end = express_month_date_range(date)
        vat01 = 0.0 if values.kind == INCOME_PV_RECEIPT else round(values.vat_amount, 2)
        amt01 = round(values.total_amount if values.kind == INCOME_PV_RECEIPT else values.base_amount, 2)
        ExpressVatService.insert(
            folder,
            ExpressVatRecord(
                vatrec=VATREC_PURCHASE,
                vatprd=express_date_to_dbf(period_start),
                vatdat=voudat,
                docdat=voudat,
                refnum=values.invoice_number,
                descrp=voucher.description,
                amt01=amt01,
                vat01=vat01,
                taxid=values.tax_id,
                docstat=JOURNAL_DOCSTAT,
                docnum=name,
            ),
        )
        return name


def _receipt_description(values: IncomeFormValues, month: int, year: str) -> str:
    has_deposit = has_amount(values.deposit_amount)
    has_install = has_amount(values.base_amount)
    if has_deposit and has_install:
        return INCOME_PV_BOTH_DESC.format(month=month, year=year)
    if has_deposit:
        return INCOME_PV_DEPOSIT_DESC.format(month=month, year=year, branch=values.branch_last5)
    return INCOME_PV_INSTALL_DESC.format(month=month, year=year, branch=values.branch_last5)
