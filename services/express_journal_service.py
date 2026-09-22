from __future__ import annotations

from datetime import datetime
from pathlib import Path

from constants.date_utils import dbf_date_today, express_date_to_dbf, voucher_year_month
from constants.routes import (
    GLJNL_FILE_NAMES,
    GLJNLIT_FILE_NAMES,
    JOURNAL_CREBY_DEFAULT,
    JOURNAL_DOCSTAT,
    JOURNAL_SRCJNL,
    JOURNAL_TRNSTAT,
    SEQIT_DEFAULT,
    TRNTYP_CREDIT,
    TRNTYP_DEBIT,
)
from models.journal_voucher import JournalVoucher
from services.cdx_index_service import CdxIndexService
from services.dbf_table_service import DbfTableService
from services.name_match_service import tidy_name


class ExpressJournalService:
    @staticmethod
    def insert(folder: Path, voucher: JournalVoucher) -> str:
        gljnl = _first_file(folder, GLJNL_FILE_NAMES)
        gljnlit = _first_file(folder, GLJNLIT_FILE_NAMES)
        year, month = voucher_year_month(voucher.voudat_express)
        prefix = f"{voucher.prefix}{year}{month}"
        next_seq = _next_seq(gljnl, prefix)
        voucher.voucher = f"{prefix}{next_seq:04d}"
        voudat = express_date_to_dbf(voucher.voudat_express)
        today = dbf_date_today()
        now = datetime.now().strftime("%H%M")
        description = _express_description(voucher.description)
        creby = _creby(gljnl)
        header = {
            "JNLTYP": voucher.jnltyp,
            "VOUDAT": voudat,
            "VOUCHER": voucher.voucher,
            "SRCJNL": JOURNAL_SRCJNL,
            "DESCRP": description,
            "TRNSTAT": JOURNAL_TRNSTAT,
            "DOCSTAT": JOURNAL_DOCSTAT,
            "CREBY": creby,
            "CREDAT": today,
            "USERID": creby,
            "CHGDAT": today,
        }
        recno = DbfTableService.append(gljnl, header)
        cdx = _cdx_path(gljnl)
        if cdx:
            CdxIndexService.insert_key(cdx, {**header, "TRNSTAT": JOURNAL_TRNSTAT}, recno)
        for line in voucher.lines:
            item = {
                "VOUCHER": voucher.voucher,
                "SEQIT": SEQIT_DEFAULT,
                "VOUDAT": voudat,
                "ACCNUM": line.account,
                "DESCRP": description,
                "TRNTYP": TRNTYP_CREDIT if line.is_credit else TRNTYP_DEBIT,
                "AMOUNT": line.amount,
                "CHGDAT": today,
                "CHGTIM": now,
            }
            item_recno = DbfTableService.append(gljnlit, item)
            item_cdx = _cdx_path(gljnlit)
            if item_cdx:
                CdxIndexService.insert_key(item_cdx, item, item_recno)
        return voucher.voucher


def _first_file(folder: Path, names: tuple[str, ...]) -> Path:
    for name in names:
        path = folder / name
        if path.exists():
            return path
    raise FileNotFoundError(names[0])


def _next_seq(gljnl: Path, prefix: str) -> int:
    highest = 0
    for row in DbfTableService.read_records(gljnl):
        voucher = row.get("VOUCHER") or ""
        if voucher.startswith(prefix) and voucher[len(prefix) :].isdigit():
            highest = max(highest, int(voucher[len(prefix) :]))
    return highest + 1


def _creby(gljnl: Path) -> str:
    for row in reversed(DbfTableService.read_records(gljnl)):
        value = (row.get("CREBY") or "").strip()
        if value:
            return value
    return JOURNAL_CREBY_DEFAULT


def _express_description(value: str) -> str:
    return tidy_name(value).replace(" ", "\xa0")


def _cdx_path(dbf_path: Path) -> Path | None:
    for suffix in (".CDX", ".cdx"):
        path = dbf_path.with_name(dbf_path.stem + suffix)
        if path.exists():
            return path
    return None
