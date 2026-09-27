from __future__ import annotations

from pathlib import Path
from typing import Callable

from api.income_sbp_api import IncomeSbpApi, pick_report_types, print_all_path
from constants.date_utils import express_date_to_iso
from constants.routes import UI_TEXT
from models.income_form_config import IncomeFormConfig
from models.income_portal_account import IncomePortalAccount
from models.income_portal_session import IncomePortalSession
from services.income_pdf_service import IncomePdfService
from services.income_portal_login_service import IncomePortalLoginService
from services.name_match_service import core_company_name


class IncomeStatementDownloadService:
    @staticmethod
    def download(
        accounts: list[IncomePortalAccount],
        form_config: IncomeFormConfig,
        *,
        on_status: Callable[[str], None],
    ) -> list[Path]:
        folder = form_config.pdf_folder.expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        start_date = express_date_to_iso(form_config.start_date)
        end_date = express_date_to_iso(form_config.end_date)
        saved: list[Path] = []
        for account in accounts:
            try:
                session = IncomePortalLoginService.login(account)
            except ValueError as exc:
                on_status(str(exc))
                continue
            saved.extend(
                IncomeStatementDownloadService._download_account(
                    session, account, folder, start_date, end_date, on_status
                )
            )
        return saved

    @staticmethod
    def _download_account(
        session: IncomePortalSession,
        account: IncomePortalAccount,
        folder: Path,
        start_date: str,
        end_date: str,
        on_status: Callable[[str], None],
    ) -> list[Path]:
        stores = IncomeSbpApi.stores(session.cookies, start_date)
        if not stores:
            on_status(UI_TEXT["income_download_none"].format(name=account.legal_name, store="-"))
            return []
        available = IncomeSbpApi.report_types(session.cookies, start_date, end_date)
        report_types = pick_report_types(available)
        if not report_types:
            on_status(UI_TEXT["income_download_none"].format(name=account.legal_name, store="-"))
            return []
        saved: list[Path] = []
        for store in stores:
            files = IncomeSbpApi.search(
                session.cookies,
                start_date,
                end_date,
                [store.store_id],
                report_types,
            )
            if not files:
                on_status(
                    UI_TEXT["income_download_none"].format(
                        name=account.legal_name,
                        store=store.store_id,
                    )
                )
                continue
            dest = print_all_path(folder, store.store_id)
            IncomeSbpApi.merge(session.cookies, files, dest)
            shop = IncomePdfService.shop_name(dest)
            if shop:
                dest = IncomeStatementDownloadService._save_as_shop(dest, shop)
            saved.append(dest)
            on_status(
                UI_TEXT["income_download_log"].format(
                    name=shop or account.legal_name,
                    store=store.store_id,
                )
            )
        return saved

    @staticmethod
    def _save_as_shop(src: Path, shop_name: str) -> Path:
        dest = print_all_path(src.parent, core_company_name(shop_name) or shop_name)
        if dest.resolve() == src.resolve():
            return src
        if dest.exists():
            dest.unlink()
        return src.replace(dest)
