from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.pnd1_form_config import Pnd1FormConfig
from models.pnd1_matched_job import Pnd1MatchedJob
from services.express_journal_date_service import ExpressJournalDateService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import tidy_name
from services.pnd1_insert_service import Pnd1InsertService
from services.pnd1_pdf_service import Pnd1PdfService
from services.pp30_match_service import Pp30MatchService


class Pnd1MatchRunService:
    @staticmethod
    def run(
        form_config: Pnd1FormConfig,
        express_data_dir: Path,
        *,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[Pnd1MatchedJob]:
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        total = len(form_config.pdf_files)
        jobs: list[Pnd1MatchedJob] = []
        inserted = 0
        for index, pdf_path in enumerate(form_config.pdf_files, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            try:
                record = Pnd1PdfService.load_record(pdf_path)
            except Exception as exc:
                on_status(f"{pdf_path.name}: {exc}")
                on_progress(index, total)
                continue
            if not record.company_name:
                on_status(UI_TEXT["pp30_pdf_name_missing"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            company = Pp30MatchService.match_name(
                record.company_name, companies, form_config.period.year
            )
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
                    folder=company.folder.name,
                )
            )
            jobs.append(
                Pnd1MatchedJob(
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
            if not record.form_values.has_tax and not record.form_values.has_surcharge:
                on_status(UI_TEXT["pnd1_skip_zero_log"].format(name=record.company_name))
                on_progress(index, total)
                continue
            try:
                voucher = Pnd1InsertService.voucher(record.form_values, form_config)
                _ready, skipped = ExpressJournalDateService.pending(company.folder, [voucher])
                for existing_date, detail in skipped:
                    on_status(
                        UI_TEXT["pp30_skip_date_exists_log"].format(
                            name=record.company_name,
                            date=existing_date,
                            detail=detail,
                        )
                    )
                if not _ready:
                    on_progress(index, total)
                    continue
                name = Pnd1InsertService.insert(company.folder, record.form_values, form_config)
                if name:
                    inserted += 1
                    on_status(
                        UI_TEXT["pnd1_insert_log"].format(
                            shop=tidy_name(company.shop_name),
                            detail=name,
                        )
                    )
            except Exception as exc:
                on_status(f"{record.company_name}: {exc}")
            on_progress(index, total)
        on_status(UI_TEXT["pp30_insert_done"].format(inserted=inserted, total=total))
        return jobs
