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
from services.pnd2_insert_lines_service import pv_pnd2, pv_pnd2_tax


class Pnd2InsertService:
    @staticmethod
    def vouchers(values: Pnd2FormValues, form: Pnd2FormConfig) -> list[JournalVoucher]:
        items: list[JournalVoucher] = []
        dividend = pv_pnd2(values, format_express_pv_date(form.pv_date), values.description)
        if dividend.lines:
            items.append(dividend)
        tax_date = format_express_pv_date(values.pv_date)
        if (
            is_complete_express_date(tax_date)
            and values.period is not None
            and values.period.is_valid
        ):
            tax = pv_pnd2_tax(values, tax_date, values.tax_description)
            if tax.lines:
                items.append(tax)
        return items

    @staticmethod
    def insert_voucher(folder: Path, voucher: JournalVoucher, values: Pnd2FormValues) -> str:
        name = ExpressJournalService.insert(folder, voucher)
        record = Pnd2InsertService.tax_vat_record(values, voucher, name)
        if record is not None:
            ExpressVatService.insert(folder, record)
        return name

    @staticmethod
    def tax_vat_record(
        values: Pnd2FormValues, voucher: JournalVoucher, docnum: str
    ) -> ExpressVatRecord | None:
        if voucher.description != values.tax_description:
            return None
        if values.period is None or not values.period.is_valid:
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
        names = [
            Pnd2InsertService.insert_voucher(folder, voucher, values)
            for voucher in Pnd2InsertService.vouchers(values, form)
            if voucher.lines
        ]
        return " ".join(names)
