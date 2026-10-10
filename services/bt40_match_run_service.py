from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.bt40_form_config import Bt40FormConfig
from models.bt40_matched_job import Bt40MatchedJob
from services.bt40_insert_service import Bt40InsertService
from services.bt40_pdf_service import Bt40PdfService
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import tidy_name
from services.pp30_match_service import Pp30MatchService


class Bt40MatchRunService:
    @staticmethod
    def run(
        form_config: Bt40FormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[Bt40MatchedJob]:
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        lookup = Pp30MatchService.lookup(companies)
        total = len(form_config.pdf_files)
        jobs: list[Bt40MatchedJob] = []
        inserted = 0
        for index, pdf_path in enumerate(form_config.pdf_files, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            try:
                record = Bt40PdfService.load_record(pdf_path)
            except Exception as exc:
                on_status(f"{pdf_path.name}: {exc}")
                on_progress(index, total)
                continue
            if not record.company_name:
                on_status(UI_TEXT["pp30_pdf_name_missing"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            company = Pp30MatchService.match_lookup(record.company_name, lookup)
            if company is None:
                on_status(
                    UI_TEXT["pp30_unmatched"].format(
                        pdf_name=record.company_name,
                        path=pdf_path.name,
                    )
                )
                on_progress(index, total)
                continue
            on_status(
                UI_TEXT["pp30_match_log"].format(
                    pdf_name=record.company_name,
                    shop_name=tidy_name(company.shop_name),
                )
            )
            jobs.append(
                Bt40MatchedJob(
                    pdf_path=record.pdf_path,
                    pdf_name=record.company_name,
                    company=company,
                    form_values=record.form_values,
                )
            )
            if record.form_values is None:
                on_status(UI_TEXT["pp30_values_missing"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            pdf_period = record.form_values.period
            if (
                pdf_period is None
                or not pdf_period.is_valid
                or pdf_period.month != form_config.period.month
                or pdf_period.year != form_config.period.year
            ):
                on_status(
                    UI_TEXT["bt40_skip_period_log"].format(
                        name=record.company_name,
                        pdf=pdf_period.text if pdf_period and pdf_period.is_valid else "-",
                        ui=form_config.period.text,
                    )
                )
                on_progress(index, total)
                continue
            if not record.form_values.has_receipt and not record.form_values.has_tax:
                on_status(UI_TEXT["bt40_skip_zero_log"].format(name=record.company_name))
                on_progress(index, total)
                continue
            if record.form_values.has_tax and not record.form_values.pv_date:
                on_status(UI_TEXT["bt40_skip_date_log"].format(name=record.company_name))
                if not record.form_values.has_receipt:
                    on_progress(index, total)
                    continue
            try:
                vouchers = Bt40InsertService.vouchers(record.form_values, form_config)
                if not vouchers:
                    on_status(UI_TEXT["bt40_skip_zero_log"].format(name=record.company_name))
                    on_progress(index, total)
                    continue
                existing_date = ExpressJournalDateService.first_existing_voucher_date(
                    company.folder, vouchers
                )
                if existing_date:
                    on_status(
                        UI_TEXT["pp30_skip_date_exists_log"].format(
                            name=record.company_name,
                            date=existing_date,
                        )
                    )
                    on_progress(index, total)
                    continue
                name = Bt40InsertService.insert(company.folder, record.form_values, form_config)
                if name:
                    inserted += 1
                    on_status(
                        UI_TEXT["bt40_insert_log"].format(
                            shop=tidy_name(company.shop_name),
                            detail=name,
                        )
                    )
            except Exception as exc:
                on_status(f"{record.company_name}: {exc}")
            on_progress(index, total)
        on_status(UI_TEXT["pp30_insert_done"].format(inserted=inserted, total=total))
        return jobs
