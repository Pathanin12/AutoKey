from __future__ import annotations

from pathlib import Path

from constants.date_utils import express_date_to_dbf, format_express_pv_date, is_complete_express_date
from constants.routes import JOURNAL_DOCSTAT, VATREC_PURCHASE
from models.express_vat_record import ExpressVatRecord
from models.journal_voucher import JournalVoucher
from models.pnd2_form_config import Pnd2FormConfig
from models.pnd2_form_values import Pnd2FormValues
from services.express_journal_service import ExpressJournalService
from services.express_vat_service import ExpressVatService
from services.pnd2_insert_lines_service import pv_pnd2


class Pnd2InsertService:
    @staticmethod
    def voucher(values: Pnd2FormValues, form: Pnd2FormConfig) -> JournalVoucher:
        date = format_express_pv_date(values.pv_date)
        return pv_pnd2(values, date, values.description)

    @staticmethod
    def tax_vat_record(
        values: Pnd2FormValues, voucher: JournalVoucher, docnum: str
    ) -> ExpressVatRecord | None:
        if values.period is None or not values.period.is_valid:
            return None
        if not voucher.lines:
            return None
        period_start = f"01/{values.period.month:02d}/{values.period.year:02d}"
        voudat = express_date_to_dbf(voucher.voudat_express)
        return ExpressVatRecord(
            vatrec=VATREC_PURCHASE,
            vatprd=express_date_to_dbf(period_start),
            vatdat=voudat,
            docdat=voudat,
            docnum=docnum,
            refnum="",
            descrp=voucher.description,
            amt01=round(values.income_amount, 2),
            vat01=round(values.tax_withheld, 2),
            taxid="",
            docstat=JOURNAL_DOCSTAT,
        )

    @staticmethod
    def insert(folder: Path, values: Pnd2FormValues, form: Pnd2FormConfig) -> str:
        voucher = Pnd2InsertService.voucher(values, form)
        if not voucher.lines or not is_complete_express_date(voucher.voudat_express):
            return ""
        name = ExpressJournalService.insert(folder, voucher)
        record = Pnd2InsertService.tax_vat_record(values, voucher, name)
        if record is not None:
            ExpressVatService.insert(folder, record)
        return name
