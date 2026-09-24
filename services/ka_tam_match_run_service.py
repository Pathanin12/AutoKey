from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.ka_tam_form_config import KaTamFormConfig
from models.ka_tam_matched_job import KaTamMatchedJob
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.ka_tam_excel_service import KaTamExcelService
from services.ka_tam_insert_service import KaTamInsertService
from services.name_match_service import tidy_name
from services.pp30_amount_service import has_amount
from services.pp30_match_service import Pp30MatchService


class KaTamMatchRunService:
    @staticmethod
    def run(
        form_config: KaTamFormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[KaTamMatchedJob]:
        rows = KaTamExcelService.load_rows(form_config.excel_path)
        on_status(UI_TEXT["ka_tam_excel_total"].format(count=len(rows)))
        if not rows:
            raise ValueError(UI_TEXT["ka_tam_excel_none"])
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        lookup = Pp30MatchService.lookup(companies)
        total = len(rows)
        jobs: list[KaTamMatchedJob] = []
        inserted = 0
        for index, row in enumerate(rows, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            company = Pp30MatchService.match_lookup(row.legal_name, lookup)
            if company is None:
                on_status(UI_TEXT["ka_tam_unmatched"].format(name=row.legal_name))
                on_progress(index, total)
                continue
            on_status(
                UI_TEXT["ka_tam_match_log"].format(
                    excel_name=row.legal_name,
                    shop_name=tidy_name(company.shop_name),
                )
            )
            jobs.append(KaTamMatchedJob(row=row, company=company))
            if not has_amount(row.service_amount):
                on_status(UI_TEXT["ka_tam_skip_zero_log"].format(name=row.legal_name))
                on_progress(index, total)
                continue
            try:
                voucher = KaTamInsertService.voucher(row, form_config)
                existing_date = ExpressJournalDateService.first_existing_voucher_date(
                    company.folder, [voucher]
                )
                if existing_date:
                    on_status(
                        UI_TEXT["pp30_skip_date_exists_log"].format(
                            name=row.legal_name,
                            date=existing_date,
                        )
                    )
                    on_progress(index, total)
                    continue
                name = KaTamInsertService.insert(company.folder, row, form_config)
                if name:
                    inserted += 1
                    on_status(
                        UI_TEXT["ka_tam_insert_log"].format(
                            shop=tidy_name(company.shop_name),
                            detail=name,
                        )
                    )
            except Exception as exc:
                on_status(f"{row.legal_name}: {exc}")
            on_progress(index, total)
        on_status(UI_TEXT["ka_tam_insert_done"].format(inserted=inserted, total=total))
        return jobs
