from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.routes import UI_TEXT
from models.pp30_form_config import Pp30FormConfig
from models.pp30_matched_job import Pp30MatchedJob
from services.express_journal_service import ExpressJournalService
from services.express_shop_index_service import ExpressShopIndexService
from services.name_match_service import tidy_name
from services.pp30_classify_service import Pp30ClassifyService
from services.pp30_insert_service import Pp30InsertService
from services.pp30_match_service import Pp30MatchService
from services.pp30_pdf_service import Pp30PdfService


class Pp30MatchRunService:
    @staticmethod
    def run(
        pdf_files: list[Path],
        express_data_dir: Path,
        *,
        form_config: Pp30FormConfig,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        should_stop: Callable[[], bool] | None = None,
    ) -> list[Pp30MatchedJob]:
        companies = ExpressShopIndexService().load(express_data_dir)
        on_status(UI_TEXT["pp30_shops_total"].format(count=len(companies)))
        if not companies:
            raise ValueError(UI_TEXT["pp30_shops_none"])
        lookup = Pp30MatchService.lookup(companies)
        total = len(pdf_files)
        jobs: list[Pp30MatchedJob] = []
        matched = 0
        inserted = 0
        for index, pdf_path in enumerate(pdf_files, start=1):
            if should_stop and should_stop():
                break
            on_progress(index - 1, total)
            try:
                record = Pp30PdfService.load_record(pdf_path)
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
            matched += 1
            on_status(
                UI_TEXT["pp30_match_log"].format(
                    pdf_name=record.company_name,
                    shop_name=tidy_name(company.shop_name),
                )
            )
            if record.form_values is None:
                on_status(UI_TEXT["pp30_values_missing"].format(path=pdf_path.name))
                on_progress(index, total)
                continue
            kind = Pp30ClassifyService.classify(record.form_values)
            on_status(UI_TEXT["pp30_kind_log"].format(kind=kind.label))
            job = Pp30MatchedJob(
                pdf_path=record.pdf_path,
                pdf_name=record.company_name,
                company=company,
                form_values=record.form_values,
                kind=kind,
            )
            jobs.append(job)
            if kind.is_skip:
                on_status(UI_TEXT["pp30_skip_zero_log"].format(name=record.company_name))
                on_progress(index, total)
                continue
            if form_config.run_mode.is_special and not kind.runs_on_special:
                on_status(UI_TEXT["pp30_skip_mode_log"].format(kind=kind.label))
                on_progress(index, total)
                continue
            if not form_config.run_mode.is_special and not kind.runs_on_normal:
                on_status(UI_TEXT["pp30_skip_mode_log"].format(kind=kind.label))
                on_progress(index, total)
                continue
            try:
                vouchers = Pp30InsertService.vouchers(kind, record.form_values, form_config)
                names: list[str] = []
                for voucher in vouchers:
                    if not voucher.lines:
                        continue
                    names.append(ExpressJournalService.insert(company.folder, voucher))
                if names:
                    inserted += 1
                    on_status(
                        UI_TEXT["pp30_insert_log"].format(
                            shop=tidy_name(company.shop_name),
                            kind=kind.label,
                            detail=" ".join(names),
                        )
                    )
                else:
                    on_status(UI_TEXT["pp30_skip_mode_log"].format(kind=kind.label))
            except Exception as exc:
                on_status(f"{record.company_name}: {exc}")
            on_progress(index, total)
        on_status(UI_TEXT["pp30_match_done"].format(matched=matched, total=total))
        on_status(UI_TEXT["pp30_insert_done"].format(inserted=inserted, total=total))
        return jobs
