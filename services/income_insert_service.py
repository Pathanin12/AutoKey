from __future__ import annotations

from pathlib import Path

from constants.date_utils import express_date_to_dbf, express_month_date_range, express_month_year_label, format_express_pv_date
from constants.routes import (
    ACCOUNT_INCOME,
    ACCOUNT_INCOME_ADVANCE,
    ACCOUNT_INCOME_GOODS,
    INCOME_RV_ADVANCE,
    INCOME_RV_DESC,
    INCOME_RV_GOODS,
    INCOME_RV_TOPIC_ADVANCE,
    INCOME_RV_TOPIC_GOODS,
    INCOME_RV_TOPIC_TAX,
    JOURNAL_DOCSTAT,
    VATREC_SALE,
)
from models.express_vat_record import ExpressVatRecord
from models.income_form_config import IncomeFormConfig
from models.income_form_values import IncomeFormValues
from services.express_journal_service import ExpressJournalService
from services.express_vat_service import ExpressVatService
from services.income_insert_lines_service import rv_income


_TOPICS = {
    INCOME_RV_GOODS: INCOME_RV_TOPIC_GOODS,
    INCOME_RV_ADVANCE: INCOME_RV_TOPIC_ADVANCE,
}


class IncomeInsertService:
    @staticmethod
    def description(values: IncomeFormValues, form: IncomeFormConfig) -> str:
        month, year = express_month_year_label(form.start_date)
        topic = _TOPICS.get(values.kind, INCOME_RV_TOPIC_TAX)
        return INCOME_RV_DESC.format(
            topic=topic,
            month=month,
            year=year,
            branch=values.branch_last5,
        )

    @staticmethod
    def voucher(values: IncomeFormValues, form: IncomeFormConfig):
        date = format_express_pv_date(values.invoice_date) or form.start_date
        return rv_income(values, date, IncomeInsertService.description(values, form))

    @staticmethod
    def insert(folder: Path, values: IncomeFormValues, form: IncomeFormConfig) -> str:
        voucher = IncomeInsertService.voucher(values, form)
        if not voucher.lines:
            return ""
        name = ExpressJournalService.insert(folder, voucher)
        date = voucher.voudat_express
        voudat = express_date_to_dbf(date)
        period_start, _end = express_month_date_range(date)
        amt01, vat01 = _vat_amounts(values, voucher)
        ExpressVatService.insert(
            folder,
            ExpressVatRecord(
                vatrec=VATREC_SALE,
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


def _vat_amounts(values: IncomeFormValues, voucher) -> tuple[float, float]:
    if values.kind == INCOME_RV_GOODS:
        line = next((item for item in voucher.lines if item.account == ACCOUNT_INCOME_GOODS), None)
        amount = line.amount if line else round(values.total_amount + values.wht_amount, 2)
        return amount, 0.0
    if values.kind == INCOME_RV_ADVANCE:
        line = next((item for item in voucher.lines if item.account == ACCOUNT_INCOME_ADVANCE), None)
        return line.amount if line else round(values.total_amount, 2), 0.0
    rest = next((line.amount for line in voucher.lines if line.account == ACCOUNT_INCOME), 0.0)
    return (
        round(rest or (values.total_amount + values.wht_amount - values.vat_amount), 2),
        round(values.vat_amount, 2),
    )
