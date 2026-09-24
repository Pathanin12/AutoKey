from __future__ import annotations

from pathlib import Path

from constants.date_utils import format_express_pv_date, is_complete_express_date, same_calendar_date
from constants.routes import GLJNL_FILE_NAMES, VOUCHER_JV_PREFIX, VOUCHER_PV_PREFIX
from models.express_journal_date import ExpressJournalDate
from models.journal_voucher import JournalVoucher
from services.dbf_table_service import DbfTableService
from services.name_match_service import tidy_name


class ExpressJournalDateService:
    @staticmethod
    def list_dates(folder: Path) -> list[ExpressJournalDate]:
        path = _gljnl_path(folder)
        if path is None:
            return []
        dates: list[ExpressJournalDate] = []
        for row in DbfTableService.read_records(path):
            voucher = (row.get("VOUCHER") or "").strip()
            voudat = (row.get("VOUDAT") or "").strip()
            if voudat and _is_jv_or_pv(voucher):
                dates.append(
                    ExpressJournalDate(
                        voudat=voudat,
                        voucher=voucher,
                        descrp=(row.get("DESCRP") or "").strip(),
                    )
                )
        return dates

    @staticmethod
    def has_express_date(folder: Path, voudat_express: str, description: str = "") -> bool:
        if not is_complete_express_date(voudat_express):
            return False
        return any(
            same_calendar_date(item.voudat, voudat_express)
            and _same_description(item.descrp, description)
            for item in ExpressJournalDateService.list_dates(folder)
        )

    @staticmethod
    def first_existing_voucher_date(folder: Path, vouchers: list[JournalVoucher]) -> str | None:
        seen: list[tuple[str, str]] = []
        for voucher in vouchers:
            if not voucher.lines:
                continue
            date = format_express_pv_date(voucher.voudat_express)
            key = (date, tidy_name(voucher.description))
            if not date or key in seen:
                continue
            seen.append(key)
            if ExpressJournalDateService.has_express_date(folder, date, voucher.description):
                return date
        return None


def _is_jv_or_pv(voucher: str) -> bool:
    return voucher.startswith(VOUCHER_JV_PREFIX) or voucher.startswith(VOUCHER_PV_PREFIX)


def _same_description(stored: str, wanted: str) -> bool:
    return tidy_name(stored) == tidy_name(wanted)


def _gljnl_path(folder: Path) -> Path | None:
    for name in GLJNL_FILE_NAMES:
        path = folder / name
        if path.exists():
            return path
    return None
