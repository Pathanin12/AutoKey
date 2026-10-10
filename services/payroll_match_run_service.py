from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.payroll_form_config import PayrollFormConfig
from models.payroll_matched_job import PayrollMatchedJob
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import tidy_name
from services.payroll_excel_service import PayrollExcelService
from services.payroll_insert_service import PayrollInsertService
from services.pp30_match_service import Pp30MatchService


class PayrollMatchRunService:
    @staticmethod
    def run(
        form_config: PayrollFormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[PayrollMatchedJob]:
        rows = PayrollExcelService.load_rows(form_config.excel_path, form_config.period)
        on_status(UI_TEXT["payroll_excel_total"].format(count=len(rows)))
        if not rows:
            raise ValueError(UI_TEXT["payroll_excel_none"])
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        total = len(rows)
        jobs: list[PayrollMatchedJob] = []
        inserted = 0
        for index, row in enumerate(rows, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            company = Pp30MatchService.match_names(
                row.match_names, companies, form_config.period.year
            )
            if company is None:
                on_status(UI_TEXT["payroll_unmatched"].format(name=row.legal_name))
                on_progress(index, total)
                continue
            on_status(
                UI_TEXT["payroll_match_log"].format(
                    excel_name=row.legal_name,
                    shop_name=tidy_name(company.shop_name),
                    folder=company.folder.name,
                )
            )
            jobs.append(PayrollMatchedJob(row=row, company=company))
            if not row.has_salary:
                on_status(UI_TEXT["payroll_skip_zero_log"].format(name=row.legal_name))
                on_progress(index, total)
                continue
            try:
                voucher = PayrollInsertService.voucher(row, form_config)
                _ready, skipped = ExpressJournalDateService.pending(company.folder, [voucher])
                for existing_date, detail in skipped:
                    on_status(
                        UI_TEXT["pp30_skip_date_exists_log"].format(
                            name=row.legal_name,
                            date=existing_date,
                            detail=detail,
                        )
                    )
                if not _ready:
                    on_progress(index, total)
                    continue
                name = PayrollInsertService.insert(company.folder, row, form_config)
                if name:
                    inserted += 1
                    on_status(
                        UI_TEXT["payroll_insert_log"].format(
                            shop=tidy_name(company.shop_name),
                            detail=name,
                        )
                    )
            except Exception as exc:
                on_status(f"{row.legal_name}: {exc}")
            on_progress(index, total)
        on_status(UI_TEXT["ka_tam_insert_done"].format(inserted=inserted, total=total))
        return jobs
