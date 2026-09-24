from __future__ import annotations

from pathlib import Path

from constants.date_utils import express_date_to_dbf, format_express_pv_date, is_complete_express_date
from constants.routes import GLJNL_FILE_NAMES
from models.express_journal_date import ExpressJournalDate
from models.journal_voucher import JournalVoucher
from services.dbf_table_service import DbfTableService


class ExpressJournalDateService:
    @staticmethod
    def list_dates(folder: Path) -> list[ExpressJournalDate]:
        path = _gljnl_path(folder)
        if path is None:
            return []
        dates: list[ExpressJournalDate] = []
        for row in DbfTableService.read_records(path):
            voudat = (row.get("VOUDAT") or "").strip()
            if voudat:
                dates.append(ExpressJournalDate(voudat=voudat))
        return dates

    @staticmethod
    def has_express_date(folder: Path, voudat_express: str) -> bool:
        if not is_complete_express_date(voudat_express):
            return False
        target = express_date_to_dbf(voudat_express)
        return any(item.voudat == target for item in ExpressJournalDateService.list_dates(folder))

    @staticmethod
    def first_existing_voucher_date(folder: Path, vouchers: list[JournalVoucher]) -> str | None:
        seen: list[str] = []
        for voucher in vouchers:
            if not voucher.lines:
                continue
            date = format_express_pv_date(voucher.voudat_express)
            if not date or date in seen:
                continue
            seen.append(date)
            if ExpressJournalDateService.has_express_date(folder, date):
                return date
        return None


def _gljnl_path(folder: Path) -> Path | None:
    for name in GLJNL_FILE_NAMES:
        path = folder / name
        if path.exists():
            return path
    return None
