from __future__ import annotations

from pathlib import Path

from constants.date_utils import express_date_to_dbf, express_month_date_range, format_express_pv_date
from constants.routes import JOURNAL_DOCSTAT, VATREC_PURCHASE
from models.express_vat_record import ExpressVatRecord
from models.ka_tam_form_config import KaTamFormConfig
from models.ka_tam_row import KaTamRow
from services.express_journal_service import ExpressJournalService
from services.express_vat_service import ExpressVatService
from services.ka_tam_insert_lines_service import pv_ka_tam


class KaTamInsertService:
    @staticmethod
    def voucher(row: KaTamRow, form: KaTamFormConfig):
        date = format_express_pv_date(form.pv_date)
        return pv_ka_tam(row, date, form.description)

    @staticmethod
    def invoice_number(row: KaTamRow) -> str:
        return (row.invoice_number or "").strip().replace("\r", "").replace("\n", "")

    @staticmethod
    def tax_payer_id(form: KaTamFormConfig) -> str:
        return (form.tax_payer_id or "").strip().replace("\r", "").replace("\n", "")

    @staticmethod
    def insert(folder: Path, row: KaTamRow, form: KaTamFormConfig) -> str:
        voucher = KaTamInsertService.voucher(row, form)
        if not voucher.lines:
            return ""
        name = ExpressJournalService.insert(folder, voucher)
        voudat = express_date_to_dbf(form.pv_date)
        period_start, _end = express_month_date_range(form.pv_date)
        ExpressVatService.insert(
            folder,
            ExpressVatRecord(
                vatrec=VATREC_PURCHASE,
                vatprd=express_date_to_dbf(period_start),
                vatdat=voudat,
                docdat=voudat,
                docnum=name,
                refnum=KaTamInsertService.invoice_number(row),
                descrp=form.description,
                amt01=round(row.service_amount, 2),
                vat01=round(row.vat_amount, 2),
                taxid=KaTamInsertService.tax_payer_id(form),
                docstat=JOURNAL_DOCSTAT,
            ),
        )
        return name
